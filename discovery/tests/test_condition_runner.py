import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from rr_discovery.model_input import CONN_COLS

RUNNER = (
    Path(__file__).resolve().parents[1] / "src" / "rr_discovery" / "shiu" / "condition_runner.py"
)


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


def _write_job(
    tmp_path: Path,
    comp: Path,
    con: Path,
    stim_ids: list[int],
    n_proc: int,
    name: str,
) -> Path:
    job = {
        "schema": 1,
        "label": "tiny",
        "completeness": str(comp),
        "connectivity": str(con),
        "stim_ids": stim_ids,
        "r_poi_hz": 150.0,
        "n_trials": 3,
        "seed_base": 7,
        "n_proc": n_proc,
    }
    path = tmp_path / name
    path.write_text(json.dumps(job))
    return path


def _condition(job: Path, spikes: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "condition",
            "--job",
            str(job),
            "--spikes",
            str(spikes),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )


def test_condition_deterministic_and_worker_independent(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    job1 = _write_job(tmp_path, comp, con, [11], 1, "job1.json")
    job2 = _write_job(tmp_path, comp, con, [11], 2, "job2.json")
    spikes1 = tmp_path / "spikes1.tsv"
    spikes2 = tmp_path / "spikes2.tsv"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    proc1 = _condition(job1, spikes1, out1)
    proc2 = _condition(job2, spikes2, out2)

    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    data = spikes1.read_bytes()
    assert data == spikes2.read_bytes()

    lines = data.decode("ascii").splitlines()
    assert lines[0] == "trial\troot_id\tn_spikes"
    rows = [tuple(int(x) for x in line.split("\t")) for line in lines[1:]]
    assert rows == sorted(rows, key=lambda r: (r[0], r[1]))
    assert {r[1] for r in rows} <= {11, 22, 33}
    assert {r[0] for r in rows if r[1] == 11 and r[2] > 0} == {0, 1, 2}

    result = json.loads(out2.read_text())
    assert result["spikes"]["sha256"] == hashlib.sha256(data).hexdigest()
    assert result["seeds"] == [7, 8, 9]
    assert "150" in result["params"]["r_poi"]


def test_condition_rejects_unknown_ids(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    job = _write_job(tmp_path, comp, con, [99], 1, "bad_job.json")

    proc = _condition(job, tmp_path / "bad_spikes.tsv", tmp_path / "bad_out.json")

    assert proc.returncode == 3
