#!/usr/bin/env python
"""Workout Tracker CLI - Operator commands for database management.

This Typer-based CLI provides operator tools for managing the workout tracker:
- Database seeding and reset
- Export to CSV/JSON
- Statistics and summaries
- Quick database operations

Usage:
    uv run python scripts/cli.py --help
    uv run python scripts/cli.py seed --count 10
    uv run python scripts/cli.py export --format csv --output data/exports/
    uv run python scripts/cli.py stats
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.api.src.database.database import get_session, init_db
from services.api.src.database.sqlmodel_repository import ExerciseRepository
from services.api.src.database.user_repository import UserRepository

app = typer.Typer(
    help="Workout Tracker CLI - Operator commands for database management",
    add_completion=False,
)
console = Console()


# Sample exercises for seeding
SAMPLE_EXERCISES = [
    {"name": "Bench Press", "sets": 4, "reps": 8, "weight": 80.0, "workout_day": "A"},
    {"name": "Squat", "sets": 4, "reps": 10, "weight": 100.0, "workout_day": "B"},
    {"name": "Deadlift", "sets": 3, "reps": 5, "weight": 120.0, "workout_day": "B"},
    {"name": "Pull-ups", "sets": 3, "reps": 12, "weight": None, "workout_day": "C"},
    {"name": "Overhead Press", "sets": 3, "reps": 10, "weight": 50.0, "workout_day": "A"},
    {"name": "Barbell Row", "sets": 4, "reps": 10, "weight": 70.0, "workout_day": "C"},
    {"name": "Dips", "sets": 3, "reps": 15, "weight": None, "workout_day": "A"},
    {"name": "Lunges", "sets": 3, "reps": 12, "weight": 30.0, "workout_day": "B"},
    {"name": "Push-ups", "sets": 3, "reps": 20, "weight": None, "workout_day": "A"},
    {"name": "Bicep Curls", "sets": 3, "reps": 12, "weight": 15.0, "workout_day": "C"},
    {"name": "Tricep Extensions", "sets": 3, "reps": 12, "weight": 25.0, "workout_day": "A"},
    {"name": "Leg Press", "sets": 3, "reps": 15, "weight": 140.0, "workout_day": "B"},
    {"name": "Lat Pulldown", "sets": 3, "reps": 10, "weight": 60.0, "workout_day": "C"},
    {"name": "Plank", "sets": 3, "reps": 60, "weight": None, "workout_day": "A"},
    {"name": "Cable Flyes", "sets": 3, "reps": 12, "weight": 20.0, "workout_day": "A"},
]


@app.command()
def seed(
    count: int = typer.Option(10, "--count", "-c", help="Number of exercises to create"),
    force: bool = typer.Option(False, "--force", "-f", help="Force seed even if data exists"),
    user_id: int = typer.Option(1, "--user-id", "-u", help="User ID to seed exercises for"),
) -> None:
    """Seed the database with sample exercises.

    Creates sample workout exercises for testing and development.
    By default, only seeds if the database is empty.

    Examples:
        uv run python scripts/cli.py seed --count 10
        uv run python scripts/cli.py seed --count 5 --force
    """
    console.print(Panel.fit("[bold cyan]Workout Tracker - Database Seeding[/bold cyan]", border_style="cyan"))

    # Initialize database
    init_db()
    console.print("✓ Database initialized", style="green")

    with next(get_session()) as session:
        repo = ExerciseRepository(session)
        existing = repo.get_all(user_id)

        if existing and not force:
            console.print(
                f"[yellow]⚠ Database already has {len(existing)} exercises. Use --force to seed anyway.[/yellow]"
            )
            raise typer.Exit(1)

        # Determine how many to create
        exercises_to_create = min(count, len(SAMPLE_EXERCISES))
        console.print(f"\n[bold]Creating {exercises_to_create} sample exercises...[/bold]\n")

        # Create exercises with progress bar
        created = []
        for i in track(range(exercises_to_create), description="Seeding exercises"):
            exercise_data = SAMPLE_EXERCISES[i]
            exercise = repo.create(user_id=user_id, **exercise_data)
            created.append(exercise)

        # Display results in a table
        table = Table(title="✓ Created Exercises", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Name", style="green")
        table.add_column("Sets×Reps", justify="center")
        table.add_column("Weight", justify="right")
        table.add_column("Day", justify="center", style="yellow")

        for ex in created:
            weight_str = f"{ex.weight} kg" if ex.weight else "bodyweight"
            table.add_row(str(ex.id), ex.name, f"{ex.sets}×{ex.reps}", weight_str, ex.workout_day)

        console.print(table)

        # Final count
        all_exercises = repo.get_all(user_id)
        console.print(f"\n[bold green]✓ Total exercises in database: {len(all_exercises)}[/bold green]\n")


@app.command()
def reset(
    sample: int = typer.Option(5, "--sample", "-s", help="Number of sample exercises to seed"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    user_id: int = typer.Option(1, "--user-id", "-u", help="User ID to seed exercises for"),
) -> None:
    """Reset the database (drop all data and reseed).

    WARNING: This will delete ALL existing exercises!

    Examples:
        uv run python scripts/cli.py reset --sample 5
        uv run python scripts/cli.py reset --yes
    """
    console.print(Panel.fit("[bold red]⚠ DATABASE RESET WARNING ⚠[/bold red]", border_style="red"))

    if not yes:
        confirm = typer.confirm("This will DELETE all exercises. Continue?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    # Reinitialize database (this creates tables fresh)
    init_db()
    console.print("✓ Database reinitialized", style="green")

    # Seed with sample data
    console.print(f"\n[bold]Seeding {sample} sample exercises...[/bold]\n")

    with next(get_session()) as session:
        repo = ExerciseRepository(session)

        # Create sample exercises
        created = []
        for i in track(range(min(sample, len(SAMPLE_EXERCISES))), description="Seeding"):
            exercise_data = SAMPLE_EXERCISES[i]
            exercise = repo.create(user_id=user_id, **exercise_data)
            created.append(exercise)

        console.print(f"[bold green]✓ Reset complete! Created {len(created)} exercises.[/bold green]\n")


@app.command()
def export(
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv or json"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output directory"),
    workout_day: str | None = typer.Option(None, "--day", "-d", help="Filter by workout day"),
    user_id: int = typer.Option(1, "--user-id", "-u", help="User ID to export exercises for"),
) -> None:
    """Export exercises to CSV or JSON format.

    Examples:
        uv run python scripts/cli.py export --format csv
        uv run python scripts/cli.py export --format json --output data/exports/
        uv run python scripts/cli.py export --day A --format csv
    """
    console.print(Panel.fit(f"[bold cyan]Exporting Exercises ({format.upper()})[/bold cyan]", border_style="cyan"))

    if format not in ["csv", "json"]:
        console.print(f"[red]✗ Invalid format: {format}. Use 'csv' or 'json'.[/red]")
        raise typer.Exit(1)

    # Get exercises
    with next(get_session()) as session:
        repo = ExerciseRepository(session)
        exercises = repo.get_all(user_id)

        # Filter by workout day if specified
        if workout_day:
            exercises = [ex for ex in exercises if ex.workout_day == workout_day]
            console.print(f"Filtered to workout day: [yellow]{workout_day}[/yellow]")

        if not exercises:
            console.print("[yellow]No exercises found to export.[/yellow]")
            raise typer.Exit(0)

        # Determine output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exercises_{timestamp}.{format}"

        if output:
            output.mkdir(parents=True, exist_ok=True)
            filepath = output / filename
        else:
            # Default to data/exports/
            default_dir = Path("data/exports")
            default_dir.mkdir(parents=True, exist_ok=True)
            filepath = default_dir / filename

        # Export
        if format == "csv":
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "name", "sets", "reps", "weight", "workout_day"])
                writer.writeheader()
                for ex in exercises:
                    writer.writerow(
                        {
                            "id": ex.id,
                            "name": ex.name,
                            "sets": ex.sets,
                            "reps": ex.reps,
                            "weight": ex.weight if ex.weight is not None else "",
                            "workout_day": ex.workout_day,
                        }
                    )
        else:  # json
            data = [
                {
                    "id": ex.id,
                    "name": ex.name,
                    "sets": ex.sets,
                    "reps": ex.reps,
                    "weight": ex.weight,
                    "workout_day": ex.workout_day,
                }
                for ex in exercises
            ]
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

        console.print(f"\n[bold green]✓ Exported {len(exercises)} exercises to:[/bold green]")
        console.print(f"  [cyan]{filepath}[/cyan]\n")


@app.command()
def stats(
    user_id: int = typer.Option(1, "--user-id", "-u", help="User ID to show stats for"),
) -> None:
    """Show workout statistics and summaries.

    Displays:
    - Total exercise count
    - Breakdown by workout day
    - Weighted vs bodyweight exercises
    - Total workout volume

    Example:
        uv run python scripts/cli.py stats
    """
    console.print(Panel.fit("[bold cyan]Workout Statistics[/bold cyan]", border_style="cyan"))

    with next(get_session()) as session:
        repo = ExerciseRepository(session)
        exercises = repo.get_all(user_id)

        if not exercises:
            console.print("[yellow]No exercises in database.[/yellow]")
            raise typer.Exit(0)

        # Calculate statistics
        total = len(exercises)
        weighted = [ex for ex in exercises if ex.weight is not None]
        bodyweight = [ex for ex in exercises if ex.weight is None]

        # Group by workout day
        by_day = {}
        for ex in exercises:
            day = ex.workout_day or "None"
            by_day[day] = by_day.get(day, 0) + 1

        # Calculate total volume (sets × reps × weight)
        total_volume = sum(ex.sets * ex.reps * ex.weight for ex in weighted)

        # Display overall stats
        table = Table(title="📊 Overall Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Total Exercises", str(total))
        table.add_row("Weighted Exercises", str(len(weighted)))
        table.add_row("Bodyweight Exercises", str(len(bodyweight)))
        table.add_row("Total Volume", f"{total_volume:,.1f} kg")

        console.print(table)

        # Display by workout day
        day_table = Table(title="📅 By Workout Day", show_header=True, header_style="bold magenta")
        day_table.add_column("Day", style="yellow", justify="center")
        day_table.add_column("Count", justify="right", style="green")
        day_table.add_column("Percentage", justify="right", style="cyan")

        for day in sorted(by_day.keys()):
            count = by_day[day]
            percentage = (count / total) * 100
            day_table.add_row(day, str(count), f"{percentage:.1f}%")

        console.print("\n", day_table)

        # Top 5 heaviest exercises
        if weighted:
            top_heavy = sorted(weighted, key=lambda ex: ex.weight or 0, reverse=True)[:5]

            heavy_table = Table(title="💪 Top 5 Heaviest", show_header=True, header_style="bold yellow")
            heavy_table.add_column("Exercise", style="green")
            heavy_table.add_column("Weight", justify="right", style="yellow")
            heavy_table.add_column("Volume (per workout)", justify="right", style="cyan")

            for ex in top_heavy:
                volume = ex.sets * ex.reps * (ex.weight or 0)
                heavy_table.add_row(ex.name, f"{ex.weight} kg", f"{volume:,.1f} kg")

            console.print("\n", heavy_table, "\n")


@app.command()
def list(
    day: str | None = typer.Option(None, "--day", "-d", help="Filter by workout day"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number to display"),
    user_id: int = typer.Option(1, "--user-id", "-u", help="User ID to list exercises for"),
) -> None:
    """List exercises in a formatted table.

    Examples:
        uv run python scripts/cli.py list
        uv run python scripts/cli.py list --day A
        uv run python scripts/cli.py list --limit 10
    """
    with next(get_session()) as session:
        repo = ExerciseRepository(session)
        exercises = repo.get_all(user_id)

        # Filter by day if specified
        if day:
            exercises = [ex for ex in exercises if ex.workout_day == day]

        # Limit results
        exercises = exercises[:limit]

        if not exercises:
            console.print("[yellow]No exercises found.[/yellow]")
            raise typer.Exit(0)

        # Display in table
        title = f"Exercises (Day {day})" if day else "All Exercises"
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Name", style="green")
        table.add_column("Sets", justify="center")
        table.add_column("Reps", justify="center")
        table.add_column("Weight", justify="right")
        table.add_column("Day", justify="center", style="yellow")

        for ex in exercises:
            weight_str = f"{ex.weight} kg" if ex.weight else "bodyweight"
            table.add_row(str(ex.id), ex.name, str(ex.sets), str(ex.reps), weight_str, ex.workout_day)

        console.print(table)
        console.print(f"\n[dim]Showing {len(exercises)} exercises[/dim]\n")


@app.command()
def info(
    user_id: int = typer.Option(1, "--user-id", "-u", help="User ID to show info for"),
) -> None:
    """Display database connection and table information.

    Example:
        uv run python scripts/cli.py info
    """
    console.print(Panel.fit("[bold cyan]Database Information[/bold cyan]", border_style="cyan"))

    with next(get_session()) as session:
        repo = ExerciseRepository(session)
        exercises = repo.get_all(user_id)

        rprint(f"[cyan]Total exercises:[/cyan] {len(exercises)}")
        rprint("[cyan]Database backend:[/cyan] SQLModel + PostgreSQL/SQLite")
        rprint("[cyan]Repository:[/cyan] ExerciseRepository")

        if exercises:
            first_id = min(ex.id for ex in exercises)
            last_id = max(ex.id for ex in exercises)
            rprint(f"[cyan]ID range:[/cyan] {first_id} - {last_id}")

        rprint()


@app.command()
def promote(
    email: str = typer.Argument(help="Email of the user to promote"),
    role: str = typer.Option("admin", "--role", "-r", help="Role to assign: admin, user, readonly"),
) -> None:
    """Promote (or change role of) a user by email.

    Examples:
        uv run python cli/workout_cli.py promote alice@example.com
        uv run python cli/workout_cli.py promote bob@example.com --role readonly
    """
    if role not in ("admin", "user", "readonly"):
        console.print(f"[red]Invalid role '{role}'. Must be admin, user, or readonly.[/red]")
        raise typer.Exit(1)

    init_db()

    with next(get_session()) as session:
        repo = UserRepository(session)
        user = repo.get_by_email(email)

        if not user:
            console.print(f"[red]User '{email}' not found.[/red]")
            raise typer.Exit(1)

        old_role = user.role
        if old_role == role:
            console.print(f"[yellow]User '{email}' already has role '{role}'.[/yellow]")
            raise typer.Exit(0)

        user.role = role
        session.add(user)
        session.commit()
        session.refresh(user)

        console.print(
            f"[bold green]Done![/bold green] {user.name} ({user.email}): "
            f"[yellow]{old_role}[/yellow] -> [cyan]{role}[/cyan]"
        )


if __name__ == "__main__":
    app()
