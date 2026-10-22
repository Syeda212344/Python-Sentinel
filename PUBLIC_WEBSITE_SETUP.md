# Python Sentinel — publish as a website that anyone can open

This is the **public Django demo**. It is not an endpoint security service and does not
scan visitors' computers. Every suspicious event generated in this version is
explicitly simulated. Visitors all share the same demo data and rule settings.

## What is different from the local Windows edition?

- Same black/white/gray logo, opening animation, dashboard, Events, Alerts,
  Detection Rules, Detection History, Django logic, and simulated scenarios.
- Removed the Dashboard “Presentation Checklist” block.
- Removed localhost-only copy and outdated SQLite claims from the public UI.
- Added Render build/start scripts, WSGI, production Django security/static settings.
- Added `DATABASE_URL` support so public hosting uses **persistent PostgreSQL**.
- `SENTINEL_PUBLIC_DEMO=1` prevents real Windows event monitoring in the public version.
- POST API requests are gently throttled as a basic precaution. The demo is shared
  across visitors, not isolated or authenticated.

## Publish on Render (website) + Neon (database)

These steps require a GitHub account, a Neon account, and a Render account.
All services offer starter/free options; check current limits before creating
resources. YOU DO NOT NEED TO EXPOSE YOUR CAMPUS WINDOWS LAPTOP TO THE INTERNET.

### 1. Check the ZIP folder

Extract the ZIP and enter **Python_Sentinel_Django**. You should see
`render.yaml`, `build.sh`, `start_render.sh`, `requirements.txt`, and `manage.py`
all in the same folder. Do **not** upload `*.db`, `.env`, passwords, or campus logs.

### 2. Put the contents of the extracted folder into a GitHub repository

Create a new **empty** repository, such as `python-sentinel`, on https://github.com.
Open the **Python_Sentinel_Django** folder in VS Code. In its PowerShell terminal:

    git init
    git add .
    git commit -m "Prepare Python Sentinel public Django demo"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/python-sentinel.git
    git push -u origin main

Replace YOUR_USERNAME with your actual GitHub username. If Git prompts for an
account sign-in, use the browser authentication flow. If Git says it is not
recognized, install Git for Windows (https://git-scm.com/downloads/win).

The GitHub repository root must show `render.yaml` and `manage.py`.
Do not push the ZIP as a single file; the hosting platform needs the source files.

### 3. Create the persistent Neon PostgreSQL database

Go to https://console.neon.tech and create a PostgreSQL project named
`python-sentinel`. Copy its connection string (a DATABASE_URL beginning
`postgresql://`, typically containing `sslmode=require`).

**Keep this URL private.** It contains database credentials.

Why? Free Render web services have an ephemeral filesystem and their local SQLite
database does not survive restart or spin-down. Neon preserves the example data.
Render free PostgreSQL has a 30-day expiry, so Neon avoids that particular
deadline issue. See the providers' official sites for updated pricing/limits.

### 4. Connect GitHub to Render and deploy

1. Go to https://dashboard.render.com and choose **New > Blueprint**.
2. Connect your GitHub account and choose your new source-code repository.
3. Render reads `render.yaml`. Choose to apply the Blueprint.
4. When prompted, enter **DATABASE_URL** using the private Neon connection
   string you copied. Leave `SENTINEL_SECRET_KEY` to be automatically generated.
5. Confirm a Free web service if available; deploy.
6. Watch the build logs for `collectstatic`, then startup logs for `migrate`,
   `seed_demo`, and `gunicorn`.
7. When marked Live, open the unique HTTPS **.onrender.com** link assigned to
   your service. This is the public link you can share.

The hosting name/URL is assigned by Render. It cannot be known in advance.

### 5. Check real public behavior

Open the HTTPS link from a phone or another computer (not only your laptop).
Verify:
- Animated square PS logo, black/gray appearance, and theme switch.
- The Dashboard shows “How the System Works” but no presentation checklist.
- Demo Mode is visible; seed_demo creates a 75-day **simulated** event history.
- Click Start Monitoring, then Normal Login (no new alert), then Failed Login
  (new alert). Open its details, and check the event/rule IDs.
- Test last 30 days and custom date filters in Detection History.
- Reload the page and verify existing events remain (persistent database).

### 6. If the deployment fails

- **Invalid URL / `DATABASE_URL`**: Use the exact connection string supplied
  by Neon and include its required SSL parameters.
- **DisallowedHost**: Render must provide `RENDER_EXTERNAL_HOSTNAME` automatically.
  For a custom domain, add it using `SENTINEL_EXTRA_HOSTS=your.domain`.
- **CSRF error**: The site must be opened with **HTTPS** and the deployed host
  must be listed in the Django allowed-host configuration.
- **White page or missing CSS**: Check `python manage.py collectstatic --noinput`
  completed during the build.
- **Application error**: Open Render service > Logs; do not publicly paste
  credentials or the complete `DATABASE_URL`.
- **The free instance sleeps**: Wait while it wakes; this is normal on a Free
  Render web service.
- **POST request limit**: Wait a minute before running more scenarios.

### Local Windows run (unchanged)

Open the extracted folder. Double-click `START_DEMO.bat`, or in PowerShell:

    py -m pip install -r requirements.txt
    py manage.py migrate
    py manage.py seed_demo
    py manage.py runserver 127.0.0.1:8000 --noreload

Open http://127.0.0.1:8000/ on the same computer.

## Important deployment and security boundaries

1. This is a **classroom demo**, not a hardened public SIEM. It is intended for
   modest audience traffic. Do not publish it as a production security product
   without accounts, per-user database separation, auditing, stronger rate limits,
   security reviews, and monitoring/backup procedures.
2. All visitors share demo events, alerts, and detection rules. If one visitor
   toggles a rule, other visitors see the change. This is expected for a demo.
3. No one should enter real student names, passwords, Windows security logs,
   campus system records, IP data, or any confidential data into the public demo.
4. Render's Free web service may spin down when idle. The Neon database remains
   separate and preserves state, subject to its own plan limits.
5. Public demo mode NEVER attempts to capture actual visitors' Windows event logs.
   The original Windows-specific collector still exists for local Windows testing.
6. Your course may require describing all tools/collaboration used; follow the
   professor's submission/disclosure requirements. The app UI itself uses
   project-specific branding, not development-tool advertising.
