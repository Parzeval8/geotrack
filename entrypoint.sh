#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
python manage.py makemigrations --no-input
python manage.py migrate --no-input

echo "Seeding database..."
python manage.py seed_cars

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000