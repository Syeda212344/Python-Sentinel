# Python Sentinel — Black/Gray Edition

This project supports both **local Windows demo/testing** and an **online public Django demo**.

**To put it online and get a public link, start with
[PUBLIC_WEBSITE_SETUP.md](PUBLIC_WEBSITE_SETUP.md).**

The public site uses simulated security events, not visitors' Windows logs. The public
demo shares data across visitors and is not a production security monitoring service.

---

# Python Sentinel — Django Edition (Fall 2026)

Cybersecurity-themed localhost capstone application based on the provided Python Sentinel SRS and prototype. Frontend: HTML, CSS, vanilla JavaScript. Backend: Python/Django. Database: SQLite.

**Download on Windows, extract the folder, then read `START_HERE_WINDOWS.md` first.**

### Quick start (Windows / PowerShell)

```powershell
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py seed_demo
py manage.py runserver 127.0.0.1:8000 --noreload
```

Visit `http://127.0.0.1:8000/`.

The optional convenience file `START_DEMO.bat` installs requirements and launches the Django development server.

### Classroom demonstrations

- Animated 3D-effect PS shield splash + persistent light/dark theme switch.
- Dashboard with monitoring control, simulation buttons, 30-day activity chart, recent events and alerts.
- 8 predefined anomaly rules + a normal-login no-alert control.
- Event History, Alert History, Alert Details, Rules on/off, date-filtered Detection History.
- Seeded historical examples for 75 days, plus a custom-date scenario generator.
- Explicit labels on all fictional test data; no actual attacks are performed.

### Testing

```powershell
py manage.py test sentinel.tests -v 2
```

### Important limitations

This is a Django development server for localhost only; security incidents in demo mode are simulated. Windows mode needs permitted Windows logs plus `pywin32`, and Windows-mode behavior is not validated by the offline project package. See `SRS_TRACEABILITY.md`.

## New optional capstone extension: Phishing Email Analyzer

The left navigation now includes **Email Analyzer**, which checks pasted sample text for explainable phishing indicators, displays the result, and stores **redacted** analysis outcomes through the existing Event → Detection Rule → Alert workflow. It does not access a mailbox or open links. The original dashboard and black/gray logo remain unchanged; no presentation checklist is shown.

See **[EMAIL_ANALYZER_GUIDE.md](EMAIL_ANALYZER_GUIDE.md)** for startup commands, demo steps, limitations, privacy controls, and verification tests.
