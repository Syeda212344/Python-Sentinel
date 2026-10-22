"""WSGI server entry point for Gunicorn / Render."""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sentinel_site.settings")
application = get_wsgi_application()
