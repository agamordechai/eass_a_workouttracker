# Worker Service Dockerfile
FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies from pyproject.toml
COPY services/worker/pyproject.toml ./pyproject.toml
COPY services/__init__.py /app/services/
COPY services/shared/ /app/services/shared/
COPY dev/ /app/dev/
COPY services/worker/ /app/services/worker/
RUN uv sync --no-dev --no-install-project

# Expose health check port
EXPOSE 8002

# Run worker
CMD ["python", "-m", "services.worker.src.worker"]
