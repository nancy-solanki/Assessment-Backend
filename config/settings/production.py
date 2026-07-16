import os
from .base import *

# Production environment configurations
DEBUG = False

# Enforce secure ALLOWED_HOSTS (never default to '*')
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip()]

# Auto-detect Render hosted environment
render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)

# Strict CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", os.environ.get("ALLOWED_ORIGINS", "")).split(",") if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins configuration
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()
]
if render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

# Production security headers and cookie policies
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False").lower() in ("true", "1", "yes")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Ensure SECRET_KEY is not empty or default insecure key in production
if not SECRET_KEY or SECRET_KEY == 'django-insecure-^xn1m_uoft1-&9hh2kk-gqabi7fz!s9kmowx5*etw12im_gfrf':
    raise ValueError("The SECRET_KEY environment variable is required and must not use the insecure default key in production.")

# Ensure DATABASE_URL is set in production
if not os.environ.get("DATABASE_URL"):
    raise ValueError("The DATABASE_URL environment variable is required in production.")

