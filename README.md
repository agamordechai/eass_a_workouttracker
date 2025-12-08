# Workout Tracker API

A FastAPI-based REST API for managing workout exercises with SQLite persistence.

## Project Structure

```
├── services/
│   ├── api/                 # FastAPI REST service
│   │   ├── Dockerfile       # API container definition
│   │   ├── pyproject.toml   # API-specific dependencies
│   │   ├── src/
│   │   │   ├── api.py       # FastAPI application
│   │   │   └── database/    # SQLite models, CRUD, schemas
│   │   └── tests/           # API tests
│   │
│   ├── frontend/            # Streamlit dashboard
│   │   ├── Dockerfile       # Frontend container definition
│   │   ├── pyproject.toml   # Frontend-specific dependencies
│   │   ├── src/
│   │   │   ├── dashboard.py # Streamlit UI
│   │   │   └── client.py    # HTTP client for API
│   │   └── tests/           # Frontend tests
│   │
│   └── cli/                 # CLI utilities
│       ├── Dockerfile       # CLI container definition
│       ├── pyproject.toml   # CLI-specific dependencies
│       ├── src/
│       │   └── cli.py       # Typer CLI commands
│       └── tests/           # CLI tests
│
├── data/
│   ├── workout_tracker.db   # SQLite database
│   └── exports/             # Exported CSV/JSON files
│
├── scripts/                 # Utility scripts
│   ├── api.http             # HTTP requests for API testing
│   └── seed.py              # Database seeding script
│
├── docker-compose.yml       # Multi-service orchestration
└── pyproject.toml           # Root project dependencies (for local dev)
```

## Setup

### Option 1: Docker Compose (Recommended)

```bash
# 1. Start all services
docker-compose up -d

# 2. Seed sample data
docker-compose run --rm cli python -m services.cli.src.cli seed --count 5

# 3. Open dashboard
open http://localhost:8501
```

**Services:**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Streamlit Dashboard**: http://localhost:8501

### Option 2: Local Development (Without Docker)

```bash
# Install dependencies
uv pip install -e .

# Terminal 1 - Start API
uvicorn services.api.src.api:app --reload

# Terminal 2 - Start dashboard
streamlit run services/frontend/src/dashboard.py

# Terminal 3 (optional) - Seed data
uv run python -m services.cli.src.cli seed --count 5
```

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

## User Interfaces

This project provides two interfaces for interacting with the Workout Tracker API:
- **Streamlit Dashboard** - Visual web interface for managing exercises
- **Typer CLI** - Command-line interface for operators and automation

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
streamlit run services/frontend/src/dashboard.py
```

**User Guide:**
1. View exercises in the main table
2. Use dropdown to filter by type (Weighted/Bodyweight/All)
3. Search exercises by name
4. Click "Load Exercise" to update an existing exercise
5. Fill the form to create new exercises
6. Delete exercises from the bottom section

### Typer CLI

Command-line interface with rich terminal output.

**Features:**
- List exercises (table, JSON, CSV formats)
- Add/remove exercises
- View statistics and metrics
- Seed sample data
- Export to JSON

**CLI Commands:**
```bash
# List exercises
uv run python -m services.cli.src.cli list
uv run python -m services.cli.src.cli list --format json
uv run python -m services.cli.src.cli list --format csv

# Add exercise
uv run python -m services.cli.src.cli add "Deadlift" --sets 5 --reps 5 --weight 120

# Show specific exercise
uv run python -m services.cli.src.cli show 1

# Delete exercise
uv run python -m services.cli.src.cli remove 1 --force

# View statistics
uv run python -m services.cli.src.cli stats

# Seed sample data
uv run python -m services.cli.src.cli seed --count 10

# Export to JSON
uv run python -m services.cli.src.cli export --output exercises.json

# Help
uv run python -m services.cli.src.cli --help
```

**With Docker:**
```bash
docker-compose run --rm cli python -m services.cli.src.cli list
docker-compose run --rm cli python -m services.cli.src.cli stats
docker-compose run --rm cli python -m services.cli.src.cli seed --count 5
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest services/api/tests/test_api.py -v
pytest services/cli/tests/test_cli.py -v

# Run with coverage
pytest --cov=services
```

### CLI Tests

CLI tests use Typer's `CliRunner` to verify command execution:

```bash
pytest services/cli/tests/test_cli.py -v
```

## Database

- **Type:** SQLite
- **Location:** `data/workout_tracker.db`
- **Persistence:** Data persists via Docker volume mount or local file
- **Seed data:** Auto-created on first run, or use CLI to seed

```bash
# Seed sample exercises
uv run python -m services.cli.src.cli seed --count 10
```

## Tech Stack

- **Framework:** FastAPI 0.115+
- **Server:** Uvicorn
- **Database:** SQLite3
- **Validation:** Pydantic 2.10+
- **Dashboard:** Streamlit 1.40+
- **CLI:** Typer + Rich
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
- CLI commands tested via `CliRunner` and manual execution
- Docker builds verified with `docker-compose up --build`
