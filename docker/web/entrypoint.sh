#!/bin/sh

mkdir -p /app/staticfiles /app/media
chown -R django:django /app/staticfiles /app/media

echo "⏳ Waiting for database..."

while ! pg_isready -h db -p 5432 -U ${DB_USER} -d ${DB_NAME}; do
    sleep 1
done

echo "✅ Database is ready"

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

python src/manage.py collectstatic --noinput

echo "🚀 Server starting..."

exec gosu django "$@"