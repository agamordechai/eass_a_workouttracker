"""Tests for the Typer CLI (scripts/cli.py).

These tests verify that all CLI commands work correctly using Typer's CliRunner.
"""
import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.cli import app
from services.api.src.database.database import init_db, get_session
from services.api.src.database.sqlmodel_repository import ExerciseRepository

runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_test_db():
    """Initialize test database before each test."""
    init_db()
    # Clean up any existing exercises
    with next(get_session()) as session:
        repo = ExerciseRepository(session)
        exercises = repo.get_all()
        for ex in exercises:
            repo.delete(ex.id)
    yield
    # Cleanup after test
    with next(get_session()) as session:
        repo = ExerciseRepository(session)
        exercises = repo.get_all()
        for ex in exercises:
            repo.delete(ex.id)


def test_cli_seed_creates_exercises():
    """Test that seed command creates sample exercises."""
    result = runner.invoke(app, ["seed", "--count", "5"])
    assert result.exit_code == 0
    assert "Creating 5 sample exercises" in result.stdout
    assert "Total exercises in database: 5" in result.stdout


def test_cli_seed_respects_existing_data():
    """Test that seed command respects existing data without --force."""
    # First seed
    runner.invoke(app, ["seed", "--count", "3"])

    # Try to seed again without --force
    result = runner.invoke(app, ["seed", "--count", "3"])
    assert result.exit_code == 1
    assert "already has 3 exercises" in result.stdout
    assert "--force" in result.stdout


def test_cli_seed_force_flag():
    """Test that --force flag allows seeding over existing data."""
    # First seed
    runner.invoke(app, ["seed", "--count", "3"])

    # Seed again with --force
    result = runner.invoke(app, ["seed", "--count", "2", "--force"])
    assert result.exit_code == 0
    # Should now have 5 exercises total (3 + 2)
    assert "Creating 2 sample exercises" in result.stdout


def test_cli_reset_with_yes_flag():
    """Test that reset command works with --yes flag."""
    # First create some exercises
    runner.invoke(app, ["seed", "--count", "5"])

    # Reset with --yes to skip confirmation
    result = runner.invoke(app, ["reset", "--sample", "3", "--yes"])
    assert result.exit_code == 0
    assert "Reset complete" in result.stdout
    assert "Created 3 exercises" in result.stdout


def test_cli_export_csv(tmp_path):
    """Test exporting exercises to CSV format."""
    # Seed some exercises
    runner.invoke(app, ["seed", "--count", "5"])

    # Export to CSV
    output_dir = tmp_path / "exports"
    result = runner.invoke(app, ["export", "--format", "csv", "--output", str(output_dir)])

    assert result.exit_code == 0
    assert "Exported 5 exercises" in result.stdout

    # Check file was created
    csv_files = list(output_dir.glob("exercises_*.csv"))
    assert len(csv_files) == 1

    # Verify CSV content
    csv_content = csv_files[0].read_text()
    assert "id,name,sets,reps,weight,workout_day" in csv_content
    assert "Bench Press" in csv_content


def test_cli_export_json(tmp_path):
    """Test exporting exercises to JSON format."""
    # Seed some exercises
    runner.invoke(app, ["seed", "--count", "3"])

    # Export to JSON
    output_dir = tmp_path / "exports"
    result = runner.invoke(app, ["export", "--format", "json", "--output", str(output_dir)])

    assert result.exit_code == 0
    assert "Exported 3 exercises" in result.stdout

    # Check file was created
    json_files = list(output_dir.glob("exercises_*.json"))
    assert len(json_files) == 1

    # Verify JSON content
    data = json.loads(json_files[0].read_text())
    assert len(data) == 3
    assert data[0]["name"] == "Bench Press"
    assert "sets" in data[0]
    assert "reps" in data[0]


def test_cli_export_filtered_by_day(tmp_path):
    """Test exporting exercises filtered by workout day."""
    # Seed exercises
    runner.invoke(app, ["seed", "--count", "10"])

    # Export only day A exercises
    output_dir = tmp_path / "exports"
    result = runner.invoke(app, [
        "export",
        "--format", "json",
        "--day", "A",
        "--output", str(output_dir)
    ])

    assert result.exit_code == 0
    assert "Filtered to workout day: A" in result.stdout

    # Verify only day A exercises
    json_files = list(output_dir.glob("exercises_*.json"))
    data = json.loads(json_files[0].read_text())
    assert all(ex["workout_day"] == "A" for ex in data)


def test_cli_stats_shows_summary():
    """Test that stats command shows workout statistics."""
    # Seed exercises
    runner.invoke(app, ["seed", "--count", "10"])

    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "Overall Statistics" in result.stdout
    assert "Total Exercises" in result.stdout
    assert "Weighted Exercises" in result.stdout
    assert "Bodyweight Exercises" in result.stdout
    assert "By Workout Day" in result.stdout


def test_cli_stats_empty_database():
    """Test stats command with empty database."""
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "No exercises in database" in result.stdout


def test_cli_list_shows_exercises():
    """Test that list command displays exercises."""
    # Seed exercises
    runner.invoke(app, ["seed", "--count", "5"])

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "All Exercises" in result.stdout
    assert "Showing 5 exercises" in result.stdout
    assert "Bench Press" in result.stdout


def test_cli_list_filtered_by_day():
    """Test list command filtered by workout day."""
    # Seed exercises
    runner.invoke(app, ["seed", "--count", "10"])

    result = runner.invoke(app, ["list", "--day", "A"])
    assert result.exit_code == 0
    assert "Exercises (Day A)" in result.stdout


def test_cli_list_with_limit():
    """Test list command with limit parameter."""
    # Seed exercises
    runner.invoke(app, ["seed", "--count", "10"])

    result = runner.invoke(app, ["list", "--limit", "3"])
    assert result.exit_code == 0
    assert "Showing 3 exercises" in result.stdout


def test_cli_info_shows_database_info():
    """Test that info command displays database information."""
    # Seed exercises
    runner.invoke(app, ["seed", "--count", "5"])

    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Database Information" in result.stdout
    assert "Total exercises: 5" in result.stdout
    assert "SQLModel" in result.stdout


def test_cli_help_displays_usage():
    """Test that --help flag shows usage information."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Workout Tracker CLI" in result.stdout
    assert "seed" in result.stdout
    assert "export" in result.stdout
    assert "stats" in result.stdout
    assert "list" in result.stdout


def test_cli_command_help():
    """Test that each command has help text."""
    commands = ["seed", "reset", "export", "stats", "list", "info"]

    for cmd in commands:
        result = runner.invoke(app, [cmd, "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout or "Examples:" in result.stdout
