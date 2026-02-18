"""AI Coach agent using Pydantic AI."""
import logging
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from services.ai_coach.src.config import get_settings
from services.ai_coach.src.models import (
    WorkoutContext,
    WorkoutRecommendation,
    ProgressAnalysis,
    MuscleGroup
)

logger = logging.getLogger(__name__)


@dataclass
class CoachDependencies:
    """Dependencies for the AI coach agent."""
    workout_context: WorkoutContext | None = None
    focus_area: str | None = None
    custom_focus: str | None = None
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

settings = get_settings()


def _build_model(api_key: str | None = None) -> AnthropicModel | None:
    """Build an AnthropicModel with a per-request key, or None to use the agent default.

    Args:
        api_key: Anthropic API key to use for this request

    Returns:
        An AnthropicModel configured with the given key, or None
    """
    if api_key is None:
        return None
    # Strip the provider prefix (e.g. "anthropic:") for the raw model name
    model_name = settings.ai_model.split(":", 1)[-1]
    provider = AnthropicProvider(api_key=api_key)
    return AnthropicModel(model_name, provider=provider)


# Initialize the coach agent

# Create the agent - using OpenAI by default
coach_agent = Agent(
    system_prompt=COACH_SYSTEM_PROMPT,
    deps_type=CoachDependencies,
)


@coach_agent.system_prompt
async def add_workout_context(ctx) -> str:
    """Add workout context to the system prompt if available.

    Args:
        ctx: Pydantic AI agent context containing dependencies

    Returns:
        Formatted string with workout context information
    """
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
    workout_context: WorkoutContext | None = None,
    api_key: str | None = None,
) -> str:
    """Chat with the AI coach.

    Args:
        message: User message
        workout_context: Optional workout context for personalized responses
        api_key: Per-request Anthropic API key override

    Returns:
        Coach response
    """
    deps = CoachDependencies(workout_context=workout_context)
    model = _build_model(api_key)

    try:
        result = await coach_agent.run(message, deps=deps, model=model)
        return result.output
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise


async def get_workout_recommendation(
    workout_context: WorkoutContext | None = None,
    focus_area: MuscleGroup | None = None,
    custom_focus_area: str | None = None,
    equipment: list[str] | None = None,
    session_duration: int = 60,
    api_key: str | None = None,
) -> WorkoutRecommendation:
    """Get a workout recommendation from the AI coach.

    Args:
        workout_context: Current workout data for context
        focus_area: Target muscle group
        equipment: Available equipment
        session_duration: Workout duration in minutes
        api_key: Per-request Anthropic API key override

    Returns:
        Structured workout recommendation
    """
    focus_label = (
        custom_focus_area
        or (focus_area.value.replace("_", "/").title() if focus_area else "Full Body")
    )

    deps = CoachDependencies(
        workout_context=workout_context,
        focus_area=focus_area.value if focus_area else None,
        custom_focus=custom_focus_area,
        equipment=equipment or ["barbell", "dumbbells", "cables", "bodyweight"],
        session_duration=session_duration
    )

    prompt = f"""Generate a complete workout routine recommendation.

Session Duration: {session_duration} minutes per session
Focus Area: {focus_label}
Available Equipment: {', '.join(deps.equipment)}

Please provide:
1. A catchy workout title
2. Brief description of the routine
3. 4-8 exercises, structured as a proper training split if full-body, or a single day if focused
4. Estimated session duration in minutes
5. Difficulty level (Beginner/Intermediate/Advanced)
6. 2-3 general tips
7. A split_type label (e.g. "Push/Pull/Legs", "Upper/Lower", "Full Body", "Single Day - Chest")

IMPORTANT - Workout Day Assignment:
- For a focused session (single muscle group): assign all exercises to workout_day "A"
- For full body or multi-muscle routines: create a proper multi-day split:
  * 2-day split: days "A" and "B"
  * 3-day split: days "A", "B", and "C"
  * Each exercise must have a workout_day field set to "A", "B", or "C"
- Distribute exercises logically across days (e.g. push muscles on Day A, pull on B, legs on C)
- Each exercise reps field must be a string like "8" or "8-12"

If workout context is available, complement existing exercises rather than duplicate them."""

    try:
        # Use structured output for the recommendation
        model = _build_model(api_key)
        recommendation_agent = Agent(
            output_type=WorkoutRecommendation,
            system_prompt=COACH_SYSTEM_PROMPT,
            deps_type=CoachDependencies,
        )

        result = await recommendation_agent.run(prompt, deps=deps, model=model)
        return result.output
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise


async def analyze_progress(
    workout_context: WorkoutContext,
    api_key: str | None = None,
) -> ProgressAnalysis:
    """Analyze workout progress and provide insights.

    Args:
        workout_context: Current workout data
        api_key: Per-request Anthropic API key override

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
        model = _build_model(api_key)
        analysis_agent = Agent(
            output_type=ProgressAnalysis,
            system_prompt=COACH_SYSTEM_PROMPT,
            deps_type=CoachDependencies,
        )

        # Register the workout context system prompt
        @analysis_agent.system_prompt
        async def add_analysis_workout_context(ctx) -> str:
            """Add workout context to the analysis system prompt.

            Args:
                ctx: Pydantic AI agent context containing dependencies

            Returns:
                Formatted string with workout context information
            """
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

        result = await analysis_agent.run(prompt, deps=deps, model=model)
        return result.output
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        logger.error(f"Workout context: {deps.workout_context}")
        # Re-raise the exception so we can see what's actually wrong
        raise



