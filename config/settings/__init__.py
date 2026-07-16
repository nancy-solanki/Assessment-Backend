import os

# Determine the Django environment: 'local' or 'production'
# Defaults to 'local' for local development
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'local').lower()

if DJANGO_ENV == 'production':
    from .production import *
else:
    from .local import *
