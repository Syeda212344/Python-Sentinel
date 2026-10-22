"""Event validation, exact-match detection, alerts, and repeatable classroom scenarios.

Everything marked 'SIMULATED' is synthetic historical data, NOT Windows telemetry.
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from .models import Event, DetectionRule, Alert

DEMO_PREFIX = 'SIMULATED / '
HISTORY_PREFIX = 'SIMULATED HISTORY / '
RULE_CATALOG = [
    ('Failed Login Detection','Detects a failed Windows login attempt.','FAILED_LOGIN','Medium'),
    ('File Change Detection','Detects changes to a monitored file.','FILE_CHANGE','Low'),
    ('Suspicious Process Detection','Flags a controlled suspicious process test event.','SUSPICIOUS_PROCESS','High'),
    ('Privilege Change Detection','Detects unexpected elevation of account privileges.','PRIVILEGE_CHANGE','High'),
    ('Account Lockout Detection','Detects an account lockout security event.','ACCOUNT_LOCKOUT','High'),
    ('Service Interruption Detection','Detects the stopping of an important system service.','SERVICE_STOPPED','Medium'),
    ('Security Log Cleared Detection','Detects a security audit log clearance event.','SECURITY_LOG_CLEARED','High'),
    ('Suspicious Network Activity','Detects a test event reporting unusual network activity.','SUSPICIOUS_NETWORK','Medium'),
    ('Suspicious Email Indicators','Flags submitted email samples with several phishing indicators.','EMAIL_PHISHING_MEDIUM','Medium'),
    ('High-Risk Email Indicators','Flags submitted email samples with multiple strong phishing indicators.','EMAIL_PHISHING_HIGH','High'),
]
SCENARIOS = {
    'NORMAL_LOGIN': ('Successful login','Windows Security Log','student','Normal','A regular successful user login. No rule should match.'),
    'FAILED_LOGIN': ('Failed login','Windows Security Log','testuser','Medium','A failed authentication attempt was recorded.'),
    'FILE_CHANGE': ('Sensitive file modified','Supported File Monitor','admin','Low','The watched file changed; user can review the file event.'),
    'SUSPICIOUS_PROCESS': ('Suspicious process','Windows Process Activity','lab-user','High','A controlled laboratory process generated a suspicious-process test event.'),
    'PRIVILEGE_CHANGE': ('Privilege change','Windows Security Log','admin','High','A test account was assigned additional privileges.'),
    'ACCOUNT_LOCKOUT': ('Account locked','Windows Security Log','testuser','High','An account lockout was reported after repeated failed sign-in attempts.'),
    'SERVICE_STOPPED': ('Service interrupted','Windows System Log','SYSTEM','Medium','A monitored system service stopped unexpectedly.'),
    'SECURITY_LOG_CLEARED': ('Audit log cleared','Windows Security Log','admin','High','A controlled test reported an audit log clearance.'),
    'SUSPICIOUS_NETWORK': ('Unusual network event','Windows Network Activity','testuser','Medium','A simulated network activity pattern was flagged by a configured rule.'),
}


def now_text():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def ensure_rules():
    """Create sample rules without changing rules a student already enabled/disabled."""
    for name, description, pattern, severity in RULE_CATALOG:
        DetectionRule.objects.get_or_create(pattern=pattern, defaults={
            'rule_name':name,'description':description,'severity':severity,'enabled':True})


def validate_event(payload):
    if not isinstance(payload, dict):
        raise ValueError('Event must be a JSON object.')
    event = {}
    for field in ('event_time','source','event_type','message'):
        val = payload.get(field)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f'Missing or invalid required field: {field}.')
        event[field] = val.strip()
    try:
        event['event_time'] = datetime.strptime(event['event_time'], '%Y-%m-%d %H:%M:%S')
    except ValueError as exc:
        raise ValueError('event_time must use YYYY-MM-DD HH:MM:SS.') from exc
    if len(event['source'])>100 or len(event['event_type'])>100 or len(event['message'])>10000:
        raise ValueError('Event source/type/message is too long.')
    for field, limit in (('username',100),('severity',20)):
        val=payload.get(field)
        if val is None or val=='':
            event[field]=None
        elif isinstance(val,str) and len(val.strip())<=limit:
            event[field]=val.strip() or None
        else:
            raise ValueError(f'Invalid field: {field}.')
    return event


def rule_matches(event, rule):
    """One white-box-testable exact, case-insensitive event-type match."""
    return bool(rule.enabled and rule.pattern.strip() and
                rule.pattern.strip().upper()==event.event_type.strip().upper())


@transaction.atomic
def process_event(payload, *, historical=False):
    """Keep event/alert foreign keys consistent in a single SQLite transaction."""
    clean = validate_event(payload)
    event = Event.objects.create(**clean)
    matches = [r for r in DetectionRule.objects.filter(enabled=True) if rule_matches(event, r)]
    ids = []
    for rule in matches:
        alert = Alert.objects.create(
            event=event,rule=rule,
            alert_time=event.event_time if historical else datetime.now().replace(microsecond=0),
            severity=rule.severity,
            description=(f'{rule.rule_name}: {event.message}' if event.event_type.startswith('EMAIL_PHISHING_')
                         else f'{rule.rule_name}: {event.event_type} matched the enabled rule.'),
            status='Open')
        ids.append(alert.alert_id)
    return {'event_id':event.event_id,'alert_ids':ids,'matched_rules':len(ids)}


def generate_scenario(event_type, *, event_time=None, historical=False, batch=False):
    if event_type not in SCENARIOS:
        raise ValueError('Unknown test scenario.')
    label, source, username, severity, message = SCENARIOS[event_type]
    if isinstance(event_time, datetime):
        timestamp = event_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        timestamp = now_text()
    return process_event({
        'event_time':timestamp,
        'source':(HISTORY_PREFIX if historical else DEMO_PREFIX)+source,
        'event_type':event_type,
        'username':username,
        'severity':severity,
        'message':f"{'[BULK HISTORY DATA]' if batch else '[SIMULATED CLASSROOM EVENT]'} {message}"
    },historical=historical)


def seed_historical_data(*, reset=False):
    """Idempotent history anchored to local date; no simulated records are real detections.

    Covers today, yesterday, last 2/30/60 days, and an older custom date range.
    """
    ensure_rules()
    if reset:
        fake = Event.objects.filter(source__startswith=HISTORY_PREFIX, message__startswith='[BULK HISTORY DATA]')
        Alert.objects.filter(event__in=fake).delete()
        fake.delete()
    if Event.objects.filter(source__startswith=HISTORY_PREFIX, message__startswith='[BULK HISTORY DATA]').exists():
        return {'created':0, 'already_seeded':True}
    today = datetime.now().replace(hour=12,minute=0,second=0,microsecond=0)
    types=['FAILED_LOGIN','SUSPICIOUS_PROCESS','FILE_CHANGE','PRIVILEGE_CHANGE',
           'ACCOUNT_LOCKOUT','SERVICE_STOPPED','SECURITY_LOG_CLEARED','SUSPICIOUS_NETWORK']
    count=0
    # Distribute records across 75 days, including today and yesterday.
    for days_ago in range(74,-1,-1):
        base = today-timedelta(days=days_ago)
        generate_scenario('NORMAL_LOGIN', event_time=base.replace(hour=9,minute=10),historical=True,batch=True)
        count+=1
        if days_ago % 2 == 0 or days_ago in (0,1,2,29,30,31,59,60):
            kind=types[days_ago%len(types)]
            generate_scenario(kind,event_time=base.replace(hour=10,minute=15),historical=True,batch=True)
            count+=1
        if days_ago % 5 == 0:
            kind=types[(days_ago+3)%len(types)]
            generate_scenario(kind,event_time=base.replace(hour=15,minute=25),historical=True,batch=True)
            count+=1
    return {'created':count,'already_seeded':False}


def seed_custom_date(date_string):
    try:
        day=datetime.strptime(date_string,'%Y-%m-%d')
    except (ValueError,TypeError) as exc:
        raise ValueError('Provide a valid date using YYYY-MM-DD.') from exc
    if day.date()>datetime.now().date():
        raise ValueError('Choose today or an earlier date for historical test events.')
    if os.getenv('SENTINEL_PUBLIC_DEMO')=='1' and day.date() < (datetime.now()-timedelta(days=365)).date():
        raise ValueError('The public demo accepts historical dates from the past 365 days.')
    # Add a distinctive three-event sequence for that chosen calendar date.
    marker='[CUSTOM DATE SIMULATION]'
    if Event.objects.filter(source__startswith=HISTORY_PREFIX,
            event_time__date=day.date(),message__startswith=marker).exists():
        return {'created':0,'already_seeded':True,'date':date_string}
    ensure_rules()
    for kind,clock in [('NORMAL_LOGIN',(9,0)),('FAILED_LOGIN',(11,15)),('SUSPICIOUS_PROCESS',(14,30))]:
        label,source,username,severity,message=SCENARIOS[kind]
        process_event({'event_time':day.replace(hour=clock[0],minute=clock[1]).strftime('%Y-%m-%d %H:%M:%S'),
            'source':HISTORY_PREFIX+source,'event_type':kind,
            'username':username,'severity':severity,
            'message':f'{marker} {message}'},historical=True)
    return {'created':3,'already_seeded':False,'date':date_string}


def event_dict(e):
    return dict(event_id=e.event_id,event_time=e.event_time.strftime('%Y-%m-%d %H:%M:%S'),
                source=e.source,event_type=e.event_type,username=e.username,
                message=e.message,severity=e.severity,
                first_alert_id=next((a.alert_id for a in e.alerts.all()),None))


def rule_dict(r):
    return dict(rule_id=r.rule_id,rule_name=r.rule_name,description=r.description,
                pattern=r.pattern,severity=r.severity,enabled=int(r.enabled))


def alert_dict(a, *, details=False):
    result=dict(alert_id=a.alert_id,event_id=a.event_id,rule_id=a.rule_id,
                alert_time=a.alert_time.strftime('%Y-%m-%d %H:%M:%S'),severity=a.severity,
                description=a.description,status=a.status,event_type=a.event.event_type,
                source=a.event.source,username=a.event.username,rule_name=a.rule.rule_name)
    if details:
        result.update(event_time=a.event.event_time.strftime('%Y-%m-%d %H:%M:%S'),
                      event_message=a.event.message,event_severity=a.event.severity,
                      rule_description=a.rule.description,pattern=a.rule.pattern,
                      rule_enabled=int(a.rule.enabled))
    return result


def summary():
    return dict(events_processed=Event.objects.count(),
                open_alerts=Alert.objects.filter(status='Open').count(),
                alerts_total=Alert.objects.count(),
                last_update=(Event.objects.order_by('-event_time').values_list('event_time',flat=True).first() or '').strftime('%Y-%m-%d %H:%M:%S') if Event.objects.exists() else None)


def activity(days=30):
    start=(datetime.now()-timedelta(days=days-1)).date()
    events = Event.objects.filter(event_time__date__gte=start).values('event_time__date').annotate(total=Count('pk'))
    alerts = Alert.objects.filter(alert_time__date__gte=start).values('alert_time__date').annotate(total=Count('pk'))
    e_counts={str(x['event_time__date']):x['total'] for x in events}
    a_counts={str(x['alert_time__date']):x['total'] for x in alerts}
    result=[]
    for i in range(days-1,-1,-1):
        d=(datetime.now()-timedelta(days=i)).date().isoformat()
        result.append({'date':d,'events':e_counts.get(d,0),'alerts':a_counts.get(d,0)})
    return result
