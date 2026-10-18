"""Pytest setup for the S1 spike: makes the sibling s1_* modules importable."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
