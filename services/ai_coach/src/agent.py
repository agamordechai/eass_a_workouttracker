"""AI Coach agent using Pydantic AI."""
import logging
from typing import Optional
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from services.ai_coach.src.config import get_settings
from services.ai_coach.src.models import (
    WorkoutContext,
    WorkoutRecommendation,
    ExerciseRecommendation,
    ProgressAnalysis,
    MuscleGroup
)

logger = logging.getLogger(__name__)


@dataclass
class CoachDependencies:
    """Dependencies for the AI coach agent."""
    workout_context: Optional[WorkoutContext] = None
    focus_area: Optional[str] = None
    equipment: list[str] | None = None
    session_duration: int = 60


# System prompt for the workout coach
COACH_SYSTEM_PROMPT = """You are an expert fitness coach and personal trainer AI assistant.
Your role is to help users with their workout routines, provide exercise recommendations,
answer fitness-related questions, and analyze their training progress.

Key responsibilities:
1. Provide personalized workout recommendations based on the user's current exercises
2. Suggest complementary exercises for balanced muscle development
3. Offer form tips and safety advice
4. Help users understand proper training volume and progression
5. Motivate and encourage users in their fitness journey

Guidelines:
- Be encouraging but honest
- Prioritize safety and proper form
- Consider the user's current workout data when making recommendations
- Provide specific, actionable advice
- Use clear, simple language avoiding excessive jargon
- When suggesting weights, be conservative and emphasize starting light

If workout context is provided, analyze it and tailor your responses accordingly.
"""

# Initialize the coach agent
settings = get_settings()

# Create the agent - using OpenAI by default
coach_agent = Agent(
    model=settings.ai_model,
    system_prompt=COACH_SYSTEM_PROMPT,
    deps_type=CoachDependencies
)


@coach_agent.system_prompt
async def add_workout_context(ctx) -> str:
    """Add workout context to the system prompt if available."""
    deps: CoachDependencies = ctx.deps

    if deps.workout_context and deps.workout_context.exercises:
        context_str = "\n\nCurrent Workout Data:\n"
        context_str += f"- Total Exercises: {deps.workout_context.exercise_count}\n"
        context_str += f"- Total Volume: {deps.workout_context.total_volume:.1f} kg\n"
        context_str += f"- Muscle Groups Worked: {', '.join(deps.workout_context.muscle_groups_worked) or 'Not identified'}\n"

        # Analyze workout split structure
        workout_days = set(ex.workout_day for ex in deps.workout_context.exercises)
        daily_exercises = [ex for ex in deps.workout_context.exercises if ex.workout_day == "None"]
        split_days = [day for day in workout_days if day != "None"]

        if daily_exercises:
            context_str += f"- Daily Exercises (done every day): {len(daily_exercises)} exercise(s)\n"

        if len(split_days) == 0 and daily_exercises:
            context_str += f"- Workout Split: ALL DAILY (no specific day split)\n"
        elif len(split_days) == 1:
            context_str += f"- Workout Split: FULL BODY (all exercises on Day {split_days[0]})\n"
        elif len(split_days) == 2:
            context_str += f"- Workout Split: A/B SPLIT (Days: {', '.join(sorted(split_days))})\n"
        elif len(split_days) == 3:
            context_str += f"- Workout Split: A/B/C SPLIT (Days: {', '.join(sorted(split_days))})\n"
        elif len(split_days) > 0:
            context_str += f"- Workout Split: {len(split_days)}-DAY SPLIT (Days: {', '.join(sorted(split_days))})\n"

        # Group exercises by workout day
        context_str += "\nExercises grouped by workout day:\n"

        # Show daily exercises first if any
        if daily_exercises:
            context_str += f"\n  Daily (Every Day):\n"
            for ex in daily_exercises:
                weight_str = f" @ {ex.weight}kg" if ex.weight else " (bodyweight)"
                context_str += f"    - {ex.name}: {ex.sets} sets x {ex.reps} reps{weight_str}\n"

        # Show split days
        for day in sorted(split_days):
            day_exercises = [ex for ex in deps.workout_context.exercises if ex.workout_day == day]
            context_str += f"\n  Day {day}:\n"
            for ex in day_exercises:
                weight_str = f" @ {ex.weight}kg" if ex.weight else " (bodyweight)"
                context_str += f"    - {ex.name}: {ex.sets} sets x {ex.reps} reps{weight_str}\n"

        return context_str

    return ""


async def chat_with_coach(
    message: str,
    workout_context: Optional[WorkoutContext] = None
) -> str:
    """Chat with the AI coach.

    Args:
        message: User message
        workout_context: Optional workout context for personalized responses

    Returns:
        Coach response
    """
    deps = CoachDependencies(workout_context=workout_context)

    try:
        result = await coach_agent.run(message, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise


async def get_workout_recommendation(
    workout_context: Optional[WorkoutContext] = None,
    focus_area: Optional[MuscleGroup] = None,
    equipment: Optional[list[str]] = None,
    session_duration: int = 60
) -> WorkoutRecommendation:
    """Get a workout recommendation from the AI coach.

    Args:
        workout_context: Current workout data for context
        focus_area: Target muscle group
        equipment: Available equipment
        session_duration: Workout duration in minutes

    Returns:
        Structured workout recommendation
    """
    deps = CoachDependencies(
        workout_context=workout_context,
        focus_area=focus_area.value if focus_area else None,
        equipment=equipment or ["barbell", "dumbbells", "cables", "bodyweight"],
        session_duration=session_duration
    )

    prompt = f"""Generate a {session_duration}-minute workout recommendation.
    
Focus Area: {focus_area.value if focus_area else 'Full body/balanced'}
Available Equipment: {', '.join(deps.equipment)}

Please provide:
1. A catchy workout title
2. Brief description of the workout
3. 4-6 exercises with sets, reps, and any notes
4. Estimated duration
5. Difficulty level (Beginner/Intermediate/Advanced)
6. 2-3 general tips

Format each exercise with: name, sets, reps (can be a range like "8-12"), optional weight suggestion, optional form notes, and primary muscle group.

If workout context is available, complement existing exercises rather than duplicate them."""

    try:
        # Use structured output for the recommendation
        recommendation_agent = Agent(
            model=settings.ai_model,
            output_type=WorkoutRecommendation,
            system_prompt=COACH_SYSTEM_PROMPT,
            deps_type=CoachDependencies
        )

        result = await recommendation_agent.run(prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        # Return a fallback recommendation
        return _get_fallback_recommendation(focus_area, session_duration)


async def analyze_progress(
    workout_context: WorkoutContext
) -> ProgressAnalysis:
    """Analyze workout progress and provide insights.

    Args:
        workout_context: Current workout data

    Returns:
        Progress analysis with recommendations
    """
    deps = CoachDependencies(workout_context=workout_context)

    prompt = """Analyze the workout routine provided in the context and give personalized feedback.

IMPORTANT: Base your analysis ONLY on the specific exercises, workout split, and training structure you see in the workout data. Do NOT provide generic advice.

Provide:
1. A brief summary of the training approach (mention the specific split type and structure you observe)
2. Identified strengths in THIS specific routine (be specific to the exercises and split shown)
3. Areas that need improvement (be specific to what's missing or imbalanced in THIS routine)
4. Specific, actionable recommendations (based on the actual exercises and gaps you see)
5. A muscle balance score (0-100) based on how well-rounded THIS specific routine is

Be encouraging but honest. Focus on practical improvements specific to this person's actual workout."""

    try:
        # Create analysis agent with the same system prompt decorator
        analysis_agent = Agent(
            model=settings.ai_model,
            output_type=ProgressAnalysis,
            system_prompt=COACH_SYSTEM_PROMPT,
            deps_type=CoachDependencies
        )

        # Register the workout context system prompt
        @analysis_agent.system_prompt
        async def add_analysis_workout_context(ctx) -> str:
            """Add workout context to the analysis system prompt."""
            deps: CoachDependencies = ctx.deps

            if deps.workout_context and deps.workout_context.exercises:
                context_str = "\n\nCurrent Workout Data:\n"
                context_str += f"- Total Exercises: {deps.workout_context.exercise_count}\n"
                context_str += f"- Total Volume: {deps.workout_context.total_volume:.1f} kg\n"
                context_str += f"- Muscle Groups Worked: {', '.join(deps.workout_context.muscle_groups_worked) or 'Not identified'}\n"

                # Analyze workout split structure
                workout_days = set(ex.workout_day for ex in deps.workout_context.exercises)
                daily_exercises = [ex for ex in deps.workout_context.exercises if ex.workout_day == "None"]
                split_days = [day for day in workout_days if day != "None"]

                if daily_exercises:
                    context_str += f"- Daily Exercises (done every day): {len(daily_exercises)} exercise(s)\n"

                if len(split_days) == 0 and daily_exercises:
                    context_str += f"- Workout Split: ALL DAILY (no specific day split)\n"
                elif len(split_days) == 1:
                    context_str += f"- Workout Split: FULL BODY (all exercises on Day {split_days[0]})\n"
                elif len(split_days) == 2:
                    context_str += f"- Workout Split: A/B SPLIT (Days: {', '.join(sorted(split_days))})\n"
                elif len(split_days) == 3:
                    context_str += f"- Workout Split: A/B/C SPLIT (Days: {', '.join(sorted(split_days))})\n"
                elif len(split_days) > 0:
                    context_str += f"- Workout Split: {len(split_days)}-DAY SPLIT (Days: {', '.join(sorted(split_days))})\n"

                # Group exercises by workout day
                context_str += "\nExercises grouped by workout day:\n"

                # Show daily exercises first if any
                if daily_exercises:
                    context_str += f"\n  Daily (Every Day):\n"
                    for ex in daily_exercises:
                        weight_str = f" @ {ex.weight}kg" if ex.weight else " (bodyweight)"
                        context_str += f"    - {ex.name}: {ex.sets} sets x {ex.reps} reps{weight_str}\n"

                # Show split days
                for day in sorted(split_days):
                    day_exercises = [ex for ex in deps.workout_context.exercises if ex.workout_day == day]
                    context_str += f"\n  Day {day}:\n"
                    for ex in day_exercises:
                        weight_str = f" @ {ex.weight}kg" if ex.weight else " (bodyweight)"
                        context_str += f"    - {ex.name}: {ex.sets} sets x {ex.reps} reps{weight_str}\n"

                return context_str

            return ""

        result = await analysis_agent.run(prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        logger.error(f"Workout context: {deps.workout_context}")
        # Re-raise the exception so we can see what's actually wrong
        raise


def _get_fallback_recommendation(
    focus_area: Optional[MuscleGroup],
    duration: int
) -> WorkoutRecommendation:
    """Get a fallback recommendation when AI is unavailable."""

    exercises_by_group = {
        MuscleGroup.CHEST: [
            ExerciseRecommendation(
                name="Bench Press", sets=4, reps="8-10",
                weight_suggestion="Start with bar only",
                notes="Keep shoulders back and down",
                muscle_group=MuscleGroup.CHEST
            ),
            ExerciseRecommendation(
                name="Incline Dumbbell Press", sets=3, reps="10-12",
                notes="30-45 degree incline",
                muscle_group=MuscleGroup.CHEST
            ),
            ExerciseRecommendation(
                name="Cable Flyes", sets=3, reps="12-15",
                notes="Focus on the squeeze",
                muscle_group=MuscleGroup.CHEST
            ),
        ],
        MuscleGroup.BACK: [
            ExerciseRecommendation(
                name="Barbell Row", sets=4, reps="8-10",
                notes="Keep back straight",
                muscle_group=MuscleGroup.BACK
            ),
            ExerciseRecommendation(
                name="Lat Pulldown", sets=3, reps="10-12",
                notes="Pull to upper chest",
                muscle_group=MuscleGroup.BACK
            ),
            ExerciseRecommendation(
                name="Seated Cable Row", sets=3, reps="12-15",
                notes="Squeeze shoulder blades",
                muscle_group=MuscleGroup.BACK
            ),
        ],
        MuscleGroup.LEGS: [
            ExerciseRecommendation(
                name="Squat", sets=4, reps="8-10",
                weight_suggestion="Start with bodyweight",
                notes="Keep knees tracking over toes",
                muscle_group=MuscleGroup.LEGS
            ),
            ExerciseRecommendation(
                name="Romanian Deadlift", sets=3, reps="10-12",
                notes="Feel the hamstring stretch",
                muscle_group=MuscleGroup.LEGS
            ),
            ExerciseRecommendation(
                name="Leg Press", sets=3, reps="12-15",
                notes="Don't lock knees at top",
                muscle_group=MuscleGroup.LEGS
            ),
        ],
    }

    # Default full body workout
    default_exercises = [
        ExerciseRecommendation(
            name="Squat", sets=3, reps="10",
            muscle_group=MuscleGroup.LEGS
        ),
        ExerciseRecommendation(
            name="Bench Press", sets=3, reps="10",
            muscle_group=MuscleGroup.CHEST
        ),
        ExerciseRecommendation(
            name="Barbell Row", sets=3, reps="10",
            muscle_group=MuscleGroup.BACK
        ),
        ExerciseRecommendation(
            name="Overhead Press", sets=3, reps="10",
            muscle_group=MuscleGroup.SHOULDERS
        ),
    ]

    exercises = exercises_by_group.get(focus_area, default_exercises) if focus_area else default_exercises

    return WorkoutRecommendation(
        title=f"{focus_area.value.title() if focus_area else 'Full Body'} Workout",
        description="A balanced workout targeting major muscle groups.",
        exercises=exercises,
        estimated_duration_minutes=duration,
        difficulty="Intermediate",
        tips=[
            "Warm up for 5-10 minutes before starting",
            "Rest 60-90 seconds between sets",
            "Focus on proper form over heavy weight"
        ]
    )

