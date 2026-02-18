# Service Communication Patterns

## Overview

This document describes how GrindLogger services communicate with each other.

## Architecture

```
┌─────────────┐
│  Frontend   │
│  (React)    │
└──────┬──────┘
       │
       │ HTTP/REST
       ▼
┌─────────────┐      ┌─────────────┐
│  Workout    │◄────►│  AI Coach   │
│    API      │      │  Service    │
└──────┬──────┘      └──────┬──────┘
       │                    │
       │                    │
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│ PostgreSQL  │      │   Redis     │
└─────────────┘      └─────────────┘
       ▲
       │
┌──────┴──────┐
│   Worker    │
│  (Arq)      │
└─────────────┘
```

## HTTP Clients

### Base Client Pattern

All services use `BaseAPIClient` from the shared library:

```python
from services.shared.clients import BaseAPIClient

class ServiceClient(BaseAPIClient):
    def __init__(self):
        super().__init__(
            base_url="http://target-service:8000",
            timeout=10.0
        )
```

### AI Coach → Workout API

The AI Coach service calls the Workout API to fetch exercise data:

**Client**: `services/ai_coach/src/workout_client.py` (extends `BaseAPIClient`)

**Endpoints used:**
- `GET /exercises` - Fetch all exercises
- `GET /health` - Health check

**Models**: Uses `ExerciseResponse` from shared library

### Worker → Services

The Worker service communicates with both API and AI Coach:

**Clients**: `services/worker/src/clients.py`

**Patterns:**
- Uses httpx.AsyncClient singletons
- Could be refactored to extend `BaseAPIClient`

## Request/Response Models

All services use the unified models from `services/shared/models/`:

- **ExerciseCreate**: Creating new exercises
- **ExerciseResponse**: API responses
- **ExerciseEditRequest**: Updating exercises

This ensures:
- Type safety across service boundaries
- Consistent validation
- Easy contract changes

## Error Handling

Services follow consistent error handling:

1. **Client-side**:
   - Catch httpx exceptions
   - Log errors with context
   - Return empty lists or default values for degraded functionality

2. **Server-side**:
   - Return appropriate HTTP status codes
   - Include error details in response body
   - Log all errors for debugging

## Health Checks

All services expose `/health` endpoints:

- **API**: `GET /health` - Checks database connectivity
- **AI Coach**: `GET /health` - Checks Redis and API connectivity
- **Worker**: Health checks via Arq job queue

## Related Documentation

- [Shared Library](./shared-library.md)
- [Service Contract](../service-contract.md)
