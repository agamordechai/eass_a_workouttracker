# Worker Service

Background job worker service for the Workout Tracker application using Arq (async task queue).

## Overview

The worker service handles scheduled background jobs including:
- **Hourly Exercise Refresh**: Updates exercise data every hour
- **Daily AI Cache Warmup**: Pre-generates AI recommendations at 6 AM UTC
- **Weekly Cleanup**: Removes stale idempotency keys on Sunday at 2 AM UTC

## Architecture

- **Task Queue**: Arq with Redis DB 1 (separate from cache DB 0)
- **Cron Scheduling**: Built-in Arq cron jobs for scheduled tasks
- **Health Monitoring**: FastAPI health server on port 8002
- **Async Processing**: Bounded concurrency with retry logic and idempotency

## Redis Database Separation

- **DB 0**: AI Coach cache and idempotency keys
- **DB 1**: Arq job queue (worker tasks)

## Configuration

All configuration uses the `WORKER_` environment variable prefix with `__` for nesting:

### Redis Settings
```bash
WORKER_REDIS__HOST=redis                # Redis host
WORKER_REDIS__PORT=6379                 # Redis port
WORKER_REDIS__DATABASE=1                # Queue database (default: 1)
WORKER_REDIS__CACHE_DATABASE=0          # Cache database (default: 0)
WORKER_REDIS__PASSWORD=                 # Redis password (optional)
```

### Service URLs
```bash
WORKER_API_CLIENT__WORKOUT_API_URL=http://api:8000
WORKER_API_CLIENT__AI_COACH_URL=http://ai-coach:8001
WORKER_API_CLIENT__TIMEOUT=30
```

### Worker Settings
```bash
WORKER_WORKER__MAX_JOBS=10              # Max concurrent jobs
WORKER_WORKER__JOB_TIMEOUT=300          # Job timeout in seconds
WORKER_WORKER__HEALTH_PORT=8002         # Health check port
```

### Schedule Settings
```bash
WORKER_SCHEDULE__ENABLE_HOURLY_REFRESH=true
WORKER_SCHEDULE__ENABLE_DAILY_WARMUP=true
WORKER_SCHEDULE__ENABLE_WEEKLY_CLEANUP=true
WORKER_SCHEDULE__WARMUP_HOUR=6          # UTC hour for daily warmup
WORKER_SCHEDULE__CLEANUP_DAY_OF_WEEK=6  # 0=Monday, 6=Sunday
WORKER_SCHEDULE__CLEANUP_HOUR=2         # UTC hour for weekly cleanup
```

### Refresh Settings
```bash
WORKER_REFRESH__CONCURRENCY=5
WORKER_REFRESH__IDEMPOTENCY_TTL=3600
WORKER_REFRESH__RETRY_DELAY=5
WORKER_REFRESH__MAX_RETRIES=3
```

## Tasks

### 1. Exercise Refresh (`refresh_exercises`)
Migrated from `scripts/refresh.py` with bounded concurrency, idempotency, and retry logic.

**Schedule**: Every hour on the hour
**Features**:
- Fetches all exercises from API
- Bounded concurrency (default: 5)
- Redis-backed idempotency (prevents duplicate processing)
- Exponential backoff retries (up to 3 attempts)

### 2. AI Cache Warmup (`warmup_ai_cache`)
Pre-generates AI recommendations for common queries to improve response times.

**Schedule**: Daily at 6 AM UTC
**Coverage**:
- Muscle groups: chest, back, shoulders, legs, biceps, triceps, core
- Equipment: barbell+dumbbells, bodyweight, cables, etc.
- Durations: 30, 45, 60, 90 minutes
- Total: ~140 request combinations

### 3. Cleanup Stale Data (`cleanup_stale_data`)
Removes orphaned idempotency keys from Redis.

**Schedule**: Sunday at 2 AM UTC
**Actions**:
- Scans for `idempotency:*` keys
- Deletes keys without TTL or very short TTL (<60s)
- Logs cleanup statistics

## Health Check

The worker exposes a health endpoint at `http://localhost:8002/health`:

```bash
curl http://localhost:8002/health
```

Response:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "queue_depth": 0,
  "api_connected": true,
  "ai_coach_connected": true,
  "details": {
    "queue_depth": "0",
    "api_status": "200",
    "ai_coach_status": "200"
  }
}
```

## Development

### Running Locally

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run worker
python -m services.worker.src.worker
```

### Running Tests

```bash
pytest services/worker/tests/ -v
```

### Docker

```bash
# Build worker image
docker compose build worker

# Start worker service
docker compose up -d worker

# View logs
docker compose logs -f worker

# Check health
curl http://localhost:8002/health
```

## Monitoring

### Check Worker Logs
```bash
docker compose logs -f worker
```

### Check Redis Queue
```bash
# Connect to Redis DB 1
docker exec grindlogger-redis redis-cli -n 1

# List queue keys
KEYS "arq:*"

# Check queue length
LLEN arq:queue
```

### Manual Job Enqueue (for testing)
```python
from arq import create_pool
from arq.connections import RedisSettings

async def enqueue_test():
    pool = await create_pool(
        RedisSettings(host="localhost", port=6379, database=1)
    )
    job = await pool.enqueue_job("refresh_exercises")
    print(f"Job ID: {job.job_id}")
```

## Integration with Existing Services

### Exercise Refresh Migration
The refresh logic from `scripts/refresh.py` is now integrated into the worker service:
- **Script**: Kept as CLI wrapper for manual execution
- **Worker**: Runs automatically every hour with idempotency
- **Shared Code**: Both use `ExerciseRefresher` class from `scripts/refresh.py`

### Service Dependencies
- **API**: Required for exercise data and health checks
- **AI Coach**: Required for cache warmup and health checks
- **Redis**: Required for queue (DB 1) and idempotency (DB 0)

## Troubleshooting

### Worker Not Starting
1. Check Redis connectivity: `docker compose logs redis`
2. Check environment variables: `docker compose config worker`
3. Check worker logs: `docker compose logs worker`

### Jobs Not Running
1. Check cron configuration in logs
2. Verify schedule settings are enabled
3. Check Redis queue: `docker exec grindlogger-redis redis-cli -n 1 LLEN arq:queue`

### Health Check Failing
1. Check Redis connectivity
2. Check API/AI Coach services are running
3. Verify network connectivity: `docker compose exec worker curl http://api:8000/health`

## Performance

- **Max Concurrent Jobs**: 10 (configurable)
- **Job Timeout**: 300 seconds (5 minutes)
- **Refresh Concurrency**: 5 exercises at a time
- **Cache Warmup**: ~140 requests with 0.5s rate limiting
- **Memory Usage**: ~50-100MB typical

## Future Enhancements

- Add job result persistence
- Implement job retry dashboard
- Add Prometheus metrics
- Support for dynamic job scheduling
- Job priority queues
- Dead letter queue for failed jobs
