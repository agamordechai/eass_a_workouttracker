"""FastAPI application for the AI Workout Coach service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import jwt
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from services.ai_coach.src.agent import analyze_progress, chat_with_coach, get_workout_recommendation
from services.ai_coach.src.config import get_settings
from services.ai_coach.src.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ProgressAnalysis,
    RecommendationRequest,
    WorkoutRecommendation,
)
from services.ai_coach.src.workout_client import close_workout_client, get_workout_client

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Redis client
redis_client: redis.Redis | None = None


def _get_auth_header(request: Request) -> str | None:
    """Extract the Authorization header from the incoming request."""
    return request.headers.get("Authorization")


def _resolve_anthropic_key(request: Request) -> str:
    """Resolve the Anthropic API key for this request.

    Priority:
      1. ``X-Anthropic-Key`` header (user-provided key)
      2. Server ``ANTHROPIC_API_KEY`` env var if the caller is an admin
      3. Raise 403

    Args:
        request: The incoming FastAPI request

    Returns:
        The resolved API key string

    Raises:
        HTTPException: 403 when no key can be resolved
    """
    # 1. User-provided key
    user_key = request.headers.get("X-Anthropic-Key")
    if user_key:
        return user_key

    # 2. Admin fallback to server key
    server_key = settings.anthropic_api_key
    if server_key:
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
        if token:
            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret_key,
                    algorithms=["HS256"],
                )
                if payload.get("role") == "admin":
                    return server_key
            except jwt.PyJWTError:
                logger.debug("JWT decode failed during admin check")

    raise HTTPException(
        status_code=403,
        detail="Anthropic API key required. Please set your API key in Settings.",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    global redis_client

    # Startup
    logger.info("Starting AI Workout Coach service")
    logger.info(f"AI Model: {settings.ai_model}")
    logger.info(f"Workout API URL: {settings.workout_api_url}")

    # Initialize Redis connection
    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Caching disabled.")
        redis_client = None

    yield

    # Shutdown
    logger.info("Shutting down AI Workout Coach service")
    await close_workout_client()
    if redis_client:
        await redis_client.aclose()


# Initialize FastAPI app
app = FastAPI(
    title="AI Workout Coach",
    description="AI-powered workout coaching service using Pydantic AI",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    workout_client = get_workout_client()
    workout_api_healthy = await workout_client.health_check()

    redis_healthy = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_healthy = True
        except Exception:
            pass

    return HealthResponse(
        status="healthy",
        service="ai-coach",
        ai_model=settings.ai_model,
        workout_api_connected=workout_api_healthy,
        redis_connected=redis_healthy,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """Chat with the AI workout coach.

    Send a message and receive personalized fitness advice.
    Optionally includes your current workout data for context.
    """
    anthropic_key = _resolve_anthropic_key(request)
    auth_header = _get_auth_header(request)
    workout_context = None

    if chat_request.include_workout_context:
        try:
            workout_client = get_workout_client()
            workout_context = await workout_client.get_workout_context(auth_header=auth_header)
        except Exception as e:
            logger.warning(f"Failed to fetch workout context: {e}")

    try:
        response = await chat_with_coach(chat_request.message, workout_context, api_key=anthropic_key)
        return ChatResponse(
            response=response, context_used=workout_context is not None and len(workout_context.exercises) > 0
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response from AI coach. Please try again.") from e


@app.post("/recommend", response_model=WorkoutRecommendation)
async def recommend_workout(request: Request, rec_request: RecommendationRequest) -> WorkoutRecommendation:
    """Get AI-generated workout recommendations.

    Generates a personalized workout plan based on your current exercises,
    target muscle group, available equipment, and desired session duration.
    """
    anthropic_key = _resolve_anthropic_key(request)
    auth_header = _get_auth_header(request)

    # Fetch current workout context
    try:
        workout_client = get_workout_client()
        workout_context = await workout_client.get_workout_context(auth_header=auth_header)
    except Exception as e:
        logger.warning(f"Failed to fetch workout context: {e}")
        workout_context = None

    try:
        recommendation = await get_workout_recommendation(
            workout_context=workout_context,
            focus_area=rec_request.focus_area,
            custom_focus_area=rec_request.custom_focus_area,
            equipment=rec_request.equipment_available,
            session_duration=rec_request.session_duration_minutes,
            api_key=anthropic_key,
        )
        return recommendation
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate workout recommendation. Please try again."
        ) from e


@app.get("/analyze", response_model=ProgressAnalysis)
async def analyze_workout(request: Request) -> ProgressAnalysis:
    """Analyze your current workout routine.

    Provides insights on your training strengths, areas for improvement,
    and actionable recommendations based on your logged exercises.
    """
    anthropic_key = _resolve_anthropic_key(request)
    auth_header = _get_auth_header(request)

    try:
        workout_client = get_workout_client()
        workout_context = await workout_client.get_workout_context(auth_header=auth_header)
    except Exception as e:
        logger.error(f"Failed to fetch workout context: {e}")
        raise HTTPException(status_code=503, detail="Unable to connect to workout API. Please try again.") from e

    if not workout_context.exercises:
        raise HTTPException(status_code=400, detail="No exercises found. Add some exercises to get analysis.")

    try:
        analysis = await analyze_progress(workout_context, api_key=anthropic_key)
        return analysis
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze workout: {str(e)}") from e


@app.get("/exercises")
async def get_current_exercises(request: Request):
    """Proxy endpoint to fetch current exercises from the workout API."""
    auth_header = _get_auth_header(request)

    try:
        workout_client = get_workout_client()
        exercises = await workout_client.get_exercises(auth_header=auth_header)
        return exercises
    except Exception as e:
        logger.error(f"Failed to fetch exercises: {e}")
        raise HTTPException(status_code=503, detail="Unable to connect to workout API.") from e
