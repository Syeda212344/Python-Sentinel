"""Standard-library smoke tests. Django app tests are in sentinel/tests/test_email.py."""
import unittest
from sentinel.email_analysis import analyze_email

class EmailHeuristicSmokeTests(unittest.TestCase):
    def test_normal(self):
        r=analyze_email({'subject':'Meeting tomorrow','body':'See you in class at 11 AM.'})
        self.assertEqual(r['risk'],'Low')
    def test_high_risk(self):
        r=analyze_email({'subject':'URGENT: Account will be suspended','body':'Verify your password immediately at http://192.0.2.55/login'})
        self.assertEqual(r['risk'],'High')
    def test_medium_risk(self):
        self.assertEqual(analyze_email({'subject':'urgent verify your password'})['risk'],'Medium')
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):analyze_email({})
    def test_private_data_not_reflected(self):
        self.assertNotIn('DO-NOT-SAVE-ME',str(analyze_email({'subject':'DO-NOT-SAVE-ME','body':'urgent verify your password'})))
    def test_executable_indicator(self):
        self.assertIn('risky_attachment_name',[r['code'] for r in analyze_email({'body':'See update.exe attached'})['findings']])
    def test_sender_reply_mismatch(self):
        self.assertIn('reply_to_mismatch',[r['code'] for r in analyze_email({'subject':'Hello','sender':'a@example.com','reply_to':'b@example.net'})['findings']])

if __name__=='__main__':unittest.main()
