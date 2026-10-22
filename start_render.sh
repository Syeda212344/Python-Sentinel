#!/usr/bin/env bash
set -euo pipefail
# Persistent Postgres is required for this public mode.
python manage.py migrate --noinput
python manage.py seed_demo
exec gunicorn sentinel_site.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 1 --threads 4 --timeout 120 --access-logfile -
