"""Host-side PAC11 driver: build the core wheel, install it offline, run the inner check."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    uv = shutil.which("uv")
    if uv is None:
        print("ERROR: uv not found on PATH", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="rr-pac11-") as tmp_name:
        tmp = Path(tmp_name)
        dist = tmp / "dist"
        try:
            subprocess.run(
                [
                    uv,
                    "build",
                    "--package",
                    "reflex-router",
                    "--wheel",
                    "--offline",
                    "--out-dir",
                    str(dist),
                ],
                cwd=root,
                check=True,
            )
            wheels = sorted(dist.glob("*.whl"))
            if len(wheels) != 1:
                print(f"ERROR: expected exactly one wheel in {dist}, found {len(wheels)}")
                return 1
            wheel = wheels[0]
            venv = tmp / "venv"
            subprocess.run(
                [uv, "venv", "--offline", "--python", "3.14", str(venv)],
                cwd=tmp,
                check=True,
            )
            py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            subprocess.run(
                [uv, "pip", "install", "--offline", "--python", str(py), str(wheel)],
                cwd=tmp,
                check=True,
            )
            env = dict(os.environ)
            env.pop("PYTHONPATH", None)
            env.pop("VIRTUAL_ENV", None)
            rc = subprocess.run(
                [str(py), "-I", str(root / "scripts" / "pac11_inner.py")],
                cwd=tmp,
                env=env,
            ).returncode
        except subprocess.CalledProcessError as exc:
            print(f"ERROR: step failed with exit code {exc.returncode}: {exc.cmd}")
            return 1
    print("PAC11 OK" if rc == 0 else f"PAC11 FAILED (exit {rc})")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
