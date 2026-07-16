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

echo "Starting command: $@"
exec "$@"
