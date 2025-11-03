"""
Django settings for genomeproperties project.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

import yaml

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# Load application configuration
try:
    with open(BASE_DIR / "config" / "gp.yml") as f:
        GP_CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    GP_CONFIG = {}

try:
    with open(BASE_DIR / "config" / "gp.local.yml") as f:
        GP_CONFIG_LOCAL = yaml.safe_load(f)
except FileNotFoundError:
    GP_CONFIG_LOCAL = {}

# Merge local config over base config
for key in GP_CONFIG_LOCAL:
    GP_CONFIG[key] = GP_CONFIG_LOCAL.get(key, None)

# Load secrets configuration
try:
    with open(BASE_DIR / "config" / "secrets.yml") as f:
        SECRETS_CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    raise RuntimeError(
        "secrets.yml not found. Please copy config/secrets-template.yml to "
        "config/secrets.yml and configure your secrets."
    )

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRETS_CONFIG.get("secret_key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = GP_CONFIG.get("debug", False)

ALLOWED_HOSTS = GP_CONFIG.get("allowed_host", [])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'web',
    'graphene_django',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',
    'https://localhost:3000',
    'http://127.0.0.1:3000',
    'https://127.0.0.1:3000',
]

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'genomeproperties.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'genomeproperties.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
# SQLite3 optimized for production use with WAL mode
# See: https://blog.pecar.me/sqlite-django-config

DB_PATH = SECRETS_CONFIG.get("database", {}).get("name", "../database/db.sqlite3")
if not Path(DB_PATH).is_absolute():
    DB_PATH = str(BASE_DIR / DB_PATH)

DATABASES = {
    "default": {
        "ENGINE": "genomeproperties.db_backend",
        "NAME": DB_PATH,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = GP_CONFIG.get("static_url", "/static_files/")
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "static_files"))

GRAPHENE = {
    'SCHEMA': 'genomeproperties.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ]
}
