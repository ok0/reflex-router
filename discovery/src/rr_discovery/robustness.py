"""M6 robustness suite driver: grid, time-budget reductions and four stages."""

import functools
import hashlib
import json
import re
import statistics
import sys
import time
import tomllib
from collections.abc import Collection, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from reflex_router.circuit import encode_circuit
from rr_discovery import (
    annotations,
    controls,
    extract,
    identify,
    pipeline,
    retention,
    robust_report,
)
from rr_discovery.annotations import descending_ids, ids_by_cell_type
from rr_discovery.config import (
    DiscoverConfig,
    DiscoveryConfig,
    RobustnessConfig,
    require_discover,
    require_model_input,
    require_robustness,
)
from rr_discovery.data import paths_from_config, sha256_file
from rr_discovery.model_input import ModelInputPaths, output_paths, verify_outputs
from rr_discovery.run import (
    ROBUSTNESS_RUNNER,
    ConditionFn,
    RunError,
    StimSets,
    read_m2_verdict,
    read_spike_counts,
    run_condition_runner,
    run_paths,
    stimulated_sets,
    write_run_log,
)


class RobustnessError(Exception):
    pass


FAMILY_ORDER: tuple[str, ...] = (
    "rate",
    "w_syn",
    "f_poi",
    "subset_side",
    "seed",
    "random_set",
    "shuffle",
    "interaction",
)
CONTROL_FAMILIES: tuple[str, ...] = ("random_set", "shuffle")
JOB_IDENTITY_KEYS: tuple[str, ...] = (
    "completeness",
    "connectivity",
    "stim_ids",
    "r_poi_hz",
    "w_syn_mult",
    "f_poi_mult",
    "n_trials",
    "seed_base",
)
BASELINE_CID = "baseline"
BASE_GROUPS: tuple[str, ...] = ("lc4", "lplc2")
SUBSET_GROUPS: dict[str, tuple[str, ...]] = {
    "lc4": ("lc4",),
    "lplc2": ("lplc2",),
    "both": ("lc4", "lplc2"),
}
SIDES: tuple[str, ...] = ("left", "right", "bilateral")
INTERACTION_GROUPS: tuple[str, ...] = ("lc4", "lplc2")
REAL = "real"
SHUFFLE_PREFIX = "shuffle-"
CONNECTIVITY_FILE = "connectivity.parquet"
TOTALS_FILE = "input_totals.parquet"
SHUFFLE_FILE = "shuffle.json"
CONN_READ_COLUMNS: tuple[str, ...] = (
    "Presynaptic_ID",
    "Postsynaptic_ID",
    "Connectivity",
    "Excitatory",
)
REPORT_BASELINE_KEYS: tuple[str, ...] = (
    "source",
    "spikes_sha256",
    "seed_base",
    "n_trials",
    "rate_hz",
    "n_responsive",
    "core_size",
    "n_members",
    "n_edges",
    "gf_ids",
    "parallel_ids",
    "parallel_cell_types",
    "circuit_sha256",
    "matches_m5",
    "side_counts",
)
_HEX64 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class GridSpec:
    schema: int
    seed_origin: int
    seed_stride: int
    time_cap_s: float
    budget_probe_conditions: int
    min_reduced_trials: int
    reduced_control_draws: int
    chance_draws: int
    chance_seed: int
    shuffle_rounds: int
    left_label: str
    right_label: str
    rate_hz: tuple[float, ...]
    w_syn_mult: tuple[float, ...]
    f_poi_mult: tuple[float, ...]
    subsets: tuple[str, ...]
    sides: tuple[str, ...]
    seed_replicates: int
    interaction_groups: tuple[str, ...]
    interaction_rate_hz: tuple[float, ...]
    random_set_draws: int
    shuffle_draws: int
    text: str
    sha256: str
    file: str
    deviations: tuple[tuple[str, str], ...]


def _grid_int(tbl: Mapping[str, Any], key: str, where: str) -> int:
    value = tbl.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RobustnessError(f"{where}: '{key}' must be an integer")
    return value


def _grid_num(tbl: Mapping[str, Any], key: str, where: str) -> float:
    value = tbl.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RobustnessError(f"{where}: '{key}' must be a number")
    return float(value)


def _grid_str(tbl: Mapping[str, Any], key: str, where: str) -> str:
    value = tbl.get(key)
    if not isinstance(value, str):
        raise RobustnessError(f"{where}: '{key}' must be a string")
    return value


def _grid_list(tbl: Mapping[str, Any], key: str, where: str) -> list[Any]:
    value = tbl.get(key)
    if not isinstance(value, list) or not value:
        raise RobustnessError(f"{where}: '{key}' must be a non-empty list")
    return value


def _grid_nums(tbl: Mapping[str, Any], key: str, where: str) -> tuple[float, ...]:
    out: list[float] = []
    for item in _grid_list(tbl, key, where):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise RobustnessError(f"{where}: '{key}' must contain only numbers")
        out.append(float(item))
    return tuple(out)


def _grid_strs(
    tbl: Mapping[str, Any], key: str, where: str, allowed: Collection[str]
) -> tuple[str, ...]:
    out: list[str] = []
    for item in _grid_list(tbl, key, where):
        if not isinstance(item, str) or item not in allowed:
            raise RobustnessError(f"{where}: '{key}' entries must be one of {sorted(allowed)}")
        out.append(item)
    return tuple(out)


def load_grid(path: Path) -> GridSpec:
    if not path.is_file():
        raise RobustnessError(f"robustness grid not found: {path}")
    raw = path.read_bytes()
    where = str(path)
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as err:
        raise RobustnessError(f"invalid robustness grid {where}: {err}") from err
    tbl = doc.get("robustness")
    if not isinstance(tbl, dict):
        raise RobustnessError(f"{where}: missing [robustness] table")
    fam = tbl.get("families")
    if not isinstance(fam, dict):
        raise RobustnessError(f"{where}: missing [robustness.families] table")

    seed_stride = _grid_int(tbl, "seed_stride", where)
    if seed_stride < 1:
        raise RobustnessError(f"{where}: seed_stride must be >= 1")
    reduced_control_draws = _grid_int(tbl, "reduced_control_draws", where)
    if reduced_control_draws < 1:
        raise RobustnessError(f"{where}: reduced_control_draws must be >= 1")
    min_reduced_trials = _grid_int(tbl, "min_reduced_trials", where)
    if min_reduced_trials < 2:
        raise RobustnessError(f"{where}: min_reduced_trials must be >= 2")

    rate_hz = _grid_nums(fam, "rate_hz", where)
    interaction_rate_hz = _grid_nums(fam, "interaction_rate_hz", where)
    for rate in (*rate_hz, *interaction_rate_hz):
        if not 0.0 < rate <= 1000.0:
            raise RobustnessError(f"{where}: rates must satisfy 0 < rate_hz <= 1000")
    w_syn_mult = _grid_nums(fam, "w_syn_mult", where)
    f_poi_mult = _grid_nums(fam, "f_poi_mult", where)
    for mult in (*w_syn_mult, *f_poi_mult):
        if not mult > 0.0:
            raise RobustnessError(f"{where}: multipliers must be > 0")
    random_set_draws = _grid_int(fam, "random_set_draws", where)
    shuffle_draws = _grid_int(fam, "shuffle_draws", where)
    for name, draws in (("random_set_draws", random_set_draws), ("shuffle_draws", shuffle_draws)):
        if draws < reduced_control_draws:
            raise RobustnessError(
                f"{where}: {name} must be >= reduced_control_draws ({reduced_control_draws})"
            )

    raw_devs = tbl.get("deviations", [])
    if not isinstance(raw_devs, list):
        raise RobustnessError(f"{where}: 'deviations' must be an array of tables")
    deviations: list[tuple[str, str]] = []
    for dev in raw_devs:
        if not isinstance(dev, dict):
            raise RobustnessError(f"{where}: each deviation must be a table")
        from_sha = dev.get("from_sha256")
        if not isinstance(from_sha, str) or not _HEX64.fullmatch(from_sha):
            raise RobustnessError(f"{where}: deviation from_sha256 must be 64 lowercase hex")
        reason = dev.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise RobustnessError(f"{where}: deviation reason must be a non-empty string")
        deviations.append((from_sha, reason))

    return GridSpec(
        schema=_grid_int(tbl, "schema", where),
        seed_origin=_grid_int(tbl, "seed_origin", where),
        seed_stride=seed_stride,
        time_cap_s=_grid_num(tbl, "time_cap_s", where),
        budget_probe_conditions=_grid_int(tbl, "budget_probe_conditions", where),
        min_reduced_trials=min_reduced_trials,
        reduced_control_draws=reduced_control_draws,
        chance_draws=_grid_int(tbl, "chance_draws", where),
        chance_seed=_grid_int(tbl, "chance_seed", where),
        shuffle_rounds=_grid_int(tbl, "shuffle_rounds", where),
        left_label=_grid_str(tbl, "left_label", where),
        right_label=_grid_str(tbl, "right_label", where),
        rate_hz=rate_hz,
        w_syn_mult=w_syn_mult,
        f_poi_mult=f_poi_mult,
        subsets=_grid_strs(fam, "subsets", where, SUBSET_GROUPS),
        sides=_grid_strs(fam, "sides", where, SIDES),
        seed_replicates=_grid_int(fam, "seed_replicates", where),
        interaction_groups=_grid_strs(fam, "interaction_groups", where, INTERACTION_GROUPS),
        interaction_rate_hz=interaction_rate_hz,
        random_set_draws=random_set_draws,
        shuffle_draws=shuffle_draws,
        text=raw.decode("utf-8"),
        sha256=hashlib.sha256(raw).hexdigest(),
        file=path.name,
        deviations=tuple(deviations),
    )


@dataclass(frozen=True)
class Condition:
    cid: str
    family: str
    rate_hz: float
    w_syn_mult: float
    f_poi_mult: float
    groups: tuple[str, ...]
    side: str
    n_trials: int
    seed_base: int
    draw: int = 0
    reduced: bool = False

    @property
    def control(self) -> bool:
        return self.family in CONTROL_FAMILIES

    def seeds(self) -> list[int]:
        return [self.seed_base + t for t in range(self.n_trials)]


def baseline_condition(dc: DiscoverConfig) -> Condition:
    return Condition(
        cid=BASELINE_CID,
        family="baseline",
        rate_hz=dc.rate_hz,
        w_syn_mult=1.0,
        f_poi_mult=1.0,
        groups=BASE_GROUPS,
        side="bilateral",
        n_trials=dc.n_trials,
        seed_base=dc.seed_base,
    )


def grid(spec: GridSpec, dc: DiscoverConfig) -> tuple[Condition, ...]:
    if spec.seed_stride < dc.n_trials:
        raise RobustnessError(f"seed_stride {spec.seed_stride} must be >= n_trials {dc.n_trials}")
    base_rate = dc.rate_hz
    specs: list[tuple[str, str, float, float, float, tuple[str, ...], str, int]] = []
    for r in spec.rate_hz:
        specs.append(("rate", f"rate-{r:g}hz", r, 1.0, 1.0, BASE_GROUPS, "bilateral", 0))
    for m in spec.w_syn_mult:
        specs.append(("w_syn", f"wsyn-x{m:.2f}", base_rate, m, 1.0, BASE_GROUPS, "bilateral", 0))
    for m in spec.f_poi_mult:
        specs.append(("f_poi", f"fpoi-x{m:.2f}", base_rate, 1.0, m, BASE_GROUPS, "bilateral", 0))
    for g in spec.subsets:
        for s in spec.sides:
            if g == "both" and s == "bilateral":
                continue
            specs.append(
                ("subset_side", f"stim-{g}-{s}", base_rate, 1.0, 1.0, SUBSET_GROUPS[g], s, 0)
            )
    for i in range(1, spec.seed_replicates + 1):
        specs.append(("seed", f"seed-{i}", base_rate, 1.0, 1.0, BASE_GROUPS, "bilateral", 0))
    for i in range(1, spec.random_set_draws + 1):
        specs.append(
            ("random_set", f"random-{i}", base_rate, 1.0, 1.0, ("random",), "bilateral", i)
        )
    for i in range(1, spec.shuffle_draws + 1):
        specs.append(("shuffle", f"shuffle-{i}", base_rate, 1.0, 1.0, BASE_GROUPS, "bilateral", i))
    for g in spec.interaction_groups:
        for r in spec.interaction_rate_hz:
            specs.append(("interaction", f"inter-{g}-{r:g}hz", r, 1.0, 1.0, (g,), "bilateral", 0))

    conds: list[Condition] = []
    for k, (family, cid, rate, w_mult, f_mult, groups, side, draw) in enumerate(specs):
        conds.append(
            Condition(
                cid=cid,
                family=family,
                rate_hz=float(rate),
                w_syn_mult=float(w_mult),
                f_poi_mult=float(f_mult),
                groups=groups,
                side=side,
                n_trials=dc.n_trials,
                seed_base=spec.seed_origin + k * spec.seed_stride,
                draw=draw,
            )
        )
    ids = [c.cid for c in conds]
    if len(set(ids)) != len(ids):
        raise RobustnessError("robustness condition ids are not unique")
    ranges: list[tuple[int, int, str]] = [(dc.seed_base, dc.seed_base + dc.n_trials, BASELINE_CID)]
    ranges += [(c.seed_base, c.seed_base + c.n_trials, c.cid) for c in conds]
    for i, (lo_a, hi_a, name_a) in enumerate(ranges):
        for lo_b, hi_b, name_b in ranges[i + 1 :]:
            if lo_a < hi_b and lo_b < hi_a:
                raise RobustnessError(f"seed ranges of {name_a} and {name_b} overlap")
    return tuple(conds)


@dataclass(frozen=True)
class Reduction:
    conditions: tuple[Condition, ...]
    steps: tuple[tuple[str, int], ...]
    dropped: tuple[str, ...]
    reduced: dict[str, int]
    within_cap: bool
    projected_s: float


def _reduced_map(conds: Sequence[Condition], done: set[str]) -> dict[str, int]:
    return {c.cid: c.n_trials for c in conds if c.reduced and c.cid not in done}


def apply_reductions(
    conditions: Sequence[Condition],
    *,
    done: Collection[str],
    sec_per_condition: float,
    elapsed_s: float,
    cap_s: float,
    base_trials: int,
    min_trials: int,
    control_draws: int,
) -> Reduction:
    done_set = set(done)

    def projected(conds: Sequence[Condition]) -> float:
        pending = sum(
            sec_per_condition * c.n_trials / base_trials for c in conds if c.cid not in done_set
        )
        return elapsed_s + pending

    def finish(
        conds: Sequence[Condition],
        steps: list[tuple[str, int]],
        dropped: list[str],
        reduced: dict[str, int],
        within: bool,
    ) -> Reduction:
        return Reduction(
            conditions=tuple(conds),
            steps=tuple(steps),
            dropped=tuple(dropped),
            reduced=dict(reduced),
            within_cap=within,
            projected_s=projected(conds),
        )

    steps: list[tuple[str, int]] = []
    dropped: list[str] = []
    current = list(conditions)
    if projected(current) <= cap_s:
        return finish(current, steps, dropped, {}, True)

    gone = [c.cid for c in current if c.cid not in done_set and c.family == "interaction"]
    if gone:
        steps.append(("drop_interaction", 0))
        dropped.extend(gone)
        current = [c for c in current if c.cid not in gone]
        if projected(current) <= cap_s:
            return finish(current, steps, dropped, {}, True)

    gone = [
        c.cid for c in current if c.cid not in done_set and c.control and c.draw > control_draws
    ]
    if gone:
        steps.append(("controls_to", control_draws))
        dropped.extend(gone)
        current = [c for c in current if c.cid not in gone]
        if projected(current) <= cap_s:
            return finish(current, steps, dropped, {}, True)

    for t in range(base_trials - 1, min_trials - 1, -1):
        cand = [c if c.cid in done_set else replace(c, n_trials=t, reduced=True) for c in current]
        if projected(cand) <= cap_s:
            steps.append(("trials_to", t))
            return finish(cand, steps, dropped, _reduced_map(cand, done_set), True)
    cand = [
        c if c.cid in done_set else replace(c, n_trials=min_trials, reduced=True) for c in current
    ]
    steps.append(("trials_to", min_trials))
    return finish(cand, steps, dropped, _reduced_map(cand, done_set), False)


def make_job(
    cond: Condition,
    *,
    stim_ids: np.ndarray,
    completeness: Path,
    connectivity: Path,
    n_proc: int,
) -> dict[str, Any]:
    return {
        "schema": 2,
        "label": cond.cid,
        "completeness": str(completeness),
        "connectivity": str(connectivity),
        "stim_ids": sorted(int(i) for i in np.asarray(stim_ids, dtype=np.int64).tolist()),
        "r_poi_hz": float(cond.rate_hz),
        "w_syn_mult": float(cond.w_syn_mult),
        "f_poi_mult": float(cond.f_poi_mult),
        "n_trials": int(cond.n_trials),
        "seed_base": int(cond.seed_base),
        "n_proc": int(n_proc),
    }


@dataclass(frozen=True)
class RobustPaths:
    work: Path
    plan: Path
    frozen: Path
    reductions: Path
    baseline: Path
    chance: Path
    conditions: Path
    shuffles: Path

    def cond_dir(self, cid: str) -> Path:
        return self.conditions / cid

    def shuffle_dir(self, draw: int) -> Path:
        return self.shuffles / f"shuffle-{draw}"


def robust_paths(rc: RobustnessConfig) -> RobustPaths:
    work = rc.work_dir
    return RobustPaths(
        work=work,
        plan=work / "plan.json",
        frozen=work / "frozen.json",
        reductions=work / "reductions.json",
        baseline=work / "baseline.json",
        chance=work / "chance.json",
        conditions=work / "conditions",
        shuffles=work / "shuffles",
    )


def _plain(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, str)):
        return obj
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return round(float(obj), 6)
    if isinstance(obj, Mapping):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray)):
        return [_plain(v) for v in obj]
    raise RobustnessError(f"value of type {type(obj).__name__} is not JSON serialisable")


def _dump(obj: Any) -> str:
    return json.dumps(_plain(obj), sort_keys=True, indent=2) + "\n"


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump(obj), encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_required(path: Path, step: str) -> Any:
    if not path.is_file():
        raise RobustnessError(f"{path.name} not found; run the {step} step first")
    return _read_json(path)


def _model_input(cfg: DiscoveryConfig) -> ModelInputPaths:
    mi = output_paths(require_model_input(cfg).out_dir, cfg.version)
    verify_outputs(mi)
    return mi


def _rule(dc: DiscoverConfig) -> extract.ResponsiveRule:
    return extract.ResponsiveRule(dc.min_rate_hz, dc.min_trial_frac)


def _read_tables(conn_path: Path, totals_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = pq.read_table(conn_path, columns=list(CONN_READ_COLUMNS)).to_pandas()
    totals = pq.read_table(totals_path).to_pandas()
    return conn, totals


def _draw_of(label: str) -> int:
    if not label.startswith(SHUFFLE_PREFIX):
        raise RobustnessError(f"unknown connectivity label {label!r}")
    return int(label[len(SHUFFLE_PREFIX) :])


def _connectivity_path(label: str, mi: ModelInputPaths, paths: RobustPaths) -> Path:
    if label == REAL:
        return mi.connectivity
    return paths.shuffle_dir(_draw_of(label)) / CONNECTIVITY_FILE


def _tables_for(
    label: str, mi: ModelInputPaths, paths: RobustPaths
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if label == REAL:
        return _read_tables(mi.connectivity, mi.input_totals)
    sdir = paths.shuffle_dir(_draw_of(label))
    return _read_tables(sdir / CONNECTIVITY_FILE, sdir / TOTALS_FILE)


def _side_counts(ann: pd.DataFrame, ids: np.ndarray, spec: GridSpec) -> dict[str, int]:
    labels = controls.side_labels(
        ann,
        np.asarray(ids, dtype=np.int64),
        left_label=spec.left_label,
        right_label=spec.right_label,
    )
    counts: dict[str, int] = {"left": 0, "right": 0, "unlabeled": 0}
    for side in labels.tolist():
        counts[str(side)] = counts.get(str(side), 0) + 1
    return counts


def _side_total(sides: controls.SideSets, side: str) -> int:
    return int(sides.lc4[side].size + sides.lplc2[side].size)


def _stim_for(
    cond: Condition,
    *,
    ann: pd.DataFrame,
    valid: np.ndarray,
    sides: controls.SideSets,
    stim: StimSets,
    dc: DiscoverConfig,
    spec: GridSpec,
    model_ids: np.ndarray,
) -> np.ndarray:
    if cond.family == "random_set":
        exclude = np.union1d(stim.all, ids_by_cell_type(ann, dc.gf_cell_type, valid_ids=valid))
        return controls.random_set(
            ann,
            np.intersect1d(valid, model_ids),
            exclude=exclude,
            n_left=_side_total(sides, "left"),
            n_right=_side_total(sides, "right"),
            n_unlabeled=_side_total(sides, "unlabeled"),
            seed=cond.seed_base,
            left_label=spec.left_label,
            right_label=spec.right_label,
        )
    return controls.condition_stim(sides, cond.groups, cond.side).all


def _cond_of(entry: Mapping[str, Any]) -> Condition:
    return Condition(
        cid=str(entry["cid"]),
        family=str(entry["family"]),
        rate_hz=float(entry["rate_hz"]),
        w_syn_mult=float(entry["w_syn_mult"]),
        f_poi_mult=float(entry["f_poi_mult"]),
        groups=tuple(str(g) for g in entry["groups"]),
        side=str(entry["side"]),
        n_trials=int(entry["n_trials"]),
        seed_base=int(entry["seed_base"]),
        draw=int(entry["draw"]),
        reduced=bool(entry["reduced"]),
    )


def _stim_ids(entry: Mapping[str, Any]) -> np.ndarray:
    return np.asarray(entry["stim_ids"], dtype=np.int64)


def _plan_entry(
    cond: Condition,
    *,
    ids: np.ndarray,
    ann: pd.DataFrame,
    spec: GridSpec,
    connectivity: str,
) -> dict[str, Any]:
    return {
        **asdict(cond),
        "stim_ids": sorted(int(i) for i in np.asarray(ids, dtype=np.int64).tolist()),
        "stim_counts": {"total": int(np.asarray(ids).size)},
        "side_counts": _side_counts(ann, ids, spec),
        "connectivity": connectivity,
    }


def _params(cond: Condition, connectivity: str) -> dict[str, Any]:
    return {
        "rate_hz": cond.rate_hz,
        "w_syn_mult": cond.w_syn_mult,
        "f_poi_mult": cond.f_poi_mult,
        "groups": list(cond.groups),
        "side": cond.side,
        "n_trials": cond.n_trials,
        "seed_base": cond.seed_base,
        "connectivity": connectivity,
    }


def _parallel_universe(
    ann: pd.DataFrame,
    valid: np.ndarray,
    dc: DiscoverConfig,
    stim: StimSets,
    conn: pd.DataFrame,
    totals: pd.DataFrame,
) -> list[dict[str, Any]]:
    gf_type = ids_by_cell_type(ann, dc.gf_cell_type, valid_ids=valid)
    typed = [
        ids_by_cell_type(ann, t, valid_ids=valid)
        for t in (*dc.prior_cell_types, *dc.reported_cell_types)
    ]
    pool = np.unique(np.concatenate([descending_ids(ann, valid_ids=valid), *typed])).astype(
        np.int64
    )
    universe = np.setdiff1d(pool, gf_type).astype(np.int64)
    eligible = retention.direct_input_ids(conn, totals, stim.all, universe)
    ok = np.isin(universe, eligible)
    cell = annotations.labels(ann, universe)["cell_type"].tolist()
    return [
        {"root_id": int(r), "cell_type": str(t), "check_ii": bool(f)}
        for r, t, f in zip(universe.tolist(), cell, ok.tolist(), strict=True)
    ]


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), path, compression="snappy")


def _shuffle_current(sdir: Path, *, seed: int, rounds: int) -> bool:
    meta_path = sdir / SHUFFLE_FILE
    if not (meta_path.is_file() and (sdir / CONNECTIVITY_FILE).is_file()):
        return False
    if not (sdir / TOTALS_FILE).is_file():
        return False
    meta = _read_json(meta_path)
    if meta.get("seed") != seed or meta.get("rounds") != rounds:
        return False
    return sha256_file(sdir / CONNECTIVITY_FILE) == meta.get("connectivity_sha256") and sha256_file(
        sdir / TOTALS_FILE
    ) == meta.get("input_totals_sha256")


def _build_shuffle(
    conn: pd.DataFrame,
    *,
    draw: int,
    seed: int,
    n_nodes: int,
    rounds: int,
    sdir: Path,
    work: Path,
) -> None:
    t0 = time.monotonic()
    pre_idx = conn["Presynaptic_Index"].to_numpy(dtype=np.int64)
    post_idx = conn["Postsynaptic_Index"].to_numpy(dtype=np.int64)
    res = controls.degree_preserving_shuffle(
        pre_idx, post_idx, n_nodes=n_nodes, seed=seed, rounds=rounds
    )
    out_conn, totals = controls.shuffle_tables(conn, res)
    checks = controls.check_shuffle(
        pre_idx,
        post_idx,
        conn["Connectivity"].to_numpy(np.int64),
        conn["Excitatory"].to_numpy(np.int64),
        out_conn["Presynaptic_Index"].to_numpy(np.int64),
        out_conn["Postsynaptic_Index"].to_numpy(np.int64),
        out_conn["Connectivity"].to_numpy(np.int64),
        out_conn["Excitatory"].to_numpy(np.int64),
        n_nodes=n_nodes,
    )
    failed = sorted(k for k, v in checks.items() if isinstance(v, bool) and not v)
    if failed:
        raise RobustnessError(f"shuffle-{draw}: checks failed: {', '.join(failed)}")
    sdir.mkdir(parents=True, exist_ok=True)
    conn_path = sdir / CONNECTIVITY_FILE
    totals_path = sdir / TOTALS_FILE
    _write_parquet(out_conn, conn_path)
    _write_parquet(totals, totals_path)
    _write_json(
        sdir / SHUFFLE_FILE,
        {
            "draw": draw,
            "seed": seed,
            "rounds": res.n_rounds,
            "n_attempted": res.n_attempted,
            "n_accepted": res.n_accepted,
            "n_changed_edges": res.n_changed_edges,
            "self_loops_before": res.self_loops_before,
            "self_loops_after": res.self_loops_after,
            "checks": checks,
            "connectivity_sha256": sha256_file(conn_path),
            "input_totals_sha256": sha256_file(totals_path),
        },
    )
    write_run_log(work, f"shuffle-{draw}", {"wall_s": time.monotonic() - t0})


def _build_shuffles(
    spec: GridSpec, mi: ModelInputPaths, paths: RobustPaths, conds: Sequence[Condition]
) -> None:
    draws: dict[int, int] = {}
    for cond in conds:
        if cond.family == "shuffle":
            draws.setdefault(cond.draw, cond.seed_base)
    if not draws:
        return
    n_nodes = len(pd.read_csv(mi.completeness, index_col=0))
    pending = [
        d
        for d in sorted(draws)
        if not _shuffle_current(paths.shuffle_dir(d), seed=draws[d], rounds=spec.shuffle_rounds)
    ]
    if not pending:
        return
    full = pq.read_table(mi.connectivity).to_pandas()
    for draw in pending:
        _build_shuffle(
            full,
            draw=draw,
            seed=draws[draw],
            n_nodes=n_nodes,
            rounds=spec.shuffle_rounds,
            sdir=paths.shuffle_dir(draw),
            work=paths.work,
        )


def prepare_stage(cfg: DiscoveryConfig) -> Path:
    dc = require_discover(cfg)
    rc = require_robustness(cfg)
    spec = load_grid(rc.grid)
    paths = robust_paths(rc)
    mi = _model_input(cfg)
    src = paths_from_config(cfg)
    ann = annotations.load_annotations(src.annotations)
    valid = annotations.load_root_ids(src.root_ids)
    stim = stimulated_sets(ann, valid, dc)
    sides = controls.side_sets(ann, stim, left_label=spec.left_label, right_label=spec.right_label)
    print(
        f"unlabeled stimulated ids: lc4 {sides.lc4['unlabeled'].size}, "
        f"lplc2 {sides.lplc2['unlabeled'].size}"
    )

    conn, totals = _read_tables(mi.connectivity, mi.input_totals)
    universe = _parallel_universe(ann, valid, dc, stim, conn, totals)
    base = baseline_condition(dc)
    entries = [_plan_entry(base, ids=stim.all, ann=ann, spec=spec, connectivity=REAL)]
    grid_conds = grid(spec, dc)
    model_ids = pd.read_csv(mi.completeness, index_col=0).index.to_numpy().astype(np.int64)
    for cond in grid_conds:
        ids = _stim_for(
            cond,
            ann=ann,
            valid=valid,
            sides=sides,
            stim=stim,
            dc=dc,
            spec=spec,
            model_ids=model_ids,
        )
        label = f"{SHUFFLE_PREFIX}{cond.draw}" if cond.family == "shuffle" else REAL
        entries.append(_plan_entry(cond, ids=ids, ann=ann, spec=spec, connectivity=label))

    _build_shuffles(spec, mi, paths, grid_conds)

    unlabeled = np.union1d(sides.lc4["unlabeled"], sides.lplc2["unlabeled"]).astype(np.int64)
    plan = {
        "schema": 1,
        "grid_file": spec.file,
        "grid_sha256": spec.sha256,
        "baseline": entries[0],
        "conditions": entries[1:],
        "unlabeled_ids": [int(x) for x in unlabeled.tolist()],
        "parallel_universe": universe,
    }
    _write_json(paths.plan, plan)
    return paths.plan


def _load_plan(paths: RobustPaths) -> dict[str, Any]:
    if not paths.plan.is_file():
        raise RobustnessError(
            "plan.json not found; run 'rr-discover robustness --step prepare' first"
        )
    plan: dict[str, Any] = _read_json(paths.plan)
    return plan


def _entries(plan: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for entry in [plan["baseline"], *plan["conditions"]]:
        out[str(entry["cid"])] = dict(entry)
    return out


def _load_saved(paths: RobustPaths) -> dict[str, Any] | None:
    if not paths.reductions.is_file():
        return None
    saved: dict[str, Any] = _read_json(paths.reductions)
    return saved


def _effective(
    conds: Sequence[Condition], saved: Mapping[str, Any] | None
) -> tuple[list[Condition], set[str]]:
    if saved is None:
        return list(conds), set()
    dropped = {str(x) for x in saved["dropped"]}
    reduced = {str(k): int(v) for k, v in saved["reduced"].items()}
    eff = [
        replace(c, n_trials=reduced[c.cid], reduced=True) if c.cid in reduced else c
        for c in conds
        if c.cid not in dropped
    ]
    return eff, dropped


def load_baseline(cfg: DiscoveryConfig) -> tuple[pd.DataFrame, dict[str, Any], str]:
    dc = require_discover(cfg)
    paths = robust_paths(require_robustness(cfg))
    _, m5_spikes, m5_run = run_paths(dc, cfg.version)
    meta_path = dc.out_dir / "metadata.json"
    if meta_path.is_file() and m5_spikes.is_file() and m5_run.is_file():
        meta = _read_json(meta_path)
        expected = str(meta["details"]["spikes"]["sha256"])
        if sha256_file(m5_spikes) == expected:
            counts = read_spike_counts(m5_spikes, expected_sha256=expected)
            run_json: dict[str, Any] = _read_json(m5_run)
            return counts, run_json, "m5"
    cdir = paths.cond_dir(BASELINE_CID)
    if (cdir / "run.json").is_file() and (cdir / "spikes.tsv").is_file():
        run_json = _read_json(cdir / "run.json")
        counts = read_spike_counts(
            cdir / "spikes.tsv", expected_sha256=str(run_json["spikes"]["sha256"])
        )
        return counts, run_json, "resimulated"
    raise RobustnessError("baseline spikes unavailable; run the run step")


def baseline_reference(
    cfg: DiscoveryConfig,
    counts: pd.DataFrame,
    run_json: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    dc = require_discover(cfg)
    spec = load_grid(require_robustness(cfg).grid)
    mi = _model_input(cfg)
    src = paths_from_config(cfg)
    ann = annotations.load_annotations(src.annotations)
    valid = annotations.load_root_ids(src.root_ids)
    stim = stimulated_sets(ann, valid, dc)
    conn, totals = _read_tables(mi.connectivity, mi.input_totals)
    n_trials = len(run_json["seeds"])
    d = pipeline.derive(
        counts,
        n_trials=n_trials,
        t_run_s=float(run_json["t_run_s"]),
        stimulated=stim.all,
        connectivity=conn,
        input_totals=totals,
        rule=_rule(dc),
    )
    out = identify.outputs(
        ann=ann,
        valid_ids=valid,
        stats=d.stats,
        members=d.members,
        stim=stim,
        connectivity=conn,
        input_totals=totals,
        gf_cell_type=dc.gf_cell_type,
        prior_cell_types=dc.prior_cell_types,
        reported_cell_types=dc.reported_cell_types,
    )
    if out.gf_ids.size == 0:
        raise RobustnessError(f"baseline has no responsive {dc.gf_cell_type} neuron")
    labels = pipeline.circuit_labels(ann, d.members, out)
    circuit = pipeline.circuit_spec(stim=stim, d=d, out=out, labels=labels, connectivity=conn)
    sha = hashlib.sha256(encode_circuit(circuit)).hexdigest()

    circuit_path = dc.out_dir / "circuit.json"
    meta_path = dc.out_dir / "metadata.json"
    if not (circuit_path.is_file() and meta_path.is_file()):
        raise RobustnessError(f"committed M5 artifact not found in {dc.out_dir}")
    details = _read_json(meta_path)["details"]
    gf_ids = sorted(int(x) for x in out.gf_ids.tolist())
    parallel_ids = sorted(int(x) for x in out.parallel_ids.tolist())
    responsive = sorted(int(x) for x in d.responsive_ids.tolist())
    mismatch: list[str] = []
    if sha256_file(circuit_path) != sha:
        mismatch.append("circuit sha256")
    if int(details["responsive_rule"]["n_responsive"]) != len(responsive):
        mismatch.append("n_responsive")
    if sorted(int(x) for x in details["outputs"]["gf_ids"]) != gf_ids:
        mismatch.append("gf_ids")
    if sorted(int(x) for x in details["outputs"]["parallel_ids"]) != parallel_ids:
        mismatch.append("parallel_ids")
    if mismatch:
        raise RobustnessError(
            "baseline does not reproduce the committed M5 circuit: " + ", ".join(mismatch)
        )

    responsive_rows = d.stats.loc[np.asarray(d.stats["responsive"], dtype=bool)]
    core_rel = {
        str(int(r)): float(x)
        for r, x in zip(
            responsive_rows["root_id"].tolist(), responsive_rows["rel_rate"].tolist(), strict=True
        )
    }
    edges = [
        [int(p), int(q)]
        for p, q in zip(d.edges["pre"].tolist(), d.edges["post"].tolist(), strict=True)
    ]
    sides = controls.side_sets(ann, stim, left_label=spec.left_label, right_label=spec.right_label)
    return {
        "source": source,
        "spikes_sha256": str(run_json["spikes"]["sha256"]),
        "seed_base": dc.seed_base,
        "n_trials": n_trials,
        "rate_hz": float(dc.rate_hz),
        "n_responsive": len(responsive),
        "core_size": len(responsive),
        "n_members": int(d.members.size),
        "n_edges": len(edges),
        "gf_type_ids": [int(x) for x in out.gf_type_ids.tolist()],
        "gf_ids": gf_ids,
        "parallel_ids": parallel_ids,
        "parallel_cell_types": sorted(
            {c.cell_type for c in out.candidates if c.role == "output_parallel"}
        ),
        "circuit_sha256": sha,
        "matches_m5": True,
        "side_counts": sides.counts(),
        "core": responsive,
        "core_rel": core_rel,
        "members": sorted(int(x) for x in d.members.tolist()),
        "edges": edges,
        "roles": {str(n.root_id): n.role for n in circuit.neurons},
    }


@dataclass(frozen=True)
class RunSummary:
    n_run: int
    n_skipped: int
    n_failed: int
    dropped: tuple[str, ...]


@dataclass(frozen=True)
class _Ctx:
    paths: RobustPaths
    mi: ModelInputPaths
    python: Path
    n_proc: int
    condition_fn: ConditionFn
    entries: Mapping[str, Mapping[str, Any]]


_robustness_runner: ConditionFn = functools.partial(run_condition_runner, runner=ROBUSTNESS_RUNNER)


def _job_of(ctx: _Ctx, cond: Condition) -> dict[str, Any]:
    entry = ctx.entries[cond.cid]
    return make_job(
        cond,
        stim_ids=_stim_ids(entry),
        completeness=ctx.mi.completeness,
        connectivity=_connectivity_path(str(entry["connectivity"]), ctx.mi, ctx.paths),
        n_proc=ctx.n_proc,
    )


def _is_done(job: Mapping[str, Any], cdir: Path) -> bool:
    run_path = cdir / "run.json"
    spikes = cdir / "spikes.tsv"
    if not (run_path.is_file() and spikes.is_file()):
        return False
    run_json = _read_json(run_path)
    prior = run_json.get("job") or {}
    if any(prior.get(k) != job[k] for k in JOB_IDENTITY_KEYS):
        return False
    digest = hashlib.sha256(spikes.read_bytes()).hexdigest()
    return digest == run_json.get("spikes", {}).get("sha256")


def _execute(ctx: _Ctx, cond: Condition) -> float | None:
    job = _job_of(ctx, cond)
    cdir = ctx.paths.cond_dir(cond.cid)
    if _is_done(job, cdir):
        return None
    cdir.mkdir(parents=True, exist_ok=True)
    job_path = cdir / "job.json"
    job_path.write_text(json.dumps(job, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    spikes = cdir / "spikes.tsv"
    run_path = cdir / "run.json"
    failed = cdir / "failed.json"
    started = datetime.now(UTC)
    t0 = time.monotonic()
    try:
        result = ctx.condition_fn(ctx.python, job_path, spikes, run_path)
    except Exception as err:
        _write_json(failed, {"cid": cond.cid, "reason": str(err)})
        raise
    wall = time.monotonic() - t0
    failed.unlink(missing_ok=True)
    write_run_log(
        ctx.paths.work,
        f"run:{cond.cid}",
        {
            "started_utc": started.isoformat(timespec="seconds"),
            "wall_s": wall,
            "n_proc": ctx.n_proc,
            "host": result.get("host"),
            "total_wall_s": result.get("total_wall_s"),
        },
    )
    return wall


def _freeze_check(paths: RobustPaths, spec: GridSpec) -> None:
    if not paths.frozen.is_file():
        _write_json(paths.frozen, {"grid_sha256": spec.sha256})
        return
    frozen = str(_read_json(paths.frozen)["grid_sha256"])
    if frozen == spec.sha256:
        return
    if any(from_sha == frozen for from_sha, _ in spec.deviations):
        return
    raise RobustnessError(
        f"grid {spec.file} changed after freezing (frozen {frozen}); add a "
        f'[[robustness.deviations]] entry with from_sha256 = "{frozen}" and a reason'
    )


def run_stage(
    cfg: DiscoveryConfig,
    *,
    python: Path | None,
    n_proc: int | None,
    time_cap_s: float | None = None,
    condition_fn: ConditionFn = _robustness_runner,
) -> RunSummary:
    t_start = time.monotonic()
    dc = require_discover(cfg)
    rc = require_robustness(cfg)
    spec = load_grid(rc.grid)
    paths = robust_paths(rc)
    plan = _load_plan(paths)
    verdict = read_m2_verdict(dc.m2_report)
    if verdict.verdict != "PASS":
        raise RunError(f"M2 verdict is {verdict.verdict}; the whole-brain run requires PASS")
    if python is None:
        if verdict.sim_env != "py314":
            raise RunError(f"M2 sim_env is {verdict.sim_env}; pass --python <fallback python>")
        python = Path(sys.executable)
    mi = _model_input(cfg)
    _freeze_check(paths, spec)
    ctx = _Ctx(
        paths=paths,
        mi=mi,
        python=python,
        n_proc=dc.n_proc if n_proc is None else n_proc,
        condition_fn=condition_fn,
        entries=_entries(plan),
    )

    try:
        load_baseline(cfg)
    except RobustnessError:
        _execute(ctx, _cond_of(plan["baseline"]))
    counts, base_run, source = load_baseline(cfg)
    baseline_reference(cfg, counts, base_run, source)

    saved = _load_saved(paths)
    conds, dropped = _effective([_cond_of(e) for e in plan["conditions"]], saved)
    cap = spec.time_cap_s if time_cap_s is None else time_cap_s
    probes: list[tuple[float, int]] = []
    budget_settled = saved is not None
    processed: set[str] = set()
    n_run = 0
    n_skipped = 0
    n_failed = 0
    while True:
        pending = [c for c in conds if c.cid not in processed]
        if not pending:
            break
        cond = pending[0]
        processed.add(cond.cid)
        try:
            wall = _execute(ctx, cond)
        except Exception:
            n_failed += 1
            continue
        if wall is None:
            n_skipped += 1
            continue
        n_run += 1
        probes.append((wall, cond.n_trials))
        if not budget_settled and len(probes) == spec.budget_probe_conditions:
            budget_settled = True
            done = {c.cid for c in conds if _is_done(_job_of(ctx, c), paths.cond_dir(c.cid))}
            sec = statistics.median(w * dc.n_trials / n for w, n in probes)
            elapsed = sum(w for w, _ in probes)
            red = apply_reductions(
                conds,
                done=done,
                sec_per_condition=sec,
                elapsed_s=elapsed,
                cap_s=cap,
                base_trials=dc.n_trials,
                min_trials=spec.min_reduced_trials,
                control_draws=spec.reduced_control_draws,
            )
            _write_json(
                paths.reductions,
                {
                    "steps": [{"code": code, "n": n} for code, n in red.steps],
                    "dropped": list(red.dropped),
                    "reduced": dict(red.reduced),
                    "within_cap": red.within_cap,
                },
            )
            write_run_log(
                paths.work,
                "budget",
                {"sec_per_condition": sec, "projected_s": red.projected_s, "cap_s": cap},
            )
            dropped = set(red.dropped)
            conds = list(red.conditions)

    write_run_log(paths.work, "run_total", {"wall_s": time.monotonic() - t_start})
    return RunSummary(
        n_run=n_run,
        n_skipped=n_skipped,
        n_failed=n_failed,
        dropped=tuple(sorted(dropped)),
    )


def _tracked_types(dc: DiscoverConfig, base: Mapping[str, Any]) -> list[str]:
    tracked = [*dc.prior_cell_types, *dc.reported_cell_types]
    for cell_type in base["parallel_cell_types"]:
        if cell_type not in tracked:
            tracked.append(str(cell_type))
    return tracked


def _gf_dict(gf: retention.GFIdentity) -> dict[str, Any]:
    return asdict(gf)


def _par_dict(par: retention.ParallelIdentity) -> dict[str, Any]:
    return asdict(par)


def extract_stage(cfg: DiscoveryConfig) -> int:
    dc = require_discover(cfg)
    rc = require_robustness(cfg)
    spec = load_grid(rc.grid)
    paths = robust_paths(rc)
    plan = _load_plan(paths)
    mi = _model_input(cfg)
    src = paths_from_config(cfg)
    ann = annotations.load_annotations(src.annotations)
    valid = annotations.load_root_ids(src.root_ids)
    stim = stimulated_sets(ann, valid, dc)

    counts, base_run, source = load_baseline(cfg)
    base = baseline_reference(cfg, counts, base_run, source)
    _write_json(paths.baseline, base)
    chance = controls.chance_reference(
        np.asarray(base["core"], dtype=np.int64),
        np.setdiff1d(valid, stim.all),
        n_draws=spec.chance_draws,
        seed=spec.chance_seed,
    )
    _write_json(paths.chance, chance.to_dict())

    entries = _entries(plan)
    saved = _load_saved(paths)
    effective, _ = _effective([_cond_of(e) for e in plan["conditions"]], saved)
    tracked = _tracked_types(dc, base)
    base_core = np.asarray(base["core"], dtype=np.int64)
    base_rel = {int(k): float(v) for k, v in base["core_rel"].items()}
    base_edges = pd.DataFrame(base["edges"], columns=["pre", "post"])
    base_gf_type = np.asarray(base["gf_type_ids"], dtype=np.int64)
    base_gf = np.asarray(base["gf_ids"], dtype=np.int64)
    base_par = np.asarray(base["parallel_ids"], dtype=np.int64)
    cell_type_of = {int(e["root_id"]): str(e["cell_type"]) for e in plan["parallel_universe"]}
    eligible = np.asarray(
        [int(e["root_id"]) for e in plan["parallel_universe"] if e["check_ii"]],
        dtype=np.int64,
    )

    n_done = 0
    for cond in effective:
        cdir = paths.cond_dir(cond.cid)
        if (cdir / "failed.json").is_file():
            continue
        run_path = cdir / "run.json"
        spikes = cdir / "spikes.tsv"
        if not (run_path.is_file() and spikes.is_file()):
            continue
        entry = entries[cond.cid]
        run_result = _read_json(run_path)
        spike_counts = read_spike_counts(
            spikes, expected_sha256=str(run_result["spikes"]["sha256"])
        )
        label = str(entry["connectivity"])
        conn, totals = _tables_for(label, mi, paths)
        stim_ids = _stim_ids(entry)
        d = pipeline.derive(
            spike_counts,
            n_trials=len(run_result["seeds"]),
            t_run_s=float(run_result["t_run_s"]),
            stimulated=stim_ids,
            connectivity=conn,
            input_totals=totals,
            rule=_rule(dc),
        )
        stats_rel = {
            int(r): float(x)
            for r, x in zip(d.stats["root_id"].tolist(), d.stats["rel_rate"].tolist(), strict=True)
        }
        core = retention.core_metrics(
            base_core=base_core,
            base_rel=base_rel,
            cond_responsive=d.responsive_ids,
            cond_rel=stats_rel,
            cond_stimulated=stim_ids,
        )
        circuit = retention.edge_metrics(
            base_edges=base_edges, cond_members=d.members, cond_edges=d.edges
        )
        gf = retention.gf_identity(
            gf_type_ids=base_gf_type, base_gf_ids=base_gf, cond_stats=d.stats
        )
        par = retention.parallel_identity(
            base_parallel_ids=base_par,
            eligible_ids=eligible,
            cell_type_of=cell_type_of,
            tracked_types=tracked,
            cond_responsive=d.responsive_ids,
            cond_members=d.members,
            cond_stimulated=stim_ids,
        )
        _write_json(
            cdir / "result.json",
            {
                "cid": cond.cid,
                "family": cond.family,
                "control": cond.control,
                "params": _params(cond, label),
                "n_stimulated": int(stim_ids.size),
                "spikes_sha256": str(run_result["spikes"]["sha256"]),
                "responsive_ids": sorted(int(x) for x in d.responsive_ids.tolist()),
                "core": core.to_dict(),
                "circuit": circuit.to_dict(),
                "gf": _gf_dict(gf),
                "parallel": _par_dict(par),
            },
        )
        n_done += 1
    return n_done


def _status(
    paths: RobustPaths, cid: str, dropped: set[str]
) -> tuple[str, str | None, dict[str, Any] | None]:
    cdir = paths.cond_dir(cid)
    if cid in dropped:
        return "dropped", "dropped by the time-budget reductions", None
    failed = cdir / "failed.json"
    if failed.is_file():
        return "failed", str(_read_json(failed)["reason"]), None
    result = cdir / "result.json"
    if result.is_file():
        metrics: dict[str, Any] = _read_json(result)
        return "completed", None, metrics
    return "failed", "no simulation output", None


def _cond_row(
    cond: Condition,
    entry: Mapping[str, Any],
    *,
    status: str,
    reason: str | None,
    metrics: Mapping[str, Any] | None,
) -> dict[str, Any]:
    m: Mapping[str, Any] = metrics or {}
    draw = None
    if cond.family == "random_set":
        draw = {
            "draw": cond.draw,
            "side_counts": entry["side_counts"],
            "ids": entry["stim_ids"],
        }
    return {
        "cid": cond.cid,
        "family": cond.family,
        "control": cond.control,
        "status": status,
        "reason": reason,
        "reduced": cond.reduced,
        "params": _params(cond, str(entry["connectivity"])),
        "n_stimulated": m.get("n_stimulated"),
        "spikes_sha256": m.get("spikes_sha256"),
        "core": m.get("core"),
        "circuit": m.get("circuit"),
        "gf": m.get("gf"),
        "parallel": m.get("parallel"),
        "random_draw": draw,
    }


def report_stage(cfg: DiscoveryConfig) -> tuple[Path, Path]:
    dc = require_discover(cfg)
    rc = require_robustness(cfg)
    spec = load_grid(rc.grid)
    paths = robust_paths(rc)
    plan = _load_plan(paths)
    base: dict[str, Any] = _read_required(paths.baseline, "extract")
    saved = _load_saved(paths)
    plan_conds = [_cond_of(e) for e in plan["conditions"]]
    effective, dropped = _effective(plan_conds, saved)
    eff_by_cid = {c.cid: c for c in effective}
    entries = _entries(plan)
    tracked = _tracked_types(dc, base)
    roles = {int(k): str(v) for k, v in base["roles"].items()}

    rows: list[dict[str, Any]] = []
    records: list[tuple[str, str, np.ndarray, np.ndarray]] = []
    for plan_cond in plan_conds:
        cid = plan_cond.cid
        entry = entries[cid]
        cond = plan_cond if cid in dropped else eff_by_cid[cid]
        status, reason, metrics = _status(paths, cid, dropped)
        rows.append(_cond_row(cond, entry, status=status, reason=reason, metrics=metrics))
        if status == "completed" and metrics is not None and not cond.control:
            records.append(
                (
                    cid,
                    cond.family,
                    np.asarray(metrics["responsive_ids"], dtype=np.int64),
                    _stim_ids(entry),
                )
            )

    shuffles: list[dict[str, Any]] = []
    for draw in sorted({c.draw for c in plan_conds if c.family == "shuffle"}):
        shuffles.append(_read_required(paths.shuffle_dir(draw) / SHUFFLE_FILE, "prepare"))

    chance = _read_json(paths.chance) if paths.chance.is_file() else None
    universe = plan["parallel_universe"]
    check_rows = [
        {
            "root_id": int(e["root_id"]),
            "cell_type": str(e["cell_type"]),
            "check_ii": bool(e["check_ii"]),
        }
        for e in universe
        if str(e["cell_type"]) in tracked
    ]
    if saved is None:
        reductions: dict[str, Any] = {"steps": [], "dropped": [], "reduced": {}, "within_cap": None}
    else:
        reductions = {
            "steps": list(saved["steps"]),
            "dropped": list(saved["dropped"]),
            "reduced": dict(saved["reduced"]),
            "within_cap": saved["within_cap"],
        }

    results: dict[str, Any] = {
        "schema": 1,
        "kind": "rr-robustness",
        "data_version": cfg.version,
        "statement": robust_report.STATEMENT,
        "grid": {
            "file": spec.file,
            "sha256": spec.sha256,
            "text": spec.text,
            "deviations": [{"from_sha256": a, "reason": b} for a, b in spec.deviations],
        },
        "baseline": {k: base[k] for k in REPORT_BASELINE_KEYS},
        "check_ii": check_rows,
        "tracked_types": tracked,
        "conditions": rows,
        "reductions": reductions,
        "chance": chance,
        "shuffles": shuffles,
        "persistence": retention.persistence(records, roles=roles),
    }
    robust_report.write(results, report=rc.report, results_path=rc.results)
    return rc.report, rc.results
