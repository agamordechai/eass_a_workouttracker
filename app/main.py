from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import logging

from app.config import get_settings
from app.models import Exercise, ExerciseResponse, ExerciseEditRequest
from app.repository import get_all_exercises, get_exercise_by_id, create_exercise, edit_exercise, delete_exercise

# Get application settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler.

    Args:
        app (FastAPI): The FastAPI application instance.
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

@app.get('/')
def read_root() -> dict[str, str]:
    """Get the root endpoint welcome message.

    Returns:
        dict: A dictionary containing a welcome message and configuration info.
    """
    return {
        'message': 'Welcome to the Workout Tracker API',
        'version': settings.api.version,
        'docs': settings.api.docs_url
    }

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
    exercise = edit_exercise(
        exercise_id,
        name=exercise_edit.name,
        sets=exercise_edit.sets,
        reps=exercise_edit.reps,
        weight=exercise_edit.weight
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
