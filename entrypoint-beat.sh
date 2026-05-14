#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait until django_celery_beat_periodictask table exists
# This ensures migrations have completed before beat starts
echo "Waiting for migrations to complete..."
until python manage.py shell -c "from django_celery_beat.models import PeriodicTask; PeriodicTask.objects.exists()" 2>/dev/null; do
  echo "Migrations not ready yet — retrying in 2 seconds..."
  sleep 2
done

echo "Migrations confirmed — starting Celery beat..."
celery -A geotrack beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler