#!/usr/bin/env python3
"""FastMCP server for Workout Tracker exercises.

This script exposes workout tracker exercises via the Model Context Protocol (MCP),
allowing AI assistants to query and interact with exercise data directly.

Usage:
    # Run the MCP server (stdio transport)
    uv run python scripts/exercises_mcp.py

    # Test with the probe script
    uv run python scripts/mcp_probe.py
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP
from sqlmodel import Session
from services.api.src.database.database import engine
from services.api.src.database.sqlmodel_repository import ExerciseRepository

# Create FastMCP server
mcp = FastMCP("io.workout.tracker")


@mcp.tool(name="list-exercises")
def list_exercises(
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "id",
    sort_order: str = "asc"
) -> dict:
    """List workout exercises with pagination and sorting.

    Args:
        page: Page number (1-indexed, default: 1)
        page_size: Number of exercises per page (1-100, default: 10)
        sort_by: Column to sort by (id, name, sets, reps, weight, workout_day)
        sort_order: Sort order ('asc' or 'desc', default: 'asc')

    Returns:
        Dictionary with pagination metadata and exercise items:
        {
            "status": 200,
            "page": 1,
            "page_size": 10,
            "total": 42,
            "items": [
                {
                    "id": 1,
                    "name": "Bench Press",
                    "sets": 4,
                    "reps": 8,
                    "weight": 80.0,
                    "workout_day": "A"
                },
                ...
            ]
        }
    """
    # Validate parameters
    if page < 1:
        return {"status": 400, "error": "page must be >= 1"}
    if page_size < 1 or page_size > 100:
        return {"status": 400, "error": "page_size must be between 1 and 100"}
    if sort_by not in ["id", "name", "sets", "reps", "weight", "workout_day"]:
        return {"status": 400, "error": f"Invalid sort_by: {sort_by}"}
    if sort_order not in ["asc", "desc"]:
        return {"status": 400, "error": "sort_order must be 'asc' or 'desc'"}

    try:
        # Create database session and repository
        with Session(engine) as session:
            repo = ExerciseRepository(session)

            # Query exercises with pagination
            exercises, total = repo.list_paginated(
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # Convert to dict format
            items = [
                {
                    "id": ex.id,
                    "name": ex.name,
                    "sets": ex.sets,
                    "reps": ex.reps,
                    "weight": ex.weight,
                    "workout_day": ex.workout_day
                }
                for ex in exercises
            ]

            return {
                "status": 200,
                "page": page,
                "page_size": page_size,
                "total": total,
                "items": items
            }

    except Exception as e:
        return {
            "status": 500,
            "error": f"Database error: {str(e)}"
        }


@mcp.tool(name="get-exercise")
def get_exercise(exercise_id: int) -> dict:
    """Get a single exercise by ID.

    Args:
        exercise_id: The unique identifier of the exercise

    Returns:
        Dictionary with exercise data or error:
        {
            "status": 200,
            "exercise": {
                "id": 1,
                "name": "Bench Press",
                "sets": 4,
                "reps": 8,
                "weight": 80.0,
                "workout_day": "A"
            }
        }
    """
    if exercise_id < 1:
        return {"status": 400, "error": "exercise_id must be >= 1"}

    try:
        with Session(engine) as session:
            repo = ExerciseRepository(session)
            exercise = repo.get_by_id(exercise_id)

            if not exercise:
                return {"status": 404, "error": f"Exercise {exercise_id} not found"}

            return {
                "status": 200,
                "exercise": {
                    "id": exercise.id,
                    "name": exercise.name,
                    "sets": exercise.sets,
                    "reps": exercise.reps,
                    "weight": exercise.weight,
                    "workout_day": exercise.workout_day
                }
            }

    except Exception as e:
        return {
            "status": 500,
            "error": f"Database error: {str(e)}"
        }


@mcp.tool(name="calculate-volume")
def calculate_volume() -> dict:
    """Calculate total workout volume (sets × reps × weight) across all exercises.

    Returns:
        Dictionary with volume statistics:
        {
            "status": 200,
            "total_volume": 12500.0,
            "exercise_count": 8,
            "weighted_exercises": 6,
            "bodyweight_exercises": 2
        }
    """
    try:
        with Session(engine) as session:
            repo = ExerciseRepository(session)
            exercises = repo.get_all()

            total_volume = 0.0
            weighted_count = 0
            bodyweight_count = 0

            for ex in exercises:
                if ex.weight is not None and ex.weight > 0:
                    total_volume += ex.sets * ex.reps * ex.weight
                    weighted_count += 1
                else:
                    bodyweight_count += 1

            return {
                "status": 200,
                "total_volume": round(total_volume, 2),
                "exercise_count": len(exercises),
                "weighted_exercises": weighted_count,
                "bodyweight_exercises": bodyweight_count
            }

    except Exception as e:
        return {
            "status": 500,
            "error": f"Database error: {str(e)}"
        }


if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run(transport="stdio")
