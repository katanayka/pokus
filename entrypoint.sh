#!/bin/sh
set -e

attempts=30
until python manage.py migrate --noinput; do
  attempts=$((attempts - 1))
  if [ "$attempts" -le 0 ]; then
    echo "Database not ready; giving up."
    exit 1
  fi
  echo "Waiting for database... ($attempts retries left)"
  sleep 2
done

python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application -b 0.0.0.0:8000
