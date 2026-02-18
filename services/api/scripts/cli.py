"""DEPRECATED: This file has been moved to cli/workout_cli.py

This wrapper provides backward compatibility. Please update your scripts to use:
    python cli/workout_cli.py

instead of:
    python scripts/cli.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("WARNING: scripts/cli.py is deprecated. Use: cli/workout_cli.py", file=sys.stderr)

from cli.workout_cli import app

if __name__ == "__main__":
    app()
