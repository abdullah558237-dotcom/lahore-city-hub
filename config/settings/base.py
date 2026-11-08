import os
import sys
from pathlib import Path

# python-decouple integration with graceful fallback
try:
    from decouple import config, Csv
except ImportError:
    def config(key, default=None, cast=None):
        val = os.getenv(key, default)
        if val is None:
            return default
        if cast is bool and isinstance(val, str):
            return val.lower() in ('true', '1', 't', 'yes')
        if callable(cast):
            return cast(val)
        return val

    class Csv:
        def __init__(self, cast=None, delimiter=',', strip=True):
            self.cast = cast
            self.delimiter = delimiter
            self.strip = strip

        def __call__(self, value):
            if isinstance(value, (list, tuple)):
                return list(value)
            parts = str(value).split(self.delimiter)
            if self.strip:
                parts = [p.strip() for p in parts]
            if self.cast:
                parts = [self.cast(p) for p in parts]
            return parts


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add apps directory to Python path
sys.path.insert(0, str(BASE_DIR / 'apps'))

# Core Security
SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-lahore-city-hub-vibe-core-2026-key-development')
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='127.0.0.1,localhost,0.0.0.0', cast=Csv())

# Baseline Security Headers & Clickjacking Protection
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Custom User Model (Mandated by Architecture before first migration)
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Application definition
INSTALLED_APPS = [
    # Core Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    # Approved Domain Applications
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.places.apps.PlacesConfig',
    'apps.restaurants.apps.RestaurantsConfig',
    'apps.hospitals.apps.HospitalsConfig',
    'apps.education.apps.EducationConfig',
    'apps.jobs.apps.JobsConfig',
    'apps.businesses.apps.BusinessesConfig',
    'apps.transport.apps.TransportConfig',
    'apps.events.apps.EventsConfig',
    'apps.updates.apps.UpdatesConfig',
    'apps.reviews.apps.ReviewsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR / 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_city_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Default Database: SQLite for development (cast to str for legacy compatibility)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / config('SQLITE_DB_NAME', default='db.sqlite3')),
    }
}

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

# Authentication URLs & Redirection
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

# Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Karachi'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [str(BASE_DIR / 'static')]
STATIC_ROOT = str(BASE_DIR / 'staticfiles')

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = str(BASE_DIR / 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# In-Memory Cache for fast query and taxonomy caching (No external infrastructure required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'lahore-city-hub-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# SQLite schema alteration safety for SQLite 3.26+ table rebuilds
from django.db.backends.signals import connection_created
def configure_sqlite_connection(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA legacy_alter_table = ON;')
        cursor.execute('PRAGMA foreign_keys = OFF;')
connection_created.connect(configure_sqlite_connection)

# Logging Architecture
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('DJANGO_LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Cookie & CSRF Configuration for Browser Compatibility
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days

# Search Engine Console Verification
GOOGLE_SITE_VERIFICATION = config('GOOGLE_SITE_VERIFICATION', default='')

