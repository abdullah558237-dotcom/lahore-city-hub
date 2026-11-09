from .base import *

DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

# Allow all hosts for local dev and public tunneling (localhost.run, pinggy, etc.)
ALLOWED_HOSTS = ['*']

# Console email backend for local development and testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache: LocMemCache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'lahore-city-hub-dev-cache',
    }
}
