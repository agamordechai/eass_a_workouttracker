# AI Workout Coach Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
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
COPY services/ai_coach/pyproject.toml ./pyproject.toml
COPY services/__init__.py ./services/
COPY services/ai_coach/ ./services/ai_coach/
RUN uv sync --no-dev --no-install-project

# Port
EXPOSE 8001

# Run the app
CMD ["python", "-m", "uvicorn", "services.ai_coach.src.api:app", "--host", "0.0.0.0", "--port", "8001"]

