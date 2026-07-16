# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV WORKDIR=/app

# Set workspace directory
WORKDIR ${WORKDIR}

# Install essential system dependencies (such as PostgreSQL client libraries and compilation tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv by copying it from the official Docker image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (improving build performance and caching)
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application files
COPY . .

# Install/sync the project package
RUN uv sync --frozen --no-dev

# Make entrypoint.sh executable
RUN chmod +x entrypoint.sh

# Expose Django port
EXPOSE 8000

# Set entrypoint (which defaults to starting Gunicorn if no command is override)
ENTRYPOINT ["/app/entrypoint.sh"]

