"""FastAPI application for the AI Workout Coach service."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import redis.asyncio as redis

from services.ai_coach.src.config import get_settings
from services.ai_coach.src.models import (
    ChatRequest,
    ChatResponse,
    RecommendationRequest,
    WorkoutRecommendation,
    ProgressAnalysis,
    HealthResponse
)
from services.ai_coach.src.workout_client import (
    get_workout_client,
    close_workout_client
)
from services.ai_coach.src.agent import (
    chat_with_coach,
    get_workout_recommendation,
    analyze_progress
)

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis client
redis_client: redis.Redis | None = None


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
    lifespan=lifespan
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
        redis_connected=redis_healthy
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with the AI workout coach.

    Send a message and receive personalized fitness advice.
    Optionally includes your current workout data for context.
    """
    workout_context = None

    if request.include_workout_context:
        try:
            workout_client = get_workout_client()
            workout_context = await workout_client.get_workout_context()
        except Exception as e:
            logger.warning(f"Failed to fetch workout context: {e}")

    try:
        response = await chat_with_coach(request.message, workout_context)
        return ChatResponse(
            response=response,
            context_used=workout_context is not None and len(workout_context.exercises) > 0
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get response from AI coach. Please try again."
        )


@app.post("/recommend", response_model=WorkoutRecommendation)
async def recommend_workout(request: RecommendationRequest) -> WorkoutRecommendation:
    """Get AI-generated workout recommendations.

    Generates a personalized workout plan based on your current exercises,
    target muscle group, available equipment, and desired session duration.
    """
    # Fetch current workout context
    try:
        workout_client = get_workout_client()
        workout_context = await workout_client.get_workout_context()
    except Exception as e:
        logger.warning(f"Failed to fetch workout context: {e}")
        workout_context = None

    try:
        recommendation = await get_workout_recommendation(
            workout_context=workout_context,
            focus_area=request.focus_area,
            equipment=request.equipment_available,
            session_duration=request.session_duration_minutes
        )
        return recommendation
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate workout recommendation. Please try again."
        )


@app.get("/analyze", response_model=ProgressAnalysis)
async def analyze_workout() -> ProgressAnalysis:
    """Analyze your current workout routine.

    Provides insights on your training strengths, areas for improvement,
    and actionable recommendations based on your logged exercises.
    """
    try:
        workout_client = get_workout_client()
        workout_context = await workout_client.get_workout_context()
    except Exception as e:
        logger.error(f"Failed to fetch workout context: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to workout API. Please try again."
        )

    if not workout_context.exercises:
        raise HTTPException(
            status_code=400,
            detail="No exercises found. Add some exercises to get analysis."
        )

    try:
        analysis = await analyze_progress(workout_context)
        return analysis
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze workout. Please try again."
        )


@app.get("/exercises")
async def get_current_exercises():
    """Proxy endpoint to fetch current exercises from the workout API."""
    try:
        workout_client = get_workout_client()
        exercises = await workout_client.get_exercises()
        return exercises
    except Exception as e:
        logger.error(f"Failed to fetch exercises: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to workout API."
        )

