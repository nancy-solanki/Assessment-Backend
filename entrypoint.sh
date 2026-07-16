#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run Django migrations
echo "Applying database migrations..."
uv run python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
uv run python manage.py collectstatic --noinput

# Seed database
echo "Seeding meals database..."
uv run python manage.py seed_meals

# Create superuser if environment variables are set
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    uv run python manage.py createsuperuser --noinput || echo "Superuser already exists or could not be created."
fi

if [ $# -eq 0 ]; then
    echo "Starting Gunicorn server on port ${PORT:-8000}..."
    exec uv run gunicorn \
        --bind "0.0.0.0:${PORT:-8000}" \
        --workers 3 \
        config.wsgi:application
else
    echo "Starting command: $@"
    exec "$@"
fi
