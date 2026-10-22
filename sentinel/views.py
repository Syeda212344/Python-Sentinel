"""Local Django JSON API. Browser frontend talks to Django, which talks to SQLite ORM."""
import json
import logging
from datetime import datetime,timedelta
from django.db import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET,require_POST
from django.db.models import Prefetch
from .models import Event,DetectionRule,Alert
from .monitoring import monitor
from . import services
from .email_service import analyze_and_record
LOG=logging.getLogger(__name__)

def fail(message,code=400):return JsonResponse({'error':str(message)},status=code)

def _limit(value,default=100,cap=500):
    try:
        x=int(value if value is not None else default)
        if not 1<=x<=cap:raise ValueError
        return x
    except (TypeError,ValueError):raise ValueError(f'limit must be between 1 and {cap}.')

def _date(value):
    if not value:return None
    try:return datetime.strptime(value,'%Y-%m-%d').date()
    except (TypeError,ValueError):raise ValueError('Use YYYY-MM-DD dates.')

def _body(request):
    if not request.content_type=='application/json':raise ValueError('Send Content-Type: application/json.')
    if len(request.body)>8192:raise ValueError('Request too large.')
    try:data=json.loads(request.body or b'{}')
    except (ValueError,UnicodeDecodeError):raise ValueError('Invalid JSON.')
    if not isinstance(data,dict):raise ValueError('JSON body must be an object.')
    return data

def guarded(handler):
    def wrapper(*args,**kwargs):
        try:return handler(*args,**kwargs)
        except (ValueError,TypeError) as exc:return fail(exc)
        except DatabaseError:
            LOG.exception('Database error')
            return fail('Database error; check the terminal.',500)
        except RuntimeError as exc:
            return fail(str(exc),400)
    return wrapper

@ensure_csrf_cookie
@require_GET
def home(request):return render(request,'sentinel/index.html')

@require_GET
@guarded
def status(request):return JsonResponse({**monitor.status(),**services.summary()})

@require_GET
@guarded
def dashboard(request):
    events=Event.objects.prefetch_related('alerts').order_by('-event_id')[:6]
    alerts=Alert.objects.select_related('event','rule').order_by('-alert_id')[:5]
    return JsonResponse({'monitor':monitor.status(),'summary':services.summary(),
        'events':[services.event_dict(e) for e in events],
        'alerts':[services.alert_dict(a) for a in alerts],
        'activity':services.activity(30)})

@require_GET
@guarded
def events(request):
    take=_limit(request.GET.get('limit'))
    records=Event.objects.prefetch_related('alerts').order_by('-event_id')[:take]
    return JsonResponse({'events':[services.event_dict(e) for e in records]})

@require_GET
@guarded
def event_detail(request,pk):
    row=Event.objects.prefetch_related('alerts').filter(pk=pk).first()
    return JsonResponse({'event':services.event_dict(row)}) if row else fail('Event not found.',404)

@require_GET
@guarded
def alerts(request):
    take=_limit(request.GET.get('limit'))
    status=request.GET.get('status')
    if status not in (None,'','Open','Reviewed'):raise ValueError('Unknown status.')
    start=_date(request.GET.get('from'))
    end=_date(request.GET.get('to'))
    if start and end and start>end:raise ValueError('From date must not exceed To date.')
    records=Alert.objects.select_related('event','rule')
    if status:records=records.filter(status=status)
    if start:records=records.filter(alert_time__date__gte=start)
    if end:records=records.filter(alert_time__date__lte=end)
    records=records.order_by('-alert_time','-alert_id')[:take]
    return JsonResponse({'alerts':[services.alert_dict(a) for a in records]})

@require_GET
@guarded
def alert_detail(request,pk):
    a=Alert.objects.select_related('event','rule').filter(pk=pk).first()
    return JsonResponse({'alert':services.alert_dict(a,details=True)}) if a else fail('Alert not found.',404)

@require_GET
@guarded
def rules(request):
    services.ensure_rules()
    return JsonResponse({'rules':[services.rule_dict(r) for r in DetectionRule.objects.all()]})

@require_POST
@guarded
def review_alert(request,pk):
    _body(request)
    changed=Alert.objects.filter(pk=pk).update(status='Reviewed')
    return JsonResponse({'updated':True}) if changed else fail('Alert not found.',404)

@require_POST
@guarded
def toggle_rule(request,pk):
    body=_body(request)
    if type(body.get('enabled')) is not bool:raise ValueError('enabled must be true/false.')
    updated=DetectionRule.objects.filter(pk=pk).update(enabled=body['enabled'])
    return JsonResponse({'updated':True}) if updated else fail('Rule not found.',404)

@require_POST
@guarded
def start_monitor(request):
    _body(request)
    return JsonResponse({'monitor':monitor.start()})

@require_POST
@guarded
def stop_monitor(request):
    _body(request)
    return JsonResponse({'monitor':monitor.stop()})

@require_POST
@guarded
def demo_event(request):
    payload=_body(request)
    return JsonResponse({'result':monitor.demo_event(payload.get('event_type'))},status=201)

@require_POST
@guarded
def seed_demo(request):
    _body(request)
    if monitor.mode!='demo':return fail('Historical simulator is only available in demo mode.',403)
    return JsonResponse({'result':services.seed_historical_data()})

@require_POST
@guarded
def seed_date(request):
    if monitor.mode!='demo':return fail('Date simulator is only available in demo mode.',403)
    payload=_body(request)
    return JsonResponse({'result':services.seed_custom_date(payload.get('date'))})

@require_GET
@guarded
def scenarios(request):
    return JsonResponse({'scenarios':[{'event_type':key,'label':v[0], 'severity':v[3]} for key,v in services.SCENARIOS.items()]})


@require_GET
def health(request):
    """Public host health probe; does not reveal private configuration."""
    return JsonResponse({"status": "ok"})


@require_POST
@guarded
def analyze_email_sample(request):
    """CSRF-protected manual text analysis; never fetch links or accept attachments."""
    payload = _body(request)
    result = analyze_and_record(payload)
    return JsonResponse({'analysis': result}, status=201)
