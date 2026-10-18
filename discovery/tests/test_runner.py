import json
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from rr_discovery.model_input import CONN_COLS

RUNNER = Path(__file__).resolve().parents[1] / "src" / "rr_discovery" / "shiu" / "runner.py"


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    comp = tmp_path / "comp.csv"
    comp.write_text(",Completed\n11,True\n22,True\n33,True\n", encoding="utf-8")
    con = tmp_path / "con.parquet"
    rows = [(11, 22, 0, 1, 50, 1, 50), (22, 33, 1, 2, 50, 1, 50)]
    table = pa.table(
        {c: pa.array([r[i] for r in rows], pa.int64()) for i, c in enumerate(CONN_COLS)}
    )
    pq.write_table(table, con)
    return comp, con


def _write_job(tmp_path: Path, comp: Path, con: Path, readout: int, name: str) -> Path:
    job = {
        "schema": 1,
        "label": "tiny",
        "completeness": str(comp),
        "connectivity": str(con),
        "stim_ids": [11],
        "readout_id": readout,
        "frequencies_hz": [10.0, 100.0],
        "n_trials": 2,
        "seed_base": 5,
        "n_proc": 1,
    }
    path = tmp_path / name
    path.write_text(json.dumps(job))
    return path


def _sweep(job: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), "sweep", "--job", str(job), "--out", str(out)],
        capture_output=True,
        text=True,
        timeout=600,
    )


def test_runner_tiny_network(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    job = _write_job(tmp_path, comp, con, readout=22, name="job.json")
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    proc1 = _sweep(job, out1)
    proc2 = _sweep(job, out2)

    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    r1 = json.loads(out1.read_text())
    r2 = json.loads(out2.read_text())
    assert len(r1["conditions"]) == 2
    assert r1["conditions"][0]["seeds"] == [5, 6]
    assert r1["conditions"][1]["seeds"] == [1005, 1006]
    for cond in r1["conditions"]:
        for n in cond["readout_spikes"]:
            assert isinstance(n, int)
            assert n >= 0
    assert [c["readout_spikes"] for c in r1["conditions"]] == [
        c["readout_spikes"] for c in r2["conditions"]
    ]
    assert r1["env"]["python"].startswith("3.14")


def test_runner_check() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "check"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stderr
    info = json.loads(proc.stdout.strip().splitlines()[-1])
    assert info["cython_available"] is True


def test_runner_rejects_unknown_ids(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    job = _write_job(tmp_path, comp, con, readout=999, name="bad_job.json")
    out = tmp_path / "bad_out.json"

    proc = _sweep(job, out)

    assert proc.returncode == 3
    assert "999" in proc.stderr
