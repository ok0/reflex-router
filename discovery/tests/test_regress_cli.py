import json
import math
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.feather
import pytest
from rr_discovery.cli import main
from rr_discovery.config import DiscoveryConfig, load_config, require_regress
from rr_discovery.data import ManifestEntry, sha256_file, write_manifest
from rr_discovery.model_input import build
from rr_discovery.regress import execute

SweepStub = Callable[[Path, Path, Path], dict[str, Any]]

PASS: dict[float, list[int]] = {
    10.0: [4, 6],
    20.0: [19, 21],
    50.0: [49, 51],
    100.0: [79, 81],
    200.0: [99, 101],
}
RATIO_FAIL: dict[float, list[int]] = {**PASS, 100.0: [59, 61]}
EQUIV_FAIL: dict[float, list[int]] = {**PASS, 200.0: [149, 151]}
CHECK_310: dict[str, Any] = {
    "python": "3.10.14",
    "brian2": "2.5.1",
    "numpy": "1.24.4",
    "pandas": "1.5.3",
    "pyarrow": "14.0.2",
    "joblib": "1.3.2",
    "cython_available": True,
}


@dataclass(frozen=True)
class Env:
    root: Path
    config: Path
    cfg: DiscoveryConfig


def _write_feather(path: Path) -> None:
    nan = float("nan")
    spec = [
        (101, 102, "A", 3, 0.1, 0.8, 0.1),
        (101, 102, "B", 2, 0.1, 0.8, 0.1),
        (101, 103, "A", 5, 0.2, 0.7, 0.1),
        (102, 103, "A", 4, 0.6, 0.2, 0.2),
        (102, 104, "B", 1, 0.1, 0.8, 0.1),
        (103, 104, "A", 6, nan, nan, nan),
        (103, 105, "A", 1, nan, nan, nan),
        (104, 101, "A", 2, 0.25, 0.5, 0.25),
    ]
    records: list[dict[str, Any]] = []
    for pre, post, neuropil, syn, gaba, ach, glut in spec:
        missing = math.isnan(gaba)
        records.append(
            {
                "pre_pt_root_id": pre,
                "post_pt_root_id": post,
                "neuropil": neuropil,
                "syn_count": syn,
                "gaba_avg": gaba,
                "ach_avg": ach,
                "glut_avg": glut,
                "oct_avg": nan if missing else 0.0,
                "ser_avg": nan if missing else 0.0,
                "da_avg": nan if missing else 0.0,
            }
        )
    df = pd.DataFrame.from_records(records)
    df = df.astype(
        {
            "pre_pt_root_id": "int64",
            "post_pt_root_id": "int64",
            "syn_count": "int64",
            "neuropil": "str",
        }
    )
    pyarrow.feather.write_feather(pa.Table.from_pandas(df, preserve_index=False), path)


def _config_text(root: Path) -> str:
    r = root.as_posix()
    return f"""\
[data]
version = "v783"
data_dir = "{r}/raw"
reports_dir = "{r}/reports"
manifest = "{r}/data_manifest.toml"

[zenodo]
record = "10676866"
doi = "10.5281/zenodo.10676866"
files = ["proofread_connections_783.feather", "proofread_root_ids_783.npy"]

[annotations]
repo = "flyconnectome/flywire_annotations"
tag = "v3.2.0"
path = "supplemental_files/Supplemental_file1_neuron_annotations.tsv"

[shiu]
repo = "philshiu/Drosophila_brain_model"
commit = "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"
raw_dir = "{r}/shiu_raw"
manifest = "{r}/shiu_manifest.toml"
vendor_files = ["LICENSE", "model.py", "utils.py"]
reference_files = ["Completeness_783.csv", "Connectivity_783.parquet"]
v630_files = ["2023_03_23_completeness_630_final.csv", "2023_03_23_connectivity_630_final.parquet"]

[model_input]
out_dir = "{r}/mi"

[regress]
frequencies_hz = [10, 20, 50, 100, 200]
n_trials = 2
seed_base = 1
n_proc = 1
work_dir = "{r}/work"
golden = "{r}/reports/golden.json"
report = "{r}/reports/report.md"
stim_source = "test"
sugar_grn_ids = [101]
mn9_id = 102

[regress.v630]
sugar_grn_ids = [101]
mn9_id = 102
"""


@pytest.fixture
def env(tmp_path: Path) -> Env:
    raw = tmp_path / "raw"
    raw.mkdir()
    feather = raw / "proofread_connections_783.feather"
    _write_feather(feather)
    build(feather, tmp_path / "mi", version="v783")
    config = tmp_path / "discovery.toml"
    config.write_text(_config_text(tmp_path), encoding="utf-8")
    return Env(root=tmp_path, config=config, cfg=load_config(config, base_dir=tmp_path))


def _fake_sweep(by_label: dict[str, dict[float, list[int]]]) -> SweepStub:
    def sweep(python: Path, job: Path, out: Path) -> dict[str, Any]:
        spec = json.loads(job.read_text(encoding="utf-8"))
        spikes_by_freq = next(v for k, v in by_label.items() if spec["label"].startswith(k))
        conditions: list[dict[str, Any]] = []
        for k, freq in enumerate(spec["frequencies_hz"]):
            counts = spikes_by_freq[freq]
            conditions.append(
                {
                    "frequency_hz": freq,
                    "seeds": [spec["seed_base"] + 1000 * k + t for t in range(spec["n_trials"])],
                    "readout_spikes": counts,
                    "trial_wall_s": [0.1 for _ in counts],
                    "wall_s": 1.5,
                }
            )
        return {
            "schema": 1,
            "label": spec["label"],
            "job": spec,
            "env": CHECK_310,
            "host": {
                "platform": "test",
                "machine": "arm64",
                "cpu": "test",
                "n_cpu": 1,
                "ram_bytes": 1,
            },
            "t_run_s": 1.0,
            "conditions": conditions,
            "total_wall_s": 3.0,
            "peak_rss": {
                "parent_bytes": 100 * 2**20,
                "max_worker_bytes": 200 * 2**20,
                "n_workers": 1,
                "sum_worker_peak_bytes": 200 * 2**20,
            },
        }

    return sweep


def _check(_: Path) -> dict[str, Any]:
    return dict(CHECK_310)


def _fake_python(tmp_path: Path) -> Path:
    py = tmp_path / "fallback-python"
    py.write_text("#!/bin/sh\n", encoding="utf-8")
    py.chmod(0o755)
    return py


def _capture(env: Env, sweep: SweepStub, python: Path | None = None, force: bool = False) -> int:
    return execute(
        env.cfg,
        mode="capture",
        python=python,
        force=force,
        sweep_fn=sweep,
        check_fn=_check,
        compiler_ok=lambda: True,
    )


def _regress(env: Env, sweep: SweepStub, compiler_ok: Callable[[], bool] = lambda: True) -> int:
    return execute(
        env.cfg,
        mode="regress",
        sweep_fn=sweep,
        check_fn=_check,
        compiler_ok=compiler_ok,
    )


def test_capture_then_pass(env: Env, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    py = _fake_python(tmp_path)
    sweep = _fake_sweep({"golden": PASS, "regress-v783": PASS})
    assert _capture(env, sweep, python=py) == 0
    doc = json.loads(require_regress(env.cfg).golden.read_text(encoding="utf-8"))
    for key in (
        "input_hashes",
        "vendored_code_hash",
        "env",
        "host",
        "frequencies_hz",
        "n_trials",
        "seed_base",
        "seeds",
        "stim",
        "rows",
        "timing",
        "peak_rss",
        "data_version",
        "seed_scheme",
    ):
        assert key in doc

    capsys.readouterr()
    assert _regress(env, sweep) == 0
    out = capsys.readouterr().out
    assert "monotonic: PASS" in out
    assert "ratio: PASS" in out
    assert "equivalence: PASS" in out
    assert "verdict: PASS" in out
    report = require_regress(env.cfg).report.read_text(encoding="utf-8")
    assert "PASS" in report
    assert "| 100" in report


def test_equivalence_fail_means_fallback(
    env: Env, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _capture(env, _fake_sweep({"golden": PASS}), python=_fake_python(tmp_path)) == 0
    capsys.readouterr()
    assert _regress(env, _fake_sweep({"regress-v783": EQUIV_FAIL})) == 1
    out = capsys.readouterr().out
    assert "equivalence: FAIL" in out
    assert "simulation env for M5/M6: fallback" in out


def test_ratio_fail_v630_unavailable(
    env: Env, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _capture(env, _fake_sweep({"golden": RATIO_FAIL}), python=_fake_python(tmp_path)) == 0
    capsys.readouterr()
    assert _regress(env, _fake_sweep({"regress-v783": RATIO_FAIL})) == 1
    out = capsys.readouterr().out
    assert "v630 inputs: unavailable" in out
    assert "verdict: FAIL" in out


def test_ratio_fail_v630_pass(env: Env, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _capture(env, _fake_sweep({"golden": RATIO_FAIL}), python=_fake_python(tmp_path)) == 0
    shiu_raw = env.root / "shiu_raw"
    shiu_raw.mkdir()
    entries: dict[str, ManifestEntry] = {}
    for name in (
        "2023_03_23_completeness_630_final.csv",
        "2023_03_23_connectivity_630_final.parquet",
    ):
        path = shiu_raw / name
        path.write_bytes(f"dummy {name}\n".encode())
        entries[name] = ManifestEntry(
            sha256=sha256_file(path), size=path.stat().st_size, source="test"
        )
    write_manifest(env.root / "shiu_manifest.toml", entries)
    capsys.readouterr()
    sweep = _fake_sweep({"regress-v783": RATIO_FAIL, "regress-v630": PASS})
    assert _regress(env, sweep) == 0
    out = capsys.readouterr().out
    assert "ratio (v630): PASS" in out


def test_missing_model_input(env: Env, capsys: pytest.CaptureFixture[str]) -> None:
    shutil.rmtree(env.root / "mi")
    assert _regress(env, _fake_sweep({"regress-v783": PASS})) == 1
    assert "rr-discover model-input" in capsys.readouterr().err


def test_missing_golden(env: Env, capsys: pytest.CaptureFixture[str]) -> None:
    assert _regress(env, _fake_sweep({"regress-v783": PASS})) == 1
    assert "--capture-golden" in capsys.readouterr().err


def test_capture_needs_python(env: Env, capsys: pytest.CaptureFixture[str]) -> None:
    assert _capture(env, _fake_sweep({"golden": PASS}), python=None) == 1
    assert "--python" in capsys.readouterr().err


def test_capture_wrong_env(env: Env, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    py = _fake_python(tmp_path)
    rc = execute(
        env.cfg,
        mode="capture",
        python=py,
        sweep_fn=_fake_sweep({"golden": PASS}),
        check_fn=lambda _: {**CHECK_310, "python": "3.14.8"},
        compiler_ok=lambda: True,
    )
    assert rc == 1
    assert "3.14.8" in capsys.readouterr().err


def test_golden_exists_needs_force(
    env: Env, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    py = _fake_python(tmp_path)
    sweep = _fake_sweep({"golden": PASS})
    assert _capture(env, sweep, python=py) == 0
    assert _capture(env, sweep, python=py) == 1
    assert "--force" in capsys.readouterr().err
    assert _capture(env, sweep, python=py, force=True) == 0


def test_no_compiler(env: Env, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _capture(env, _fake_sweep({"golden": PASS}), python=_fake_python(tmp_path)) == 0
    capsys.readouterr()
    assert _regress(env, _fake_sweep({"regress-v783": PASS}), compiler_ok=lambda: False) == 1
    assert "compiler" in capsys.readouterr().err


def test_cli_regress_missing_section(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "discovery.toml"
    p.write_text(
        """\
[data]
version = "v783"
data_dir = "circuit-data/v783/raw"
reports_dir = "circuit-data/v783/reports"
manifest = "discovery/data_manifest.toml"

[zenodo]
record = "10676866"
doi = "10.5281/zenodo.10676866"
files = ["proofread_connections_783.feather", "proofread_root_ids_783.npy"]

[annotations]
repo = "flyconnectome/flywire_annotations"
tag = "v3.2.0"
path = "supplemental_files/Supplemental_file1_neuron_annotations.tsv"
""",
        encoding="utf-8",
    )
    assert main(["regress", "--config", str(p)]) == 2
    assert "missing required section [regress]" in capsys.readouterr().err


def test_cli_model_input_writes_outputs(env: Env, capsys: pytest.CaptureFixture[str]) -> None:
    out_dir = env.root / "o"
    assert main(["model-input", "--config", str(env.config), "--out-dir", str(out_dir)]) == 0
    for name in (
        "completeness_v783.csv",
        "connectivity_v783.parquet",
        "input_totals_v783.parquet",
        "model_input_v783.json",
    ):
        assert (out_dir / name).is_file()
