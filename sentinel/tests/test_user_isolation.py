import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from sentinel.models import Event, Alert
from sentinel.services import ensure_rules, process_event

class AccountIsolationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", password="test-strong-pass-123")
        self.bob = User.objects.create_user(username="bob", password="test-strong-pass-456")
        ensure_rules()
        self.client.force_login(self.alice)
        self.own = process_event({"event_time":"2026-10-20 12:00:00", "source":"SIMULATED / Test", "event_type":"FAILED_LOGIN", "message":"Alice's test event"}, owner=self.alice)
        self.other = process_event({"event_time":"2026-10-20 12:01:00", "source":"SIMULATED / Test", "event_type":"FAILED_LOGIN", "message":"Bob's test event"}, owner=self.bob)

    def test_events_are_private(self):
        response=self.client.get('/api/events')
        self.assertEqual(response.status_code,200)
        self.assertIn(str(self.own['event_id']),response.content.decode())
        self.assertNotIn("Bob's test event",response.content.decode())

    def test_other_event_detail_hidden(self):
        self.assertEqual(self.client.get(f"/api/events/{self.other['event_id']}").status_code,404)

    def test_other_alert_cannot_be_reviewed(self):
        aid=self.other['alert_ids'][0]
        self.assertEqual(self.client.post(f"/api/alerts/{aid}/review",data=json.dumps({}),content_type='application/json').status_code,404)
        self.assertEqual(Alert.objects.get(pk=aid).status,'Open')

    def test_logged_out_api_denied(self):
        self.client.logout()
        self.assertEqual(self.client.get('/api/events').status_code,401)

    def test_shared_rule_changes_staff_only(self):
        self.assertEqual(self.client.post('/api/rules/1/toggle',data=json.dumps({'enabled':False}),content_type='application/json').status_code,403)

    def test_bob_only_sees_bob(self):
        self.client.force_login(self.bob)
        response=self.client.get('/api/events')
        self.assertEqual(response.status_code,200)
        self.assertNotIn("Alice's test event",response.content.decode())
        self.assertIn("Bob's test event",response.content.decode())

    def test_alert_list_is_private(self):
        response=self.client.get('/api/alerts')
        self.assertEqual(response.status_code,200)
        ids=[item['alert_id'] for item in response.json()['alerts']]
        self.assertIn(self.own['alert_ids'][0],ids)
        self.assertNotIn(self.other['alert_ids'][0],ids)

    def test_dashboard_requires_login(self):
        self.client.logout()
        response=self.client.get('/')
        self.assertEqual(response.status_code,302)
        self.assertIn('/accounts/login/',response['Location'])
