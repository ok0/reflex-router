"""PAC11: the core wheel installs into an isolated venv and passes the inner check."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_pac11_isolated_env() -> None:
    if shutil.which("uv") is None:
        pytest.skip("uv not on PATH")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "pac11_check.py")],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PAC11 OK" in result.stdout
