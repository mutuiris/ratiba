#!/bin/bash
set -euo pipefail

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed

echo "Starting Gunicorn."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --access-logfile - --error-logfile -
