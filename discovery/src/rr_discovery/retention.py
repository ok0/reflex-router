"""Retention, edge, GF and parallel identity metrics for M6 conditions. Pure."""

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import pandas as pd

from rr_discovery import connfilter

NOT_IN_BASELINE = "not in baseline circuit"
_BINS: tuple[tuple[str, Fraction], ...] = (
    ("100%", Fraction(1)),
    (">=90%", Fraction(9, 10)),
    (">=75%", Fraction(3, 4)),
    (">=50%", Fraction(1, 2)),
)


def _ids(values: Any) -> set[int]:
    return set(np.asarray(values, dtype=np.int64).tolist())


def _rank(values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    n = arr.size
    order = np.argsort(arr, kind="mergesort")
    sorted_vals = arr[order]
    ranks = np.empty(n, dtype=np.float64)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 2:
        return None
    rx = _rank(x)
    ry = _rank(y)
    dx = rx - rx.mean()
    dy = ry - ry.mean()
    denom = float(np.sqrt(np.sum(dx * dx) * np.sum(dy * dy)))
    if denom == 0.0:
        return None
    return float(np.sum(dx * dy) / denom)


@dataclass(frozen=True)
class CoreMetrics:
    n_stimulated: int
    n_core_excluded: int
    reference_size: int
    retained: int
    n_new: int
    n_both: int
    core_retention: float | None
    jaccard: float | None
    spearman: float | None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in asdict(self).items():
            out[key] = round(value, 6) if isinstance(value, float) else value
        return out


def core_metrics(
    *,
    base_core: np.ndarray,
    base_rel: Mapping[int, float],
    cond_responsive: np.ndarray,
    cond_rel: Mapping[int, float],
    cond_stimulated: np.ndarray,
) -> CoreMetrics:
    stim = _ids(cond_stimulated)
    core = _ids(base_core)
    ref = core - stim
    cnd = _ids(cond_responsive) - stim
    both = ref & cnd
    union = ref | cnd
    shared = sorted(both)
    rho = spearman([base_rel[r] for r in shared], [cond_rel[r] for r in shared])
    return CoreMetrics(
        n_stimulated=len(stim),
        n_core_excluded=len(core & stim),
        reference_size=len(ref),
        retained=len(both),
        n_new=len(cnd - ref),
        n_both=len(both),
        core_retention=len(both) / len(ref) if ref else None,
        jaccard=len(both) / len(union) if union else None,
        spearman=rho,
    )


@dataclass(frozen=True)
class EdgeMetrics:
    n_members: int
    n_edges: int
    n_edges_shared: int
    edge_jaccard: float | None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in asdict(self).items():
            out[key] = round(value, 6) if isinstance(value, float) else value
        return out


def _pairs(edges: pd.DataFrame) -> set[tuple[int, int]]:
    pre = edges["pre"].to_numpy(dtype=np.int64).tolist()
    post = edges["post"].to_numpy(dtype=np.int64).tolist()
    return set(zip(pre, post, strict=True))


def edge_metrics(
    *, base_edges: pd.DataFrame, cond_members: np.ndarray, cond_edges: pd.DataFrame
) -> EdgeMetrics:
    base = _pairs(base_edges)
    cond = _pairs(cond_edges)
    shared = base & cond
    union = base | cond
    return EdgeMetrics(
        n_members=len(_ids(cond_members)),
        n_edges=len(cond),
        n_edges_shared=len(shared),
        edge_jaccard=len(shared) / len(union) if union else None,
    )


@dataclass(frozen=True)
class GFNeuron:
    root_id: int
    responsive: bool
    rate_hz: float
    rel_rate: float
    rank: int | None
    trial_frac: float


@dataclass(frozen=True)
class GFIdentity:
    ids: tuple[int, ...]
    equals_baseline: bool
    missing: tuple[GFNeuron, ...]
    extra: tuple[int, ...]


def gf_identity(
    *, gf_type_ids: np.ndarray, base_gf_ids: np.ndarray, cond_stats: pd.DataFrame
) -> GFIdentity:
    if cond_stats.empty:
        cond_stats = pd.DataFrame(
            {
                "root_id": np.empty(0, dtype=np.int64),
                "responsive": np.empty(0, dtype=bool),
                "rate_hz": np.empty(0, dtype=np.float64),
                "rel_rate": np.empty(0, dtype=np.float64),
                "rank": np.empty(0, dtype=np.int64),
                "trial_frac": np.empty(0, dtype=np.float64),
            }
        )
    responsive = _ids(cond_stats.loc[cond_stats["responsive"].astype(bool), "root_id"])
    ids = _ids(gf_type_ids) & responsive
    base = _ids(base_gf_ids)
    rows = cond_stats.set_index("root_id")
    missing: list[GFNeuron] = []
    for rid in sorted(base - ids):
        if rid in rows.index:
            row = rows.loc[rid]
            rank = int(row["rank"])
            missing.append(
                GFNeuron(
                    root_id=rid,
                    responsive=bool(row["responsive"]),
                    rate_hz=float(row["rate_hz"]),
                    rel_rate=float(row["rel_rate"]),
                    rank=rank if rank > 0 else None,
                    trial_frac=float(row["trial_frac"]),
                )
            )
        else:
            missing.append(
                GFNeuron(
                    root_id=rid,
                    responsive=False,
                    rate_hz=0.0,
                    rel_rate=0.0,
                    rank=None,
                    trial_frac=0.0,
                )
            )
    return GFIdentity(
        ids=tuple(sorted(ids)),
        equals_baseline=ids == base,
        missing=tuple(missing),
        extra=tuple(sorted(ids - base)),
    )


def direct_input_ids(
    connectivity: pd.DataFrame,
    input_totals: pd.DataFrame,
    stim_all: np.ndarray,
    candidate_ids: np.ndarray,
) -> np.ndarray:
    pre_col = connectivity["Presynaptic_ID"].to_numpy(dtype=np.int64)
    post_col = connectivity["Postsynaptic_ID"].to_numpy(dtype=np.int64)
    syn_col = connectivity["Connectivity"].to_numpy(dtype=np.int64)
    sel = np.isin(pre_col, np.asarray(stim_all, dtype=np.int64)) & np.isin(
        post_col, np.asarray(candidate_ids, dtype=np.int64)
    )
    edges = pd.DataFrame({"pre": pre_col[sel], "post": post_col[sel], "syn": syn_col[sel]})
    kept = connfilter.keep(edges, input_totals)
    sums = edges.loc[kept].groupby("post")["syn"].sum()
    return np.asarray(sums.index[sums > 0], dtype=np.int64)


@dataclass(frozen=True)
class ParallelTypeRow:
    cell_type: str
    n_baseline: int
    n_retained: int
    n_condition: int


@dataclass(frozen=True)
class ParallelIdentity:
    baseline_has_parallel: bool
    condition_ids: tuple[int, ...]
    retained_ids: tuple[int, ...]
    new_ids: tuple[int, ...]
    lost: tuple[tuple[int, str, bool, bool], ...]
    new_cell_types: tuple[str, ...]
    equals_baseline: bool
    per_type: tuple[ParallelTypeRow, ...]


def parallel_identity(
    *,
    base_parallel_ids: np.ndarray,
    eligible_ids: np.ndarray,
    cell_type_of: Mapping[int, str],
    tracked_types: Sequence[str],
    cond_responsive: np.ndarray,
    cond_members: np.ndarray,
    cond_stimulated: np.ndarray,
) -> ParallelIdentity:
    base = _ids(base_parallel_ids)
    responsive = _ids(cond_responsive)
    members = _ids(cond_members)
    stim = _ids(cond_stimulated)
    cond = (_ids(eligible_ids) & responsive & members) - stim
    retained = base & cond
    lost = base - cond
    new = cond - base
    base_types = {cell_type_of[r] for r in base}
    new_types = sorted({cell_type_of[r] for r in new} - base_types)
    lost_rows = tuple(
        (rid, cell_type_of[rid], rid in responsive, rid in members) for rid in sorted(lost)
    )
    per_type = tuple(
        ParallelTypeRow(
            cell_type=t,
            n_baseline=sum(1 for r in base if cell_type_of[r] == t),
            n_retained=sum(1 for r in retained if cell_type_of[r] == t),
            n_condition=sum(1 for r in cond if cell_type_of[r] == t),
        )
        for t in tracked_types
    )
    return ParallelIdentity(
        baseline_has_parallel=len(base) > 0,
        condition_ids=tuple(sorted(cond)),
        retained_ids=tuple(sorted(retained)),
        new_ids=tuple(sorted(new)),
        lost=lost_rows,
        new_cell_types=tuple(new_types),
        equals_baseline=cond == base,
        per_type=per_type,
    )


def persistence(
    records: Sequence[tuple[str, str, np.ndarray, np.ndarray]], *, roles: Mapping[int, str]
) -> dict[str, Any]:
    responsive_any: set[int] = set()
    for _, _, resp, _ in records:
        responsive_any |= _ids(resp)
    counts: dict[int, list[int]] = {rid: [0, 0] for rid in responsive_any}
    per_family: dict[int, dict[str, list[int]]] = {rid: {} for rid in responsive_any}
    for _, family, resp, stim in records:
        resp_set = _ids(resp)
        stim_set = _ids(stim)
        for rid in responsive_any:
            fam = per_family[rid].setdefault(family, [0, 0])
            if rid in stim_set:
                continue
            hit = 1 if rid in resp_set else 0
            fam[0] += hit
            fam[1] += 1
            counts[rid][0] += hit
            counts[rid][1] += 1

    def in_bin(frac: Fraction, label: str, bound: Fraction) -> bool:
        return frac == bound if label == "100%" else frac >= bound

    bins = [{"label": label, "count": 0} for label, _ in _BINS]
    by_role: dict[str, list[int]] = {}
    neurons: list[dict[str, Any]] = []
    for rid in sorted(responsive_any):
        r, e = counts[rid]
        role = roles.get(rid, NOT_IN_BASELINE)
        neurons.append(
            {
                "root_id": rid,
                "role": role,
                "n_responsive": r,
                "n_eligible": e,
                "per_family": {fam: list(pair) for fam, pair in sorted(per_family[rid].items())},
            }
        )
        if e == 0:
            continue
        frac = Fraction(r, e)
        role_bins = by_role.setdefault(role, [0] * len(_BINS))
        for i, (label, bound) in enumerate(_BINS):
            if in_bin(frac, label, bound):
                bins[i]["count"] += 1
                role_bins[i] += 1
    return {
        "n_conditions": len(records),
        "bins": bins,
        "by_role": by_role,
        "neurons": neurons,
    }
