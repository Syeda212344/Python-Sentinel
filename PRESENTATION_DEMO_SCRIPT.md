# Python Sentinel — 6–8 minute classroom demo (Fall 2026)

## Before the professor arrives

1. Connect your Windows laptop to a power source. Open the project in VS Code.
2. Start `START_DEMO.bat`, or run `py manage.py migrate`, `py manage.py seed_demo`, and `py manage.py runserver 127.0.0.1:8000 --noreload`.
3. Open `http://127.0.0.1:8000/` in the browser, verify the splash, and refresh once.
4. Check that Detection History -> Last 30 Days shows sample alerts. (They are synthetic examples, **not actual security incidents**.)
5. Keep the terminal minimized but available if the professor wants to see Django running.

## Suggested shared speaking script

**Presenter 1 — Project introduction (45 seconds)**

> Our project is Python Sentinel, an Automated Monitoring and Alert Platform. It is a local Python/Django application designed to monitor supported Windows events, analyze them against enabled predefined rules, store results in SQLite, and display alerts in a readable dashboard. Our interface follows the prototype: Dashboard, Events, Alerts, Detection Rules, and Detection History. For this classroom demo we're showing labeled simulated security events so the workflow can be tested without generating real attacks.

**Presenter 2 — Frontend (60 seconds)**

- Refresh the browser. Show the animated PS logo intro and the warm-blue cybersecurity dashboard.
- Toggle between light and dark mode, noting that preference is saved locally.
- Show Events, Alerts, and Detection Rules navigation.

**Presenter 3 — Core detection and database (2 minutes)**

- On Dashboard, click **Start Monitoring**.
- Click **Normal Login**: explain that the event is stored but no detection rule matches.
- Click **Failed Login**: explain that an enabled rule with pattern `FAILED_LOGIN` matches this event type and an alert is generated.
- Click **Suspicious Process** or **Account Lockout**: show different rules and severity levels.
- Open **Alerts** -> open the newest alert. Show **Event ID** and **Rule ID** relationships and the alert's severity, description and time. Mark it **Reviewed**.
- Visit **Detection Rules**, disable **Failed Login Detection**, click Failed Login again, and explain the new event produces no new alert. Re-enable the rule.

**Presenter 4 — History, Django, testing (2 minutes)**

- Open **Detection History**. Choose Last 2 Days, Last 30 Days and Last 2 Months; click Apply each time.
- Explain that historical examples were loaded with `py manage.py seed_demo`, and their source names explicitly begin `SIMULATED HISTORY`.
- Choose a past date on Dashboard in **Simulate a Specific Date**, generate records, and show the automatic navigation to that day's Detection History.
- Switch to VS Code: show `sentinel/models.py` (three SQLite tables), `sentinel/services.py` (rule evaluation + linked alerts), `sentinel/views.py` (API), and `sentinel/static/sentinel/app.js` (browser requests).
- Run `py manage.py test sentinel.tests -v 2` and discuss actual observed test results.

**Close (20 seconds)**

> Python Sentinel demonstrates the complete process from event input to validation, rule matching, alert creation, storage, and dashboard review. The app also has a Windows Event Log collector for permitted Windows environments. The classroom data is simulated and is not a substitute for validating live collection on the target laptop.

## Most common professor questions

**Q: Is this just a frontend mockup?**
A: No. The browser calls Django endpoints, which use Django ORM to store events, rules, and alerts in a real SQLite database. Toggling an enabled rule changes how subsequent events are detected. The sample telemetry is synthetic, but the detection and storage pipeline executes.

**Q: Can it really read Windows events?**
A: Optional Windows mode uses pywin32 to access supported logs, mapping 4625 to failed-login and 4624 to normal-login events. We must verify access/permissions on the actual Windows machine before claiming live collection succeeded.

**Q: How do you know alerts are correct?**
A: Unit/integration tests include normal events, enabled-rule matches, disabled-rule non-matches, error input and event/rule foreign key relationships. We show the test output from the current laptop.

**Q: Where is the data kept?**
A: SQLite `data/sentinel.db`, with core tables `events`, `detection_rules`, and `alerts` as in the SRS.

**Q: Is this enterprise SIEM?**
A: No, the SRS explicitly limits scope to selected rules, selected Windows sources, and a course-scale deployment. It does not include ML detection, automated remediation, packet inspection, or enterprise integrations.
