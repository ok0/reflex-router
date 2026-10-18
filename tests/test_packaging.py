import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_core_distribution_excludes_circuit_data(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("uv not on PATH")
    subprocess.run(
        [uv, "build", "--package", "reflex-router", "--out-dir", str(tmp_path)],
        cwd=ROOT,
        check=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    sdists = list(tmp_path.glob("*.tar.gz"))
    assert len(wheels) == 1
    assert len(sdists) == 1

    with zipfile.ZipFile(wheels[0]) as zf:
        wheel_names = zf.namelist()
    with tarfile.open(sdists[0], "r:gz") as tf:
        sdist_names = tf.getnames()

    all_names = wheel_names + sdist_names
    assert not any("circuit-data" in n for n in all_names)
    assert "reflex_router/__init__.py" in wheel_names
    assert "reflex_router/py.typed" in wheel_names
    assert not any(n.startswith("rr_discovery") for n in wheel_names)
