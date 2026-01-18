#!/usr/bin/env bash
set -e

# Wait for DB (optional; adjust host/port if needed)
# while ! nc -z "$DB_HOST" "$DB_PORT"; do sleep 1; done

cd backend
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:"${PORT:-8000}" --workers 3