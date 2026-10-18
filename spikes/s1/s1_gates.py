"""Decision gates (oracle, constants, formula, MLP, circuit) and their fitting procedures for S1."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from s1_frozen import (
    ADAM_BETAS,
    ADAM_EPS,
    CIRCUIT_ITERS_PER_RESTART,
    CIRCUIT_RESTARTS,
    COST_CORRECT,
    COST_ESCALATE,
    ES_DECAY,
    ES_SIGMA0,
    GAIN_BOUNDS,
    INIT_GAIN_RANGE,
    INIT_OFFSET_RANGE,
    LR_L2,
    LR_MAX_ITER,
    LR_TOL,
    MATCHED_SHARE,
    MATCHED_TOL,
    MLP_HIDDEN,
    MLP_L2,
    MLP_LR,
    MLP_STEPS,
    N_TRAIN,
    OFFSET_BOUNDS,
    THETA0,
)
from s1_synth import mapping_outcomes

_INFEASIBLE_BASE = 1e9


@dataclass(frozen=True)
class FormulaFit:
    w: NDArray[np.float64]
    t: float
    t_matched: float
    budget: int


@dataclass(frozen=True)
class CircuitFit:
    theta: NDArray[np.float64]
    train_cost: float
    evals: int
    feasible: bool


@dataclass(frozen=True)
class MLP:
    W1: NDArray[np.float64]
    b1: NDArray[np.float64]
    W2: NDArray[np.float64]
    b2: float

    def predict(self, X: NDArray[np.float64]) -> NDArray[np.float64]:
        h = np.tanh(X @ self.W1 + self.b1)
        return 1.0 / (1.0 + np.exp(-(h @ self.W2 + self.b2)))


def train_cost(acc: NDArray[np.bool_], y: NDArray[np.int8], P: float) -> float:
    yf = y.astype(np.float64)
    return float(np.mean(np.where(acc, COST_CORRECT + P * (1.0 - yf), COST_ESCALATE)))


def metrics(
    acc: NDArray[np.bool_],
    p: NDArray[np.float64],
    P: float,
    oracle_acc: NDArray[np.bool_],
) -> dict[str, float]:
    cost = float(np.mean(np.where(acc, COST_CORRECT + P * (1.0 - p), COST_ESCALATE)))
    n_acc = int(np.sum(acc))
    if n_acc == 0:
        false_reflex = float("nan")
    else:
        false_reflex = float(np.sum(acc.astype(np.float64) * (1.0 - p)) / n_acc)
    return {
        "cost": cost,
        "false_reflex": false_reflex,
        "share": float(np.mean(acc)),
        "decision_acc": float(np.mean(acc == oracle_acc)),
    }


def oracle(p: NDArray[np.float64], P: float) -> NDArray[np.bool_]:
    return COST_CORRECT + P * (1.0 - p) < COST_ESCALATE


def const_reflex(n: int) -> NDArray[np.bool_]:
    return np.ones(n, dtype=np.bool_)


def const_escalate(n: int) -> NDArray[np.bool_]:
    return np.zeros(n, dtype=np.bool_)


def fit_logistic(
    X: NDArray[np.float64], y: NDArray[np.int8]
) -> tuple[NDArray[np.float64], float, int]:
    xa = np.column_stack([X, np.ones(len(X))])
    yf = y.astype(np.float64)
    pen = np.array([2.0 * LR_L2] * 4 + [0.0])
    beta = np.zeros(5)
    for it in range(1, LR_MAX_ITER + 1):
        mu = 1.0 / (1.0 + np.exp(-(xa @ beta)))
        grad = xa.T @ (yf - mu) - pen * beta
        hess = (xa * (mu * (1.0 - mu))[:, None]).T @ xa + np.diag(pen)
        delta = np.linalg.solve(hess, grad)
        beta = beta + delta
        if float(np.max(np.abs(delta))) < LR_TOL:
            return beta[:4].copy(), float(beta[4]), it
    return beta[:4].copy(), float(beta[4]), LR_MAX_ITER


def choose_threshold(
    score: NDArray[np.float64], y: NDArray[np.int8], P: float
) -> tuple[float, int]:
    uniq = np.unique(score)
    mids = (uniq[:-1] + uniq[1:]) / 2.0
    candidates = np.concatenate([[-np.inf], mids, [np.inf]])
    costs = np.array([train_cost(score > t, y, P) for t in candidates])
    return float(candidates[int(np.argmin(costs))]), len(candidates)


def matched_threshold(score: NDArray[np.float64]) -> float:
    ss = np.sort(score)
    return float((ss[N_TRAIN // 2 - 1] + ss[N_TRAIN // 2]) / 2.0)


def fit_formula(X: NDArray[np.float64], y: NDArray[np.int8], P: float) -> FormulaFit:
    w, _, iters = fit_logistic(X, y)
    score = X @ w
    t, n_candidates = choose_threshold(score, y, P)
    return FormulaFit(
        w=w,
        t=t,
        t_matched=matched_threshold(score),
        budget=iters + n_candidates,
    )


def fit_mlp(X: NDArray[np.float64], y: NDArray[np.int8], rng: np.random.Generator) -> MLP:
    n_in = X.shape[1]
    n = len(X)
    yf = y.astype(np.float64)
    W1 = rng.normal(0.0, 1.0 / np.sqrt(n_in), (n_in, MLP_HIDDEN))
    W2 = rng.normal(0.0, 1.0 / np.sqrt(MLP_HIDDEN), MLP_HIDDEN)
    b1 = np.zeros(MLP_HIDDEN)
    b2 = np.zeros(1)
    params: list[NDArray[np.float64]] = [W1, b1, W2, b2]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    beta1, beta2 = ADAM_BETAS
    for t in range(1, MLP_STEPS + 1):
        W1, b1, W2, b2 = params
        h = np.tanh(X @ W1 + b1)
        z = h @ W2 + b2[0]
        p = 1.0 / (1.0 + np.exp(-z))
        dz = (p - yf) / n
        gW2 = h.T @ dz + 2.0 * MLP_L2 * W2
        gb2 = np.array([float(np.sum(dz))])
        dpre = np.outer(dz, W2) * (1.0 - h * h)
        gW1 = X.T @ dpre + 2.0 * MLP_L2 * W1
        gb1 = np.sum(dpre, axis=0)
        grads = [gW1, gb1, gW2, gb2]
        for idx in range(4):
            m[idx] = beta1 * m[idx] + (1.0 - beta1) * grads[idx]
            v[idx] = beta2 * v[idx] + (1.0 - beta2) * grads[idx] ** 2
            mhat = m[idx] / (1.0 - beta1**t)
            vhat = v[idx] / (1.0 - beta2**t)
            params[idx] = params[idx] - MLP_LR * mhat / (np.sqrt(vhat) + ADAM_EPS)
    W1, b1, W2, b2 = params
    return MLP(W1=W1, b1=b1, W2=W2, b2=float(b2[0]))


def _circuit_bounds() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    lo = np.array(
        [GAIN_BOUNDS[0]] * 4 + [OFFSET_BOUNDS[0]] + [GAIN_BOUNDS[0]] * 4 + [OFFSET_BOUNDS[0]]
    )
    hi = np.array(
        [GAIN_BOUNDS[1]] * 4 + [OFFSET_BOUNDS[1]] + [GAIN_BOUNDS[1]] * 4 + [OFFSET_BOUNDS[1]]
    )
    return lo, hi


def _circuit_objective(
    theta: NDArray[np.float64],
    fc: NDArray[np.float64],
    y: NDArray[np.int8],
    P: float,
    grid: NDArray[np.str_],
    n: int,
    matched: bool,
) -> tuple[float, float]:
    acc = mapping_outcomes(theta, fc, grid, n) == "gf_first"
    cost = train_cost(acc, y, P)
    if matched:
        gap = abs(float(np.mean(acc)) - MATCHED_SHARE)
        if gap > MATCHED_TOL:
            return _INFEASIBLE_BASE + gap, cost
    return cost, cost


def fit_circuit(
    fc: NDArray[np.float64],
    y: NDArray[np.int8],
    P: float,
    grid: NDArray[np.str_],
    n: int,
    rng_key: list[int],
    matched: bool,
) -> CircuitFit:
    lo, hi = _circuit_bounds()
    init_lo = np.array(
        [INIT_GAIN_RANGE[0]] * 4
        + [INIT_OFFSET_RANGE[0]]
        + [INIT_GAIN_RANGE[0]] * 4
        + [INIT_OFFSET_RANGE[0]]
    )
    init_hi = np.array(
        [INIT_GAIN_RANGE[1]] * 4
        + [INIT_OFFSET_RANGE[1]]
        + [INIT_GAIN_RANGE[1]] * 4
        + [INIT_OFFSET_RANGE[1]]
    )
    best_obj = float("inf")
    best_cost = float("inf")
    best_theta = np.array(THETA0, dtype=np.float64)
    for r in range(CIRCUIT_RESTARTS):
        rng = np.random.default_rng(rng_key + [r])
        if r == 0:
            theta = np.array(THETA0, dtype=np.float64)
        else:
            theta = rng.uniform(init_lo, init_hi)
        obj, cost = _circuit_objective(theta, fc, y, P, grid, n, matched)
        sigma = ES_SIGMA0
        for _ in range(CIRCUIT_ITERS_PER_RESTART - 1):
            cand = np.clip(theta + sigma * rng.standard_normal(theta.shape), lo, hi)
            cand_obj, cand_cost = _circuit_objective(cand, fc, y, P, grid, n, matched)
            if cand_obj <= obj:
                theta, obj, cost = cand, cand_obj, cand_cost
            sigma *= ES_DECAY
        if obj < best_obj:
            best_obj, best_cost, best_theta = obj, cost, theta
    return CircuitFit(
        theta=best_theta,
        train_cost=best_cost,
        evals=CIRCUIT_RESTARTS * CIRCUIT_ITERS_PER_RESTART,
        feasible=best_obj < _INFEASIBLE_BASE,
    )
