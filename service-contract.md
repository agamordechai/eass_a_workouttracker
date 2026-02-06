# Service Contract — Workout Tracker

Session 10 artifact. Defines every public endpoint, every request/response schema,
every inter-service call, and every piece of shared infrastructure the system relies on.
Nothing here is aspirational; every entry is grounded in the current source.

---

## Table of Contents

1. [Architecture & dependency graph](#1-architecture--dependency-graph)
2. [Shared infrastructure](#2-shared-infrastructure)
3. [Workout API — `api` (port 8000)](#3-workout-api--api-port-8000)
4. [AI Coach — `ai-coach` (port 8001)](#4-ai-coach--ai-coach-port-8001)
5. [Worker — `worker` (port 8002)](#5-worker--worker-port-8002)
6. [Frontend — `frontend` (port 3000)](#6-frontend--frontend-port-3000)
7. [Cross-cutting concerns](#7-cross-cutting-concerns)
8. [Known gaps](#8-known-gaps)

---

## 1. Architecture & dependency graph

```
┌──────────┐   HTTP    ┌───────────┐   HTTP   ┌─────────────┐
│ Frontend │ ─────────>│ Workout   │          │ PostgreSQL  │
│ :3000    │           │ API :8000 │ ─────────> :5432        │
└────┬─────┘           └─────┬─────┘          └─────────────┘
     │                       │
     │ HTTP                  │ read (GET /exercises, GET /health)
     ▼                       ▼
┌───────────┐         ┌───────────┐
│ AI Coach  │<────────│ Worker    │  write (POST /generate*)
│ :8001     │         │ :8002     │
└─────┬─────┘         └─────┬─────┘
      │                     │
      │ HTTP (Anthropic)    │ read/write
      ▼                     ▼
┌─────────────┐       ┌───────────┐
│ Anthropic   │       │ Redis     │
│ Claude API  │       │ :6379     │
└─────────────┘       └───────────┘
                      (also used by API and AI Coach)
```

*Worker → AI Coach POST `/generate` is exercised by the cache-warmup task but
`/generate` does not exist on AI Coach — see [Known gaps](#8-known-gaps).*

**Startup order** (enforced by `depends_on` + `condition: service_healthy`):

| Service | Requires healthy |
|---|---|
| `db` | — |
| `redis` | — |
| `api` | `db` |
| `ai-coach` | `api`, `redis` |
| `worker` | `api`, `ai-coach`, `redis` |
| `frontend` | `api` |

---

## 2. Shared infrastructure

### 2.1 PostgreSQL

| Property | Value |
|---|---|
| Image | `postgres:15-alpine` |
| Container | `workout-tracker-db` |
| Database | `workout_tracker` |
| User / password | `workout` / `workout123` |
| Healthcheck | `pg_isready -U workout -d workout_tracker` |
| Volume | `postgres_data` (local driver) |
| Network | `workout-net` (bridge) |

Schema is managed by **Alembic** (`services/api/alembic/`). Tables are also
created at API startup via `init_db()` if they do not already exist.

### 2.2 Redis

Single Redis 7 instance; logical separation via database numbers.

| DB | Owner | Purpose |
|---|---|---|
| 0 | AI Coach, Worker | Response cache; idempotency keys (`idempotency:*`) |
| 1 | Worker | Arq job queue (`arq:queue`) |
| 2 | API | Rate-limit counters (slowapi) |

| Property | Value |
|---|---|
| Image | `redis:7-alpine` |
| Container | `workout-tracker-redis` |
| Host port | 6379 |
| Healthcheck | `redis-cli ping` |
| Volume | `redis_data` (local driver) |

### 2.3 Network

All containers share the `workout-net` bridge network. Services reference
each other by their Compose service name (`api`, `redis`, `db`, `ai-coach`).

---

## 3. Workout API — `api` (port 8000)

**Technology:** FastAPI + SQLModel + PostgreSQL (SQLite fallback in dev)
**OpenAPI:** `GET /openapi.json`
**Docs:** `GET /docs`

### 3.1 Response headers (all endpoints)

Added by the request-logging middleware:

| Header | Value |
|---|---|
| `X-Request-Id` | Echo of incoming `X-Trace-Id`, or a generated 8-char UUID fragment |
| `X-Response-Time` | Duration in milliseconds (e.g. `"3.42ms"`) |

### 3.2 Health

```
GET /health
```

No authentication. No rate limit.

**Response 200** — `HealthResponse`

```json
{
  "status": "healthy",          // "healthy" | "unhealthy"
  "version": "0.1.0",
  "timestamp": "2026-02-05T12:00:00Z",   // ISO 8601, Z suffix
  "database": {
    "status": "connected",      // "connected" | "disconnected"
    "message": "Connected",
    "exercise_count": 42
  }
}
```

### 3.3 Root

```
GET /
```

Rate-limited: public limit (100/min). No auth.

**Response 200**

```json
{
  "message": "Welcome to the Workout Tracker API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

### 3.4 Exercise CRUD

All exercise endpoints are **unauthenticated** (no `Depends(get_current_active_user)`)
but are rate-limited.

#### List exercises

```
GET /exercises
```

Rate limit: 120/min (user-level read).

**Query Parameters:**
- `page` (int, default: 1, min: 1) — Page number (1-indexed)
- `page_size` (int, default: 20, min: 1, max: 200) — Items per page
- `sort_by` (str, default: "id") — Column to sort by (id, name, sets, reps, weight, workout_day)
- `sort_order` (str, default: "asc") — Sort order ("asc" or "desc")
- `format` (str, default: "json") — Response format ("json" or "csv")

**Response Headers:**
- `X-Total-Count` — Total number of exercises across all pages
- `ETag` — Weak validator hash for caching (format: `W/"<sha256>"`)
- `X-Request-Id` — Request trace ID
- `X-Response-Time` — Response time in milliseconds

**ETag Support (Session 12):**
Clients can send an `If-None-Match` header with a previously received ETag.
If the ETag matches (data unchanged), the server returns `304 Not Modified`
with no body, saving bandwidth and improving performance.

**Response 200 (JSON)** — Paginated exercise list

```json
{
  "page": 1,
  "page_size": 20,
  "total": 27,
  "items": [
    {
      "id": 1,
      "name": "Bench Press",
      "sets": 4,
      "reps": 8,
      "weight": 80.0,
      "workout_day": "A"
    }
  ]
}
```

**Response 200 (CSV)** — When `format=csv`

Returns a `text/csv` file with headers: `id,name,sets,reps,weight,workout_day`.
The `Content-Disposition` header specifies `attachment; filename="exercises.csv"`.

**Response 304 Not Modified** — When `If-None-Match` matches current ETag

No body returned. Headers include `ETag`, `X-Total-Count`, `X-Request-Id`, `X-Response-Time`.

**Response 400** — Invalid `sort_by` column

```json
{
  "detail": "sort_by must be one of: ['id', 'name', 'reps', 'sets', 'weight', 'workout_day']"
}
```

#### Get exercise

```
GET /exercises/{exercise_id}
```

Rate limit: 120/min.

**Response 200** — `ExerciseResponse` (same shape as list item)
**Response 404** — `{"detail": "Exercise not found"}`

#### Create exercise

```
POST /exercises
```

Rate limit: 60/min. Returns **201**.

**Request body** — `Exercise`

| Field | Type | Constraints |
|---|---|---|
| `name` | `str` | 1–100 chars, required |
| `sets` | `int` | 1–100, required |
| `reps` | `int` | 1–1000, required |
| `weight` | `float \| null` | ≥ 0, default `null` |
| `workout_day` | `str` | 1–10 chars, default `"A"` |

**Response 201** — `ExerciseResponse`

#### Update exercise (partial)

```
PATCH /exercises/{exercise_id}
```

Rate limit: 60/min.

**Request body** — `ExerciseEditRequest` (all fields optional, same constraints as
`Exercise`). Only fields present in the JSON body are updated. Sending
`"weight": null` explicitly clears the weight; omitting `weight` leaves it
unchanged.

**Response 200** — `ExerciseResponse`
**Response 404** — `{"detail": "Exercise not found"}`

#### Delete exercise

```
DELETE /exercises/{exercise_id}
```

Rate limit: 60/min. Returns **204 No Content** on success.

**Response 404** — `{"detail": "Exercise not found"}`

### 3.5 Authentication

#### Login

```
POST /auth/login
```

Rate limit: 10/min (brute-force protection).

**Request body** — `LoginRequest`

| Field | Type | Constraints |
|---|---|---|
| `username` | `str` | 3–50 chars |
| `password` | `str` | ≥ 6 chars |

**Response 200** — `Token`

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 1800,            // seconds (30 min)
  "refresh_token": "<JWT>"       // expires in 7 days
}
```

**Response 401** — `{"detail": "Incorrect username or password"}`
Header: `WWW-Authenticate: Bearer`

#### Current user

```
GET /auth/me
```

Requires valid Bearer token. Rate limit: 10/min.

**Response 200** — `User`

```json
{
  "username": "admin",
  "email": "admin@workout.local",
  "role": "admin",               // "admin" | "user" | "readonly"
  "disabled": false
}
```

**Response 401** — invalid / missing token
**Response 403** — disabled account

### 3.6 Admin endpoints

Both require a Bearer token with role `admin`.

#### List users

```
GET /admin/users
```

Rate limit: 100/min.

**Response 200** — `List[User]` (same shape as `/auth/me` response)

#### Admin delete exercise

```
DELETE /admin/exercises/{exercise_id}
```

Rate limit: 100/min. Returns **204 No Content**.

**Response 404** — `{"detail": "Exercise not found"}`

### 3.7 Rate-limit error response

When any rate limit is exceeded the API returns **429** via the custom
`rate_limit_exceeded_handler`. The handler is defined in `services/api/src/ratelimit/__init__.py`.

Slowapi rate-limit response headers are **disabled** (`headers_enabled=False`)
due to FastAPI `response_model` compatibility.

---

## 4. AI Coach — `ai-coach` (port 8001)

**Technology:** FastAPI + Pydantic AI + Anthropic Claude
**Model (default):** `anthropic:claude-3-5-haiku-latest`

### 4.1 Upstream calls this service makes

| Target | Endpoint | When |
|---|---|---|
| Workout API | `GET /exercises` | Every `/chat` (if `include_workout_context`), every `/recommend`, every `/analyze` |
| Workout API | `GET /health` | Own `/health` check |
| Anthropic API | Claude inference | Every `/chat`, `/recommend`, `/analyze` |
| Redis DB 0 | read/write | Response caching (best-effort; disabled gracefully if Redis is down) |

HTTP client timeout to Workout API: **10 s** (default in `WorkoutAPIClient`).

### 4.2 Health

```
GET /health
```

**Response 200** — `HealthResponse`

```json
{
  "status": "healthy",
  "service": "ai-coach",
  "ai_model": "anthropic:claude-3-5-haiku-latest",
  "workout_api_connected": true,
  "redis_connected": true
}
```

`status` is always `"healthy"` in the current implementation regardless of
dependency status; individual booleans carry the actual check results.

### 4.3 Chat

```
POST /chat
```

**Request body** — `ChatRequest`

| Field | Type | Constraints |
|---|---|---|
| `message` | `str` | 1–2000 chars, required |
| `include_workout_context` | `bool` | default `true` |

When `include_workout_context` is `true` the service fetches
`GET /exercises` from the Workout API, computes volume and infers muscle
groups from exercise names, and passes that context to the AI model.
A failure to fetch context is logged as a warning and the request
continues without context.

**Response 200** — `ChatResponse`

```json
{
  "response": "Here is your personalized advice…",
  "context_used": true     // false if context fetch failed or was disabled
}
```

**Response 500** — `{"detail": "Failed to get response from AI coach. Please try again."}`

### 4.4 Recommend

```
POST /recommend
```

**Request body** — `RecommendationRequest`

| Field | Type | Constraints |
|---|---|---|
| `focus_area` | `MuscleGroup \| null` | `chest`, `back`, `shoulders`, `biceps`, `triceps`, `legs`, `core`, `full_body`; default `null` |
| `equipment_available` | `List[str]` | default `["barbell","dumbbells","cables","bodyweight"]` |
| `session_duration_minutes` | `int` | 15–180, default 60 |

**Response 200** — `WorkoutRecommendation`

```json
{
  "title": "Upper Body Power",
  "description": "…",
  "exercises": [
    {
      "name": "Bench Press",
      "sets": 4,
      "reps": "8-12",
      "weight_suggestion": "70-80% 1RM",
      "notes": "Keep elbows tucked.",
      "muscle_group": "chest"
    }
  ],
  "estimated_duration_minutes": 55,
  "difficulty": "intermediate",
  "tips": ["Warm up for 5 minutes"]
}
```

**Response 500** — `{"detail": "Failed to generate workout recommendation. Please try again."}`

### 4.5 Analyze

```
GET /analyze
```

Fetches current exercises from the Workout API. Returns **400** if the
exercise list is empty; **503** if the Workout API is unreachable.

**Response 200** — `ProgressAnalysis`

```json
{
  "summary": "Your routine is well-balanced…",
  "strengths": ["Good upper-body variety"],
  "areas_to_improve": ["Add more leg work"],
  "recommendations": ["Include a squat variant"],
  "muscle_balance_score": 72.5    // 0–100 | null
}
```

### 4.6 Exercise proxy

```
GET /exercises
```

Forwards the response from `GET /exercises` on the Workout API unchanged.

**Response 200** — same `List[ExerciseResponse]` array the Workout API returns
**Response 503** — `{"detail": "Unable to connect to workout API."}`

---

## 5. Worker — `worker` (port 8002)

**Technology:** Arq (async task queue) + FastAPI health server
The worker process runs two things concurrently via `asyncio.gather`:
the Arq worker loop and a lightweight FastAPI health server.

### 5.1 Health

```
GET /health
```

**Response 200** — `HealthResponse`

```json
{
  "status": "healthy",          // "healthy" | "degraded" | "unhealthy"
  "redis_connected": true,
  "queue_depth": 0,             // current length of arq:queue in Redis DB 1
  "api_connected": true,
  "ai_coach_connected": true,
  "details": {
    "queue_depth": "0",
    "api_status": "200",
    "ai_coach_status": "200"
  }
}
```

Status rules:
- `healthy` — Redis, API, and AI Coach all reachable
- `degraded` — Redis reachable but at least one other service is not
- `unhealthy` — Redis unreachable

### 5.2 Scheduled tasks

All tasks are Arq cron jobs with `unique=True` (prevents overlapping runs).

#### 5.2.1 `refresh_exercises` — hourly

| Property | Value |
|---|---|
| Schedule | Every hour at minute 0 |
| Toggle | `WORKER_SCHEDULE__ENABLE_HOURLY_REFRESH` |

Calls `GET /exercises` on the Workout API via the `ExerciseRefresher`
helper (migrated from `scripts/refresh.py`). Uses bounded concurrency
(default 5), Redis DB 0 for idempotency keys (`idempotency:*`, TTL 3600 s),
and exponential-backoff retries (up to 3, base delay 5 s).

**Return value** (logged, stored as Arq job result):

```json
{
  "processed": 42,
  "skipped": 0,
  "failed": 0,
  "total": 42,
  "success_rate": 100.0
}
```

#### 5.2.2 `warmup_ai_cache` — daily

| Property | Value |
|---|---|
| Schedule | Daily at configurable UTC hour (default 06:00) |
| Toggle | `WORKER_SCHEDULE__ENABLE_DAILY_WARMUP` |

Iterates over 7 muscle groups × 5 equipment combos × 4 durations = 140
combinations and POSTs each to `POST /generate` on the AI Coach service
with a 0.5 s inter-request delay.

> **Note:** The AI Coach service does not expose a `/generate` endpoint.
> See [Known gaps](#8-known-gaps).

**Return value:**

```json
{
  "total_requests": 140,
  "successful": 0,
  "failed": 140
}
```

#### 5.2.3 `cleanup_stale_data` — weekly

| Property | Value |
|---|---|
| Schedule | Weekly on configurable day (default Sunday, day 6) at configurable hour (default 02:00 UTC) |
| Toggle | `WORKER_SCHEDULE__ENABLE_WEEKLY_CLEANUP` |

Scans Redis DB 0 for keys matching `idempotency:*`. Deletes any key that
has no TTL (`-1`) or a TTL under 60 seconds — these are considered orphaned.

**Return value:**

```json
{
  "deleted_idempotency_keys": 3,
  "cleanup_time_ms": 12
}
```

### 5.3 Worker configuration summary

All environment variables are prefixed `WORKER_`; nested keys use `__`.

| Env var | Default | Meaning |
|---|---|---|
| `WORKER_REDIS__HOST` | `localhost` | Redis host |
| `WORKER_REDIS__PORT` | `6379` | Redis port |
| `WORKER_REDIS__DATABASE` | `1` | Arq queue DB |
| `WORKER_REDIS__CACHE_DATABASE` | `0` | Cache / idempotency DB |
| `WORKER_API_CLIENT__WORKOUT_API_URL` | `http://localhost:8000` | Workout API base URL |
| `WORKER_API_CLIENT__AI_COACH_URL` | `http://localhost:8001` | AI Coach base URL |
| `WORKER_API_CLIENT__TIMEOUT` | `30` | HTTP client timeout (s) |
| `WORKER_WORKER__MAX_JOBS` | `10` | Max concurrent Arq jobs |
| `WORKER_WORKER__JOB_TIMEOUT` | `300` | Per-job timeout (s) |
| `WORKER_WORKER__HEALTH_PORT` | `8002` | Health server port |
| `WORKER_SCHEDULE__ENABLE_HOURLY_REFRESH` | `true` | |
| `WORKER_SCHEDULE__ENABLE_DAILY_WARMUP` | `true` | |
| `WORKER_SCHEDULE__ENABLE_WEEKLY_CLEANUP` | `true` | |
| `WORKER_SCHEDULE__WARMUP_HOUR` | `6` | UTC hour for daily warmup |
| `WORKER_SCHEDULE__CLEANUP_DAY_OF_WEEK` | `6` | 0=Mon … 6=Sun |
| `WORKER_SCHEDULE__CLEANUP_HOUR` | `2` | UTC hour for weekly cleanup |
| `WORKER_REFRESH__CONCURRENCY` | `5` | Bounded concurrency for refresh |
| `WORKER_REFRESH__IDEMPOTENCY_TTL` | `3600` | Idempotency key TTL (s) |
| `WORKER_REFRESH__RETRY_DELAY` | `5` | Base retry delay (s) |
| `WORKER_REFRESH__MAX_RETRIES` | `3` | Max retries per exercise |

---

## 6. Frontend — `frontend` (port 3000)

**Technology:** React + TypeScript + Vite, served via Nginx.

The frontend makes HTTP requests to two backends. In production the base URLs
are configured via `VITE_API_BASE_URL` / `VITE_AI_COACH_BASE_URL`; in
development Vite proxies `/api` → `localhost:8000` and `/ai-coach` →
`localhost:8001`.

A static `X-Trace-Id: ui-react` header is sent on every request.

### 6.1 Calls to Workout API

| Method | Path | Timeout |
|---|---|---|
| GET | `/exercises` | 10 s |
| GET | `/exercises/{id}` | 10 s |
| POST | `/exercises` | 10 s |
| PATCH | `/exercises/{id}` | 10 s |
| DELETE | `/exercises/{id}` | 10 s |

### 6.2 Calls to AI Coach

| Method | Path | Timeout |
|---|---|---|
| GET | `/health` | 60 s |
| POST | `/chat` | 60 s |
| POST | `/recommend` | 60 s |
| GET | `/analyze` | 60 s |

---

## 7. Cross-cutting concerns

### 7.1 Rate limiting

Enforced on the Workout API only, via **slowapi** backed by Redis DB 2.
Degrades gracefully (`swallow_errors=True`) if Redis is unavailable.

Rate-limit key resolution:
- **Unauthenticated** requests → keyed by client IP
- **Authenticated** requests → keyed by `{username}:{role}`

| Endpoint category | Anonymous | USER | ADMIN |
|---|---|---|---|
| `GET /` (public) | 100/min | 100/min | 100/min |
| `POST /auth/*` | 10/min | 10/min | 10/min |
| `GET /exercises*` (read) | 60/min | 120/min | 300/min |
| `POST / PATCH / DELETE /exercises*` (write) | 30/min | 60/min | 150/min |
| `GET /admin/*` | — | — | 100/min |
| `GET /health` | unlimited | unlimited | unlimited |

All limits are overridable via the `RATELIMIT_*` environment variables
(see `services/api/src/ratelimit/config.py`).

### 7.2 JWT authentication

| Property | Value |
|---|---|
| Algorithm | HS256 |
| Access token TTL | 30 minutes |
| Refresh token TTL | 7 days |
| Secret key | `SECRET_KEY` constant in `auth.py` (must be overridden in production) |
| Scheme | Bearer (`Authorization: Bearer <token>`) |

Token payload contains `sub` (username), `role`, and `exp`.

**Password hashing:** bcrypt with work factor 12 (~300ms per hash). Provides:
- GPU/ASIC resistance via memory-hard algorithm
- Automatic salt generation and storage
- Configurable computational cost (2^12 = 4096 iterations)
- Industry standard for secure password storage

Hardcoded users (in-memory, no user-creation endpoint):

| Username | Role | Password | Hash Algorithm |
|---|---|---|---|
| `admin` | ADMIN | `admin123` | bcrypt (work factor 12) |
| `user` | USER | `user123` | bcrypt (work factor 12) |

### 7.3 Request tracing

The Workout API middleware reads an incoming `X-Trace-Id` header (or
generates one) and echoes it back as `X-Request-Id`. Every request is
logged with its trace ID and response time. The Frontend sends
`X-Trace-Id: ui-react` on all requests. The Worker sends
`User-Agent: workout-tracker-worker`.

### 7.4 ETag caching (Session 12)

**Implementation:** `services/api/src/etag.py`
**Endpoints:** `GET /exercises` (JSON responses only, not CSV)

The Workout API supports HTTP caching via **ETags** (Entity Tags) to reduce
bandwidth and improve response times for unchanged data.

**How it works:**

1. **First request:** Client requests data
   - Server computes SHA-256 hash of JSON response body
   - Returns `200 OK` with `ETag: W/"<hash>"` header

2. **Subsequent requests:** Client sends `If-None-Match: W/"<hash>"`
   - Server recomputes hash for current data
   - If hash matches (data unchanged): returns `304 Not Modified` with no body
   - If hash differs (data changed): returns `200 OK` with new data and updated ETag

**ETag format:** Weak validator (`W/"<sha256>"`)

The hash is computed from the JSON response with sorted keys to ensure
deterministic hashing. Different query parameters (page, sort, etc.)
produce different ETags since they return different data.

**Benefits:**
- **Bandwidth savings:** 304 responses contain no body (only headers)
- **Faster responses:** Server skips JSON serialization for 304s
- **Tool-friendly:** AI assistants can efficiently cache API responses

**Example:**

```bash
# First request - get data + ETag
curl -i "http://localhost:8000/exercises?page=1&page_size=3"
# Response: 200 OK, ETag: W/"14da4b2f...", [data]

# Second request - send If-None-Match
curl -i "http://localhost:8000/exercises?page=1&page_size=3" \
  -H "If-None-Match: W/\"14da4b2f...\""
# Response: 304 Not Modified, no body
```

**Verification:**

See `docs/EX3-notes.md` Session 12 section for full test suite output.

---

## 8. FastMCP Integration (Session 12)

**Technology:** FastMCP (Model Context Protocol)
**Location:** `scripts/exercises_mcp.py`
**Transport:** stdio (JSON-RPC over stdin/stdout)

The FastMCP server exposes Workout Tracker exercises as MCP tools that AI assistants can call directly. It reuses the same `ExerciseRepository` and database connection as the REST API.

### 8.1 MCP Tools

All tools return JSON responses with an HTTP-style `status` field.

#### 8.1.1 list-exercises

```
Tool: list-exercises
Args: page (int), page_size (int), sort_by (str), sort_order (str)
```

Lists exercises with pagination and sorting. Mirrors `GET /exercises` behavior.

**Response 200:**
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

**Response 400:** Invalid parameters (page < 1, invalid sort_by, etc.)

#### 8.1.2 get-exercise

```
Tool: get-exercise
Args: exercise_id (int)
```

Retrieves a single exercise by ID. Mirrors `GET /exercises/{id}`.

**Response 200:**
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

**Response 404:** Exercise not found
**Response 400:** Invalid exercise_id (< 1)

#### 8.1.3 calculate-volume

```
Tool: calculate-volume
Args: None
```

Calculates total workout volume (sets × reps × weight) across all exercises.

**Response 200:**
```json
{
  "status": 200,
  "total_volume": 15432.5,
  "exercise_count": 382,
  "weighted_exercises": 68,
  "bodyweight_exercises": 314
}
```

### 8.2 Database Connection

The MCP server connects to the same database as the REST API:
- **PostgreSQL** in Docker (via `DATABASE_URL`)
- **SQLite** in local development (`data/workout_tracker.db`)

Uses `services.api.src.database.database.engine` for consistency.

### 8.3 Running the Server

```bash
# Start MCP server (stdio transport)
uv run python scripts/exercises_mcp.py

# Test with probe script
uv run python scripts/mcp_probe.py
```

The probe script (`scripts/mcp_probe.py`) demonstrates all tools and provides verification output for EX3 grading.

---

## 9. Known gaps

| # | Location | Description |
|---|---|---|
| 1 | `services/worker/src/tasks/cache_warmup.py:55` | The warmup task POSTs to `/generate` on the AI Coach, but AI Coach exposes no `/generate` endpoint. Every warmup iteration will receive a 404 or 405, meaning the daily cache-warmup task currently has a 0 % success rate. The intended target is likely `POST /recommend`. |
| 2 | `services/api/src/auth.py:14` | `SECRET_KEY` is a plaintext constant. It must be loaded from an environment variable or secret manager before any production deployment. |
| 3 | `services/ai_coach/src/api.py:105` | The AI Coach health endpoint always returns `"status": "healthy"` regardless of whether its upstream dependencies are actually reachable. The per-dependency booleans are accurate but the top-level status does not reflect them. |
| 4 | Auth scope | Exercise CRUD endpoints (`/exercises/*`) have no authentication guard — any caller (including unauthenticated) can create, edit, and delete exercises. Only the `/admin/*` routes and `/auth/me` require a token. |
