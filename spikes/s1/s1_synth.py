"""Synthetic signals, true reflex-success probabilities, labels and circuit mapping for S1."""

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from s1_frozen import (
    C1_DEGENERATE_BOUNDS,
    C1_LC4,
    C1_LPLC2,
    C1_LPLC2_OFFSET,
    C1_OFFSET_CANDIDATES,
    C1_REF_N,
    COPULA_RHO,
    HIGH_NOISE_SHRINK,
    L1_COEF,
    L2_CUT,
    L2_LO,
    L2_SPAN,
    L2_STEEP,
    L2_U,
    L_LOG_HI,
    L_LOG_LO,
    L_LOG_MU,
    L_LOG_SIGMA,
    N0_P,
    N_TEST,
    N_TRAIN,
    NOISES,
    P_HIGH,
    P_LOW,
    RISK_PROBS,
    RNG_C1_REF,
    RNG_LABELS,
    RNG_TEST_SIGNALS,
    RNG_TRAIN_SIGNALS,
    ROOT_SEED,
    SCENARIOS,
    X1_L_CUT,
    X1_S_CUT,
    X2_BAND,
    X2_S_CUT_K0,
    X2_XOR_CUT,
)
from s1_part_a import lookup_index

_erf = np.vectorize(math.erf, otypes=[np.float64])


@dataclass(frozen=True)
class Dataset:
    train_sig: dict[str, NDArray[Any]]
    test_sig: dict[str, NDArray[Any]]
    p_train: NDArray[np.float64]
    p_test: NDArray[np.float64]
    y_train: NDArray[np.int8]


def signals(rng: np.random.Generator, n: int) -> dict[str, NDArray[Any]]:
    z = rng.multivariate_normal([0.0, 0.0], [[1.0, COPULA_RHO], [COPULA_RHO, 1.0]], n)
    s = 0.5 * (1.0 + _erf(z[:, 0] / math.sqrt(2.0)))
    log_l = L_LOG_MU + L_LOG_SIGMA * z[:, 1]
    lval = np.clip((log_l - L_LOG_LO) / (L_LOG_HI - L_LOG_LO), 0.0, 1.0)
    k = rng.choice(3, n, p=RISK_PROBS)
    b = rng.uniform(0.0, 1.0, n)
    return {"s": s, "L": lval, "k": k, "b": b}


def features(sig: dict[str, NDArray[Any]]) -> NDArray[np.float64]:
    return np.column_stack([sig["s"], sig["L"], sig["k"].astype(np.float64), sig["b"]]).astype(
        np.float64
    )


def circuit_features(sig: dict[str, NDArray[Any]]) -> NDArray[np.float64]:
    return np.column_stack(
        [sig["s"], sig["L"], sig["k"].astype(np.float64) / 2.0, sig["b"]]
    ).astype(np.float64)


def _sigmoid(x: NDArray[np.float64]) -> NDArray[np.float64]:
    return 1.0 / (1.0 + np.exp(-x))


def c1_theta(offset: float) -> NDArray[np.float64]:
    return np.array([*C1_LC4, offset, *C1_LPLC2, C1_LPLC2_OFFSET], dtype=np.float64)


def mapping_outcomes(
    theta: NDArray[np.float64],
    fc: NDArray[np.float64],
    grid: NDArray[np.str_],
    n: int,
) -> NDArray[np.str_]:
    x1 = np.clip(theta[4] + fc @ theta[0:4], 0.0, 3.0)
    x2 = np.clip(theta[9] + fc @ theta[5:9], 0.0, 3.0)
    return grid[lookup_index(x2, n), lookup_index(x1, n)]


def p_true(
    scenario: str,
    sig: dict[str, NDArray[Any]],
    *,
    c1_lookup: Callable[[dict[str, NDArray[Any]]], NDArray[np.str_]] | None,
) -> NDArray[np.float64]:
    s = sig["s"]
    lval = sig["L"]
    k = sig["k"]
    b = sig["b"]
    n = len(s)
    if scenario == "N0":
        return np.full(n, N0_P, dtype=np.float64)
    if scenario == "L1":
        logit = (
            L1_COEF[0]
            + L1_COEF[1] * (s - 0.5)
            + L1_COEF[2] * (lval - 0.3)
            + L1_COEF[3] * k
            + L1_COEF[4] * (b - 0.5)
        )
        return _sigmoid(logit)
    if scenario == "L2":
        u = L2_U[0] * s + L2_U[1] * lval + L2_U[2] * k + L2_U[3] * b
        return L2_LO + L2_SPAN * _sigmoid(L2_STEEP * (u - L2_CUT))
    if scenario == "X1":
        high = (s > X1_S_CUT) & ((lval < X1_L_CUT) | (k == 0))
        return np.where(high, P_HIGH, P_LOW).astype(np.float64)
    if scenario == "X2":
        high = np.where(
            k == 0,
            (s > X2_S_CUT_K0) & (b > X2_BAND[0]) & (b < X2_BAND[1]),
            np.logical_xor(s > X2_XOR_CUT, b > 0.5),
        )
        return np.where(high, P_HIGH, P_LOW).astype(np.float64)
    if scenario == "C1":
        if c1_lookup is None:
            raise ValueError("C1 scenario requires c1_lookup")
        high = c1_lookup(sig) == "gf_first"
        return np.where(high, P_HIGH, P_LOW).astype(np.float64)
    raise ValueError(f"unknown scenario: {scenario}")


def apply_noise(p: NDArray[np.float64], noise: str) -> NDArray[np.float64]:
    if noise == "base":
        return p
    if noise == "high":
        return 0.5 + HIGH_NOISE_SHRINK * (p - 0.5)
    raise ValueError(f"unknown noise: {noise}")


def labels(rng: np.random.Generator, p: NDArray[np.float64]) -> NDArray[np.int8]:
    return (rng.uniform(0.0, 1.0, len(p)) < p).astype(np.int8)


def make_dataset(
    scenario: str,
    noise: str,
    seed: int,
    c1_lookup: Callable[[dict[str, NDArray[Any]]], NDArray[np.str_]] | None,
) -> Dataset:
    scen_idx = SCENARIOS.index(scenario)
    noise_idx = NOISES.index(noise)
    train_sig = signals(np.random.default_rng([ROOT_SEED, RNG_TRAIN_SIGNALS, seed]), N_TRAIN)
    test_sig = signals(np.random.default_rng([ROOT_SEED, RNG_TEST_SIGNALS, seed]), N_TEST)
    p_train = apply_noise(p_true(scenario, train_sig, c1_lookup=c1_lookup), noise)
    p_test = apply_noise(p_true(scenario, test_sig, c1_lookup=c1_lookup), noise)
    rng = np.random.default_rng([ROOT_SEED, RNG_LABELS, scen_idx, noise_idx, seed])
    y_train = labels(rng, p_train)
    return Dataset(
        train_sig=train_sig,
        test_sig=test_sig,
        p_train=p_train,
        p_test=p_test,
        y_train=y_train,
    )


def c1_offset(grid: NDArray[np.str_], n: int) -> tuple[float, float, bool]:
    rng = np.random.default_rng([ROOT_SEED, RNG_C1_REF])
    fc = circuit_features(signals(rng, C1_REF_N))
    best: tuple[tuple[float, float, float], float, float] | None = None
    for o in C1_OFFSET_CANDIDATES:
        share = float(np.mean(mapping_outcomes(c1_theta(o), fc, grid, n) == "gf_first"))
        key = (abs(share - 0.5), abs(o), o)
        if best is None or key < best[0]:
            best = (key, o, share)
    if best is None:
        raise ValueError("no C1 offset candidates")
    _, o_star, share_star = best
    lo, hi = C1_DEGENERATE_BOUNDS
    degenerate = share_star <= lo or share_star >= hi
    return o_star, share_star, degenerate


def signal_summary(sig: dict[str, NDArray[Any]]) -> dict[str, Any]:
    s = sig["s"]
    lval = sig["L"]
    k = sig["k"]
    b = sig["b"]
    return {
        "n": int(len(s)),
        "mean_s": float(np.mean(s)),
        "sd_s": float(np.std(s)),
        "mean_L": float(np.mean(lval)),
        "sd_L": float(np.std(lval)),
        "mean_b": float(np.mean(b)),
        "sd_b": float(np.std(b)),
        "k_props": [float(np.mean(k == v)) for v in (0, 1, 2)],
        "corr_sL": float(np.corrcoef(s, lval)[0, 1]),
    }
