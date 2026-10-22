"""Email-analysis functional tests (run with python manage.py test sentinel.tests)."""
import json
from django.test import Client, TestCase
from sentinel.email_analysis import analyze_email
from sentinel.models import Alert, DetectionRule, Event
from sentinel.services import ensure_rules

NORMAL = {
    'sender':'team@example.com',
    'reply_to':'',
    'subject':'Project meeting on Friday',
    'body':'Hello team, our meeting is Friday at 2 PM. Please bring your notes.',
}
SUSPICIOUS = {
    'sender':'security@campus-example.test',
    'reply_to':'response@different-example.test',
    'subject':'URGENT: Account will be suspended',
    'body':'Act now! Your mailbox will be disabled unless you verify your password immediately at http://192.0.2.55/account.',
}

class EmailHeuristicTests(TestCase):
    def test_normal_sample_has_no_findings(self):
        result=analyze_email(NORMAL)
        self.assertEqual(result['risk'],'Low')
        self.assertEqual(result['score'],0)

    def test_suspicious_sample_has_explanations(self):
        result=analyze_email(SUSPICIOUS)
        self.assertEqual(result['risk'],'High')
        self.assertGreaterEqual(len(result['findings']),4)
        self.assertIn('credentials',[x['code'] for x in result['findings']])

    def test_medium_score_possible(self):
        result=analyze_email({'subject':'Urgent: verify your password','body':''})
        self.assertEqual(result['risk'],'Medium')

    def test_reply_to_mismatch_is_an_indicator(self):
        result=analyze_email({'subject':'Meeting','sender':'a@example.com','reply_to':'b@other.com'})
        self.assertIn('reply_to_mismatch',[x['code'] for x in result['findings']])

    def test_empty_and_invalid_requests_rejected(self):
        for payload in ({},{'body':4},{'body':'x'*6001},{'body':'','subject':''}):
            with self.subTest(payload=str(payload)[:20]):
                with self.assertRaises(ValueError):analyze_email(payload)

    def test_no_email_text_ever_echoed_in_result(self):
        private='PRIVATE-COURSE-SECRET-123456'
        result=analyze_email({'subject':'URGENT: '+private,'body':'verify your password immediately'})
        self.assertNotIn(private,json.dumps(result))


class EmailAPIIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_rules()

    def post_email(self, data):
        return self.client.post('/api/email/analyze',json.dumps(data),content_type='application/json')

    def test_normal_email_stored_without_alert(self):
        response=self.post_email(NORMAL)
        self.assertEqual(response.status_code,201)
        result=response.json()['analysis']
        self.assertEqual(result['risk'],'Low')
        self.assertEqual(result['alert_ids'],[])
        self.assertEqual(Event.objects.get(pk=result['event_id']).event_type,'EMAIL_REVIEWED_NORMAL')
        self.assertEqual(Alert.objects.count(),0)

    def test_high_risk_email_creates_linked_alert(self):
        response=self.post_email(SUSPICIOUS)
        self.assertEqual(response.status_code,201)
        result=response.json()['analysis']
        self.assertEqual(result['risk'],'High')
        self.assertEqual(len(result['alert_ids']),1)
        alert=Alert.objects.select_related('event','rule').get(pk=result['alert_ids'][0])
        self.assertEqual(alert.event_id,result['event_id'])
        self.assertEqual(alert.rule.pattern,'EMAIL_PHISHING_HIGH')
        self.assertEqual(alert.severity,'High')
        self.assertEqual(self.client.get(f'/api/alerts/{alert.pk}').status_code,200)
        self.assertEqual(len(self.client.get('/api/alerts').json()['alerts']),1)

    def test_medium_risk_matches_medium_rule(self):
        response=self.post_email({'subject':'Urgent: verify your password','body':''})
        self.assertEqual(response.status_code,201)
        alert=Alert.objects.get()
        self.assertEqual(alert.rule.pattern,'EMAIL_PHISHING_MEDIUM')

    def test_disabled_rule_generates_no_alert(self):
        DetectionRule.objects.filter(pattern='EMAIL_PHISHING_HIGH').update(enabled=False)
        response=self.post_email(SUSPICIOUS)
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json()['analysis']['alert_ids'],[])
        self.assertEqual(Event.objects.count(),1)

    def test_invalid_input_does_not_create_records(self):
        response=self.post_email({'subject':'', 'body':''})
        self.assertEqual(response.status_code,400)
        self.assertEqual(Event.objects.count(),0)
        self.assertEqual(Alert.objects.count(),0)

    def test_email_body_sender_and_urls_not_persisted(self):
        secret='NEVER-STORE-MY-SECRET-PASSWORD'
        data={**SUSPICIOUS,'body':SUSPICIOUS['body']+' '+secret}
        response=self.post_email(data)
        self.assertEqual(response.status_code,201)
        stored=' '.join(Event.objects.values_list('message',flat=True))+' '.join(Alert.objects.values_list('description',flat=True))
        for sensitive in (secret,'security@campus-example.test','http://192.0.2.55/account','different-example.test'):
            self.assertNotIn(sensitive,stored)
        self.assertNotIn(secret,json.dumps(response.json()))

    def test_csrf_required_for_mutation(self):
        strict=Client(enforce_csrf_checks=True)
        response=strict.post('/api/email/analyze',json.dumps(SUSPICIOUS),content_type='application/json')
        self.assertEqual(response.status_code,403)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get('/api/email/analyze').status_code,405)

    def test_navigation_page_exists(self):
        html=self.client.get('/').content.decode()
        self.assertIn('#/email',html)
        self.assertNotIn('Presentation Checklist',html)

    def test_existing_rules_are_preserved(self):
        result=self.post_email(SUSPICIOUS)
        self.assertEqual(result.status_code,201)
        self.assertEqual(DetectionRule.objects.count(),10)
        self.assertTrue(DetectionRule.objects.filter(pattern='FAILED_LOGIN').exists())
