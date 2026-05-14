import os
from celery import Celery

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geotrack.settings')

app = Celery('geotrack')

# Load Celery configuration from Django settings using the CELERY_ namespace
# This means all Celery config keys in settings.py must start with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
# Celery will look for a tasks.py file in each app
app.autodiscover_tasks()