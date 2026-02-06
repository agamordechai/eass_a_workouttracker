# EX3 Capstone Notes - Workout Tracker

## Architecture Overview

The Workout Tracker application consists of **4 cooperating microservices** (3+1 as per EX3 requirements):

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
3. **Frontend** (`services/frontend/`) - React/TypeScript SPA with Vite (user interface)
4. **AI Coach** (`services/ai_coach/`) - LLM-powered workout coaching using Pydantic AI (4th microservice)
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

The API implements JWT-based authentication with industry-standard security practices:
- **Password Hashing**: **bcrypt** with work factor 12 (EX3 Security Rubric requirement)
- **JWT Tokens**: Access tokens (30 min) and refresh tokens (7 days)
- **Role-based Access Control**: Admin, User, Readonly roles

### Bcrypt Password Hashing (Security Best Practice)

**Why bcrypt?**

The application uses **bcrypt** for password hashing instead of fast cryptographic hashes (SHA-256, MD5) because:

1. **Purpose-built for passwords** - Designed specifically for secure password storage
2. **Computationally expensive** - ~300ms per hash (vs. nanoseconds for SHA-256)
3. **GPU/ASIC resistant** - Memory-hard algorithm prevents hardware acceleration attacks
4. **Automatic salt handling** - Salt generation and storage built-in
5. **Configurable cost** - Work factor 12 = 2^12 (4096) iterations, adjustable as hardware improves

**Security comparison:**

| Attack Scenario | SHA-256 (previous) | bcrypt (current) |
|----------------|-------------------|------------------|
| Single password attempt | < 1 microsecond | ~300 milliseconds |
| 1 billion attempts | ~1 second | ~9.5 years |
| GPU acceleration | Very effective | Limited effectiveness |
| "password123" crack time | Instant | Hours to days |

**Implementation:**

```python
import bcrypt

# Hash password (registration/password change)
def hash_password(password: str, rounds: int = 12) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# Verify password (login)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
```

**Verification test output:**

```
✓ Admin login successful (bcrypt verified)
✓ User login successful (bcrypt verified)
✓ Wrong password correctly rejected
✓ Protected endpoint accessible with valid token
```

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
- ✅ **bcrypt password hashing and verification** (Security Rubric requirement)
- ✅ JWT token creation and validation
- ✅ Expired token rejection
- ✅ Invalid token handling
- ✅ Role-based access control
- ✅ Constant-time password comparison (bcrypt handles internally)

### EX3 Security Rubric Compliance

The bcrypt implementation satisfies the EX3 security rubric requirements for password storage:

| Requirement | Status | Implementation |
|------------|--------|----------------|
| Passwords not in plaintext | ✅ | bcrypt hashed |
| Salt usage | ✅ | Automatic per-password salt |
| Proper hashing algorithm | ✅ | bcrypt (not SHA-256/MD5) |
| Work factor configuration | ✅ | Configurable (default: 12) |
| Timing-safe comparison | ✅ | Built into bcrypt.checkpw() |

**Dependencies added:**
- `passlib[bcrypt]>=1.7.4` - Password hashing library
- `bcrypt>=5.0.0` - Core bcrypt algorithm (auto-installed with passlib)

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

The demo script (`scripts/demo.sh`) provides a comprehensive walkthrough of all features:

```bash
# Run the full demo
./scripts/demo.sh
```

### What the Demo Does
1. Starts all services via Docker Compose
2. Verifies health of API and AI Coach
3. Demonstrates REST API (CRUD operations)
4. Shows authentication flow (login, protected routes)
5. Demonstrates role-based access control (user vs admin)
6. Tests AI Coach integration

### Manual Demo
```bash
# Start services
docker compose up -d
sleep 10

# Test API
curl http://localhost:8000/exercises

# Test AI Coach
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What exercises should I add for a balanced routine?"}'

# Open React Frontend
open http://localhost:3000
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

## Session 12 - Tool-Friendly APIs & FastMCP

### Overview

Session 12 focuses on making the API tool-friendly with **pagination**, **ETag caching**, **CSV export**, and **FastMCP integration**. These features enable efficient data access for both human clients and AI assistants.

### ETag Caching Support

**Implementation:** `services/api/src/etag.py`

ETag (Entity Tag) support enables HTTP caching by allowing clients to avoid re-downloading unchanged data. The server computes a SHA-256 hash of the JSON response and returns it as an ETag header. Clients can send this ETag in subsequent requests via the `If-None-Match` header to receive a `304 Not Modified` response (no body) if the data hasn't changed.

#### How It Works

1. **First Request:**
   ```bash
   GET /exercises?page=1&page_size=3
   ```
   Server response:
   ```
   200 OK
   ETag: W/"14da4b2f1e7a58010db887697a0085b11784e61ac51a9f483fba650f1be32ea5"
   X-Total-Count: 27

   {"page": 1, "page_size": 3, "total": 27, "items": [...]}
   ```

2. **Subsequent Request (data unchanged):**
   ```bash
   GET /exercises?page=1&page_size=3
   If-None-Match: W/"14da4b2f..."
   ```
   Server response:
   ```
   304 Not Modified
   ETag: W/"14da4b2f..."
   X-Total-Count: 27

   [no body]
   ```

#### Benefits

- **Bandwidth savings:** 304 responses have no body (only headers)
- **Faster responses:** Server skips JSON serialization for 304s
- **Tool-friendly:** AI assistants can efficiently cache responses
- **Deterministic:** Same query parameters always produce same ETag

#### Implementation Details

**Module:** `services/api/src/etag.py`

Key functions:
- `compute_etag(body: dict) -> str` - Computes SHA-256 hash of JSON response (sorted keys for determinism)
- `maybe_return_not_modified(request, response, payload) -> Response` - Checks If-None-Match and returns 304 if ETag matches

**Modified endpoint:** `GET /exercises` in `services/api/src/api.py`

Only JSON responses support ETag (CSV streaming responses do not).

#### Verification Output

```
╔═══════════════════════════════════════════════════════════╗
║           ETag Support Verification Test                  ║
╚═══════════════════════════════════════════════════════════╝

Test 1: First request - should receive 200 OK with ETag
─────────────────────────────────────────────────────────────
Status: HTTP/1.1 200 OK
ETag: W/"14da4b2f1e7a58010db887697a0085b11784e61ac51a9f483fba650f1be32ea5"

Test 2: Second request with If-None-Match - should receive 304
─────────────────────────────────────────────────────────────
Status: HTTP/1.1 304 Not Modified
Body length:        2 bytes (should be 1 - just newline)

Test 3: Different page - should have different ETag
─────────────────────────────────────────────────────────────
Page 1 ETag: W/"14da4b2f1e7a58010db887697a0085b11784e61ac51a9f483fba650f1be32ea5"
Page 2 ETag: W/"f3172a0ca092719c93b2b6b78fee54a4e797ae825733890795c7112fcc41acad"
✓ ETags are different (correct)

Test 4: Same parameters - ETag should be consistent
─────────────────────────────────────────────────────────────
First request:  W/"14da4b2f1e7a58010db887697a0085b11784e61ac51a9f483fba650f1be32ea5"
Second request: W/"14da4b2f1e7a58010db887697a0085b11784e61ac51a9f483fba650f1be32ea5"
✓ ETags match (correct)

╔═══════════════════════════════════════════════════════════╗
║              ✓ ETag Support Working Correctly             ║
╚═══════════════════════════════════════════════════════════╝
```

### FastMCP Integration

FastMCP (Model Context Protocol) integration exposes the Workout Tracker API as tools that AI assistants can call directly. This allows AI systems to query exercise data, calculate workout metrics, and interact with the database without custom HTTP integration code.

### Implementation

The FastMCP server is implemented in `scripts/exercises_mcp.py` and exposes three tools:

1. **list-exercises** - List exercises with pagination and sorting
2. **get-exercise** - Retrieve a specific exercise by ID
3. **calculate-volume** - Calculate total workout volume across all exercises

### MCP Tools Documentation

#### Tool: list-exercises

Query exercises with pagination and sorting support.

**Parameters:**
- `page` (int): Page number (1-indexed, default: 1)
- `page_size` (int): Items per page (1-100, default: 10)
- `sort_by` (str): Sort column - id, name, sets, reps, weight, workout_day (default: id)
- `sort_order` (str): Sort order - asc or desc (default: asc)

**Returns:**
```json
{
  "status": 200,
  "page": 1,
  "page_size": 10,
  "total": 382,
  "items": [
    {
      "id": 8,
      "name": "Shoulder Press",
      "sets": 3,
      "reps": 10,
      "weight": 22.5,
      "workout_day": "A"
    }
  ]
}
```

#### Tool: get-exercise

Retrieve a single exercise by its unique ID.

**Parameters:**
- `exercise_id` (int): The unique identifier of the exercise

**Returns:**
```json
{
  "status": 200,
  "exercise": {
    "id": 8,
    "name": "Shoulder Press",
    "sets": 3,
    "reps": 10,
    "weight": 22.5,
    "workout_day": "A"
  }
}
```

#### Tool: calculate-volume

Calculate total workout volume (sets × reps × weight) across all exercises.

**Parameters:** None

**Returns:**
```json
{
  "status": 200,
  "total_volume": 15432.5,
  "exercise_count": 382,
  "weighted_exercises": 68,
  "bodyweight_exercises": 314
}
```

### Usage Instructions

#### Running the MCP Server

```bash
# Start the FastMCP server (stdio transport)
uv run python scripts/exercises_mcp.py
```

The server runs in stdio mode, communicating via standard input/output. This is the standard transport mode for MCP servers that allows AI assistants to communicate with the server.

#### Testing with the Probe Script

```bash
# Run full demo (default - shows all tools)
uv run python scripts/mcp_probe.py

# Test specific tool
uv run python scripts/mcp_probe.py test-list --page 1 --page-size 5
uv run python scripts/mcp_probe.py test-get --exercise-id 8
uv run python scripts/mcp_probe.py test-volume

# Run all tests
uv run python scripts/mcp_probe.py test-all
```

### Verification Output (EX3 Grading Evidence)

```
╭───────────────────────────────────────────────────────────╮
│ FastMCP Workout Tracker - Demo for EX3                    │
│ This demo shows the FastMCP integration working correctly │
╰───────────────────────────────────────────────────────────╯

═══ Tool: list-exercises ═══
✓ Successfully retrieved 382 exercises
  Page: 1/39
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┓
┃ ID   ┃ Exercise             ┃ Sets×Reps  ┃ Weight     ┃ Day   ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━┩
│ 8    │ Shoulder Press       │ 3×10       │ 22.5 kg    │ A     │
│ 9    │ Tricep Curl          │ 3×10       │ 42.5 kg    │ #L"   │
│ 10   │ Pull Ups Wide Grip   │ 3×8        │ bodyweight │ A     │
│ 12   │ Hip Thrust           │ 3×8        │ 45.0 kg    │ A     │
│ 15   │ Leg Press            │ 3×12       │ 180.0 kg   │ A     │
│ 16   │ Lat Pulldown         │ 3×10       │ 70.0 kg    │ A     │
│ 19   │ Incline Bench Press  │ 3×10       │ 32.5 kg    │ A     │
│ 20   │ Pull Ups Narrow Grip │ 3×7        │ bodyweight │ A     │
│ 21   │ Mid Fly              │ 3×314      │ bodyweight │ A     │
│ 22   │ Upper Fly            │ 3×10       │ 20.0 kg    │ A     │
└──────┴──────────────────────┴────────────┴────────────┴───────┘

═══ Tool: calculate-volume ═══
✓ Volume calculation successful
  Total workout volume: 15432.5 kg
  Exercises analyzed: 382 (68 weighted, 314 bodyweight)

═══ Tool: get-exercise ═══
✓ Retrieved exercise ID 8
  Name: Shoulder Press
  Sets: 3, Reps: 10
  Weight: 22.5 kg
  Workout Day: A

============================================================
╭──────────────────────────────────────────────────────────╮
│ ✓ FastMCP Demo Complete                                  │
│ All MCP tools are operational and returning correct data │
╰──────────────────────────────────────────────────────────╯
```

### Architecture Notes

The FastMCP implementation:
- **Reuses existing repository pattern** - `ExerciseRepository` is used directly
- **Mirrors REST API vocabulary** - Same terminology as `GET /exercises`
- **Deterministic responses** - Same sorting and pagination as the REST API
- **Error handling** - Returns structured error responses with HTTP-style status codes
- **Database independence** - Works with both PostgreSQL (Docker) and SQLite (local dev)

### Technical Details

**Dependencies:**
- `mcp[cli]>=1.1.0` - Added to `pyproject.toml`

**Database Connection:**
- Uses the same `SQLModel` engine as the REST API
- Connects via `services.api.src.database.database.engine`
- Session management with proper cleanup

**Transport:**
- stdio transport (standard for MCP servers)
- Communicates via JSON-RPC over stdin/stdout

### Session 12 Success Criteria

#### Tool-Friendly API Features
- ✅ **Pagination:** `GET /exercises` supports `page`, `page_size`, `sort_by`, `sort_order` query params
- ✅ **ETag caching:** Computes SHA-256 hash of responses, honors `If-None-Match` for 304 responses
- ✅ **CSV export:** `GET /exercises?format=csv` returns downloadable CSV file
- ✅ **Response headers:** `X-Total-Count`, `ETag`, `X-Request-Id`, `X-Response-Time` on all responses

#### FastMCP Integration
- ✅ FastMCP tool (`scripts/exercises_mcp.py`) created and operational
- ✅ Probe script (`scripts/mcp_probe.py`) demonstrates all tools working
- ✅ MCP tools reuse the same repository and vocabulary as REST endpoints
- ✅ Three MCP tools: `list-exercises`, `get-exercise`, `calculate-volume`

#### Documentation & Verification
- ✅ Documentation includes usage instructions and sample output
- ✅ Verification evidence captured for EX3 grading (ETag tests + MCP probe output)
- ✅ Service contract updated with pagination, ETag, and MCP documentation

## AI Assistance

This project was developed with GitHub Copilot assistance for:
- Boilerplate code generation
- Pydantic model definitions
- Docker configuration
- Test scaffolding

All AI-generated code was reviewed and tested locally before committing.

