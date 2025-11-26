# Workout Tracker API - EX1

A FastAPI-based workout tracking service that allows users to manage exercises, sets, reps, and workout logs.

## 🏋️ Domain Theme

This project implements a **Workout Tracker** with the following core resources:
- **Exercises**: Catalog of exercises (e.g., bench press, squats, deadlifts)
- **Workout Logs**: Record of workout sessions with exercises, sets, and reps
- **Sets & Reps**: Tracking of individual sets within each exercise

## 📋 EX1 Todo

- [x] Set up FastAPI project structure
- [x] Create Pydantic models with validation
- [x] Implement CRUD endpoints
- [x] Write pytest tests
- [x] Add SQLite persistence (optional)

## 🚀 Setup

### Prerequisites
- Python 3.10+
- `uv` package manager (recommended) or `pip`

### Installation

Using `uv`:
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -r requirements.txt
```

Using `pip`:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## 🏃 Running the API

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

**Note**: The database (`workout_tracker.db`) is automatically created on first run with seed data.

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 💾 Database

The application uses **SQLite** for data persistence:
- Database file: `workout_tracker.db` (created automatically)
- Seed data: 6 sample exercises are inserted on first run
- All CRUD operations persist to disk
- Connection management via context managers for safety

## 🧪 Running Tests

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## 📡 API Endpoints

### Exercises
- `GET /exercises` - List all exercises
- `GET /exercises/{id}` - Get specific exercise
- `POST /exercises` - Create new exercise
- `PATCH /exercises/{id}` - Update exercise
- `DELETE /exercises/{id}` - Delete exercise

### Example Request
```bash
# Create an exercise
curl -X POST "http://localhost:8000/exercises" \
  -H "Content-Type: application/json" \
  -d '{"name": "Deadlift", "sets": 5, "reps": 5, "weight": 135.0}'

# Get all exercises
curl http://localhost:8000/exercises
```

## 📁 Project Structure

```
workout-tracker/
├── app/
│   ├── main.py           # FastAPI app
│   ├── models.py         # Pydantic models
│   └── repository.py     # Data layer
├── tests/
│   └── test_api.py       # API tests
└── README.md
```

---

**Due Date**: Tuesday, Dec 2, 2025 at 23:59

