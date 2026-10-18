import ast
import json
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from rr_discovery.model_input import CONN_COLS

RUNNER = (
    Path(__file__).resolve().parents[1] / "src" / "rr_discovery" / "shiu" / "robustness_runner.py"
)
CONDITION_RUNNER = RUNNER.with_name("condition_runner.py")
ALLOWED_IMPORTS = {
    "argparse",
    "importlib",
    "json",
    "os",
    "sys",
    "time",
    "pathlib",
    "typing",
    "hashlib",
    "brian2",
    "joblib",
    "pandas",
}


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
    *,
    w_syn_mult: float = 1.0,
    f_poi_mult: float = 1.0,
    schema: int = 2,
) -> Path:
    job: dict[str, object] = {
        "schema": schema,
        "label": "tiny",
        "completeness": str(comp),
        "connectivity": str(con),
        "stim_ids": stim_ids,
        "r_poi_hz": 150.0,
        "n_trials": 3,
        "seed_base": 7,
        "n_proc": n_proc,
    }
    if schema == 2:
        job["w_syn_mult"] = w_syn_mult
        job["f_poi_mult"] = f_poi_mult
    path = tmp_path / name
    path.write_text(json.dumps(job))
    return path


def _run(script: Path, job: Path, spikes: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(script),
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


def test_robustness_runner_py310_and_imports() -> None:
    src = RUNNER.read_text(encoding="utf-8")
    ast.parse(src, feature_version=(3, 10))
    modules: set[str] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    assert modules <= ALLOWED_IMPORTS


def test_worker_independent(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    job1 = _write_job(tmp_path, comp, con, [11], 1, "job1.json")
    job2 = _write_job(tmp_path, comp, con, [11], 2, "job2.json")
    spikes1 = tmp_path / "spikes1.tsv"
    spikes2 = tmp_path / "spikes2.tsv"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    proc1 = _run(RUNNER, job1, spikes1, out1)
    proc2 = _run(RUNNER, job2, spikes2, out2)

    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    assert spikes1.read_bytes() == spikes2.read_bytes()
    result = json.loads(out2.read_text())
    assert result["seeds"] == [7, 8, 9]
    assert result["schema"] == 2


def test_unit_mults_match_condition_runner(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    job_v1 = _write_job(tmp_path, comp, con, [11], 1, "job_v1.json", schema=1)
    job_v2 = _write_job(tmp_path, comp, con, [11], 1, "job_v2.json")
    spikes_v1 = tmp_path / "spikes_v1.tsv"
    spikes_v2 = tmp_path / "spikes_v2.tsv"
    out_v1 = tmp_path / "out_v1.json"
    out_v2 = tmp_path / "out_v2.json"

    proc_v1 = _run(CONDITION_RUNNER, job_v1, spikes_v1, out_v1)
    proc_v2 = _run(RUNNER, job_v2, spikes_v2, out_v2)

    assert proc_v1.returncode == 0, proc_v1.stderr
    assert proc_v2.returncode == 0, proc_v2.stderr
    assert spikes_v1.read_bytes() == spikes_v2.read_bytes()
    assert json.loads(out_v1.read_text())["params"] == json.loads(out_v2.read_text())["params"]


def test_w_syn_and_f_poi_applied(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    unit = _write_job(tmp_path, comp, con, [11], 1, "unit.json")
    w_job = _write_job(tmp_path, comp, con, [11], 1, "w.json", w_syn_mult=2.0, f_poi_mult=1.0)
    f_job = _write_job(tmp_path, comp, con, [11], 1, "f.json", w_syn_mult=1.0, f_poi_mult=0.5)
    out_unit = tmp_path / "out_unit.json"
    out_w = tmp_path / "out_w.json"
    out_f = tmp_path / "out_f.json"

    assert _run(RUNNER, unit, tmp_path / "s_unit.tsv", out_unit).returncode == 0
    assert _run(RUNNER, w_job, tmp_path / "s_w.tsv", out_w).returncode == 0
    assert _run(RUNNER, f_job, tmp_path / "s_f.tsv", out_f).returncode == 0

    p_unit = json.loads(out_unit.read_text())["params"]
    p_w = json.loads(out_w.read_text())["params"]
    p_f = json.loads(out_f.read_text())["params"]
    assert p_w["w_syn"] != p_unit["w_syn"]
    assert p_w["r_poi"] == p_unit["r_poi"]
    assert p_f["f_poi"] == "125.0"
    assert p_f["r_poi"] == p_unit["r_poi"]


def test_rejects_schema1_and_unknown_ids(tmp_path: Path) -> None:
    comp, con = _write_inputs(tmp_path)
    schema1 = _write_job(tmp_path, comp, con, [11], 1, "schema1.json", schema=1)
    unknown = _write_job(tmp_path, comp, con, [99], 1, "unknown.json")

    assert _run(RUNNER, schema1, tmp_path / "s1.tsv", tmp_path / "o1.json").returncode == 2
    assert _run(RUNNER, unknown, tmp_path / "s2.tsv", tmp_path / "o2.json").returncode == 3
