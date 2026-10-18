"""Statistics and pre-registered verdict logic for S1 (pure functions, no I/O)."""

from typing import Any

import numpy as np
from numpy.typing import NDArray
from s1_frozen import (
    A_MAX_FRACTION_LINES_OVER,
    A_MIN_FRACTION,
    A_MIN_LARGEST_REGION_SHARE,
    N_BOOT,
    NONLIN_REL,
    V1_REL,
    V3_REL,
    WIN_REL,
)


def bootstrap_ci(
    diffs: NDArray[np.float64], rng: np.random.Generator, n_boot: int
) -> tuple[float, float]:
    idx = rng.integers(0, len(diffs), (n_boot, len(diffs)))
    means = diffs[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def compare(
    c_circuit: NDArray[np.float64], c_formula: NDArray[np.float64], rng: np.random.Generator
) -> dict[str, Any]:
    diff = c_circuit - c_formula
    mean_diff = float(np.mean(diff))
    rel = mean_diff / float(np.mean(c_formula))
    ci_lo, ci_hi = bootstrap_ci(diff, rng, N_BOOT)
    if rel <= -WIN_REL and ci_hi < 0:
        label = "circuit_win"
    elif rel >= WIN_REL and ci_lo > 0:
        label = "formula_win"
    else:
        label = "tie"
    return {
        "diff": diff,
        "mean_diff": mean_diff,
        "rel": rel,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "label": label,
    }


def nonlinearity_available(c_mlp: NDArray[np.float64], c_formula: NDArray[np.float64]) -> bool:
    gap = (float(np.mean(c_formula)) - float(np.mean(c_mlp))) / float(np.mean(c_formula))
    return gap >= NONLIN_REL


def part_a_verdict(stats: dict[str, Any], has_parallel: bool) -> str:
    regions = stats["regions"]
    gf = regions["gf_first"]
    pf = regions["parallel_first"]
    ns = regions["no_fire"]
    fraction_over = stats["line_changes"]["fraction_over"]
    if (
        gf["fraction"] >= A_MIN_FRACTION
        and pf["fraction"] >= A_MIN_FRACTION
        and gf["largest_share"] >= A_MIN_LARGEST_REGION_SHARE
        and pf["largest_share"] >= A_MIN_LARGEST_REGION_SHARE
        and fraction_over < A_MAX_FRACTION_LINES_OVER
    ):
        return "A_PASS"
    if has_parallel and gf["fraction"] >= A_MIN_FRACTION and pf["count"] > 0:
        return "A_PARTIAL"
    if (
        not has_parallel
        and gf["fraction"] >= A_MIN_FRACTION
        and ns["fraction"] >= A_MIN_FRACTION
        and gf["n_regions"] == 1
        and ns["n_regions"] == 1
    ):
        return "A_PARTIAL"
    return "A_FAIL"


def effective_label(
    label_p10: str,
    mean_diff_p3: float,
    mean_diff_p30: float,
    scenario: str,
    flagged: bool,
) -> str:
    if label_p10 == "circuit_win":
        if scenario in ("X1", "X2") and flagged and mean_diff_p3 <= 0 and mean_diff_p30 <= 0:
            return "circuit_win"
        return "tie"
    if label_p10 == "formula_win":
        if mean_diff_p3 >= 0 and mean_diff_p30 >= 0:
            return "formula_win"
        return "tie"
    return "tie"


def part_b_verdict(eff: dict[str, str]) -> str:
    cw = eff.get("X1") == "circuit_win" or eff.get("X2") == "circuit_win"
    fw_l = eff.get("L1") == "formula_win" or eff.get("L2") == "formula_win"
    fw_x = eff.get("X1") == "formula_win" or eff.get("X2") == "formula_win"
    if cw and fw_l:
        return "B_MIXED"
    if cw:
        return "B_WIN"
    if fw_l or fw_x:
        return "B_LOSE"
    return "B_TIE"


def validity(v1_ok: bool, v2_ok: bool, v3_ok: bool) -> bool:
    return v1_ok and v2_ok and v3_ok


def combined(a: str, b: str, valid: bool, c1_circuit_win: bool) -> tuple[str, str]:
    if not valid:
        return "INVALID", "INVALID: a validity check (V1, V2 or V3) failed; no verdict."
    if a == "A_PASS" and b == "B_WIN":
        return "GO", "GO: Part A passes (AC1) and Part B shows a circuit win."
    if a == "A_PARTIAL" and b == "B_WIN":
        return (
            "GO",
            "GO (conditional): Part A partial and Part B circuit win; ADR-5 revision required.",
        )
    if a == "A_FAIL" and b in ("B_TIE", "B_LOSE"):
        return "STOP", "STOP: Part A fails (AC1) and Part B shows no circuit win."
    text = f"REFRAME: {a} with {b} matches the AC1 REFRAME clause (no GO or STOP row)."
    if c1_circuit_win and b != "B_WIN":
        text += " Circuit wins only in C1."
    return "REFRAME", text


def v1(
    c_gate_means: dict[tuple[float, str], dict[str, float]],
    c_best_const_means: dict[tuple[float, str], float],
) -> bool:
    return all(
        (best - c_gate_means[key][gate]) / best <= V1_REL
        for key, best in c_best_const_means.items()
        for gate in ("circuit", "formula")
    )


def v2(label_c1_p10_base: str) -> bool:
    return label_c1_p10_base != "formula_win"


def v3(c_formula: NDArray[np.float64], c_oracle: NDArray[np.float64]) -> bool:
    gap = (float(np.mean(c_formula)) - float(np.mean(c_oracle))) / float(np.mean(c_oracle))
    return gap <= V3_REL
