# EX3 Capstone Notes - Workout Tracker

## Architecture Overview

The Workout Tracker application consists of **4 cooperating microservices**:

```
┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│   Workout API   │
│  (React + Vite) │     │    (FastAPI)    │
│   Port: 3000    │     │   Port: 8000    │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Coach      │     │   PostgreSQL    │     │     Redis       │
│  (Pydantic AI)  │────▶│    Database     │     │    (Cache)      │
│   Port: 8001    │     │   Port: 5432    │     │   Port: 6379    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Services

1. **Workout API** (`services/api/`) - Core FastAPI backend with CRUD operations for exercises
2. **PostgreSQL** - Persistent storage for workout data
3. **Frontend** (`services/frontend/`) - React/TypeScript SPA with Vite
4. **AI Coach** (`services/ai_coach/`) - LLM-powered workout coaching using Pydantic AI
5. **Redis** - Caching layer for AI Coach responses

## 4th Microservice: AI Workout Coach

### Purpose
The AI Coach provides intelligent workout recommendations and fitness advice using OpenAI's GPT models through Pydantic AI.

### Features
- **Chat Endpoint** (`POST /chat`) - Natural language conversation with fitness context
- **Recommendations** (`POST /recommend`) - Generate personalized workout plans
- **Progress Analysis** (`GET /analyze`) - Analyze current workout routine

### Technology Stack
- FastAPI for the REST API
- Pydantic AI for LLM integration
- Redis for response caching
- httpx for async HTTP client

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with service status |
| `/chat` | POST | Chat with AI coach |
| `/recommend` | POST | Get workout recommendations |
| `/analyze` | GET | Analyze current routine |
| `/exercises` | GET | Proxy to main API exercises |

## Docker Compose Orchestration

### Starting the Stack
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Service Dependencies
- `api` depends on `db` (healthy)
- `ai-coach` depends on `api` (healthy) and `redis` (healthy)
- `frontend` depends on `api` (healthy)

### Environment Variables
Create a `.env` file with:
```bash
# Required for AI Coach
OPENAI_API_KEY=your-api-key-here

# Optional overrides
AI_MODEL=openai:gpt-4o-mini
AI_TEMPERATURE=0.7
```

## Health Checks

All services expose health endpoints:

```bash
# Main API
curl http://localhost:8000/health

# AI Coach
curl http://localhost:8001/health

# Redis
docker exec workout-tracker-redis redis-cli ping
```

## Session 09 - Async Refresher

The `scripts/refresh.py` script demonstrates async best practices:

### Features
- **Bounded Concurrency**: Uses `asyncio.Semaphore` to limit parallel requests
- **Retry Logic**: Exponential backoff with configurable max retries
- **Redis-backed Idempotency**: Prevents duplicate processing of exercises
- **Graceful Fallback**: In-memory idempotency when Redis unavailable

### Usage
```bash
# Basic usage (with services running)
uv run python scripts/refresh.py

# With custom options
uv run python scripts/refresh.py --concurrency 5 --api-url http://localhost:8000

# Full options
uv run python scripts/refresh.py \
  --api-url http://localhost:8000 \
  --redis-url redis://localhost:6379/0 \
  --concurrency 3 \
  --retries 3 \
  --timeout 10
```

### Redis Trace Example
```
2026-01-15 10:30:00 - INFO - Connected to Redis at redis://localhost:6379/0
2026-01-15 10:30:00 - INFO - Idempotency store: redis
2026-01-15 10:30:00 - INFO - Starting refresh of 5 exercises (max concurrency: 3)
2026-01-15 10:30:00 - INFO - [OK] Exercise 1 (Bench Press) refreshed in 45.23ms
2026-01-15 10:30:00 - INFO - [OK] Exercise 2 (Squat) refreshed in 52.10ms
2026-01-15 10:30:01 - INFO - [OK] Exercise 3 (Pull-ups) refreshed in 48.75ms
...
2026-01-15 10:30:01 - INFO - REFRESH COMPLETE
2026-01-15 10:30:01 - INFO - Processed: 5
2026-01-15 10:30:01 - INFO - Skipped (idempotent): 0
2026-01-15 10:30:01 - INFO - Success Rate: 100.0%
```

### Running Tests
```bash
# Run refresh script tests with anyio
pytest scripts/test_refresh.py -v --anyio-backends=asyncio
```

## Session 11 - Security Baseline

### Authentication Implementation

The API implements JWT-based authentication with:
- **Password Hashing**: SHA-256 with salt (PBKDF2-style format)
- **JWT Tokens**: Access tokens (30 min) and refresh tokens (7 days)
- **Role-based Access Control**: Admin, User, Readonly roles

### Auth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Authenticate and get tokens |
| `/auth/me` | GET | Get current user (protected) |
| `/admin/users` | GET | List all users (admin only) |
| `/admin/exercises/{id}` | DELETE | Delete exercise (admin only) |

### Example Auth Flow
```bash
# 1. Login to get tokens
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer",
#   "expires_in": 1800,
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
# }

# 2. Use token to access protected routes
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# 3. Admin-only route
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Default Users (Development Only)
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | ADMIN |
| user | user123 | USER |

⚠️ **Note**: These are development-only credentials. In production, use environment variables and secure password storage.

### Key Rotation Steps
1. Generate new secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Update `SECRET_KEY` in environment variable `JWT_SECRET_KEY`
3. All existing tokens will be invalidated
4. Users must re-authenticate

### Security Tests
```bash
# Run auth tests
pytest services/api/tests/test_auth.py -v
```

Tests verify:
- ✅ Password hashing and verification
- ✅ JWT token creation and validation
- ✅ Expired token rejection
- ✅ Invalid token handling
- ✅ Role-based access control

## Testing

### Running Tests
```bash
# API tests
cd services/api && pytest tests/ -v

# AI Coach tests
cd services/ai_coach && pytest tests/ -v --anyio-backends=asyncio

# Refresh script tests
pytest scripts/test_refresh.py -v --anyio-backends=asyncio
```

### Test Coverage
- Unit tests for Pydantic models
- Integration tests for workout client
- Fallback behavior tests for offline operation
- Authentication and authorization tests
- Async refresh with idempotency tests

## Demo Script

```bash
# Quick demo
./scripts/demo.sh

# Or manually:
docker compose up -d
sleep 10
curl http://localhost:8000/exercises
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What exercises should I add for a balanced routine?"}'
```

## Logfire/Redis Traces

After running `scripts/refresh.py` with Redis:
```
$ uv run python scripts/refresh.py
============================================================
Exercise Refresh Script - Session 09
============================================================
API URL: http://localhost:8000
Redis URL: redis://localhost:6379/0
Max Concurrency: 3
============================================================
Connected to Redis at redis://localhost:6379/0
Idempotency store: redis
Starting refresh of 3 exercises (max concurrency: 3)
[OK] Exercise 1 (Bench Press) refreshed in 12.45ms
[OK] Exercise 2 (Squat) refreshed in 15.23ms
[OK] Exercise 3 (Deadlift) refreshed in 11.89ms
============================================================
REFRESH COMPLETE
============================================================
Processed: 3
Skipped (idempotent): 0
Failed: 0
Total: 3
Success Rate: 100.0%
Avg Duration: 13.19ms
Total Time: 0.05s
============================================================
```

## AI Assistance

This project was developed with GitHub Copilot assistance for:
- Boilerplate code generation
- Pydantic model definitions
- Docker configuration
- Test scaffolding

All AI-generated code was reviewed and tested locally before committing.

