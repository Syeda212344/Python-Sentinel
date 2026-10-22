"""Integrate email analysis with existing SRS Events, Detection Rules and Alerts.

No raw email text, addresses, links or attachments are stored in the database.
"""
from datetime import datetime
from .email_analysis import analyze_email
from .services import ensure_rules, process_event


def analyze_and_record(payload):
    result = analyze_email(payload)  # All validation before any database insert
    ensure_rules()
    event_type = 'EMAIL_PHISHING_HIGH' if result['risk'] == 'High' else (
        'EMAIL_PHISHING_MEDIUM' if result['risk'] == 'Medium' else 'EMAIL_REVIEWED_NORMAL'
    )
    # Only predefined reason codes, not text, sender, subject or URLs, reach SQLite.
    names = ', '.join(item['title'] for item in result['findings']) or 'No configured indicators identified'
    stored_message = f'[SUBMITTED EMAIL SAMPLE — CONTENT NOT STORED] Risk: {result["risk"]}; score: {result["score"]}; indicators: {names}.'
    saved = process_event({
        'event_time':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source':'EMAIL ANALYSIS / User-submitted text (redacted)',
        'event_type':event_type,
        'username':None,
        'message':stored_message,
        'severity':result['risk'],
    })
    return {**result, **saved, 'event_type':event_type, 'saved':'Summary only; email content is not retained.'}
