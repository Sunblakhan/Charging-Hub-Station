"""
Test package bootstrap.

Ensures the project root is on sys.path so that imports like
`from src.domain.value_objects import ...` work in all test files.
"""

import sys
from pathlib import Path

# Path to project root (folder that contains `src` and `tests`)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))