# Workout Tracker API

A FastAPI-based REST API for managing workout exercises with PostgreSQL persistence and AI-powered coaching.

## Prerequisites

- **Docker** and **Docker Compose** (recommended)
- **OpenAI API Key** (for AI Coach features)
- Or for local development:
  - Python 3.12+
  - [uv](https://docs.astral.sh/uv/) package manager

## Project Structure

```
├── services/
│   ├── api/                 # FastAPI REST service
│   │   ├── Dockerfile       # API container definition
│   │   ├── pyproject.toml   # API-specific dependencies
│   │   ├── src/
│   │   │   ├── api.py       # FastAPI application
│   │   │   └── database/    # Database models, config, repository
│   │   └── tests/           # API tests
│   │
│   ├── ai_coach/            # AI Workout Coach (Pydantic AI)
│   │   ├── Dockerfile       # AI Coach container definition
│   │   ├── pyproject.toml   # AI Coach dependencies
│   │   ├── src/
│   │   │   ├── api.py       # FastAPI application
│   │   │   ├── agent.py     # Pydantic AI agent
│   │   │   ├── models.py    # Request/Response models
│   │   │   └── workout_client.py  # HTTP client for main API
│   │   └── tests/           # AI Coach tests
│   │
│   └── frontend/            # React frontend
│       ├── Dockerfile       # Frontend container definition
│       └── src/             # React components
│
├── docs/                    # Documentation
│   ├── EX3-notes.md         # EX3 capstone documentation
│   └── runbooks/
│       └── compose.md       # Docker Compose runbook
│
├── data/                    # Local development data
│   └── exports/             # Exported CSV/JSON files
│
├── scripts/                 # Utility scripts
│   ├── api.http             # HTTP requests for API testing
│   ├── seed.py              # Database seeding script
│   └── demo.sh              # Demo script for EX3
│
├── docker-compose.yml       # Multi-service orchestration
└── pyproject.toml           # Root project dependencies (for local dev)
```

## Setup

### Option 1: Docker Compose (Recommended)

```bash
# 1. Create .env file with your OpenAI API key
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here

# 2. Start all services (database, API, AI Coach, frontend)
docker-compose up -d

# 3. Check all services are running
docker-compose ps

# 4. Open frontend
open http://localhost:3000

# 5. Stop all services
docker-compose down

# 6. Stop and remove all data (fresh start)
docker-compose down -v
```

**Services:**
- **PostgreSQL Database**: Internal (port 5432)
- **Redis**: Internal (port 6379)
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **AI Coach**: http://localhost:8001
- **AI Coach Docs**: http://localhost:8001/docs
- **Frontend**: http://localhost:3000

### Option 2: Local Development (Without Docker)

```bash
# Install dependencies using uv
uv sync

# Terminal 1 - Start API
uv run uvicorn services.api.src.api:app --reload

# Terminal 2 - Start AI Coach (requires OPENAI_API_KEY)
export OPENAI_API_KEY=your-key-here
uv run uvicorn services.ai_coach.src.api:app --port 8001 --reload
```

> **Note:** Local development uses SQLite by default. Set `DATABASE_URL` environment variable to use PostgreSQL.

## Configuration

The application uses sensible defaults. Override via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `data/workout_tracker.db` | Database file path |
| `API_PORT` | `8000` | API server port |
| `API_DEBUG` | `false` | Enable debug mode |
| `APP_LOG_LEVEL` | `INFO` | Logging level |
| `APP_CORS_ORIGINS` | `*` | Allowed CORS origins |

```bash
# Optional: Create .env from example
cp .env.example .env
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check with DB status |
| GET | `/exercises` | List all exercises |
| GET | `/exercises/{id}` | Get exercise by ID |
| POST | `/exercises` | Create new exercise |
| PATCH | `/exercises/{id}` | Update exercise (partial) |
| DELETE | `/exercises/{id}` | Delete exercise |

### Example API Calls

```bash
# Get all exercises
curl http://localhost:8000/exercises

# Create new exercise
curl -X POST http://localhost:8000/exercises \
  -H "Content-Type: application/json" \
  -d '{"name": "Deadlift", "sets": 3, "reps": 8, "weight": 100.0}'

# Update exercise
curl -X PATCH http://localhost:8000/exercises/1 \
  -H "Content-Type: application/json" \
  -d '{"weight": 105.0}'

# Delete exercise
curl -X DELETE http://localhost:8000/exercises/1
```

The `scripts/api.http` file contains ready-to-use HTTP requests for VS Code REST Client or JetBrains HTTP Client.

## AI Coach Service

The AI Coach provides intelligent workout recommendations and fitness advice using OpenAI's GPT models through Pydantic AI.

### AI Coach Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with service status |
| POST | `/chat` | Chat with AI coach |
| POST | `/recommend` | Get workout recommendations |
| GET | `/analyze` | Analyze current routine |
| GET | `/exercises` | Proxy to main API |

### Example AI Coach Calls

```bash
# Chat with AI coach
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What exercises should I add for a balanced routine?", "include_workout_context": true}'

# Get workout recommendation for back
curl -X POST http://localhost:8001/recommend \
  -H "Content-Type: application/json" \
  -d '{"focus_area": "back", "session_duration_minutes": 45}'

# Analyze current workout
curl http://localhost:8001/analyze
```

## User Interfaces

The Streamlit Dashboard provides a visual web interface for managing exercises.

### Streamlit Dashboard

A web-based dashboard with real-time statistics and full CRUD operations.

**Features:**
- List & filter exercises (Weighted/Bodyweight/All)
- Search by exercise name
- Real-time metrics (total exercises, sets, volume)
- Create, update, and delete exercises
- Auto-refresh every 30 seconds

**Running the Dashboard:**
```bash
# With Docker
docker-compose up -d
# Access at http://localhost:8501

# Without Docker (API must be running)
uv run streamlit run services/frontend/src/dashboard.py
```

**User Guide:**
1. View exercises in the main table
2. Use dropdown to filter by type (Weighted/Bodyweight/All)
3. Search exercises by name
4. Click "Load Exercise" to update an existing exercise
5. Fill the form to create new exercises
6. Delete exercises from the bottom section


## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest services/api/tests/test_api.py -v
uv run pytest services/frontend/tests/test_client.py -v

# Run with coverage
uv run pytest --cov=services
```


## Database

- **Docker:** PostgreSQL 15 (data persists via Docker volume)
- **Local dev:** SQLite (`data/workout_tracker.db`)
- **Seed data:** Use the dashboard to add exercises, or run:
  ```bash
  uv run python scripts/seed.py
  ```

## Tech Stack

- **Framework:** FastAPI 0.115+
- **Server:** Uvicorn
- **Database:** PostgreSQL 15 (Docker) / SQLite3 (local)
- **Validation:** Pydantic 2.10+
- **Dashboard:** Streamlit 1.40+
- **HTTP Client:** httpx
- **Package Manager:** uv
- **Container:** Docker + Docker Compose

## AI Assistance

### Tools Used
- **GitHub Copilot:** Code completion for FastAPI routes, Pydantic models, and test cases
- **Claude (AI Assistant):** Architecture guidance, project restructuring, and documentation

### How Outputs Were Verified
- All generated code was tested locally using `pytest`
- API endpoints verified via Swagger UI and `scripts/api.http`
- Dashboard functionality tested manually in browser
- Docker builds verified with `docker-compose up --build`
