from .base import *

DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='*', cast=Csv())

# CSRF Trusted Origins for HTTPS form submissions (Django 4.0+)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://lahorecityhub.pk,https://www.lahorecityhub.pk,https://*.vercel.app,https://*.onrender.com',
    cast=Csv()
)

# Reverse Proxy SSL Header (Nginx / Cloudflare / Render / Railway / AWS ALB)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# PostgreSQL Production Database Configuration
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=config('DB_CONN_MAX_AGE', default=600, cast=int),
                conn_health_checks=True,
            )
        }
    except ImportError:
        if DATABASE_URL.startswith('sqlite:'):
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': DATABASE_URL.replace('sqlite:///', ''),
                }
            }
        else:
            DATABASES = {
                'default': {
                    'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
                    'NAME': config('DB_NAME', default='lahore_city_hub'),
                    'USER': config('DB_USER', default='postgres'),
                    'PASSWORD': config('DB_PASSWORD', default=''),
                    'HOST': config('DB_HOST', default='localhost'),
                    'PORT': config('DB_PORT', default='5432'),
                    'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
                }
            }
else:
    # Standard PostgreSQL production settings with environment overrides
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': config('DB_NAME', default='lahore_city_hub'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
        }
    }

# Production Security Headers & SSL Hardening
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# WhiteNoise for Static Assets in Production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Media Storage Configuration: Local Volume or S3-Compatible Cloud Storage
MEDIA_STORAGE_BACKEND = config('MEDIA_STORAGE_BACKEND', default='local').lower()
if MEDIA_STORAGE_BACKEND == 's3':
    try:
        import storages
        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
        AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
        AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='ap-south-1')
        AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default=None)
        AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default=None)
        AWS_DEFAULT_ACL = 'public-read'
        AWS_QUERYSTRING_AUTH = False
        AWS_S3_FILE_OVERWRITE = False
    except ImportError:
        pass  # Falls back to local FileSystemStorage defined in base.py

# Production Logging Architecture (12-Factor App Console Logging)
LOGGING['handlers']['console']['formatter'] = 'verbose'
LOGGING['root']['level'] = config('DJANGO_LOG_LEVEL', default='INFO')
