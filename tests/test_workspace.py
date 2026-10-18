import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str) -> dict:
    with (ROOT / rel).open("rb") as f:
        return tomllib.load(f)


def test_workspace_members_exact() -> None:
    data = _load("pyproject.toml")
    assert data["tool"]["uv"]["workspace"]["members"] == ["discovery"]


@pytest.mark.parametrize(
    ("rel", "name"),
    [
        ("pyproject.toml", "reflex-router"),
        ("discovery/pyproject.toml", "reflex-router-discovery"),
    ],
)
def test_package_names_and_python(rel: str, name: str) -> None:
    project = _load(rel)["project"]
    assert project["name"] == name
    assert project["requires-python"] == ">=3.14"


def test_core_runtime_deps_numpy_only() -> None:
    deps = _load("pyproject.toml")["project"]["dependencies"]
    assert len(deps) == 1
    req = deps[0]
    cut = len(req)
    for ch in "<>=!~[; ":
        idx = req.find(ch)
        if idx != -1:
            cut = min(cut, idx)
    assert req[:cut] == "numpy"


def test_core_imports() -> None:
    import reflex_router

    assert reflex_router.__version__ == "0.0.1"


def test_running_on_314() -> None:
    assert sys.version_info[:2] >= (3, 14)
