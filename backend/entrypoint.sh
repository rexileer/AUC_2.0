#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
sleep 30
echo "Database is ready!"

# Run migrations (skip if SKIP_MIGRATIONS is set)
if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput
else
    echo "Skipping migrations (SKIP_MIGRATIONS=true)"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (skip if SKIP_MIGRATIONS is set)
if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo "Creating superuser..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END
else
    echo "Skipping superuser creation (SKIP_MIGRATIONS=true)"
fi

# Load initial data if needed
if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo "Loading initial data..."
    python manage.py loaddata initial_data.json || echo "No initial data to load"
else
    echo "Skipping initial data loading (SKIP_MIGRATIONS=true)"
fi

# Start the server
echo "Starting Django server..."
exec "$@"
