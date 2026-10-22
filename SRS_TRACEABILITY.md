# Python Sentinel — Mapping implementation to the supplied SRS and prototype

The original SRS asks for three relational entities (Events, Detection Rules, Alerts), a GUI/dashboard, log/event collection, rule-based analysis, notifications, data integrity, and testability. The prototype shows Dashboard, Events, Alerts, alert details, Detection Rules, and History. The Django app preserves this workflow as a **browser-based localhost GUI** instead of a traditional Windows desktop GUI.

| SRS requirement | Implementation |
|---|---|
| FR-01–FR-05 monitoring, collection, identification, details, operation | `sentinel/monitoring.py`, optional `sentinel/windows_events.py`, `Event` ORM model, start/stop API |
| FR-06–FR-10 analysis, active rules, detection, no false alerts | `sentinel/services.py` `rule_matches` and `process_event`, `DetectionRule.enabled` |
| FR-11–FR-18 alert creation, severity/time, description, notification and associations | `Alert` ORM model, transactional `process_event`, toast feedback, JS periodic alert checks |
| FR-19–FR-23 relational storage, rule maintenance, retrieval, integrity | `models.py`, `migrations/0001_initial.py`, Django ORM querysets, FK `PROTECT` |
| FR-24–FR-28 GUI/dashboard, event and alert displays, usability | Django `index.html`, warm-blue `style.css`, dynamic `app.js`, details and date filters |
| FR-29–FR-31 invalid input, monitoring/database errors | `validate_event`, Django guarded handlers, Windows collector warnings, API error responses |

## SRS-aligned table names and attributes

- **events**: `event_id`, `event_time`, `source`, `event_type`, `username`, `message`, `severity`
- **detection_rules**: `rule_id`, `rule_name`, `description`, `pattern`, `severity`, `enabled`
- **alerts**: `alert_id`, `event_id` FK, `rule_id` FK, `alert_time`, `severity`, `description`, `status`

Django adds its own `django_migrations` bookkeeping table automatically, which is not part of the three conceptual SRS entities.

## Scope / truthfulness

- **SIMULATED CLASSROOM MODE** emits predefined fake Windows-like events. Event sources are prefixed `SIMULATED /` or `SIMULATED HISTORY /`. Historical alert timestamps are deliberately set to event timestamps for an understandable date-filter demonstration.
- **WINDOWS MODE** attempts to poll Windows Security/System/Application event logs using pywin32; the collector maps Windows Event IDs 4625/4624 and optionally a watched file. The broader simulated anomaly types (process/privilege/account lockout/network/service/log cleared) are **not** claimed to be wired to native Windows event IDs. Real Windows collection remains unverified until tested with permission on Windows.
- Detection rules use a straightforward **case-insensitive exact event-type match**, not machine learning, multi-event correlations, or automatic blocking.
- Seeded historical data covers **the previous 75 days** relative to the date the seed command is run. For dates outside that span (today or earlier), users can generate **clearly labeled custom-date samples**. The app does not falsely show a detection on a date for which neither real nor simulated data was recorded.
- The project is **local classroom software only**: no user authentication, no production security hardening, and the Django development server must not be deployed on a public network.

## White-box verification

Run `py manage.py test sentinel.tests -v 2`; the test module covers matching/nonmatching/disabled branches, validation errors, ORM foreign keys, date boundaries, alert status, API errors and CSRF. Record actual run results, do not invent success counts.


## Optional professor-requested email analysis extension (after original SRS)

The **Email Analyzer** is additional, not part of the original Windows monitoring scope. It reuses SRS relationships among Events, Detection Rules, and Alerts. Proposed EXT-01–EXT-05, privacy limitations, and tests are documented in `EMAIL_ANALYZER_GUIDE.md`.
