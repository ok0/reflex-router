"""Responsive-neuron rule and responsive table rendering (M5, R4/R5). Pure; no I/O."""

from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pandas as pd

RULE_TEXT = (
    "responsive iff mean rate over trials >= min_rate_hz and fired in >= min_trial_frac "
    "of trials; applied to non-stimulated neurons; stimulated neurons are inputs"
)

_STATS_COLUMNS = ["root_id", "total_spikes", "trials_fired", "rate_hz", "trial_frac"]
_TABLE_HEADER = (
    "rank\troot_id\tcell_type\tside\trate_hz\trel_rate\ttrial_frac\ttotal_spikes\ttrials_fired"
)


@dataclass(frozen=True)
class ResponsiveRule:
    min_rate_hz: float = 2.0
    min_trial_frac: float = 0.5

    def __post_init__(self) -> None:
        if not self.min_rate_hz > 0:
            raise ValueError("min_rate_hz must be > 0")
        if not 0 < self.min_trial_frac <= 1:
            raise ValueError("min_trial_frac must be in (0, 1]")


def neuron_stats(counts: pd.DataFrame, *, n_trials: int, t_run_s: float) -> pd.DataFrame:
    trial = counts["trial"].to_numpy(dtype=np.int64)
    spikes = counts["n_spikes"].to_numpy(dtype=np.int64)
    if trial.size and ((trial < 0).any() or (trial >= n_trials).any()):
        raise ValueError(f"trial outside [0, {n_trials})")
    if spikes.size and (spikes <= 0).any():
        raise ValueError("n_spikes must be > 0")
    if counts.empty:
        return pd.DataFrame(
            {
                "root_id": np.empty(0, dtype=np.int64),
                "total_spikes": np.empty(0, dtype=np.int64),
                "trials_fired": np.empty(0, dtype=np.int64),
                "rate_hz": np.empty(0, dtype=np.float64),
                "trial_frac": np.empty(0, dtype=np.float64),
            }
        )
    frame = pd.DataFrame(
        {"root_id": counts["root_id"].to_numpy(dtype=np.int64), "n_spikes": spikes}
    )
    agg = (
        frame.groupby("root_id", sort=True)
        .agg(total_spikes=("n_spikes", "sum"), trials_fired=("n_spikes", "size"))
        .reset_index()
    )
    agg["total_spikes"] = agg["total_spikes"].astype(np.int64)
    agg["trials_fired"] = agg["trials_fired"].astype(np.int64)
    agg["rate_hz"] = agg["total_spikes"] / (n_trials * float(t_run_s))
    agg["trial_frac"] = agg["trials_fired"] / n_trials
    return pd.DataFrame({column: np.asarray(agg[column]) for column in _STATS_COLUMNS})


def responsive(
    counts: pd.DataFrame,
    rule: ResponsiveRule,
    *,
    n_trials: int,
    t_run_s: float,
    stimulated: np.ndarray,
) -> pd.DataFrame:
    stats = neuron_stats(counts, n_trials=n_trials, t_run_s=t_run_s)
    root = np.asarray(stats["root_id"], dtype=np.int64)
    total = np.asarray(stats["total_spikes"], dtype=np.int64)
    fired = np.asarray(stats["trials_fired"], dtype=np.int64)
    rate = np.asarray(stats["rate_hz"], dtype=np.float64)
    frac = np.asarray(stats["trial_frac"], dtype=np.float64)
    keep_rows = ~np.isin(root, np.asarray(stimulated, dtype=np.int64))
    root = root[keep_rows]
    total = total[keep_rows]
    fired = fired[keep_rows]
    rate = rate[keep_rows]
    frac = frac[keep_rows]

    t_run = Fraction(repr(float(t_run_s)))
    min_rate = Fraction(repr(float(rule.min_rate_hz)))
    min_frac = Fraction(repr(float(rule.min_trial_frac)))
    resp = np.array(
        [
            Fraction(int(tot)) / (n_trials * t_run) >= min_rate
            and Fraction(int(fi), n_trials) >= min_frac
            for tot, fi in zip(total.tolist(), fired.tolist(), strict=True)
        ],
        dtype=bool,
    )

    rate_max = float(rate.max()) if rate.size else 1.0
    rel = rate / rate_max

    order = np.lexsort((root, -rel))
    root = root[order]
    total = total[order]
    fired = fired[order]
    rate = rate[order]
    frac = frac[order]
    rel = rel[order]
    resp = resp[order]
    rank = np.zeros(root.size, dtype=np.int64)
    rank[resp] = np.arange(1, int(resp.sum()) + 1, dtype=np.int64)
    return pd.DataFrame(
        {
            "root_id": root,
            "total_spikes": total,
            "trials_fired": fired,
            "rate_hz": rate,
            "rel_rate": rel,
            "trial_frac": frac,
            "responsive": resp,
            "rank": rank,
        }
    )


def render_responsive_table(stats: pd.DataFrame, labels: pd.DataFrame) -> str:
    lookup = {
        int(root): (str(cell_type), str(side))
        for root, cell_type, side in zip(
            np.asarray(labels["root_id"]).tolist(),
            np.asarray(labels["cell_type"]).tolist(),
            np.asarray(labels["side"]).tolist(),
            strict=True,
        )
    }
    lines = [_TABLE_HEADER]
    rank_all = np.asarray(stats["rank"], dtype=np.int64)
    responsive_all = np.asarray(stats["responsive"], dtype=bool)
    idx = np.flatnonzero(responsive_all)
    idx = idx[np.argsort(rank_all[idx], kind="stable")]
    rank = rank_all[idx]
    root_ids = np.asarray(stats["root_id"], dtype=np.int64)[idx]
    rate_all = np.asarray(stats["rate_hz"], dtype=np.float64)[idx]
    rel_all = np.asarray(stats["rel_rate"], dtype=np.float64)[idx]
    frac_all = np.asarray(stats["trial_frac"], dtype=np.float64)[idx]
    total_all = np.asarray(stats["total_spikes"], dtype=np.int64)[idx]
    fired_all = np.asarray(stats["trials_fired"], dtype=np.int64)[idx]
    for rank_i, root, rate, rel, frac, total, fired in zip(
        rank.tolist(),
        root_ids.tolist(),
        rate_all.tolist(),
        rel_all.tolist(),
        frac_all.tolist(),
        total_all.tolist(),
        fired_all.tolist(),
        strict=True,
    ):
        cell_type, side = lookup.get(int(root), ("", ""))
        lines.append(
            f"{rank_i}\t{root}\t{cell_type}\t{side}\t"
            f"{rate:.6f}\t{rel:.6f}\t{frac:.6f}\t{int(total)}\t{int(fired)}"
        )
    return "\n".join(lines) + "\n"
