# Docker Compose Runbook

## Prerequisites

- Docker and Docker Compose installed
- `.env` file with `OPENAI_API_KEY` (for AI Coach)

## Quick Start

```bash
# Start all services
docker compose up -d

# Wait for services to be healthy
docker compose ps

# View logs
docker compose logs -f
```

## Services Overview

| Service | Port | Health Check URL |
|---------|------|------------------|
| API | 8000 | http://localhost:8000/health |
| AI Coach | 8001 | http://localhost:8001/health |
| Frontend | 3000 | http://localhost:3000 |
| PostgreSQL | 5432 | Internal only |
| Redis | 6379 | Internal only |

## Verifying Health

```bash
# Check all service statuses
docker compose ps

# Individual health checks
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8001/health | jq .

# Check rate limit headers (API)
curl -I http://localhost:8000/exercises
```

## Common Operations

### Restart a Service
```bash
docker compose restart api
docker compose restart ai-coach
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ai-coach
```

### Rebuild After Code Changes
```bash
docker compose build api
docker compose build ai-coach
docker compose up -d
```

### Reset Database
```bash
docker compose down -v
docker compose up -d
```

## Running Tests

### With Docker
```bash
# API tests
docker compose exec api pytest tests/ -v

# AI Coach tests (when installed)
docker compose exec ai-coach pytest tests/ -v
```

### Locally (outside Docker)
```bash
# Install dependencies
uv sync

# Run API tests
cd services/api && pytest tests/ -v

# Run AI Coach tests
cd services/ai_coach && pytest tests/ -v
```

## Schemathesis API Testing

```bash
# Install schemathesis
pip install schemathesis

# Run against API
schemathesis run http://localhost:8000/openapi.json

# Run against AI Coach
schemathesis run http://localhost:8001/openapi.json
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs <service-name>

# Check if port is in use
lsof -i :8000
lsof -i :8001
```

### Database Connection Issues
```bash
# Check database is running
docker compose ps db

# Connect to database
docker compose exec db psql -U workout -d workout_tracker
```

### AI Coach Not Responding
1. Check `OPENAI_API_KEY` is set in `.env`
2. Verify API is healthy: `curl http://localhost:8000/health`
3. Check Redis connection: `docker compose exec redis redis-cli ping`

## Stopping Services

```bash
# Stop but keep volumes
docker compose down

# Stop and remove volumes (data loss!)
docker compose down -v

# Stop specific service
docker compose stop ai-coach
```

