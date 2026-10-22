"""Python Sentinel configuration for local Windows/Mac demo and public HTTPS hosting.

Local mode keeps SQLite and DEBUG enabled. Set SENTINEL_PUBLIC_DEMO=1
on a public host; that mode requires a secret and a persistent DATABASE_URL.
"""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DEMO = os.environ.get("SENTINEL_PUBLIC_DEMO", "").strip().lower() in ("1", "true", "yes")
SECRET_KEY = os.getenv("SENTINEL_SECRET_KEY", "")
if PUBLIC_DEMO and (len(SECRET_KEY) < 32):
    raise ImproperlyConfigured("Set a private SENTINEL_SECRET_KEY (32+ characters) on the public host.")
if not SECRET_KEY:
    SECRET_KEY = "development-local-only-python-sentinel-change-for-deployment"

DEBUG = (not PUBLIC_DEMO) and os.getenv("SENTINEL_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
additional_hosts = [h.strip() for h in os.getenv("SENTINEL_EXTRA_HOSTS", "").split(",") if h.strip()]
ALLOWED_HOSTS.extend(([render_host] if render_host else []) + additional_hosts)
CSRF_TRUSTED_ORIGINS = ["https://" + h for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1", "testserver")]

INSTALLED_APPS = ["django.contrib.staticfiles", "sentinel"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if PUBLIC_DEMO:
    MIDDLEWARE.append("sentinel.public_safety.PublicDemoRateLimitMiddleware")
ROOT_URLCONF = "sentinel_site.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": []},
}]
database_url = os.getenv("DATABASE_URL", "").strip()
if PUBLIC_DEMO and not database_url:
    raise ImproperlyConfigured("Public deployment needs a persistent DATABASE_URL (e.g. Neon Postgres).")
if database_url:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(database_url, conn_max_age=60, conn_health_checks=True)}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "data" / "sentinel.db",
        "OPTIONS": {"timeout": 10}
    }}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_TZ = False  # Keep the original app's local clock behavior.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

if PUBLIC_DEMO:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
