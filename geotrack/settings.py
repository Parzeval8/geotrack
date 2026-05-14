import os
from pathlib import Path
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings — loaded from environment variables to avoid hardcoding secrets
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # GeoDjango — enables geographic model fields and PostGIS backend
    'django.contrib.gis',

    # Third-party
    'rest_framework',        # REST API framework
    'django_filters',        # Queryset filtering via URL params
    'corsheaders',           # Cross-Origin Resource Sharing headers
    'drf_spectacular',       # OpenAPI 3 schema generation (Swagger UI)
    'django_celery_beat',    # Periodic task scheduling stored in DB

    # Local apps
    'fleet',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # CorsMiddleware must be placed before CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'geotrack.urls'

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

WSGI_APPLICATION = 'geotrack.wsgi.application'

# Database
# Uses PostGIS backend instead of standard PostgreSQL to enable
# geographic fields (PointField) and spatial queries (ST_DWithin)
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME', 'geotrack'),
        'USER': os.environ.get('DB_USER', 'geotrack'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'geotrack'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Allow all origins in development — restrict in production
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Django REST Framework
# AutoSchema enables drf-spectacular to auto-generate OpenAPI docs
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# Swagger / OpenAPI settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'GeoTrack API',
    'DESCRIPTION': 'Fleet tracking system with geographic data and weather integration',
    'VERSION': '1.0.0',
}

# Celery
# Redis is used as both the message broker and result backend
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TIMEZONE = 'America/Sao_Paulo'

# Simulation
# Controls how often the background task updates vehicle positions
SIMULATION_INTERVAL_SECONDS = int(os.environ.get('SIMULATION_INTERVAL_SECONDS', 30))

# Periodic tasks schedule
# simulate_fleet runs every SIMULATION_INTERVAL_SECONDS seconds
CELERY_BEAT_SCHEDULE = {
    'simulate-fleet': {
        'task': 'fleet.tasks.simulate_fleet',
        'schedule': SIMULATION_INTERVAL_SECONDS,
    },
}