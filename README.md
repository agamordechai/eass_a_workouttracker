# GrindLogger

A full-stack workout tracking app with an AI-powered coaching system. Log exercises, track volume analytics, and get personalized routine recommendations from an integrated Claude-based coach.

## Features

- **Workout tracking** — manage exercises across multi-day splits (A/B/C etc.)
- **Volume analytics** — per-day volume charts with bodyweight exercise support
- **AI Coach** — chat, generate full routine splits, and import them directly into your tracker
- **Auth** — email/password and Google OAuth
- **Admin dashboard** — user management and platform stats

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| API | FastAPI, SQLModel, PostgreSQL |
| AI Coach | FastAPI, Pydantic AI, Anthropic Claude |
| Cache | Redis |
| Auth | JWT (access + refresh tokens), Google OAuth |
| Infra | Docker, Docker Compose |

## Quick Start

```bash
# 1. Clone and copy env template
git clone https://github.com/your-username/grindlogger.git
cd grindlogger
cp .env.example .env

# 2. Add your Anthropic API key to .env (required for AI Coach)
# ANTHROPIC_API_KEY=sk-ant-...

# 3. Start all services
docker compose up -d

# 4. Open the app
open http://localhost:3000
```

**Running services:**

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| AI Coach | http://localhost:8001 |
| AI Coach Docs | http://localhost:8001/docs |

## Project Structure

```
services/
├── api/            # FastAPI REST service (exercises, auth, admin)
├── ai_coach/       # AI coaching service (chat, recommendations, analysis)
├── frontend/       # React SPA
└── shared/         # Shared Pydantic models and utilities

scripts/            # Operator CLI and seeding utilities
docker-compose.yml
.env.example
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for AI Coach (Claude) |
| `AI_MODEL` | `anthropic:claude-haiku-4-5` | Claude model to use |
| `DATABASE_URL` | SQLite (local) / Postgres (Docker) | Database connection string |
| `API_PORT` | `8000` | API server port |
| `APP_LOG_LEVEL` | `INFO` | Log level |
| `APP_CORS_ORIGINS` | `*` | Allowed CORS origins |

> The full variable reference is in `.env.example`.

## Development

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 18+

```bash
# Install Python dependencies
uv sync

# Terminal 1 — API (SQLite by default)
uv run uvicorn services.api.src.api:app --reload

# Terminal 2 — AI Coach
ANTHROPIC_API_KEY=your-key uv run uvicorn services.ai_coach.src.api:app --port 8001 --reload

# Terminal 3 — Frontend
cd services/frontend
npm install
npm run dev
```

## Running Tests

```bash
# All tests
uv run pytest

# Skip slow tests (faster iteration)
uv run pytest -m "not slow" -q

# Specific suites
uv run pytest services/api/tests/ -v
uv run pytest services/ai_coach/tests/ -v

# With coverage
uv run pytest --cov=services
```

## AI Coach

The AI Coach runs as a separate service and talks to the main API to fetch workout context. Users supply their own Anthropic API key in Settings (stored in localStorage, sent per-request via `X-Anthropic-Key` header).

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Free-form chat with context awareness |
| `POST` | `/recommend` | Generate a multi-day routine split |
| `GET` | `/analyze` | Analyze current routine and score muscle balance |