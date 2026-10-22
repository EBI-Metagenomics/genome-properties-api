"""Django settings for the Genome Properties GraphQL API."""

import logging

from pathlib import Path

from corsheaders.defaults import default_headers
from decouple import Csv, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)


def _extend_allowed_hosts(hosts, *extra):
    allowed = list(hosts)
    for host in extra:
        if host and host not in allowed:
            allowed.append(host)
    return allowed


# Public hostnames from env. Kubelet probes use the pod IP as HTTP Host, so
# append POD_IP when the downward API provides it.
_configured_hosts = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
ALLOWED_HOSTS = _extend_allowed_hosts(_configured_hosts, config("POD_IP", default=""))

FORCE_SCRIPT_NAME = config("DJANGO_FORCE_SCRIPT_NAME", default="") or None

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_filters",
    "graphene_django",
    "web.apps.WebConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = config("DJANGO_CORS_ALLOW_ALL", default=DEBUG, cast=bool)

CORS_ALLOWED_ORIGINS = [f"http://{h}" for h in _configured_hosts] + [
    f"https://{h}" for h in _configured_hosts
]
if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
logger.info("ALLOWED_HOSTS: %s", ALLOWED_HOSTS)
logger.info("CORS_ALLOWED_ORIGINS: %s", CORS_ALLOWED_ORIGINS)

CORS_ALLOW_HEADERS = list(default_headers) + ["apollo-require-preflight"]

ROOT_URLCONF = "genomeproperties.urls"
WSGI_APPLICATION = "genomeproperties.wsgi.application"
ASGI_APPLICATION = "genomeproperties.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASE_PATH = Path(config("DATABASE_PATH", default=str(BASE_DIR / "genome_properties.db")))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = BASE_DIR / DATABASE_PATH

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATABASE_PATH),
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = config("DJANGO_STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedStaticFilesStorage"
        ),
    },
}
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

GRAPHENE = {
    "SCHEMA": "genomeproperties.schema.schema",
}

if DEBUG:
    GRAPHENE["MIDDLEWARE"] = ["graphene_django.debug.DjangoDebugMiddleware"]

from genomeproperties import static_handler as _static_handler  # noqa: E402,F401
