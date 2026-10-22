"""White-box / API tests. Run: py manage.py test sentinel.tests -v 2"""
import json
from datetime import datetime,timedelta
from django.test import TestCase,Client
from sentinel.models import Event,Alert,DetectionRule
from sentinel.services import (ensure_rules,process_event,seed_historical_data,
                               seed_custom_date,generate_scenario,rule_matches,validate_event)
from sentinel.monitoring import monitor

class PythonSentinelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_rules()

    def setUp(self):
        monitor.stop()
        monitor.mode='demo'
        self.client=Client(enforce_csrf_checks=False)

    def event(self,kind='NORMAL_LOGIN',day=None):
        return dict(event_time=(day or datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
            source='Test Windows Security Log',event_type=kind,username='testuser',
            message='Controlled classroom test',severity='Medium')

    def test_three_main_tables_and_seeded_rules(self):
        self.assertEqual(Event._meta.db_table,'events')
        self.assertEqual(DetectionRule._meta.db_table,'detection_rules')
        self.assertEqual(Alert._meta.db_table,'alerts')
        self.assertEqual(DetectionRule.objects.count(),10)

    def test_normal_event_does_not_alert(self):
        res=process_event(self.event())
        self.assertEqual(res['matched_rules'],0)
        self.assertEqual(Alert.objects.count(),0)

    def test_failed_login_creates_linked_alert(self):
        out=process_event(self.event('FAILED_LOGIN'))
        a=Alert.objects.get(pk=out['alert_ids'][0])
        self.assertEqual(a.event_id,out['event_id'])
        self.assertEqual(a.rule.pattern,'FAILED_LOGIN')
        self.assertEqual(a.severity,'Medium')
        self.assertEqual(a.status,'Open')

    def test_all_eight_anomaly_scenarios_match(self):
        for kind in ['FAILED_LOGIN','FILE_CHANGE','SUSPICIOUS_PROCESS','PRIVILEGE_CHANGE',
                     'ACCOUNT_LOCKOUT','SERVICE_STOPPED','SECURITY_LOG_CLEARED','SUSPICIOUS_NETWORK']:
            with self.subTest(kind=kind):
                self.assertEqual(process_event(self.event(kind))['matched_rules'],1)
        self.assertEqual(Alert.objects.count(),8)

    def test_disabled_rule_suppresses_new_alert(self):
        DetectionRule.objects.filter(pattern='FAILED_LOGIN').update(enabled=False)
        self.assertEqual(process_event(self.event('FAILED_LOGIN'))['matched_rules'],0)

    def test_case_insensitive_exact_match(self):
        self.assertEqual(process_event(self.event('failed_login'))['matched_rules'],1)
        self.assertEqual(process_event(self.event('FAILED_LOGIN_CHANGED'))['matched_rules'],0)

    def test_optional_missing_fields_are_safe(self):
        event=self.event(); event.pop('username');event.pop('severity')
        self.assertEqual(process_event(event)['matched_rules'],0)
        self.assertIsNone(Event.objects.first().username)

    def test_missing_required_field_raises(self):
        event=self.event(); event['message']=''
        with self.assertRaises(ValueError):process_event(event)
        self.assertEqual(Event.objects.count(),0)

    def test_malformed_date_raises(self):
        event=self.event();event['event_time']='invalid'
        with self.assertRaises(ValueError):process_event(event)

    def test_non_dict_event_raises(self):
        with self.assertRaises(ValueError):process_event(['not','object'])

    def test_seed_75_day_history_creates_backdated_alerts(self):
        out=seed_historical_data()
        self.assertGreater(out['created'],100)
        self.assertTrue(Event.objects.filter(event_time__date=(datetime.now()-timedelta(days=29)).date()).exists())
        self.assertTrue(Alert.objects.filter(alert_time__date__gte=(datetime.now()-timedelta(days=30)).date()).exists())
        self.assertTrue(Alert.objects.filter(alert_time__date__lte=(datetime.now()-timedelta(days=60)).date()).exists())
        self.assertEqual(seed_historical_data()['created'],0)

    def test_interactive_sample_does_not_prevent_history_seed(self):
        generate_scenario('FAILED_LOGIN')
        self.assertGreater(seed_historical_data()['created'],100)

    def test_custom_date_generates_linked_history(self):
        day=(datetime.now()-timedelta(days=11)).date().isoformat()
        x=seed_custom_date(day)
        self.assertEqual(x['created'],3)
        self.assertEqual(Alert.objects.filter(alert_time__date=day).count(),2)
        self.assertEqual(seed_custom_date(day)['created'],0)

    def test_custom_future_date_rejected(self):
        day=(datetime.now()+timedelta(days=1)).date().isoformat()
        with self.assertRaises(ValueError):seed_custom_date(day)

    def test_get_dashboard_contains_activity(self):
        response=self.client.get('/api/dashboard')
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()['activity']),30)
        self.assertIn('events',response.json())

    def test_status_and_events_endpoints(self):
        process_event(self.event())
        self.assertEqual(self.client.get('/api/status').json()['events_processed'],1)
        self.assertEqual(len(self.client.get('/api/events').json()['events']),1)
        e=Event.objects.first()
        self.assertEqual(self.client.get(f'/api/events/{e.pk}').json()['event']['event_id'],e.pk)

    def test_alert_detail_has_event_and_rule(self):
        out=process_event(self.event('FILE_CHANGE'))
        body=self.client.get(f"/api/alerts/{out['alert_ids'][0]}").json()['alert']
        self.assertEqual(body['event_type'],'FILE_CHANGE')
        self.assertEqual(body['pattern'],'FILE_CHANGE')

    def test_mark_reviewed_via_api(self):
        out=process_event(self.event('FAILED_LOGIN'))
        response=self.client.post(f"/api/alerts/{out['alert_ids'][0]}/review",'{}',content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(Alert.objects.first().status,'Reviewed')
        self.assertEqual(len(self.client.get('/api/alerts?status=Open').json()['alerts']),0)

    def test_rule_toggle_api(self):
        rule=DetectionRule.objects.get(pattern='FAILED_LOGIN')
        r=self.client.post(f'/api/rules/{rule.pk}/toggle',json.dumps({'enabled':False}),content_type='application/json')
        self.assertEqual(r.status_code,200)
        self.assertEqual(process_event(self.event('FAILED_LOGIN'))['matched_rules'],0)

    def test_invalid_rule_toggle_rejected(self):
        rule=DetectionRule.objects.first()
        self.assertEqual(self.client.post(f'/api/rules/{rule.pk}/toggle','{"enabled":"yes"}',content_type='application/json').status_code,400)

    def test_date_filter_exact_inclusive(self):
        today=datetime.now()
        old=today-timedelta(days=16)
        process_event(self.event('FAILED_LOGIN',old),historical=True)
        process_event(self.event('FILE_CHANGE',today),historical=True)
        day=old.date().isoformat()
        rows=self.client.get(f'/api/alerts?from={day}&to={day}').json()['alerts']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['event_type'],'FAILED_LOGIN')

    def test_date_range_invalid_rejected(self):
        self.assertEqual(self.client.get('/api/alerts?from=2026-11-30&to=2026-10-01').status_code,400)
        self.assertEqual(self.client.get('/api/alerts?from=hello').status_code,400)

    def test_api_limit_bounds(self):
        self.assertEqual(self.client.get('/api/events?limit=999999').status_code,400)
        self.assertEqual(self.client.get('/api/alerts?limit=0').status_code,400)

    def test_seed_date_endpoint(self):
        day=(datetime.now()-timedelta(days=18)).date().isoformat()
        r=self.client.post('/api/demo/date',json.dumps({'date':day}),content_type='application/json')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['result']['created'],3)

    def test_demo_buttons_require_monitoring_started(self):
        r=self.client.post('/api/demo/event','{"event_type":"FAILED_LOGIN"}',content_type='application/json')
        self.assertEqual(r.status_code,400)
        r=self.client.post('/api/monitor/start','{}',content_type='application/json')
        self.assertEqual(r.status_code,200)
        r=self.client.post('/api/demo/event','{"event_type":"FAILED_LOGIN"}',content_type='application/json')
        self.assertEqual(r.status_code,201)
        monitor.stop()

    def test_csrf_protects_mutating_endpoints(self):
        strict=Client(enforce_csrf_checks=True)
        response=strict.post('/api/monitor/start','{}',content_type='application/json')
        self.assertEqual(response.status_code,403)
        page=strict.get('/')
        self.assertEqual(page.status_code,200)
        token=page.cookies['csrftoken'].value
        response=strict.post('/api/monitor/start','{}',content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200)
        monitor.stop()

    def test_new_event_datetime_validated(self):
        event=self.event();event['event_time']='2026-02-30 12:00:00'
        with self.assertRaises(ValueError):process_event(event)

    def test_reset_only_deletes_historical_simulations(self):
        generate_scenario('FAILED_LOGIN')
        seed_historical_data()
        count=Event.objects.filter(source='SIMULATED / Windows Security Log').count()
        seed_historical_data(reset=True)
        self.assertEqual(Event.objects.filter(source='SIMULATED / Windows Security Log').count(),count)

    def test_toggle_does_not_delete_historical_alert(self):
        process_event(self.event('FAILED_LOGIN'))
        DetectionRule.objects.filter(pattern='FAILED_LOGIN').update(enabled=False)
        self.assertEqual(Alert.objects.count(),1)
        self.assertFalse(Alert.objects.first().rule.enabled)


class PublicSiteSmokeTests(TestCase):
    def test_homepage_does_not_render_classroom_checklist(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Presentation Checklist', response.content)

    def test_health_endpoint(self):
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
