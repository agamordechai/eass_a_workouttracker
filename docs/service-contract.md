# Service Contract

Defines every public endpoint, every request/response schema, every inter-service call,
and every piece of shared infrastructure the system relies on.

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Shared infrastructure](#2-shared-infrastructure)
3. [Workout API — port 8000](#3-workout-api--port-8000)
4. [AI Coach — port 8001](#4-ai-coach--port-8001)
5. [Worker — port 8002](#5-worker--port-8002)
6. [Frontend — port 3000](#6-frontend--port-3000)
7. [Cross-cutting concerns](#7-cross-cutting-concerns)

---

## 1. Architecture

```
┌──────────┐   HTTP    ┌───────────┐   SQL    ┌─────────────┐
│ Frontend │ ─────────>│ Workout   │ ─────────> PostgreSQL   │
│ :3000    │           │ API :8000 │          └─────────────┘
└────┬─────┘           └─────┬─────┘
     │                       │ GET /exercises, GET /health
     │ HTTP                  ▼
     ▼                 ┌───────────┐
┌───────────┐          │ AI Coach  │──── Anthropic API
│ AI Coach  │<──────── │ :8001     │
│ :8001     │  Worker  └─────┬─────┘
└───────────┘                │
                             │ read/write
┌───────────┐                ▼
│ Worker    │ ──────────> ┌───────┐
│ :8002     │             │ Redis │
└───────────┘             │ :6379 │
                          └───────┘
     (API also uses Redis for rate limiting — DB 2)
```

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
| Container | `grindlogger-db` |
| Database | `workout_tracker` |
| User / password | `workout` / configured via `POSTGRES_PASSWORD` |
| Healthcheck | `pg_isready -U workout -d workout_tracker` |
| Volume | `postgres_data` |
| Network | `grindlogger-net` (bridge) |

Schema is created at API startup via `init_db()` (SQLModel). Alembic migrations in `services/api/alembic/`.

### 2.2 Redis

Single Redis 7 instance; logical separation via database numbers.

| DB | Owner | Purpose |
|---|---|---|
| 0 | AI Coach, Worker | Response cache; idempotency keys (`idempotency:*`, TTL 3600 s) |
| 1 | Worker | Arq job queue (`arq:queue`) |
| 2 | API | Rate-limit counters (slowapi) |

| Property | Value |
|---|---|
| Image | `redis:7-alpine` |
| Container | `grindlogger-redis` |
| Healthcheck | `redis-cli ping` |
| Volume | `redis_data` |

### 2.3 Network

All containers share the `grindlogger-net` bridge network. Services reference each other by Compose service name (`api`, `redis`, `db`, `ai-coach`).

---

## 3. Workout API — port 8000

**Technology:** FastAPI + SQLModel + PostgreSQL (SQLite fallback in local dev)
**OpenAPI:** `GET /openapi.json` | **Docs:** `GET /docs`

### 3.1 Response headers (all endpoints)

| Header | Value |
|---|---|
| `X-Request-Id` | Echo of incoming `X-Trace-Id`, or a generated 8-char UUID fragment |
| `X-Response-Time` | Duration in milliseconds |

### 3.2 Health

```
GET /health
```

No authentication. No rate limit.

**Response 200**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-02-05T12:00:00Z",
  "database": {
    "status": "connected",
    "message": "Connected",
    "exercise_count": 42
  }
}
```

### 3.3 Exercise CRUD

All write endpoints (`POST`, `PATCH`, `DELETE`) require a valid Bearer token.
Read endpoints (`GET`) are scoped to the authenticated user's exercises.

#### List exercises

```
GET /exercises
```

Rate limit: 120/min.

**Query parameters:**

| Param | Default | Notes |
|---|---|---|
| `page` | 1 | Min 1 |
| `page_size` | 20 | Max 200 |
| `sort_by` | `id` | `id`, `name`, `sets`, `reps`, `weight`, `workout_day` |
| `sort_order` | `asc` | `asc` \| `desc` |
| `format` | `json` | `json` \| `csv` |

**Response headers:** `X-Total-Count`, `ETag` (weak validator, JSON only)

**Response 200 (JSON)**

```json
{
  "page": 1,
  "page_size": 20,
  "total": 12,
  "items": [
    { "id": 1, "name": "Bench Press", "sets": 4, "reps": 8, "weight": 80.0, "workout_day": "A" }
  ]
}
```

**Response 200 (CSV)** — `Content-Disposition: attachment; filename="exercises.csv"`

**Response 304** — when `If-None-Match` matches current ETag (no body)

#### Get exercise

```
GET /exercises/{id}
```

**Response 200** — single exercise object
**Response 404** — `{"detail": "Exercise not found"}`

#### Create exercise

```
POST /exercises                → 201
```

**Request body:**

| Field | Type | Constraints |
|---|---|---|
| `name` | `str` | 1–100 chars |
| `sets` | `int` | 1–100 |
| `reps` | `int` | 1–1000 |
| `weight` | `float \| null` | ≥ 0, `null` = bodyweight |
| `workout_day` | `str` | 1–10 chars, default `"A"` |

#### Update exercise

```
PATCH /exercises/{id}          → 200
```

All fields optional. Sending `"weight": null` clears weight; omitting it leaves it unchanged.

#### Delete exercise

```
DELETE /exercises/{id}         → 204
DELETE /exercises              → 200  {"deleted": N}  (clears all for current user)
```

#### Seed exercises

```
POST /exercises/seed?split=ppl → 200  {"seeded": N}
```

Seeds sample data if user has no exercises. `split`: `ppl` | `ab` | `fullbody`.

### 3.4 Authentication

#### Register

```
POST /auth/register            → 201
```

Body: `{ "email": str, "name": str, "password": str }`
Returns: `Token`

#### Login (email)

```
POST /auth/login
```

Body: `{ "email": str, "password": str }`

**Response 200** — `Token`

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "<JWT>"
}
```

#### Google OAuth

```
POST /auth/google
```

Body: `{ "id_token": str }` — the Google ID token from the frontend.

#### Refresh

```
POST /auth/refresh
```

Body: `{ "refresh_token": str }` — returns a new `Token`.

#### Current user

```
GET  /auth/me    → UserResponse
PATCH /auth/me   → UserResponse  (update name)
DELETE /auth/me  → 204          (delete account + all exercises)
```

### 3.5 Admin endpoints

Require Bearer token with `admin` role.

```
GET    /admin/users              → list of users with exercise counts
PATCH  /admin/users/{id}         → update role or disabled status
DELETE /admin/users/{id}         → delete user + their exercises
DELETE /admin/exercises/{id}     → delete any exercise (no user scoping)
GET    /admin/stats              → platform-wide counts
```

### 3.6 Rate limiting

Enforced via **slowapi** backed by Redis DB 2. Degrades gracefully if Redis is down.

| Endpoint category | User | Admin |
|---|---|---|
| `GET /` | 100/min | 100/min |
| `POST /auth/*` | 10/min | 10/min |
| `GET /exercises*` | 120/min | 300/min |
| Write `/exercises*` | 60/min | 150/min |
| `/admin/*` | — | 100/min |
| `/health` | unlimited | unlimited |

All limits overridable via `RATELIMIT_*` env vars.

---

## 4. AI Coach — port 8001

**Technology:** FastAPI + Pydantic AI + Anthropic Claude
**Default model:** `anthropic:claude-3-5-haiku-latest`

The user's Anthropic API key is sent per-request via the `X-Anthropic-Key` header (set from localStorage by the frontend). Server-side key from `ANTHROPIC_API_KEY` is used as fallback for admin users only.

### 4.1 Upstream calls

| Target | Endpoint | When |
|---|---|---|
| Workout API | `GET /exercises` | Every `/chat` (with context), `/recommend`, `/analyze` |
| Workout API | `GET /health` | Own `/health` check |
| Anthropic API | Claude inference | Every `/chat`, `/recommend`, `/analyze` |
| Redis DB 0 | read/write | Response caching (best-effort) |

### 4.2 Health

```
GET /health
```

```json
{
  "status": "healthy",
  "service": "ai-coach",
  "ai_model": "anthropic:claude-3-5-haiku-latest",
  "workout_api_connected": true,
  "redis_connected": true
}
```

### 4.3 Chat

```
POST /chat
```

| Field | Type | Constraints |
|---|---|---|
| `message` | `str` | 1–2000 chars |
| `include_workout_context` | `bool` | default `true` |

**Response 200**

```json
{
  "response": "Here is your personalized advice…",
  "context_used": true
}
```

### 4.4 Recommend

```
POST /recommend
```

| Field | Type | Notes |
|---|---|---|
| `focus_area` | `MuscleGroup \| null` | `chest`, `back`, `shoulders`, `biceps`, `triceps`, `legs`, `core`, `full_body`, `upper_lower`, `push_pull_legs` |
| `custom_focus_area` | `str \| null` | Freeform override; takes precedence over `focus_area` when set |
| `equipment_available` | `List[str]` | default `["barbell","dumbbells","cables","bodyweight"]` |
| `session_duration_minutes` | `int` | 15–180, default 60 |

**Response 200** — `WorkoutRecommendation`

```json
{
  "title": "Push / Pull / Legs — 3-Day Split",
  "description": "…",
  "split_type": "Push/Pull/Legs",
  "estimated_duration_minutes": 55,
  "difficulty": "Intermediate",
  "exercises": [
    {
      "name": "Bench Press",
      "sets": 4,
      "reps": "8-12",
      "weight_suggestion": "70kg",
      "notes": "Keep elbows tucked.",
      "muscle_group": "chest",
      "workout_day": "A"
    }
  ],
  "tips": ["Warm up for 5 minutes before starting"]
}
```

### 4.5 Analyze

```
GET /analyze
```

Fetches the current user's exercises from the Workout API, then analyzes them.

**Response 400** — no exercises found
**Response 503** — Workout API unreachable

**Response 200** — `ProgressAnalysis`

```json
{
  "summary": "Your routine is well-balanced…",
  "strengths": ["Good upper-body variety"],
  "areas_to_improve": ["Add more leg work"],
  "recommendations": ["Include a squat variant"],
  "muscle_balance_score": 72.5
}
```

---

## 5. Worker — port 8002

**Technology:** Arq (async job queue) + lightweight FastAPI health server

### 5.1 Health

```
GET /health
```

```json
{
  "status": "healthy",
  "redis_connected": true,
  "queue_depth": 0,
  "api_connected": true,
  "ai_coach_connected": true
}
```

Status: `healthy` (all up) | `degraded` (Redis up, something else down) | `unhealthy` (Redis down)

### 5.2 Scheduled tasks

| Task | Schedule | Toggle env var |
|---|---|---|
| `refresh_exercises` | Hourly at :00 | `WORKER_SCHEDULE__ENABLE_HOURLY_REFRESH` |
| `warmup_ai_cache` | Daily at configured UTC hour (default 06:00) | `WORKER_SCHEDULE__ENABLE_DAILY_WARMUP` |
| `cleanup_stale_data` | Weekly on configured day/hour (default Sun 02:00 UTC) | `WORKER_SCHEDULE__ENABLE_WEEKLY_CLEANUP` |

All tasks use `unique=True` (no overlapping runs). All environment variables are prefixed `WORKER_`.

---

## 6. Frontend — port 3000

**Technology:** React + TypeScript + Vite, served via Nginx.

In development, Vite proxies `/api` → `localhost:8000` and `/ai-coach` → `localhost:8001`.
In production, set `VITE_API_BASE_URL` and `VITE_AI_COACH_BASE_URL` build args.

Every request includes `X-Trace-Id: ui-react`. AI Coach requests also include the user's Anthropic key as `X-Anthropic-Key` (from localStorage).

### Calls to Workout API (10 s timeout)

`GET/POST/PATCH/DELETE /exercises`, `GET /exercises/{id}`, `DELETE /exercises`
`POST /auth/*`, `GET|PATCH|DELETE /auth/me`
`GET|PATCH|DELETE /admin/*`

### Calls to AI Coach (60 s timeout)

`GET /health`, `POST /chat`, `POST /recommend`, `GET /analyze`

---

## 7. Cross-cutting concerns

### 7.1 JWT authentication

| Property | Value |
|---|---|
| Algorithm | HS256 |
| Access token TTL | 30 minutes |
| Refresh token TTL | 7 days |
| Secret key | `JWT_SECRET_KEY` env var |
| Scheme | `Authorization: Bearer <token>` |

Token payload: `sub` (user ID), `role`, `exp`.
Passwords hashed with bcrypt (work factor 12).

### 7.2 Request tracing

The API middleware echoes `X-Trace-Id` back as `X-Request-Id` and logs every request with its trace ID and response time.

### 7.3 ETag caching

**Endpoint:** `GET /exercises` (JSON only)

On first request the API computes a SHA-256 hash of the response body and returns it as a weak ETag (`W/"<hash>"`). Clients can send `If-None-Match` on subsequent requests; unchanged data returns **304 Not Modified** with no body.

```bash
# First request
curl -i http://localhost:8000/exercises
# → 200 OK, ETag: W/"abc123..."

# Conditional request
curl -i http://localhost:8000/exercises -H 'If-None-Match: W/"abc123..."'
# → 304 Not Modified
```
