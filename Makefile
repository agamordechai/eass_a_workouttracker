# Workout Tracker - Development Commands
# Quick reference for common development tasks

.PHONY: help test test-fast test-slow test-parallel install lint format clean

help:  ## Show this help message
	@echo "Workout Tracker Development Commands"
	@echo "====================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Testing Commands
# ----------------

test:  ## Run all tests (default speed)
	uv run pytest services/api/tests/ -v

test-fast:  ## Run tests excluding slow tests (Schemathesis) and Redis tests
	uv run pytest services/api/tests/ -v -m "not slow and not redis"

test-slow:  ## Run only slow tests (Schemathesis property-based)
	uv run pytest services/api/tests/ -v -m slow

test-parallel:  ## Run tests in parallel (faster, requires pytest-xdist)
	uv run pytest services/api/tests/ -n auto -m "not slow"

test-coverage:  ## Run tests with coverage report
	uv run pytest services/api/tests/ --cov=services/api/src --cov-report=html --cov-report=term

test-quick:  ## Fastest test run (parallel + skip slow + skip Redis)
	@echo "Running fast tests in parallel..."
	uv run pytest services/api/tests/ -n auto -m "not slow and not redis" -q

# CLI Testing
test-cli:  ## Run Typer CLI tests
	uv run pytest scripts/test_cli.py -v

# Specific test suites
test-api:  ## Run API tests only
	uv run pytest services/api/tests/test_api.py -v

test-auth:  ## Run authentication tests only
	uv run pytest services/api/tests/test_auth.py -v

test-refresh:  ## Run async refresh tests
	uv run pytest scripts/test_refresh.py -v

# Installation & Setup
# --------------------

install:  ## Install dependencies
	uv sync

install-dev:  ## Install with dev dependencies
	uv sync --all-extras

# Code Quality
# ------------

lint:  ## Run linter (ruff)
	uv run ruff check services/

format:  ## Format code with ruff
	uv run ruff format services/

format-check:  ## Check formatting without modifying
	uv run ruff format --check services/

# Database & Services
# -------------------

db-seed:  ## Seed database with sample data
	uv run python scripts/cli.py seed --count 10

db-reset:  ## Reset database (WARNING: deletes all data)
	uv run python scripts/cli.py reset --yes --sample 5

stats:  ## Show workout statistics
	uv run python scripts/cli.py stats

export-csv:  ## Export exercises to CSV
	uv run python scripts/cli.py export --format csv

# Docker Commands
# ---------------

docker-up:  ## Start all services with Docker Compose
	docker compose up -d

docker-down:  ## Stop all services
	docker compose down

docker-logs:  ## View logs from all services
	docker compose logs -f

docker-build:  ## Rebuild Docker images
	docker compose build

docker-clean:  ## Stop and remove all containers and volumes
	docker compose down -v

# Redis (for local testing)
# -------------------------

redis-start:  ## Start Redis in Docker (for rate limit tests)
	docker run -d --name workout-redis -p 6379:6379 redis:7-alpine

redis-stop:  ## Stop Redis container
	docker stop workout-redis && docker rm workout-redis

# Cleanup
# -------

clean:  ## Remove Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

clean-db:  ## Remove local SQLite database files
	find . -name "*.db" -type f -delete
	find . -name "test_*.db" -type f -delete

# Demo & Presentation
# -------------------

demo:  ## Run EX3 demo script
	./scripts/demo.sh

# Development Workflow Examples
# -----------------------------
#
# Quick development cycle:
#   make test-quick           # Fast tests before commit
#   make format              # Auto-format code
#   make test-coverage       # Full test run with coverage
#
# Before submission:
#   make clean               # Clean up artifacts
#   make docker-build        # Rebuild containers
#   make docker-up           # Start full stack
#   make test                # Run all tests
#   make demo                # Final demo run
