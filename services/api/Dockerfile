# API Dockerfile for Workout Tracker
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies from pyproject.toml
COPY pyproject.toml uv.lock ./
COPY services/__init__.py ./services/
COPY services/shared/ ./services/shared/
COPY services/api/ ./services/api/
RUN uv sync --no-dev --no-install-project

# Create directory for database
RUN mkdir -p /app/data

# Port
EXPOSE 8000

# Run the app
CMD ["python", "-m", "uvicorn", "services.api.src.api:app", "--host", "0.0.0.0", "--port", "8000"]
