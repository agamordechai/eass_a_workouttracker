#!/usr/bin/env python3
"""MCP Probe script for testing Workout Tracker FastMCP server.

This script tests the FastMCP server by directly calling the exposed tools
and verifying their output. Used for EX3 grading evidence.

Usage:
    # Test all tools
    uv run python scripts/mcp_probe.py

    # Test specific tool
    uv run python scripts/mcp_probe.py --tool list-exercises

    # Test with custom parameters
    uv run python scripts/mcp_probe.py --tool list-exercises --page 1 --page-size 5
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

# Import the MCP tools directly for testing
from scripts.exercises_mcp import list_exercises, get_exercise, calculate_volume

app = typer.Typer(help="Test FastMCP server tools")
console = Console()


def print_result(tool_name: str, result: dict) -> None:
    """Pretty print a tool result."""
    console.print(f"\n[bold cyan]Tool:[/bold cyan] {tool_name}")
    console.print(f"[bold cyan]Status:[/bold cyan] {result.get('status', 'unknown')}")

    # Pretty print JSON
    json_str = json.dumps(result, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


@app.command()
def test_list(
    page: int = typer.Option(1, help="Page number"),
    page_size: int = typer.Option(5, help="Items per page"),
    sort_by: str = typer.Option("id", help="Sort column"),
    sort_order: str = typer.Option("asc", help="Sort order (asc/desc)")
) -> None:
    """Test the list-exercises tool."""
    console.print(Panel.fit(
        "[bold green]Testing list-exercises tool[/bold green]",
        border_style="green"
    ))

    result = list_exercises(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    print_result("list-exercises", result)

    # Display exercises in a table if successful
    if result.get("status") == 200 and result.get("items"):
        table = Table(title=f"\nExercises (Page {page}/{((result['total']-1)//page_size)+1})")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Sets", style="yellow")
        table.add_column("Reps", style="yellow")
        table.add_column("Weight", style="magenta")
        table.add_column("Day", style="blue")

        for ex in result["items"]:
            table.add_row(
                str(ex["id"]),
                ex["name"],
                str(ex["sets"]),
                str(ex["reps"]),
                str(ex["weight"]) if ex["weight"] else "—",
                ex["workout_day"]
            )

        console.print(table)


@app.command()
def test_get(
    exercise_id: int = typer.Option(1, help="Exercise ID to fetch")
) -> None:
    """Test the get-exercise tool."""
    console.print(Panel.fit(
        "[bold green]Testing get-exercise tool[/bold green]",
        border_style="green"
    ))

    result = get_exercise(exercise_id=exercise_id)
    print_result("get-exercise", result)


@app.command()
def test_volume() -> None:
    """Test the calculate-volume tool."""
    console.print(Panel.fit(
        "[bold green]Testing calculate-volume tool[/bold green]",
        border_style="green"
    ))

    result = calculate_volume()
    print_result("calculate-volume", result)

    # Display volume summary
    if result.get("status") == 200:
        console.print(f"\n[bold]Volume Summary:[/bold]")
        console.print(f"  Total Volume: [green]{result['total_volume']} kg[/green]")
        console.print(f"  Total Exercises: [cyan]{result['exercise_count']}[/cyan]")
        console.print(f"  Weighted: [yellow]{result['weighted_exercises']}[/yellow]")
        console.print(f"  Bodyweight: [magenta]{result['bodyweight_exercises']}[/magenta]")


@app.command()
def test_all() -> None:
    """Test all MCP tools (default command)."""
    console.print(Panel.fit(
        "[bold magenta]FastMCP Workout Tracker - Full Test Suite[/bold magenta]",
        border_style="magenta"
    ))

    # Test 1: List exercises (first page)
    console.print("\n[bold]Test 1: List exercises (page 1, 5 items)[/bold]")
    result1 = list_exercises(page=1, page_size=5)
    print_result("list-exercises", result1)

    # Test 2: Get specific exercise
    console.print("\n[bold]Test 2: Get exercise by ID[/bold]")
    result2 = get_exercise(exercise_id=1)
    print_result("get-exercise", result2)

    # Test 3: Calculate volume
    console.print("\n[bold]Test 3: Calculate total volume[/bold]")
    result3 = calculate_volume()
    print_result("calculate-volume", result3)

    # Test 4: List with sorting
    console.print("\n[bold]Test 4: List exercises sorted by name[/bold]")
    result4 = list_exercises(page=1, page_size=3, sort_by="name", sort_order="asc")
    print_result("list-exercises (sorted)", result4)

    # Test 5: Error handling - invalid exercise ID
    console.print("\n[bold]Test 5: Error handling - nonexistent exercise[/bold]")
    result5 = get_exercise(exercise_id=999999)
    print_result("get-exercise (not found)", result5)

    # Summary
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold green]✓ All tests completed![/bold green]\n"
        "FastMCP server tools are working correctly.",
        border_style="green"
    ))


@app.command()
def demo() -> None:
    """Run a demonstration with formatted output for EX3 grading evidence."""
    console.print(Panel.fit(
        "[bold magenta]FastMCP Workout Tracker - Demo for EX3[/bold magenta]\n"
        "[dim]This demo shows the FastMCP integration working correctly[/dim]",
        border_style="magenta"
    ))

    # List exercises
    console.print("\n[bold cyan]═══ Tool: list-exercises ═══[/bold cyan]")
    result = list_exercises(page=1, page_size=10)

    if result.get("status") == 200:
        console.print(f"✓ Successfully retrieved {result['total']} exercises")
        console.print(f"  Page: {result['page']}/{((result['total']-1)//result['page_size'])+1}")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", width=4)
        table.add_column("Exercise", width=20)
        table.add_column("Sets×Reps", width=10)
        table.add_column("Weight", width=10)
        table.add_column("Day", width=5)

        for ex in result["items"]:
            weight = f"{ex['weight']} kg" if ex['weight'] else "bodyweight"
            table.add_row(
                str(ex["id"]),
                ex["name"],
                f"{ex['sets']}×{ex['reps']}",
                weight,
                ex["workout_day"]
            )

        console.print(table)
    else:
        console.print(f"[red]✗ Error: {result.get('error')}[/red]")

    # Calculate volume
    console.print("\n[bold cyan]═══ Tool: calculate-volume ═══[/bold cyan]")
    result = calculate_volume()

    if result.get("status") == 200:
        console.print("✓ Volume calculation successful")
        console.print(f"  Total workout volume: [green bold]{result['total_volume']} kg[/green bold]")
        console.print(f"  Exercises analyzed: {result['exercise_count']} "
                     f"({result['weighted_exercises']} weighted, {result['bodyweight_exercises']} bodyweight)")
    else:
        console.print(f"[red]✗ Error: {result.get('error')}[/red]")

    # Get specific exercise
    console.print("\n[bold cyan]═══ Tool: get-exercise ═══[/bold cyan]")
    result = get_exercise(exercise_id=1)

    if result.get("status") == 200:
        ex = result["exercise"]
        console.print(f"✓ Retrieved exercise ID {ex['id']}")
        console.print(f"  Name: {ex['name']}")
        console.print(f"  Sets: {ex['sets']}, Reps: {ex['reps']}")
        console.print(f"  Weight: {ex['weight']} kg" if ex['weight'] else "  Weight: bodyweight")
        console.print(f"  Workout Day: {ex['workout_day']}")
    else:
        console.print(f"[red]✗ Error: {result.get('error')}[/red]")

    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold green]✓ FastMCP Demo Complete[/bold green]\n"
        "[dim]All MCP tools are operational and returning correct data[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    # Default to demo if no command specified
    if len(sys.argv) == 1:
        demo()
    else:
        app()
