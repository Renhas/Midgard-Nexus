#!/bin/sh

mkdir -p /app/staticfiles /app/media
chown -R django:django /app/staticfiles /app/media

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo "⏳ Waiting for database..."

while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
    sleep 1
done

echo "✅ Database is ready"

if [ ! -f /app/src/static/vendor/htmx/htmx.min.js ]; then
    echo "📦 Vendor static missing, downloading..."
    /app/download_static.sh
fi

python src/manage.py migrate

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "👤 Creating superuser if not exists..."
    python src/manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print('👤 Superuser created.')
else:
    print('👤 Superuser already exists.')
    "
fi

if [ "${COLLECTSTATIC:-0}" = "1" ]; then
    python src/manage.py collectstatic --noinput
fi

echo "🚀 Server starting..."

exec gosu django "$@"
