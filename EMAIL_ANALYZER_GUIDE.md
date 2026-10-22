# Python Sentinel — Phishing Email Analyzer

**Status:** Optional capstone extension to the original Windows-event monitoring SRS; classroom demo implementation. This module is a rule-based text assessment, **not** a trained phishing classifier or email provider connection. No emails are downloaded and no URLs are visited.

## How to start on Windows

1. Extract the ZIP, then open the **inner `Python_Sentinel_Django`** folder in VS Code. You must be in the folder with `manage.py` and `requirements.txt`.
2. In VS Code Terminal (PowerShell), enter:

   ```powershell
   py -m pip install -r requirements.txt
   py manage.py migrate
   py manage.py seed_demo
   $env:SENTINEL_MODE="demo"
   py manage.py runserver 127.0.0.1:8000 --noreload
   ```

3. Open `http://127.0.0.1:8000/` in Chrome or Edge.
4. Click **Email Analyzer** in the left navigation.
5. Click **Load Normal Sample** then **Analyze and Save Result**. Expect **Low**, a stored Event, and **no Alert**.
6. Click **Load Suspicious Sample** then **Analyze and Save Result**. Expect **High**, several explainable indicators, an Event, and a linked Alert. Click the alert link to see its related rule, and open Detection History to find it.
7. On Detection Rules, disable **High-Risk Email Indicators**, then repeat the suspicious email analysis. Expect a result but no **new alert**. Re-enable the rule afterward.

To stop the server: press `Ctrl+C` in the terminal. To reload new static assets: press `Ctrl+F5` in Chrome.

### Automated tests

```powershell
py manage.py test sentinel.tests -v 2
```

A lightweight analysis-only test that needs no Django is also available:

```powershell
py -m unittest discover -s standalone_tests -v
```

If `requirements.txt` cannot be found, run `dir` and open/cd into `Python_Sentinel_Django` rather than the outer extracted ZIP directory.

## How it works

- **Frontend:** `sentinel/templates/sentinel/index.html` adds navigation. `sentinel/static/sentinel/app.js` adds the form, demo samples, findings, alert links, and API request. `style.css` adds matching monochrome styles.
- **API:** `POST /api/email/analyze` in `sentinel/views.py` validates JSON, uses existing CSRF protections, and calls `analyze_and_record`.
- **Analyzer:** `sentinel/email_analysis.py` evaluates urgency, account warnings, requests for credentials/payment, HTTP/IP/shortened URLs, executable filenames, and reply-to mismatches. It never downloads, executes, follows, or resolves a URL.
- **Rules:** The existing rule engine in `sentinel/services.py` now supports `EMAIL_PHISHING_MEDIUM` and `EMAIL_PHISHING_HIGH`. Thresholds: **Low 0–2**, **Medium 3–5**, **High 6+**.
- **Database:** `sentinel/email_service.py` stores a **redacted Event** for every scan and creates an **Alert** only if the matching enabled rule applies. An alert retains the Event and DetectionRule foreign-key relationships from the SRS. No schema change/migration was necessary.
- **History:** Email-generated alerts are part of the existing `/api/alerts` query and Date Range / Detection History views. This integration is deliberately additive.

## Privacy and safety

**Never paste real passwords, verification codes, student email records, personal messages, financial details, or other confidential content into a public demo.** Use the prepared synthetic samples. The server stores only score, risk, and generic indicator labels—not the submitted sender, recipient, subject, body, or link address. The browser receives only the explanation labels and links to database record IDs.

All heuristic assessments are approximate and can be false positives or false negatives. A **Low** result does not mean an email is safe, and a **High** result does not prove fraud. No antivirus scanning, Gmail/Outlook connection, domain reputation lookup, attachment scanning, machine learning, or malware detonation is provided.

On public hosting, all demonstration Event, Rule, and Alert records remain shared across visitors, as in the prior public demo. Do not collect real emails without proper access control and privacy measures. The POST endpoint uses Django CSRF protection and the existing public-demo rate limiter, but this is still a classroom application and not production grade.

## Requirement/test traceability addendum (proposed, not part of original SRS)

| Proposed extension | Implementation | Test evidence |
|---|---|---|
| EXT-01: Analyze user-supplied sample email text offline | `email_analysis.analyze_email` | `EmailHeuristicTests` |
| EXT-02: Distinguish low, medium, high heuristic results | `email_analysis.py` | severity tests |
| EXT-03: Store summary as Event, generate Alert only for enabled matching rule | `email_service.py`, `services.py` | `EmailAPIIntegrationTests` |
| EXT-04: Show explanations without storing submitted email content | `app.js`, `email_service.py` | privacy tests |
| EXT-05: Show new alerts in the existing history and rules screens | `app.js`, existing alert APIs | API/link tests |

This is an optional feature in addition to FR-01–FR-31, which originally cover Windows event monitoring. Discuss any SRS-scope change with your professor.

## Live presentation (1 minute)

> Our professor suggested investigating whether Python Sentinel could recognize suspicious email activity. We added a separate manual Email Analyzer. The user supplies a sample email, and the backend checks predefined indicators such as urgent wording, credential requests, and suspicious link formats. A normal sample creates a recorded event but no alert. A suspicious sample creates a linked alert in the existing SQLite database if its rule is enabled. We also tested invalid submissions, disabled rules, and privacy handling. This is a heuristic demonstration, not a verified inbox security solution.
