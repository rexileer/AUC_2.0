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

# Collect static files and ensure pl.js exists
echo "Collecting static files..."
# Ensure directories for pl.js exist
mkdir -p backend/staticfiles/admin/js/vendor/select2/i18n

# Ensure pl.js file exists
if [ ! -f backend/staticfiles/admin/js/vendor/select2/i18n/pl.js ]; then
    echo "Creating missing pl.js file..."
    echo "(function ($) {
        $.extend($.fn.select2.amd, {
            default: function () {
                return {
                    translations: {
                        pl: {
                            errorLoading: function () { return \\\"Nie można załadować wyników.\\\"; },
                            inputTooLong: function (args) { var overChars = args.input.length - args.maximum; return (\\\"Proszę usunąć \\\" + overChars + \\\" znak\\\" + (overChars === 1 ? \\\"\\\" : \\\"i\\\") + \\\".\\\"); },
                            inputTooShort: function (args) { var remainingChars = args.minimum - args.input.length; return (\\\"Proszę wpisać jeszcze \\\" + remainingChars + \\\" znak\\\" + (remainingChars === 1 ? \\\"\\\" : \\\"i\\\") + \\\".\\\"); },
                            loadingMore: function () { return \\\"Ładowanie więcej wyników...\\\"; },
                            maximumSelected: function (args) { return (\\\"Możesz wybrać tylko \\\" + args.maximum + \\\" element\\\" + (args.maximum === 1 ? \\\"\\\" : \\\"y\\\") + \\\".\\\"); },
                            noResults: function () { return \\\"Brak wyników.\\\"; },
                            searching: function () { return \\\"Wyszukiwanie...\\\"; },
                        },
                    },
                };
            },
        });
    })(jQuery);" > backend/staticfiles/admin/js/vendor/select2/i18n/pl.js
fi

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
