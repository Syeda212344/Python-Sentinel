Python Sentinel 🛡️
A Django-based cybersecurity monitoring and phishing email analysis web application.

Python Sentinel is a student capstone project that demonstrates how security events can be collected, checked against configurable detection rules, stored in a database, and presented through an interactive dashboard. It also includes an explainable phishing-email analyzer for pasted sample emails.
Project status: Classroom prototype. Security events in demo mode are simulated. This is not a production intrusion detection service.

Features
- Security dashboard: Event and alert summaries, activity charts, and recent detections.
- Rule-based detection: Predefined suspicious-activity scenarios and rules that can be enabled or disabled.
- Phishing email analyzer: Checks pasted sender, subject, and message content for common phishing indicators and explains its findings.
- Database integration: Stores events, detection rules, and linked alerts using the Django ORM.
- Detection history: Browse alerts and events, including date-based filtering.
- Responsive interface: Black-and-gray cybersecurity theme with light/dark appearance options.
- Automated tests: Django tests for core monitoring and email-analysis functionality.
Privacy note: The email analyzer is intended for sample messages. It does not access an inbox or open submitted links, and it stores redacted analysis results rather than the full email body.
Technology stack
Layer	Technology
Frontend	HTML, CSS, JavaScript
Backend	Python, Django
Local database	SQLite
Optional hosted database	PostgreSQL via DATABASE_URL
Deployment configuration	Render, Gunicorn, WhiteNoise
Tests	Django test framework


Run locally (Windows)
1. Install Python and open the project folder (the one containing manage.py) in VS Code.
2. Open the VS Code terminal and run:
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py seed_demo
$env:SENTINEL_MODE="demo"
py manage.py runserver 127.0.0.1:8000 --noreload
3. Open http://127.0.0.1:8000/ in your browser.
For additional instructions, see [`START_HERE_WINDOWS.md`](START_HERE_WINDOWS.md).
Run tests
py manage.py test sentinel.tests -v 2
Demonstrate the application
1. Open the dashboard and review simulated event activity.
2. Trigger a normal-login scenario and confirm it does not create a suspicious-activity alert.
3. Trigger a failed-login or other suspicious scenario and review the resulting alert.
4. Open Email Analyzer, analyze a normal sample, then analyze a suspicious sample.
5. Review the resulting records in Detection History and toggle a detection rule to show how alert generation changes.
See [`EMAIL_ANALYZER_GUIDE.md`](EMAIL_ANALYZER_GUIDE.md) and [`PRESENTATION_DEMO_SCRIPT.md`](PRESENTATION_DEMO_SCRIPT.md).
Database and data protection
Django models define the event, rule, and alert records. Local development uses SQLite; hosted deployments can use PostgreSQL. Do not commit local database files, .env files, passwords, API keys, or actual personal email content.

The current uploaded version is a shared classroom demo. Public self-service registration, per-user data isolation, and database encryption are planned improvements, not implemented features in this version. Do not deploy this build as a public multi-user security service without completing those controls and testing them.
Deployment
See [`PUBLIC_WEBSITE_SETUP.md`](PUBLIC_WEBSITE_SETUP.md) for the existing public demo deployment configuration. Use persistent database storage and environment variables for secrets. Public demo visitors currently share demo data.
Project structure
Python_Sentinel_Django/
├── manage.py
├── requirements.txt
├── sentinel/
│   ├── models.py            # Database models
│   ├── services.py          # Event processing and detection rules
│   ├── email_analysis.py    # Phishing indicator analysis
│   ├── email_service.py     # Email analysis integration
│   ├── views.py             # Django views and API endpoints
│   ├── templates/           # HTML interface
│   ├── static/              # CSS, JavaScript, images
│   └── tests/               # Automated tests
├── sentinel_site/           # Django configuration
├── data/                    # Local database directory (private)
└── PUBLIC_WEBSITE_SETUP.md
Limitations and roadmap
- Demo events are simulated and must not be presented as real incidents.
- Phishing detection is heuristic: results are indicators, not definitive proof that an email is malicious or safe.
- Live Windows event collection depends on Windows permissions and environment configuration.
- Planned: Django signup/login, individual user dashboards, account-level access controls, and encryption of sensitive stored data.
License
This project is licensed under the MIT License. See the LICENSE file for details.
