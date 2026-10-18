"""Inner PAC11 check, run inside the isolated venv with -I (repo src/ is not on the path)."""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import pkgutil
import sys
from collections.abc import Callable
from pathlib import Path

import reflex_router

VENDOR = (
    "anthropic",
    "openai",
    "google",
    "cohere",
    "mistralai",
    "litellm",
    "boto3",
    "groq",
    "together",
)


def step_import() -> None:
    if "site-packages" not in Path(reflex_router.__file__).parts:
        raise AssertionError(f"reflex_router loaded from {reflex_router.__file__}")


def step_distributions() -> None:
    names = {
        str(d.metadata["Name"]).lower().replace("_", "-").replace(".", "-")
        for d in importlib.metadata.distributions()
    }
    if names != {"reflex-router", "numpy"}:
        raise AssertionError(f"installed distributions are {sorted(names)}")


def step_submodules() -> None:
    for info in pkgutil.walk_packages(reflex_router.__path__, "reflex_router."):
        importlib.import_module(info.name)


def step_vendor_absent() -> None:
    for name in VENDOR:
        if importlib.util.find_spec(name) is not None:
            raise AssertionError(f"vendor package {name} is importable")
        for key in sys.modules:
            if key == name or key.startswith(name + "."):
                raise AssertionError(f"vendor module {key} is loaded")


STEPS: list[tuple[str, Callable[[], None]]] = [
    ("import reflex_router", step_import),
    ("distribution set", step_distributions),
    ("import submodules", step_submodules),
    ("vendor SDKs absent", step_vendor_absent),
]


def main() -> int:
    for name, fn in STEPS:
        try:
            fn()
        except Exception as exc:
            print(f"FAIL: {name}: {type(exc).__name__}: {exc}")
            return 1
        print(f"ok: {name}")
    print("PAC11 OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
