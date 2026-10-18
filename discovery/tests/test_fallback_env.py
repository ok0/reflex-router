import json
import os
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from rr_discovery import regress
from rr_discovery.model_input import CONN_COLS

pytestmark = pytest.mark.fallback_env

_FALLBACK = os.environ.get("RR_FALLBACK_PYTHON")
if _FALLBACK is None:
    pytest.skip(
        "set RR_FALLBACK_PYTHON to the fallback env python to run",
        allow_module_level=True,
    )

FALLBACK_PYTHON = Path(_FALLBACK)
RUNNER = Path(__file__).resolve().parents[1] / "src" / "rr_discovery" / "shiu" / "runner.py"


def test_fallback_versions() -> None:
    info = regress.runner_check(FALLBACK_PYTHON)
    assert str(info["python"]).startswith("3.10.")
    assert info["brian2"] == "2.5.1"
    assert info["cython_available"] is True


def test_fallback_tiny_sweep(tmp_path: Path) -> None:
    comp = tmp_path / "comp.csv"
    comp.write_text(",Completed\n11,True\n22,True\n33,True\n", encoding="utf-8")
    con = tmp_path / "con.parquet"
    rows = [(11, 22, 0, 1, 50, 1, 50), (22, 33, 1, 2, 50, 1, 50)]
    table = pa.table(
        {c: pa.array([r[i] for r in rows], pa.int64()) for i, c in enumerate(CONN_COLS)}
    )
    pq.write_table(table, con)
    job = tmp_path / "job.json"
    job.write_text(
        json.dumps(
            {
                "schema": 1,
                "label": "fallback-tiny",
                "completeness": str(comp),
                "connectivity": str(con),
                "stim_ids": [11],
                "readout_id": 22,
                "frequencies_hz": [10.0, 100.0],
                "n_trials": 2,
                "seed_base": 5,
                "n_proc": 1,
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    proc = subprocess.run(
        [str(FALLBACK_PYTHON), str(RUNNER), "sweep", "--job", str(job), "--out", str(out)],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(out.read_text(encoding="utf-8"))
    assert len(result["conditions"]) == 2
