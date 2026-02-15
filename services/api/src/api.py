"""FastAPI application for Workout Tracker.

This module defines the REST API endpoints for managing workout exercises.
"""
from fastapi import FastAPI, HTTPException, Request, Response, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import RequestResponseEndpoint
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal, Annotated
from datetime import datetime, timezone, timedelta
from sqlmodel import Session
import csv
from io import StringIO
import logging
import time
import uuid

from services.api.src.database.config import get_settings
from services.api.src.database.models import Exercise, ExerciseResponse, ExerciseEditRequest, HealthResponse
from services.api.src.database.dependencies import RepositoryDep, UserRepositoryDep
from services.api.src.database.database import init_db, get_session
from services.api.src.database.sqlmodel_repository import ExerciseRepository
from services.api.src.database.db_models import UserTable
from services.api.src.auth import (
    Token,
    GoogleLoginRequest,
    RefreshRequest,
    RegisterRequest,
    EmailLoginRequest,
    UpdateProfileRequest,
    UserResponse,
    verify_google_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_admin,
    hash_password,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from services.api.src.ratelimit import (
    get_rate_limit_key,
    rate_limit_exceeded_handler,
    get_ratelimit_settings
)
from services.api.src.etag import maybe_return_not_modified

# Get application settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
ratelimit_settings = get_ratelimit_settings()
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=ratelimit_settings.redis_url,
    enabled=ratelimit_settings.enabled,
    headers_enabled=False,  # Disabled due to FastAPI response_model compatibility
    swallow_errors=True  # Graceful degradation if Redis unavailable
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan event handler.

    Manages startup and shutdown events for the FastAPI application.
    Logs configuration information on startup and cleanup on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control is yielded to the application during its runtime.
    """
    # Startup
    logger.info(f"Starting Workout Tracker API v{settings.api.version}")
    logger.info(f"Database: {'PostgreSQL' if settings.db.is_postgres else 'SQLite'}")
    logger.info(f"Debug mode: {settings.api.debug}")

    # Initialize database tables
    init_db()
    logger.info("Database tables initialized")

    yield

    # Shutdown
    logger.info("Shutting down Workout Tracker API")


# Initialize FastAPI app with settings
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    docs_url=settings.api.docs_url,
    openapi_url=settings.api.openapi_url,
    debug=settings.api.debug,
    lifespan=lifespan
)

# Add limiter to app state
app.state.limiter = limiter

# Add custom exception handler for rate limit exceeded
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add SlowAPI middleware (initialises request.state.view_rate_limit for decorators)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint
) -> Response:
    """Middleware to log all incoming requests with timing and trace ID.

    Args:
        request: The incoming HTTP request object.
        call_next: The next middleware or route handler in the chain.

    Returns:
        The HTTP response with X-Request-Id and X-Response-Time headers added.
    """
    # Generate or use existing trace ID
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4())[:8])
    start_time = time.time()

    # Log request
    logger.info(
        f"[{trace_id}] {request.method} {request.url.path} - Started"
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    logger.info(
        f"[{trace_id}] {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms"
    )

    # Add trace headers to response
    response.headers["X-Request-Id"] = trace_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

    return response


@app.get('/')
@limiter.limit(lambda: ratelimit_settings.public_limit)
def read_root(request: Request) -> dict[str, str]:
    """Get the root endpoint welcome message.

    Returns:
        A dictionary containing a welcome message and configuration info.
    """
    return {
        'message': 'Welcome to the Workout Tracker API',
        'version': settings.api.version,
        'docs': settings.api.docs_url
    }


@app.get('/health', response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Health check endpoint for monitoring and container orchestration.

    Returns:
        Health status including service info and database connectivity.
    """
    db_healthy = True
    db_message = "Connected"

    try:
        # Quick database connectivity check using system user
        with next(get_session()) as session:
            repo = ExerciseRepository(session)
            exercises = repo.get_all(user_id=1)
            exercise_count = len(exercises)
    except Exception as e:
        db_healthy = False
        db_message = f"Error: {str(e)}"
        exercise_count = 0

    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        version=settings.api.version,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        database={
            "status": "connected" if db_healthy else "disconnected",
            "message": db_message,
            "exercise_count": exercise_count
        }
    )


_SORTABLE_COLUMNS = {"id", "name", "sets", "reps", "weight", "workout_day"}


@app.get('/exercises')
@limiter.limit("120/minute")  # User-level read limit
def read_exercises(
    request: Request,
    repository: RepositoryDep,
    current_user: Annotated[UserTable, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
    sort_by: str = Query("id", description="Column to sort by"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    format: Literal["json", "csv"] = Query("json", description="Response format"),
) -> Response:
    """Get exercises with pagination, sorting, and optional CSV export.

    Returns paginated JSON by default. Pass ?format=csv to download as CSV.
    All responses include an X-Total-Count header with the total exercise count.
    """
    if sort_by not in _SORTABLE_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"sort_by must be one of: {sorted(_SORTABLE_COLUMNS)}"
        )

    items, total = repository.list_paginated(current_user.id, page, page_size, sort_by, sort_order)

    if format == "csv":
        buffer = StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=["id", "name", "sets", "reps", "weight", "workout_day"]
        )
        writer.writeheader()
        for item in items:
            row = item.model_dump()
            row["weight"] = row["weight"] if row["weight"] is not None else ""
            writer.writerow(row)
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.read()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="exercises.csv"',
                "X-Total-Count": str(total),
            },
        )

    # JSON response with ETag support
    payload = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [item.model_dump() for item in items],
    }
    response = JSONResponse(
        content=payload,
        headers={"X-Total-Count": str(total)},
    )

    # Return 304 Not Modified if If-None-Match matches, or add ETag header
    return maybe_return_not_modified(request, response, payload)


@app.get('/exercises/{exercise_id}', response_model=ExerciseResponse)
@limiter.limit("120/minute")  # User-level read limit
def read_exercise(
    request: Request,
    exercise_id: int,
    repository: RepositoryDep,
    current_user: Annotated[UserTable, Depends(get_current_user)],
) -> ExerciseResponse:
    """Get a specific exercise by ID.

    Args:
        exercise_id: The unique identifier of the exercise to retrieve.

    Returns:
        The exercise details if found.

    Raises:
        HTTPException: 404 error if the exercise is not found.
    """
    exercise = repository.get_by_id(exercise_id, current_user.id)
    if not exercise:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return exercise


@app.post('/exercises', response_model=ExerciseResponse, status_code=201, tags=["Exercises"])
@limiter.limit("60/minute")  # User-level write limit
def add_exercise(
    request: Request,
    exercise: Exercise,
    repository: RepositoryDep,
    current_user: Annotated[UserTable, Depends(get_current_user)],
) -> ExerciseResponse:
    """Create a new exercise in the database.

    Args:
        exercise: The exercise data including name, sets, reps, optional weight, and workout_day.

    Returns:
        The newly created exercise with its assigned ID.
    """
    return repository.create(
        user_id=current_user.id,
        name=exercise.name,
        sets=exercise.sets,
        reps=exercise.reps,
        weight=exercise.weight,
        workout_day=exercise.workout_day
    )


@app.patch('/exercises/{exercise_id}', response_model=ExerciseResponse, tags=["Exercises"])
@limiter.limit("60/minute")  # User-level write limit
def edit_exercise_endpoint(
    request: Request,
    exercise_id: int,
    exercise_edit: ExerciseEditRequest,
    repository: RepositoryDep,
    current_user: Annotated[UserTable, Depends(get_current_user)],
) -> ExerciseResponse:
    """Update any attributes of a specific exercise.

    Args:
        exercise_id: The unique identifier of the exercise to update.
        exercise_edit: The exercise fields to update (all fields optional).

    Returns:
        The updated exercise details.

    Raises:
        HTTPException: 404 error if the exercise is not found.
    """
    provided_fields = exercise_edit.model_dump(exclude_unset=True)
    update_weight_flag = 'weight' in provided_fields

    exercise = repository.update(
        exercise_id,
        user_id=current_user.id,
        name=exercise_edit.name,
        sets=exercise_edit.sets,
        reps=exercise_edit.reps,
        weight=exercise_edit.weight,
        update_weight=update_weight_flag,
        workout_day=exercise_edit.workout_day
    )
    if not exercise:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return exercise


@app.delete('/exercises/{exercise_id}', status_code=204, tags=["Exercises"])
@limiter.limit("60/minute")  # User-level write limit
def delete_exercise_endpoint(
    request: Request,
    exercise_id: int,
    repository: RepositoryDep,
    current_user: Annotated[UserTable, Depends(get_current_user)],
) -> None:
    """Delete a specific exercise from the database.

    Args:
        exercise_id: The unique identifier of the exercise to delete.

    Raises:
        HTTPException: 404 error if the exercise is not found.
    """
    success = repository.delete(exercise_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return None


@app.post('/exercises/seed', status_code=200, tags=["Exercises"])
@limiter.limit("5/minute")
def seed_exercises(
    request: Request,
    repository: RepositoryDep,
    current_user: Annotated[UserTable, Depends(get_current_user)],
) -> dict:
    """Seed default sample exercises for the current user.

    Only seeds if the user has no exercises yet.

    Returns:
        Count of exercises seeded.
    """
    count = repository.seed_initial_data(current_user.id)
    return {"seeded": count}


# ============ Authentication Endpoints ============

@app.post('/auth/google', response_model=Token, tags=["Authentication"])
@limiter.limit(lambda: ratelimit_settings.auth_limit)
def google_login(
    request: Request,
    login_request: GoogleLoginRequest,
    user_repo: UserRepositoryDep,
    exercise_repo: RepositoryDep,
) -> Token:
    """Authenticate with Google and return JWT tokens.

    Verifies the Google ID token, creates or finds the user, seeds
    exercises for new users, and issues JWT access/refresh tokens.

    Args:
        login_request: Contains the Google ID token from the frontend.

    Returns:
        Access and refresh tokens.
    """
    google_info = verify_google_token(login_request.id_token, settings.google_client_id)

    user, is_new = user_repo.find_or_create(
        google_id=google_info["sub"],
        email=google_info["email"],
        name=google_info["name"],
        picture_url=google_info.get("picture"),
    )

    if is_new:
        logger.info(f"New user {user.email} created via Google")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )


@app.post('/auth/register', response_model=Token, status_code=201, tags=["Authentication"])
@limiter.limit(lambda: ratelimit_settings.auth_limit)
def register_email(
    request: Request,
    register_request: RegisterRequest,
    user_repo: UserRepositoryDep,
) -> Token:
    """Register a new user with email and password.

    Args:
        register_request: Email, name, and password.

    Returns:
        Access and refresh tokens.

    Raises:
        HTTPException: 409 if email is already registered.
    """
    existing = user_repo.get_by_email(register_request.email)
    if existing:
        if existing.password_hash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        # Link password to existing Google-only account
        existing.password_hash = hash_password(register_request.password)
        user_repo.session.add(existing)
        user_repo.session.commit()
        user_repo.session.refresh(existing)
        user = existing
        logger.info(f"Linked email/password to existing Google account {user.email}")
    else:
        hashed = hash_password(register_request.password)
        user = user_repo.create_email_user(
            email=register_request.email,
            name=register_request.name,
            password_hash=hashed,
        )
        logger.info(f"New email user {user.email} registered")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
    )


@app.post('/auth/login', response_model=Token, tags=["Authentication"])
@limiter.limit(lambda: ratelimit_settings.auth_limit)
def login_email(
    request: Request,
    login_request: EmailLoginRequest,
    user_repo: UserRepositoryDep,
) -> Token:
    """Authenticate with email and password.

    Args:
        login_request: Email and password.

    Returns:
        Access and refresh tokens.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = user_repo.get_by_email(login_request.email)
    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(login_request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
    )


@app.post('/auth/refresh', response_model=Token, tags=["Authentication"])
@limiter.limit(lambda: ratelimit_settings.auth_limit)
def refresh_token(
    request: Request,
    refresh_request: RefreshRequest,
    user_repo: UserRepositoryDep,
) -> Token:
    """Refresh an access token using a refresh token.

    Args:
        refresh_request: Contains the refresh token.

    Returns:
        New access and refresh tokens.

    Raises:
        HTTPException: 401 if refresh token is invalid.
    """
    payload = decode_token(refresh_request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=new_refresh,
    )


@app.get('/auth/me', response_model=UserResponse, tags=["Authentication"])
@limiter.limit(lambda: ratelimit_settings.auth_limit)
async def get_me(
    request: Request,
    current_user: Annotated[UserTable, Depends(get_current_user)],
) -> UserResponse:
    """Get current authenticated user info.

    Args:
        current_user: Current user from JWT token.

    Returns:
        Current user details.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture_url=current_user.picture_url,
        role=current_user.role,
    )


@app.patch('/auth/me', response_model=UserResponse, tags=["Authentication"])
@limiter.limit(lambda: ratelimit_settings.auth_limit)
async def update_me(
    request: Request,
    update_data: UpdateProfileRequest,
    current_user: Annotated[UserTable, Depends(get_current_user)],
    session: Session = Depends(get_session),
) -> UserResponse:
    """Update current authenticated user's profile.

    Args:
        update_data: Profile fields to update.
        current_user: Current user from JWT token.
        session: Database session.

    Returns:
        Updated user details.
    """
    if update_data.name is not None:
        current_user.name = update_data.name

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture_url=current_user.picture_url,
        role=current_user.role,
    )


@app.delete('/auth/me', status_code=status.HTTP_204_NO_CONTENT, tags=["Authentication"])
@limiter.limit(lambda: ratelimit_settings.auth_limit)
async def delete_me(
    request: Request,
    current_user: Annotated[UserTable, Depends(get_current_user)],
    session: Session = Depends(get_session),
) -> None:
    """Permanently delete current authenticated user's account.

    This action is irreversible. All user data will be removed.

    Args:
        current_user: Current user from JWT token.
        session: Database session.
    """
    session.delete(current_user)
    session.commit()


@app.get('/admin/users', tags=["Admin"])
@limiter.limit(lambda: ratelimit_settings.admin_limit)
async def list_users(
    request: Request,
    current_user: Annotated[UserTable, Depends(require_admin)],
) -> list[dict]:
    """List all users (admin only).

    Args:
        current_user: Current admin user.

    Returns:
        List of users.
    """
    # For now return just the current admin user info
    return [
        {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "disabled": current_user.disabled,
        }
    ]


@app.delete('/admin/exercises/{exercise_id}', status_code=204, tags=["Admin"])
@limiter.limit(lambda: ratelimit_settings.admin_limit)
async def admin_delete_exercise(
    request: Request,
    exercise_id: int,
    current_user: Annotated[UserTable, Depends(require_admin)],
    repository: RepositoryDep
) -> None:
    """Delete exercise (admin only, protected route).

    Args:
        exercise_id: ID of exercise to delete.
        current_user: Current admin user.

    Raises:
        HTTPException: 404 if exercise not found.
    """
    success = repository.delete(exercise_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return None
