"""Negative-control helpers for M6: side split, random sets, chance, degree-preserving shuffle."""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from rr_discovery import annotations
from rr_discovery.model_input import CONN_COLS
from rr_discovery.run import StimSets

UNLABELED = "unlabeled"
_LEFT = "left"
_RIGHT = "right"
_GROUPS = ("lc4", "lplc2")
_SIDES = ("left", "right", "bilateral")


class ControlsError(Exception):
    pass


def side_labels(
    ann: pd.DataFrame, ids: np.ndarray, *, left_label: str, right_label: str
) -> np.ndarray:
    labelled = annotations.labels(ann, ids)
    out: list[str] = []
    for side in labelled["side"].tolist():
        if side == left_label:
            out.append(_LEFT)
        elif side == right_label:
            out.append(_RIGHT)
        else:
            out.append(UNLABELED)
    return np.asarray(out, dtype=str)


def _unique_ids(ids: Any) -> np.ndarray:
    return np.unique(np.asarray(ids, dtype=np.int64))


def _union(arrays: Sequence[np.ndarray]) -> np.ndarray:
    if not arrays:
        return np.empty(0, dtype=np.int64)
    return np.unique(np.concatenate([np.asarray(a, dtype=np.int64) for a in arrays]))


@dataclass(frozen=True)
class SideSets:
    lc4: dict[str, np.ndarray]
    lplc2: dict[str, np.ndarray]

    def counts(self) -> dict[str, dict[str, int]]:
        return {
            "lc4": {key: int(val.size) for key, val in self.lc4.items()},
            "lplc2": {key: int(val.size) for key, val in self.lplc2.items()},
        }


def _split_group(
    ann: pd.DataFrame, ids: np.ndarray, *, left_label: str, right_label: str
) -> dict[str, np.ndarray]:
    wanted = _unique_ids(ids)
    labels = side_labels(ann, wanted, left_label=left_label, right_label=right_label)
    return {
        _LEFT: wanted[labels == _LEFT],
        _RIGHT: wanted[labels == _RIGHT],
        UNLABELED: wanted[labels == UNLABELED],
    }


def side_sets(ann: pd.DataFrame, stim: StimSets, *, left_label: str, right_label: str) -> SideSets:
    lc4 = _split_group(ann, stim.lc4, left_label=left_label, right_label=right_label)
    lplc2 = _split_group(ann, stim.lplc2, left_label=left_label, right_label=right_label)
    for name, group, split in (("lc4", stim.lc4, lc4), ("lplc2", stim.lplc2, lplc2)):
        total = sum(int(v.size) for v in split.values())
        expected = _unique_ids(group).size
        if total != expected:
            raise ControlsError(
                f"{name} side split sums to {total}, expected group size {expected}"
            )
    return SideSets(lc4=lc4, lplc2=lplc2)


def condition_stim(sides: SideSets, groups: Sequence[str], side: str) -> StimSets:
    for group in groups:
        if group not in _GROUPS:
            raise ControlsError(f"unknown stimulated group {group!r}; expected one of {_GROUPS}")
    if side not in _SIDES:
        raise ControlsError(f"unknown side {side!r}; expected one of {_SIDES}")
    keys: tuple[str, ...]
    if side == "bilateral":
        keys = (_LEFT, _RIGHT, UNLABELED)
    else:
        keys = (side,)

    def pick(split: dict[str, np.ndarray], group: str) -> np.ndarray:
        if group not in groups:
            return np.empty(0, dtype=np.int64)
        return _union([split[k] for k in keys])

    return StimSets(
        lc4=pick(sides.lc4, "lc4"),
        lplc2=pick(sides.lplc2, "lplc2"),
    )


def random_set(
    ann: pd.DataFrame,
    valid_ids: np.ndarray,
    *,
    exclude: np.ndarray,
    n_left: int,
    n_right: int,
    n_unlabeled: int,
    seed: int,
    left_label: str,
    right_label: str,
) -> np.ndarray:
    pool = np.setdiff1d(_unique_ids(valid_ids), _unique_ids(exclude))
    labels = side_labels(ann, pool, left_label=left_label, right_label=right_label)
    pools = {
        _LEFT: pool[labels == _LEFT],
        _RIGHT: pool[labels == _RIGHT],
        UNLABELED: pool[labels == UNLABELED],
    }
    requested = ((_LEFT, n_left), (_RIGHT, n_right), (UNLABELED, n_unlabeled))
    for key, n in requested:
        if pools[key].size < n:
            raise ControlsError(f"random_set: {key} pool has {pools[key].size} ids, requested {n}")
    rng = np.random.default_rng(seed)
    drawn = [rng.choice(pools[key], size=n, replace=False) for key, n in requested]
    return _union(drawn)


@dataclass(frozen=True)
class ChanceRef:
    n_draws: int
    seed: int
    set_size: int
    population_size: int
    retention_mean: float
    retention_sd: float
    retention_min: float
    retention_max: float
    jaccard_mean: float
    jaccard_sd: float
    jaccard_min: float
    jaccard_max: float

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in asdict(self).items():
            out[key] = round(value, 6) if isinstance(value, float) else value
        return out


def chance_reference(
    core: np.ndarray, population: np.ndarray, *, n_draws: int, seed: int
) -> ChanceRef:
    core_ids = _unique_ids(core)
    pop = _unique_ids(population)
    k = int(core_ids.size)
    if k == 0:
        raise ControlsError("chance_reference: core is empty")
    if k > pop.size:
        raise ControlsError(f"chance_reference: core size {k} exceeds population {pop.size}")
    rng = np.random.default_rng(seed)
    retention: list[float] = []
    jaccard: list[float] = []
    for _ in range(n_draws):
        draw = rng.choice(pop, k, replace=False)
        inter = int(np.intersect1d(draw, core_ids).size)
        retention.append(inter / k)
        jaccard.append(inter / (2 * k - inter))
    ret = np.asarray(retention, dtype=np.float64)
    jac = np.asarray(jaccard, dtype=np.float64)
    ret_sd = float(np.std(ret, ddof=1)) if n_draws > 1 else 0.0
    jac_sd = float(np.std(jac, ddof=1)) if n_draws > 1 else 0.0
    return ChanceRef(
        n_draws=n_draws,
        seed=seed,
        set_size=k,
        population_size=int(pop.size),
        retention_mean=float(np.mean(ret)),
        retention_sd=ret_sd,
        retention_min=float(np.min(ret)),
        retention_max=float(np.max(ret)),
        jaccard_mean=float(np.mean(jac)),
        jaccard_sd=jac_sd,
        jaccard_min=float(np.min(jac)),
        jaccard_max=float(np.max(jac)),
    )


@dataclass(frozen=True)
class ShuffleResult:
    post_idx: np.ndarray
    n_rounds: int
    n_attempted: int
    n_accepted: int
    n_changed_edges: int
    self_loops_before: int
    self_loops_after: int


def degree_preserving_shuffle(
    pre_idx: np.ndarray,
    post_idx: np.ndarray,
    *,
    n_nodes: int,
    seed: int,
    rounds: int,
) -> ShuffleResult:
    pre = np.asarray(pre_idx, dtype=np.int64).copy()
    post = np.asarray(post_idx, dtype=np.int64).copy()
    n_edges = int(pre.size)
    if np.unique(pre * n_nodes + post).size != n_edges:
        raise ControlsError("degree_preserving_shuffle: duplicate (pre, post) pair in input")
    post_orig = post.copy()
    self_before = int(np.sum(pre == post))
    rng = np.random.default_rng(seed)
    n_attempted = 0
    n_accepted = 0
    m = n_edges // 2
    for _ in range(rounds):
        perm = rng.permutation(n_edges)
        a = perm[:m]
        b = perm[m : 2 * m]
        ka = pre[a] * n_nodes + post[b]
        kb = pre[b] * n_nodes + post[a]
        ok = (pre[a] != post[b]) & (pre[b] != post[a])
        keys = np.sort(pre * n_nodes + post)
        for proposal in (ka, kb):
            idx = np.minimum(np.searchsorted(keys, proposal), max(keys.size - 1, 0))
            if keys.size:
                ok &= keys[idx] != proposal
        cand = np.nonzero(ok)[0]
        uniq, counts = np.unique(np.concatenate([ka[cand], kb[cand]]), return_counts=True)
        dup = uniq[counts > 1]
        ok &= ~(np.isin(ka, dup) | np.isin(kb, dup))
        n_attempted += m
        n_accepted += int(ok.sum())
        sel_a = a[ok]
        sel_b = b[ok]
        moved = post[sel_b].copy()
        post[sel_b] = post[sel_a]
        post[sel_a] = moved
    return ShuffleResult(
        post_idx=post,
        n_rounds=rounds,
        n_attempted=n_attempted,
        n_accepted=n_accepted,
        n_changed_edges=int(np.sum(post != post_orig)),
        self_loops_before=self_before,
        self_loops_after=int(np.sum(pre == post)),
    )


def check_shuffle(
    pre_before: np.ndarray,
    post_before: np.ndarray,
    syn_before: np.ndarray,
    sign_before: np.ndarray,
    pre_after: np.ndarray,
    post_after: np.ndarray,
    syn_after: np.ndarray,
    sign_after: np.ndarray,
    *,
    n_nodes: int,
) -> dict[str, int | bool]:
    pre_b = np.asarray(pre_before, dtype=np.int64)
    post_b = np.asarray(post_before, dtype=np.int64)
    syn_b = np.asarray(syn_before, dtype=np.int64)
    sign_b = np.asarray(sign_before, dtype=np.int64)
    pre_a = np.asarray(pre_after, dtype=np.int64)
    post_a = np.asarray(post_after, dtype=np.int64)
    syn_a = np.asarray(syn_after, dtype=np.int64)
    sign_a = np.asarray(sign_after, dtype=np.int64)
    k = int(max(syn_b.max(initial=0), syn_a.max(initial=0))) + 1
    sb = np.zeros(n_nodes, dtype=np.int64)
    sb[pre_b] = sign_b
    signs_ok = bool(np.array_equal(sb[pre_b], sign_b) and np.array_equal(sb[pre_a], sign_a))
    loops_before = int(np.sum(pre_b == post_b))
    loops_after = int(np.sum(pre_a == post_a))
    return {
        "out_degree_equal": bool(
            pre_b.size == pre_a.size
            and np.array_equal(
                np.bincount(pre_b, minlength=n_nodes), np.bincount(pre_a, minlength=n_nodes)
            )
        ),
        "in_degree_equal": bool(
            np.array_equal(
                np.bincount(post_b, minlength=n_nodes),
                np.bincount(post_a, minlength=n_nodes),
            )
        ),
        "syn_multiset_equal": bool(
            np.array_equal(np.sort(syn_b), np.sort(syn_a))
            and np.array_equal(np.sort(pre_b * k + syn_b), np.sort(pre_a * k + syn_a))
        ),
        "signs_follow_pre": signs_ok,
        "no_duplicates": bool(np.unique(pre_a * n_nodes + post_a).size == pre_a.size),
        "self_loops_before": loops_before,
        "self_loops_after": loops_after,
        "no_new_self_loops": bool(loops_after <= loops_before),
    }


def shuffle_tables(conn: pd.DataFrame, res: ShuffleResult) -> tuple[pd.DataFrame, pd.DataFrame]:
    pre_id = conn["Presynaptic_ID"].to_numpy(dtype=np.int64)
    post_id_orig = conn["Postsynaptic_ID"].to_numpy(dtype=np.int64)
    pre_idx = conn["Presynaptic_Index"].to_numpy(dtype=np.int64)
    post_idx_orig = conn["Postsynaptic_Index"].to_numpy(dtype=np.int64)
    conn_vals = conn["Connectivity"].to_numpy(dtype=np.int64)
    exc = conn["Excitatory"].to_numpy(dtype=np.int64)
    exc_x = conn["Excitatory x Connectivity"].to_numpy(dtype=np.int64)
    idx_all = np.concatenate([pre_idx, post_idx_orig])
    id_all = np.concatenate([pre_id, post_id_orig])
    pairs = np.unique(np.column_stack([idx_all, id_all]), axis=0)
    uniq_idx = pairs[:, 0]
    post_idx = np.asarray(res.post_idx, dtype=np.int64)
    pos = np.clip(np.searchsorted(uniq_idx, post_idx), 0, max(uniq_idx.size - 1, 0))
    if uniq_idx.size == 0 or np.any(uniq_idx[pos] != post_idx):
        raise ControlsError("shuffle_tables: shuffled post index has no root id")
    post_id = pairs[pos, 1]
    order = np.lexsort((post_idx, pre_idx))
    table: dict[str, np.ndarray] = {
        "Presynaptic_ID": pre_id[order],
        "Postsynaptic_ID": post_id[order],
        "Presynaptic_Index": pre_idx[order],
        "Postsynaptic_Index": post_idx[order],
        "Connectivity": conn_vals[order],
        "Excitatory": exc[order],
        "Excitatory x Connectivity": exc_x[order],
    }
    out = pd.DataFrame({col: table[col] for col in CONN_COLS})
    roots, inverse = np.unique(post_id, return_inverse=True)
    sums = np.zeros(roots.size, dtype=np.int64)
    np.add.at(sums, inverse, conn_vals)
    totals = pd.DataFrame({"root_id": roots.astype(np.int64), "input_total": sums})
    return out, totals
