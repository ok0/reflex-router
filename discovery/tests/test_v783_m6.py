import json
import math

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
from rr_discovery import controls, robustness
from rr_discovery.annotations import ids_by_cell_type, load_annotations, load_root_ids
from rr_discovery.config import (
    DiscoveryConfig,
    require_discover,
    require_model_input,
    require_robustness,
)
from rr_discovery.data import Paths
from rr_discovery.model_input import output_paths
from rr_discovery.run import run_paths, stimulated_sets

pytestmark = pytest.mark.flywire


def test_side_split_v783(v783_paths: tuple[DiscoveryConfig, Paths]) -> None:
    cfg, paths = v783_paths
    dc = require_discover(cfg)
    spec = robustness.load_grid(require_robustness(cfg).grid)
    ann = load_annotations(paths.annotations)
    valid = load_root_ids(paths.root_ids)
    stim = stimulated_sets(ann, valid, dc)
    sides = controls.side_sets(ann, stim, left_label=spec.left_label, right_label=spec.right_label)
    counts = sides.counts()
    print(f"v783 side counts: {counts}")
    assert stim.lc4.size == 104
    assert stim.lplc2.size == 210
    assert sum(counts["lc4"].values()) == 104
    assert sum(counts["lplc2"].values()) == 210


def test_random_draws_v783(v783_paths: tuple[DiscoveryConfig, Paths]) -> None:
    cfg, paths = v783_paths
    dc = require_discover(cfg)
    spec = robustness.load_grid(require_robustness(cfg).grid)
    ann = load_annotations(paths.annotations)
    valid = load_root_ids(paths.root_ids)
    stim = stimulated_sets(ann, valid, dc)
    sides = controls.side_sets(ann, stim, left_label=spec.left_label, right_label=spec.right_label)
    cond = next(c for c in robustness.grid(spec, dc) if c.cid == "random-1")
    gf = ids_by_cell_type(ann, dc.gf_cell_type, valid_ids=valid)
    n_left = int(sides.lc4["left"].size + sides.lplc2["left"].size)
    n_right = int(sides.lc4["right"].size + sides.lplc2["right"].size)
    n_unlabeled = int(sides.lc4["unlabeled"].size + sides.lplc2["unlabeled"].size)
    drawn = controls.random_set(
        ann,
        valid,
        exclude=np.union1d(stim.all, gf),
        n_left=n_left,
        n_right=n_right,
        n_unlabeled=n_unlabeled,
        seed=cond.seed_base,
        left_label=spec.left_label,
        right_label=spec.right_label,
    )
    assert drawn.size == stim.all.size == 314
    labels = controls.side_labels(
        ann, drawn, left_label=spec.left_label, right_label=spec.right_label
    )
    assert int(np.sum(labels == "left")) == n_left
    assert int(np.sum(labels == "right")) == n_right
    assert int(np.sum(labels == controls.UNLABELED)) == n_unlabeled
    assert np.intersect1d(drawn, stim.all).size == 0
    assert np.intersect1d(drawn, gf).size == 0


def test_shuffle_v783(v783_paths: tuple[DiscoveryConfig, Paths]) -> None:
    cfg, _ = v783_paths
    rc = require_robustness(cfg)
    rp = robustness.robust_paths(rc)
    sdir = rp.shuffle_dir(1)
    if not (sdir / "shuffle.json").is_file():
        pytest.skip("shuffle-1 not built; run 'uv run rr-discover robustness --step prepare'")
    mi = output_paths(require_model_input(cfg).out_dir, cfg.version)
    if not (mi.completeness.exists() and mi.connectivity.exists()):
        pytest.skip("model input not built; run 'uv run rr-discover model-input'")
    meta = json.loads((sdir / "shuffle.json").read_text(encoding="utf-8"))
    conn = pq.read_table(mi.connectivity).to_pandas()
    n_nodes = len(pd.read_csv(mi.completeness, index_col=0))
    pre = conn["Presynaptic_Index"].to_numpy(dtype=np.int64)
    post = conn["Postsynaptic_Index"].to_numpy(dtype=np.int64)
    syn = conn["Connectivity"].to_numpy(dtype=np.int64)
    sign = conn["Excitatory"].to_numpy(dtype=np.int64)
    res = controls.degree_preserving_shuffle(
        pre, post, n_nodes=n_nodes, seed=int(meta["seed"]), rounds=int(meta["rounds"])
    )
    assert res.n_accepted > 0

    shuf = pq.read_table(sdir / "connectivity.parquet").to_pandas()
    totals = pq.read_table(sdir / "input_totals.parquet").to_pandas()
    checks = controls.check_shuffle(
        pre,
        post,
        syn,
        sign,
        shuf["Presynaptic_Index"].to_numpy(dtype=np.int64),
        shuf["Postsynaptic_Index"].to_numpy(dtype=np.int64),
        shuf["Connectivity"].to_numpy(dtype=np.int64),
        shuf["Excitatory"].to_numpy(dtype=np.int64),
        n_nodes=n_nodes,
    )
    assert all(v for v in checks.values() if isinstance(v, bool))
    assert len(shuf) == len(conn)
    assert np.array_equal(
        np.bincount(shuf["Presynaptic_Index"].to_numpy(dtype=np.int64), minlength=n_nodes),
        np.bincount(pre, minlength=n_nodes),
    )
    assert np.array_equal(
        np.bincount(shuf["Postsynaptic_Index"].to_numpy(dtype=np.int64), minlength=n_nodes),
        np.bincount(post, minlength=n_nodes),
    )
    assert np.array_equal(np.sort(shuf["Connectivity"].to_numpy(dtype=np.int64)), np.sort(syn))
    per_post = shuf.groupby("Postsynaptic_ID")["Connectivity"].sum()
    recomputed = per_post.reindex(totals["root_id"].to_numpy(), fill_value=0)
    assert np.array_equal(
        recomputed.to_numpy(dtype=np.int64),
        totals["input_total"].to_numpy(dtype=np.int64),
    )

    for draw in range(1, 6):
        path = rp.shuffle_dir(draw) / "shuffle.json"
        assert path.is_file(), f"shuffle-{draw} missing; run the prepare step"
        recorded = json.loads(path.read_text(encoding="utf-8"))["checks"]
        assert all(v for v in recorded.values() if isinstance(v, bool))

    log = json.loads((rp.work / "run_log.json").read_text(encoding="utf-8"))
    assert "wall_s" in log["shuffle-1"]


def test_baseline_sanity_and_chance_v783(v783_paths: tuple[DiscoveryConfig, Paths]) -> None:
    cfg, paths = v783_paths
    dc = require_discover(cfg)
    spec = robustness.load_grid(require_robustness(cfg).grid)
    _, m5_spikes, _ = run_paths(dc, cfg.version)
    if not m5_spikes.is_file():
        pytest.skip("M5 spike file absent; run 'uv run rr-discover discover --step run'")
    counts, run_json, source = robustness.load_baseline(cfg)
    assert source == "m5"
    base = robustness.baseline_reference(cfg, counts, run_json, source)
    assert base["core_size"] == 917
    meta = json.loads((dc.out_dir / "metadata.json").read_text(encoding="utf-8"))["details"]
    assert sorted(base["gf_ids"]) == sorted(int(x) for x in meta["outputs"]["gf_ids"])

    ann = load_annotations(paths.annotations)
    valid = load_root_ids(paths.root_ids)
    stim = stimulated_sets(ann, valid, dc)
    chance = controls.chance_reference(
        np.asarray(base["core"], dtype=np.int64),
        np.setdiff1d(valid, stim.all),
        n_draws=1000,
        seed=spec.chance_seed,
    )
    for key, value in chance.to_dict().items():
        if isinstance(value, float):
            assert math.isfinite(value), key
    assert chance.retention_mean < 0.05
