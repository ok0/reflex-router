import dataclasses
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.feather
import pytest
from rr_discovery import cli, controls, pipeline, robustness, run, sanity
from rr_discovery.config import (
    RobustnessConfig,
    load_config,
    require_discover,
    require_model_input,
)
from rr_discovery.data import paths_from_config
from rr_discovery.model_input import build
from rr_discovery.robustness import (
    RobustnessError,
    apply_reductions,
    grid,
    load_grid,
    make_job,
)

REPO = Path(__file__).resolve().parents[2]
M2_TEXT = "## Verdict\n\n**PASS**\n\n- sim_env: py314\n"

FIXTURE_GRID = """
[robustness]
schema = 1
seed_origin = 786000
seed_stride = 100
time_cap_s = 10800
budget_probe_conditions = 3
min_reduced_trials = 15
reduced_control_draws = 1
chance_draws = 10
chance_seed = 791000
shuffle_rounds = 2
left_label = "left"
right_label = "right"

[robustness.families]
rate_hz = [50.0]
w_syn_mult = [0.5]
f_poi_mult = [2.0]
subsets = ["lc4", "both"]
sides = ["left", "bilateral"]
seed_replicates = 1
interaction_groups = ["lc4"]
interaction_rate_hz = [50.0]
random_set_draws = 1
shuffle_draws = 1
"""


def test_committed_grid_counts() -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    dc = require_discover(cfg)
    spec = load_grid(REPO / "discovery/robustness.toml")
    conds = grid(spec, dc)
    assert len(conds) == 40
    assert sum(1 for c in conds if not c.control) == 30
    assert sum(1 for c in conds if c.control) == 10
    assert Counter(c.family for c in conds) == {
        "rate": 3,
        "w_syn": 4,
        "f_poi": 4,
        "subset_side": 8,
        "seed": 5,
        "interaction": 6,
        "random_set": 5,
        "shuffle": 5,
    }
    cids = [c.cid for c in conds]
    assert len(set(cids)) == len(cids)
    assert "stim-both-bilateral" not in cids
    ranges = [(c.seed_base, c.seed_base + c.n_trials) for c in conds]
    base_lo, base_hi = dc.seed_base, dc.seed_base + dc.n_trials
    for lo, hi in ranges:
        assert not (lo < base_hi and base_lo < hi)
    for i, (lo_a, hi_a) in enumerate(ranges):
        for lo_b, hi_b in ranges[i + 1 :]:
            assert not (lo_a < hi_b and lo_b < hi_a)


def test_jobs_independent_of_worker_count() -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    dc = require_discover(cfg)
    cond = grid(load_grid(REPO / "discovery/robustness.toml"), dc)[0]
    stim = np.array([102, 101], dtype=np.int64)
    one = make_job(
        cond, stim_ids=stim, completeness=Path("c.csv"), connectivity=Path("p.parquet"), n_proc=1
    )
    eight = make_job(
        cond, stim_ids=stim, completeness=Path("c.csv"), connectivity=Path("p.parquet"), n_proc=8
    )
    assert one["n_proc"] == 1
    assert eight["n_proc"] == 8
    assert {k: v for k, v in one.items() if k != "n_proc"} == {
        k: v for k, v in eight.items() if k != "n_proc"
    }
    assert one["stim_ids"] == [101, 102]
    assert cond.seeds() == [cond.seed_base + t for t in range(cond.n_trials)]


def test_reduction_order() -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    dc = require_discover(cfg)
    conds = grid(load_grid(REPO / "discovery/robustness.toml"), dc)
    kw: dict[str, Any] = {
        "done": (),
        "elapsed_s": 0.0,
        "cap_s": 10800.0,
        "base_trials": 30,
        "min_trials": 15,
        "control_draws": 3,
    }
    small = apply_reductions(conds, sec_per_condition=100.0, **kw)
    assert small.steps == ()
    assert len(small.conditions) == 40
    assert small.within_cap

    one = apply_reductions(conds, sec_per_condition=300.0, **kw)
    assert one.steps == (("drop_interaction", 0),)
    assert len(one.conditions) == 34

    mid = apply_reductions(conds, sec_per_condition=400.0, **kw)
    assert mid.steps == (("drop_interaction", 0), ("controls_to", 3), ("trials_to", 27))
    assert len(mid.conditions) == 30
    assert all(c.reduced and c.n_trials == 27 for c in mid.conditions)
    assert mid.within_cap

    large = apply_reductions(conds, sec_per_condition=1000.0, **kw)
    assert large.steps[-1] == ("trials_to", 15)
    assert not large.within_cap

    done = [c.cid for c in conds[:3]]
    partial = apply_reductions(conds, sec_per_condition=400.0, **{**kw, "done": done})
    kept = [c for c in partial.conditions if c.cid in done]
    assert len(kept) == 3
    assert all(c.n_trials == 30 and not c.reduced for c in kept)


def test_load_grid_rejects_bad_values(tmp_path: Path) -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    dc = require_discover(cfg)
    text = (REPO / "discovery/robustness.toml").read_text(encoding="utf-8")

    short = tmp_path / "short.toml"
    assert "seed_stride = 100" in text
    short.write_text(text.replace("seed_stride = 100", "seed_stride = 10"), encoding="utf-8")
    with pytest.raises(RobustnessError):
        grid(load_grid(short), dc)

    empty_reason = tmp_path / "reason.toml"
    empty_reason.write_text(
        text + '\n[[robustness.deviations]]\nfrom_sha256 = "' + "a" * 64 + '"\nreason = ""\n',
        encoding="utf-8",
    )
    with pytest.raises(RobustnessError):
        load_grid(empty_reason)

    bad_side = tmp_path / "side.toml"
    assert 'sides = ["left", "right", "bilateral"]' in text
    bad_side.write_text(
        text.replace('sides = ["left", "right", "bilateral"]', 'sides = ["up"]'),
        encoding="utf-8",
    )
    with pytest.raises(RobustnessError):
        load_grid(bad_side)


def _ann() -> pd.DataFrame:
    rows: list[tuple[int, str, str, str]] = [
        (101, "LC4", "optic", "left"),
        (102, "LC4", "optic", "right"),
        (201, "LPLC2", "optic", "left"),
        (202, "LPLC2", "optic", "right"),
        (301, "DNp01", "descending", "left"),
        (401, "DNp02", "descending", "left"),
    ]
    for i in range(20):
        rows.append((501 + i, "T4", "optic", "left" if i % 2 == 0 else "right"))
    return pd.DataFrame(rows, columns=["root_id", "cell_type", "super_class", "side"])


def _write_raw(cfg: Any, ann_path: Path) -> None:
    paths = paths_from_config(cfg)
    paths.annotations.parent.mkdir(parents=True, exist_ok=True)
    _ann().to_csv(ann_path, sep="\t", index=False)
    ids = [101, 102, 201, 202, 301, 401, *range(501, 521)]
    np.save(paths.root_ids, np.array(ids, dtype=np.int64))
    nt = {
        "gaba_avg": 0.1,
        "ach_avg": 0.8,
        "glut_avg": 0.1,
        "oct_avg": 0.0,
        "ser_avg": 0.0,
        "da_avg": 0.0,
    }
    edges: list[tuple[int, int, int]] = [(101, 301, 50), (201, 401, 20), (301, 401, 7)]
    edges += [(501 + i, 501 + (i + 1) % 20, 3) for i in range(20)]
    edges += [(501 + i, 510 + i, 4) for i in range(10)]
    rows = [{"pre_pt_root_id": p, "post_pt_root_id": q, "syn_count": s, **nt} for p, q, s in edges]
    pyarrow.feather.write_feather(pd.DataFrame(rows), paths.connections)


def _fake(
    fail_cid: str | None = None,
) -> Callable[[Path, Path, Path, Path], dict[str, Any]]:
    def fake(python: Path, job: Path, spikes: Path, out: Path) -> dict[str, Any]:
        spec_job: dict[str, Any] = json.loads(job.read_text(encoding="utf-8"))
        if spec_job["label"] == fail_cid:
            raise run.RunError("fake failure")
        n_trials = int(spec_job["n_trials"])
        seeds = [int(spec_job["seed_base"]) + t for t in range(n_trials)]
        rows: list[tuple[int, int, int]] = []
        for t in range(n_trials):
            per: dict[int, int] = {int(r): 10 for r in spec_job["stim_ids"]}
            per[301] = 5
            per[401] = 3
            if float(spec_job.get("w_syn_mult", 1.0)) >= 1.0:
                per[505] = 2
            rows += [(t, rid, per[rid]) for rid in sorted(per)]
        data = b"trial\troot_id\tn_spikes\n" + "".join(
            f"{t}\t{r}\t{n}\n" for t, r, n in rows
        ).encode("ascii")
        spikes.write_bytes(data)
        result: dict[str, Any] = {
            "schema": 1,
            "label": spec_job["label"],
            "job": spec_job,
            "env": {"python": "fake"},
            "params": {"r_poi": "150. Hz"},
            "host": {"cpu": "fake"},
            "t_run_s": 1.0,
            "seeds": seeds,
            "spikes": {
                "file": spikes.name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "n_rows": len(rows),
            },
            "trial_wall_s": [0.01] * n_trials,
            "total_wall_s": 0.1,
            "peak_rss": {"parent_bytes": 1},
        }
        out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return result

    return fake


def test_fixture_suite_leaves_m5_artifacts_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_cfg = load_config(REPO / "discovery/discovery.toml", base_dir=tmp_path)
    dc = dataclasses.replace(require_discover(base_cfg), expected_lc4=2, expected_lplc2=2)
    grid_path = tmp_path / "robustness.toml"
    grid_path.write_text(FIXTURE_GRID, encoding="utf-8")
    rc = RobustnessConfig(
        grid=grid_path,
        work_dir=tmp_path / "robust_work",
        report=tmp_path / "reports" / "robustness.md",
        results=tmp_path / "reports" / "robustness_results.json",
    )
    cfg = dataclasses.replace(base_cfg, discover=dc, robustness=rc)
    paths = paths_from_config(cfg)
    _write_raw(cfg, paths.annotations)
    build(paths.connections, require_model_input(cfg).out_dir, version=cfg.version)
    dc.m2_report.parent.mkdir(parents=True, exist_ok=True)
    dc.m2_report.write_text(M2_TEXT, encoding="utf-8")
    monkeypatch.setattr(sanity, "check_gf_in_circuit", lambda gf, members: None)

    fake = _fake()
    run.run_stage(cfg, python=Path(sys.executable), n_proc=None, condition_fn=fake)
    pipeline.post_stage(cfg)
    artifact = {
        name: hashlib.sha256((dc.out_dir / name).read_bytes()).hexdigest()
        for name in ("circuit.json", "metadata.json")
    }

    robustness.prepare_stage(cfg)
    summary = robustness.run_stage(cfg, python=Path(sys.executable), n_proc=None, condition_fn=fake)
    assert summary.n_run == 10
    assert robustness.extract_stage(cfg) == 10
    report_path, results_path = robustness.report_stage(cfg)
    assert report_path.is_file()
    assert results_path.is_file()
    first_report = report_path.read_bytes()
    first_results = results_path.read_bytes()
    robustness.report_stage(cfg)
    assert report_path.read_bytes() == first_report
    assert results_path.read_bytes() == first_results

    conditions = json.loads(results_path.read_text(encoding="utf-8"))["conditions"]
    n_conditions = len(conditions)
    rerun = robustness.run_stage(cfg, python=Path(sys.executable), n_proc=None, condition_fn=fake)
    assert rerun.n_run == 0
    assert rerun.n_skipped == n_conditions

    target = "seed-1"
    target_dir = robustness.robust_paths(rc).cond_dir(target)
    (target_dir / "run.json").unlink()
    (target_dir / "spikes.tsv").unlink()
    flaky = _fake(fail_cid=target)
    failed_run = robustness.run_stage(
        cfg, python=Path(sys.executable), n_proc=None, condition_fn=flaky
    )
    assert failed_run.n_failed == 1
    assert robustness.extract_stage(cfg) == n_conditions - 1
    robustness.report_stage(cfg)
    results = json.loads(results_path.read_text(encoding="utf-8"))
    by_cid = {c["cid"]: c for c in results["conditions"]}
    assert by_cid[target]["status"] == "failed"
    assert by_cid[target]["reason"] == "fake failure"
    others = [c for cid, c in by_cid.items() if cid != target and not c["control"]]
    assert all(c["status"] == "completed" for c in others)
    assert "fake failure" in report_path.read_text(encoding="utf-8")

    assert {
        name: hashlib.sha256((dc.out_dir / name).read_bytes()).hexdigest()
        for name in ("circuit.json", "metadata.json")
    } == artifact


def test_random_set_pool_restricted_to_model_input(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    dc = require_discover(cfg)
    spec = load_grid(REPO / "discovery/robustness.toml")
    cond = next(c for c in grid(spec, dc) if c.family == "random_set")
    ann = _ann()
    valid = np.array([101, 102, 201, 202, 301, 401, *range(501, 521), 9999], dtype=np.int64)
    model_ids = valid[valid != 9999]
    seen: dict[str, np.ndarray] = {}

    def fake_random_set(ann_arg: Any, pool: np.ndarray, **kwargs: Any) -> np.ndarray:
        seen["pool"] = np.asarray(pool)
        return np.array([501, 502], dtype=np.int64)

    monkeypatch.setattr(controls, "random_set", fake_random_set)
    empty = np.array([], dtype=np.int64)
    sides: Any = SimpleNamespace(
        lc4={"left": np.array([101]), "right": np.array([102]), "unlabeled": empty},
        lplc2={"left": np.array([201]), "right": np.array([202]), "unlabeled": empty},
    )
    stim: Any = SimpleNamespace(all=np.array([101, 102, 201, 202], dtype=np.int64))
    ids = robustness._stim_for(
        cond,
        ann=ann,
        valid=valid,
        sides=sides,
        stim=stim,
        dc=dc,
        spec=spec,
        model_ids=model_ids,
    )
    assert 9999 in valid
    assert 9999 not in seen["pool"]
    assert np.isin(seen["pool"], model_ids).all()
    assert np.isin(ids, model_ids).all()


def test_cli_robustness_help() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["robustness", "--help"])
    assert exc.value.code == 0
