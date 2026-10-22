"""Conservative, offline heuristic analysis of user-supplied sample email text.

This is NOT a spam filter, antivirus, inbox connector, or proof of phishing.
Never opens links, downloads attachments, or retains the email body.
"""
from __future__ import annotations
import ipaddress
import re
from email.utils import parseaddr
from urllib.parse import urlsplit

URL_RE = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)
URGENCY_RE = re.compile(r'\b(urgent|immediately|act now|within (?:\d+|one|two) hours?|final warning|last chance)\b', re.I)
CREDENTIAL_RE = re.compile(r'\b(password|passcode|otp|one.time code|verification code|login credentials|verify your account|confirm your account)\b', re.I)
THREAT_RE = re.compile(r'\b(account (?:will be |has been )?(?:suspended|locked|disabled)|mailbox (?:will be )?(?:closed|disabled)|failure to respond|access will be revoked)\b', re.I)
MONEY_RE = re.compile(r'\b(gift cards?|wire transfer|bank details|payment information)\b', re.I)
ATTACHMENT_RE = re.compile(r'(?<![\w.-])[\w-]+\.(?:exe|scr|js|vbs|bat|cmd|ps1)\b', re.I)
SHORTENERS = {'bit.ly','tinyurl.com','t.co','cutt.ly','is.gd','shorturl.at'}


def _domain(email_header):
    """Return normalized mail domain; never persist or echo the supplied address."""
    _, address = parseaddr(email_header or '')
    return address.rsplit('@', 1)[-1].lower() if '@' in address else ''


def analyze_email(payload):
    """Return bounded, non-sensitive findings. Score is indicative only.

    Input: {sender, reply_to, subject, body}. Only subject and body are needed.
    No caller-supplied content is included in the returned explanations.
    """
    if not isinstance(payload, dict):
        raise ValueError('Email data must be an object.')
    limits = {'sender':254, 'reply_to':254, 'subject':250, 'body':6000}
    fields = {}
    for key, limit in limits.items():
        val = payload.get(key, '')
        if not isinstance(val, str) or len(val) > limit:
            raise ValueError(f'{key} must be text of at most {limit} characters.')
        fields[key] = val.strip()
    if not fields['subject'] and not fields['body']:
        raise ValueError('Enter an email subject or body to analyze.')
    combined = f"{fields['subject']}\n{fields['body']}"
    findings = []

    def add(code, title, explanation, points):
        findings.append({'code':code, 'title':title, 'explanation':explanation, 'points':points})

    if URGENCY_RE.search(combined):
        add('urgency','Urgent wording','Uses language intended to pressure a quick decision.',1)
    if CREDENTIAL_RE.search(combined):
        add('credentials','Credential request','Mentions passwords, verification codes, or account verification.',2)
    if THREAT_RE.search(combined):
        add('account_threat','Account-access threat','Suggests account access may be suspended or removed.',2)
    if MONEY_RE.search(combined):
        add('payment_request','Payment or gift-card request','Mentions money transfers, payment details, or gift cards.',2)
    if ATTACHMENT_RE.search(combined):
        add('risky_attachment_name','Executable attachment name','References an executable or script file extension; no file was opened.',3)

    urls = URL_RE.findall(combined)[:15]
    if urls:
        hosts = []
        http_found = False
        ip_found = False
        short_found = False
        puny_found = False
        for raw in urls:
            url = raw.rstrip('.,;:!?)]}')
            try:
                parts = urlsplit(url)
                host = (parts.hostname or '').lower().rstrip('.')
            except ValueError:
                continue
            if not host:
                continue
            hosts.append(host)
            if parts.scheme.lower() == 'http':
                http_found = True
            try:
                ipaddress.ip_address(host.strip('[]'))
                ip_found = True
            except ValueError:
                pass
            if host in SHORTENERS or any(host.endswith('.'+short) for short in SHORTENERS):
                short_found = True
            if 'xn--' in host:
                puny_found = True
        if http_found:
            add('unencrypted_link','Non-HTTPS link','Contains a plain HTTP link. Not all HTTP links are phishing.',1)
        if ip_found:
            add('ip_link','IP-address link','A URL uses a numeric IP address rather than a domain name.',2)
        if short_found:
            add('short_link','Shortened link','Uses a link shortener, which can obscure the destination.',2)
        if puny_found:
            add('internationalized_domain','Encoded domain','Contains a punycode domain that may warrant inspection.',1)
        sender_domain = _domain(fields['sender'])
        if sender_domain and hosts and all(
            host != sender_domain and not host.endswith('.'+sender_domain)
            for host in hosts
        ):
            add('external_link','External link domain','The website hostname differs from the sender domain; legitimate mail may also do this.',1)

    sender = _domain(fields['sender'])
    reply = _domain(fields['reply_to'])
    if sender and reply and sender != reply:
        add('reply_to_mismatch','Different reply-to domain','The sender and reply-to email domains do not match.',2)

    score = sum(item['points'] for item in findings)
    risk = 'High' if score >= 6 else ('Medium' if score >= 3 else 'Low')
    return {
        'risk':risk,
        'score':score,
        'findings':findings,
        'indicators':len(findings),
        'disclaimer':'Heuristic review of submitted sample text only. A warning is not proof of phishing; no links or attachments were opened.',
    }
