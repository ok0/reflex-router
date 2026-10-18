import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.feather
import pytest
from rr_discovery.config import (
    DiscoverConfig,
    DiscoveryConfig,
    load_config,
    require_discover,
    require_model_input,
)
from rr_discovery.data import paths_from_config
from rr_discovery.model_input import build
from rr_discovery.run import (
    M2Verdict,
    RunError,
    read_m2_verdict,
    read_spike_counts,
    run_stage,
    stimulated_sets,
)

REPO = Path(__file__).resolve().parents[2]
M2_TEXT = "## Verdict\n\n**PASS**\n\n- sim_env: py314\n"


def _ann() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "root_id": [101, 102, 201, 202, 301],
            "cell_type": ["LC4", "LC4", "LPLC2", "LPLC2", "DNp01"],
            "super_class": ["optic", "optic", "optic", "optic", "descending"],
            "side": ["left", "left", "left", "left", "left"],
        }
    )


def _small_config(tmp_path: Path) -> tuple[DiscoveryConfig, DiscoverConfig]:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=tmp_path)
    dc = dataclasses.replace(require_discover(cfg), expected_lc4=2, expected_lplc2=2)
    return dataclasses.replace(cfg, discover=dc), dc


def test_stimulated_sets_counts(tmp_path: Path) -> None:
    valid = np.array([101, 102, 201, 202, 301], dtype=np.int64)
    _, dc = _small_config(tmp_path)
    sets = stimulated_sets(_ann(), valid, dc)
    assert sets.lc4.tolist() == [101, 102]
    assert sets.lplc2.tolist() == [201, 202]
    assert sets.all.tolist() == [101, 102, 201, 202]
    strict = dataclasses.replace(dc, expected_lc4=3)
    with pytest.raises(RunError, match="LC4 count 2 != expected 3"):
        stimulated_sets(_ann(), valid, strict)


def test_read_m2_verdict(tmp_path: Path) -> None:
    report = tmp_path / "m2.md"
    report.write_text(M2_TEXT, encoding="utf-8")
    assert read_m2_verdict(report) == M2Verdict("PASS", "py314")
    report.write_text("## Verdict\n\n**PASS**\n", encoding="utf-8")
    with pytest.raises(RunError):
        read_m2_verdict(report)


def test_read_spike_counts_sha_checked(tmp_path: Path) -> None:
    path = tmp_path / "spikes.tsv"
    data = b"trial\troot_id\tn_spikes\n0\t101\t3\n1\t101\t2\n"
    path.write_bytes(data)
    good = hashlib.sha256(data).hexdigest()
    frame = read_spike_counts(path, expected_sha256=good)
    assert list(frame.columns) == ["trial", "root_id", "n_spikes"]
    assert frame["n_spikes"].tolist() == [3, 2]
    with pytest.raises(RunError):
        read_spike_counts(path, expected_sha256="0" * 64)


def _write_raw(cfg: DiscoveryConfig, ann_path: Path) -> None:
    paths = paths_from_config(cfg)
    paths.annotations.parent.mkdir(parents=True, exist_ok=True)
    _ann().to_csv(ann_path, sep="\t", index=False)
    np.save(paths.root_ids, np.array([101, 102, 201, 202, 301, 401], dtype=np.int64))
    nt = {
        "gaba_avg": 0.1,
        "ach_avg": 0.8,
        "glut_avg": 0.1,
        "oct_avg": 0.0,
        "ser_avg": 0.0,
        "da_avg": 0.0,
    }
    rows = [
        {"pre_pt_root_id": 101, "post_pt_root_id": 301, "syn_count": 50, **nt},
        {"pre_pt_root_id": 201, "post_pt_root_id": 401, "syn_count": 20, **nt},
        {"pre_pt_root_id": 301, "post_pt_root_id": 401, "syn_count": 7, **nt},
    ]
    pyarrow.feather.write_feather(pd.DataFrame(rows), paths.connections)


def test_run_stage_with_fake_runner(tmp_path: Path) -> None:
    cfg, dc = _small_config(tmp_path)
    paths = paths_from_config(cfg)
    _write_raw(cfg, paths.annotations)
    build(paths.connections, require_model_input(cfg).out_dir, version=cfg.version)
    dc.m2_report.parent.mkdir(parents=True, exist_ok=True)
    dc.m2_report.write_text(M2_TEXT, encoding="utf-8")

    def fake(python: Path, job: Path, spikes: Path, out: Path) -> dict[str, Any]:
        spikes.write_bytes(b"trial\troot_id\tn_spikes\n0\t101\t3\n0\t201\t2\n")
        result: dict[str, Any] = {
            "schema": 1,
            "host": {"cpu": "fake"},
            "total_wall_s": 1.5,
            "trial_wall_s": [0.5, 0.6],
            "peak_rss": {"parent_bytes": 1},
            "seeds": [1, 2],
        }
        out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return result

    out = run_stage(cfg, python=Path(sys.executable), n_proc=None, condition_fn=fake)
    assert out == dc.work_dir / "run_v783.json"

    job = json.loads((dc.work_dir / "condition_v783.job.json").read_text(encoding="utf-8"))
    assert job["stim_ids"] == [101, 102, 201, 202]
    assert job["r_poi_hz"] == 150.0
    assert job["n_trials"] == 30
    assert job["n_proc"] == dc.n_proc

    run_log = json.loads((dc.work_dir / "run_log.json").read_text(encoding="utf-8"))
    assert "host" in run_log["run"]
