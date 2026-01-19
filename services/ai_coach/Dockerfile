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
    PYTHONPATH=/app

# Install dependencies directly
RUN uv pip install --system \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "pydantic>=2.10.0" \
    "pydantic-settings>=2.0.0" \
    "pydantic-ai>=0.0.24" \
    "httpx>=0.27.0" \
    "redis>=5.0.0"

# Copy AI Coach source code
COPY services/__init__.py ./services/
COPY services/ai_coach/ ./services/ai_coach/

# Port
EXPOSE 8001

# Run the app
CMD ["uvicorn", "services.ai_coach.src.api:app", "--host", "0.0.0.0", "--port", "8001"]

