#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U auction_user; do
    echo "Database is unavailable - sleeping"
    sleep 1
done
echo "Database is ready!"

# Skip migrations - they will be run manually
echo "Skipping automatic migrations..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Skip superuser creation for now
echo "Skipping superuser creation..."

# Skip initial data loading
echo "Skipping initial data loading..."

# Start the server
echo "Starting Django server..."
exec "$@"
