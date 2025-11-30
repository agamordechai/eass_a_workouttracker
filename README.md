# Workout Tracker API

A FastAPI-based REST API for managing workout exercises with SQLite persistence.

## Quick Start with Docker

### Build and Run
```bash
# Build and start the API
docker compose up --build

# Or run in background
docker compose up -d --build
```

The API runs at **http://localhost:8000**

### Stop
```bash
docker compose down
```

## API Usage Examples

### View API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example API Calls

#### Using curl

```bash
# Get all exercises
curl http://localhost:8000/exercises

# Get specific exercise
curl http://localhost:8000/exercises/1

# Create new exercise
curl -X POST http://localhost:8000/exercises \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deadlift",
    "sets": 3,
    "reps": 8,
    "weight": 100.0
  }'

# Update exercise (partial update)
curl -X PATCH http://localhost:8000/exercises/1 \
  -H "Content-Type: application/json" \
  -d '{"weight": 105.0}'

# Delete exercise
curl -X DELETE http://localhost:8000/exercises/1
```

#### Using HTTPie

```bash
# Get all exercises
http GET http://localhost:8000/exercises

# Create new exercise
http POST http://localhost:8000/exercises \
  name="Deadlift" \
  sets:=3 \
  reps:=8 \
  weight:=100.0

# Update exercise
http PATCH http://localhost:8000/exercises/1 \
  weight:=105.0
```

## Test Script

Create a file `test_api.sh`:

```bash
#!/bin/bash
API_URL="http://localhost:8000"

echo "=== Testing Workout Tracker API ==="

# Test 1: Root endpoint
echo -e "\n1. Testing root endpoint..."
curl -s $API_URL/ | jq

# Test 2: Get all exercises
echo -e "\n2. Getting all exercises..."
curl -s $API_URL/exercises | jq

# Test 3: Create new exercise
echo -e "\n3. Creating new exercise..."
curl -s -X POST $API_URL/exercises \
  -H "Content-Type: application/json" \
  -d '{"name":"Barbell Row","sets":4,"reps":10,"weight":80.0}' | jq

# Test 4: Get specific exercise
echo -e "\n4. Getting exercise #1..."
curl -s $API_URL/exercises/1 | jq

# Test 5: Update exercise
echo -e "\n5. Updating exercise #1..."
curl -s -X PATCH $API_URL/exercises/1 \
  -H "Content-Type: application/json" \
  -d '{"weight":100.0}' | jq

echo -e "\n=== Tests Complete ==="
```

Run with: `chmod +x test_api.sh && ./test_api.sh`

## Local Development (without Docker)

```bash
# Install dependencies with uv
uv pip install -e .

# Run the server
uvicorn app.main:app --reload
```

## Database

- **Location**: `./data/workout_tracker.db`
- **Type**: SQLite
- **Persistence**: Data persists via Docker volume mount
- **Seed data**: 6 sample exercises created on first run

## Tech Stack

- **Framework**: FastAPI 0.115+
- **Server**: Uvicorn
- **Database**: SQLite3
- **Validation**: Pydantic 2.10+
- **Package Manager**: uv
- **Container**: Docker + Docker Compose

## Project Structure

```
workout-tracker/
├── app/
│   ├── main.py           # FastAPI routes
│   ├── models.py         # Pydantic models
│   └── repository.py     # Database layer
├── data/                 # SQLite database (gitignored)
├── Dockerfile            # Container definition
├── docker-compose.yml    # Docker orchestration
└── pyproject.toml        # Dependencies
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/exercises` | List all exercises |
| GET | `/exercises/{id}` | Get exercise by ID |
| POST | `/exercises` | Create new exercise |
| PATCH | `/exercises/{id}` | Update exercise |
| DELETE | `/exercises/{id}` | Delete exercise |

## Running Tests

```bash
pytest
pytest -v  # verbose
pytest --cov=app tests/  # with coverage
```

