#!/usr/bin/env python3
"""Run the project quality checks inside the virtual environment."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT_DIR / "venv"

if not (VENV_DIR / "bin" / "python").exists():
    sys.stderr.write("Virtual environment not found. Run 'make setup' first.\n")
    sys.exit(1)

COMMANDS = [
    [VENV_DIR / "bin" / "ruff", "check", "src", "tests"],
    [VENV_DIR / "bin" / "black", "--check", "src", "tests"],
    [VENV_DIR / "bin" / "pytest", "--maxfail=1", "--disable-warnings", "-q"],
]

for command in COMMANDS:
    subprocess.run([str(part) for part in command], check=True, cwd=ROOT_DIR)
