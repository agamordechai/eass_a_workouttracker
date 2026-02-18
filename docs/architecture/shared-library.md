# Shared Library Architecture

## Overview

The `/services/shared/` directory contains a shared library used across all microservices (API, AI Coach, Worker) to reduce code duplication and ensure consistency.

## Structure

```
services/shared/
├── models/              # Pydantic models
│   └── exercise.py      # Unified Exercise models
├── clients/             # Base HTTP clients
│   └── base_client.py   # BaseAPIClient for service communication
└── config/              # Configuration utilities
    └── base_settings.py # Common settings helpers
```

## Components

### Models (`services/shared/models/`)

Unified Pydantic models used across all services:

- **ExerciseBase**: Base model with common exercise fields
- **ExerciseCreate**: Model for creating new exercises
- **ExerciseResponse**: Model for API responses (includes ID)
- **ExerciseEditRequest**: Model for partial updates
- **PaginatedExerciseResponse**: Paginated list wrapper

**Benefits:**
- Single source of truth for data validation
- Consistent field validation across services
- Easier to maintain and update schemas

### Clients (`services/shared/clients/`)

Base HTTP client for service-to-service communication:

- **BaseAPIClient**: Abstract base class with:
  - Connection management
  - Health check functionality
  - Timeout configuration
  - Async context manager support

**Usage:**
```python
from services.shared.clients import BaseAPIClient

class WorkoutAPIClient(BaseAPIClient):
    async def get_exercises(self):
        client = await self.get_client()
        response = await client.get("/exercises")
        return response.json()
```

### Config (`services/shared/config/`)

Common configuration utilities:

- **LogLevel**: Enum for consistent log levels
- **build_redis_url()**: Helper to construct Redis connection URLs

## Usage Guidelines

1. **Always import from shared when available**: Don't recreate models that exist in shared
2. **Extend, don't modify**: If you need service-specific models, extend the shared base classes
3. **Keep it generic**: Only add to shared if it's truly used by multiple services

## Related Documentation

- [Service Communication](./service-communication.md)
- [Service Contract](../service-contract.md)
