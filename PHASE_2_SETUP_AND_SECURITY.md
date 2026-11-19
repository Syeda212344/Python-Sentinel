# Python Sentinel — Phase 2 user data isolation

## Setup (Windows / VS Code)
1. Extract this ZIP. Open `Python_Sentinel_Email_Analyzer_Updated/Python_Sentinel_Django` in VS Code.
2. Make a copy of your existing `data/sentinel.db` **outside the project** before changing anything. If you want to keep your existing accounts, copy that database into `data/sentinel.db` before running migrations. Do not commit the database to GitHub.
3. Run `py -m pip install -r requirements.txt`, `py manage.py migrate`, `py manage.py check`, then `py manage.py test sentinel.tests.test_user_isolation`.
4. Run `py manage.py runserver 127.0.0.1:8000 --noreload`.

## Changes
- Event records now have an optional Django user owner. Alerts and detection history are scoped through their event owner. Email-analysis summary events are also owned by the user who submitted them.
- Dashboard, lists, details, review operations, summary, and activity chart are scoped to the signed-in user.
- Simulated events and historical seed data are owned by the initiating user. Historical seeding is idempotent **per user**.
- Shared detection rules remain global; only staff may change them. Real Windows collection is a machine-wide resource, and start/stop is staff-only in Windows mode. The demo monitor start/stop flag is shared across accounts.
- Existing events are left **unassigned (owner=NULL)** by the migration. They are intentionally hidden from normal user dashboards, not deleted. This means counts may initially be zero. Do not assign legacy records to an arbitrary user.

## Security limitations / next phase
- Django stores account passwords using password hashing; passwords are **not reversible encryption**.
- Raw email text, sender addresses and links are **not stored** by the email analyzer. Its risk summary and indicator labels are stored in the owned event.
- **SQLite at-rest encryption has not been implemented.** Use OS disk encryption, restricted filesystem permissions and secure backups locally. For production, use an encrypted managed database and HTTPS, plus environment-managed secrets.
- Rules and the monitor's active state are shared system resources, not private per-user configuration. Windows background telemetry is unassigned and not displayed to ordinary accounts.
- Do not publicly deploy until production security, rate limits, HTTPS, CSRF, database backups, and multi-user testing have been reviewed.
