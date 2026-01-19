"""FastAPI application for Workout Tracker.

This module defines the REST API endpoints for managing workout exercises.
"""
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from contextlib import asynccontextmanager
from typing import List, AsyncGenerator
from datetime import datetime, timezone, timedelta
import logging
import time
import uuid

from services.api.src.database.config import get_settings
from services.api.src.database.models import Exercise, ExerciseResponse, ExerciseEditRequest, HealthResponse
from services.api.src.database.repository import (
    get_all_exercises,
    get_exercise_by_id,
    create_exercise,
    edit_exercise,
    delete_exercise
)
from services.api.src.auth import (
    User,
    Token,
    LoginRequest,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    require_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    USERS_DB,
)
from typing import Annotated

# Get application settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan event handler.

    Manages startup and shutdown events for the FastAPI application.
    Logs configuration information on startup and cleanup on shutdown.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control is yielded to the application during its runtime.
    """
    # Startup
    logger.info(f"Starting Workout Tracker API v{settings.api.version}")
    logger.info(f"Database path: {settings.db.path}")
    logger.info(f"Debug mode: {settings.api.debug}")

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

    Adds request tracing capabilities and performance monitoring by logging
    each request with a unique trace ID and calculating response time.

    Args:
        request (Request): The incoming HTTP request object.
        call_next (RequestResponseEndpoint): The next middleware or route handler in the chain.

    Returns:
        Response: The HTTP response with X-Request-Id and X-Response-Time headers added.
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
def read_root() -> dict[str, str]:
    """Get the root endpoint welcome message.

    Returns:
        dict[str, str]: A dictionary containing a welcome message and configuration info.
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
        HealthResponse: Health status including service info and database connectivity.
    """
    db_healthy = True
    db_message = "Connected"

    try:
        # Quick database connectivity check
        exercises = get_all_exercises()
        exercise_count = len(exercises) if exercises else 0
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


@app.get('/exercises', response_model=List[ExerciseResponse])
def read_exercises() -> List[ExerciseResponse]:
    """Get all exercises from the database.

    Returns:
        List[ExerciseResponse]: A list of all exercises with their details.
    """
    return get_all_exercises()


@app.get('/exercises/{exercise_id}', response_model=ExerciseResponse)
def read_exercise(exercise_id: int) -> ExerciseResponse:
    """Get a specific exercise by ID.

    Args:
        exercise_id (int): The unique identifier of the exercise to retrieve.

    Returns:
        ExerciseResponse: The exercise details if found.

    Raises:
        HTTPException: 404 error if the exercise is not found.
    """
    exercise = get_exercise_by_id(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return exercise


@app.post('/exercises', response_model=ExerciseResponse, status_code=201)
def add_exercise(exercise: Exercise) -> ExerciseResponse:
    """Create a new exercise in the database.

    Args:
        exercise (Exercise): The exercise data including name, sets, reps, and optional weight.

    Returns:
        ExerciseResponse: The newly created exercise with its assigned ID.
    """
    new_exercise = create_exercise(
        name=exercise.name,
        sets=exercise.sets,
        reps=exercise.reps,
        weight=exercise.weight
    )
    return new_exercise


@app.patch('/exercises/{exercise_id}', response_model=ExerciseResponse)
def edit_exercise_endpoint(exercise_id: int, exercise_edit: ExerciseEditRequest) -> ExerciseResponse:
    """Update any attributes of a specific exercise.

    Args:
        exercise_id (int): The unique identifier of the exercise to update.
        exercise_edit (ExerciseEditRequest): The exercise fields to update (all fields optional).

    Returns:
        ExerciseResponse: The updated exercise details.

    Raises:
        HTTPException: 404 error if the exercise is not found.
    """
    # Check if weight was explicitly provided in the request (even if None/null)
    # model_dump(exclude_unset=True) only includes fields that were actually set
    provided_fields = exercise_edit.model_dump(exclude_unset=True)
    update_weight_flag = 'weight' in provided_fields

    exercise = edit_exercise(
        exercise_id,
        name=exercise_edit.name,
        sets=exercise_edit.sets,
        reps=exercise_edit.reps,
        weight=exercise_edit.weight,
        update_weight=update_weight_flag
    )
    if not exercise:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return exercise


@app.delete('/exercises/{exercise_id}', status_code=204)
def delete_exercise_endpoint(exercise_id: int) -> None:
    """Delete a specific exercise from the database.

    Args:
        exercise_id (int): The unique identifier of the exercise to delete.

    Returns:
        None: No content on successful deletion.

    Raises:
        HTTPException: 404 error if the exercise is not found.
    """
    success = delete_exercise(exercise_id)
    if not success:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return None


# ============ Authentication Endpoints ============

@app.post('/auth/login', response_model=Token, tags=["Authentication"])
def login(login_request: LoginRequest) -> Token:
    """Authenticate user and return JWT tokens.

    Args:
        login_request: Username and password

    Returns:
        Token: Access and refresh tokens

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user = authenticate_user(login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(user.username)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )


@app.get('/auth/me', response_model=User, tags=["Authentication"])
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Get current authenticated user info.

    Args:
        current_user: Current user from JWT token

    Returns:
        User: Current user details
    """
    return current_user


@app.get('/admin/users', tags=["Admin"])
async def list_users(
    current_user: Annotated[User, Depends(require_admin)]
) -> list[dict]:
    """List all users (admin only).

    Args:
        current_user: Current admin user

    Returns:
        List of users (without passwords)
    """
    return [
        {
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "disabled": user.disabled
        }
        for user in USERS_DB.values()
    ]


@app.delete('/admin/exercises/{exercise_id}', status_code=204, tags=["Admin"])
async def admin_delete_exercise(
    exercise_id: int,
    current_user: Annotated[User, Depends(require_admin)]
) -> None:
    """Delete exercise (admin only, protected route).

    Args:
        exercise_id: ID of exercise to delete
        current_user: Current admin user

    Raises:
        HTTPException: 404 if exercise not found
    """
    success = delete_exercise(exercise_id)
    if not success:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return None

