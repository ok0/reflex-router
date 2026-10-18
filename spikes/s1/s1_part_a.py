"""Part A: deterministic sweep of the circuit over a 64x64 log-rate grid and map statistics."""

from collections import Counter, deque
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from s1_frozen import (
    A_MAX_CHANGES_PER_LINE,
    DT_MS,
    LOG10_RATE_MAX,
    LOG10_RATE_MIN,
    OUTCOMES,
    WINDOW_MS,
)

from reflex_router.circuit import Circuit, LIFSimulator, Stimulus


@dataclass(frozen=True)
class CircuitFacts:
    n_neurons: int
    n_connections: int
    n_gf: int
    n_parallel: int
    has_parallel: bool
    parallel_types: dict[str, int]
    gf_types: dict[str, int]


def circuit_facts(circuit: Circuit) -> CircuitFacts:
    gf_idx = circuit.role_indices("output_gf")
    par_idx = circuit.role_indices("output_parallel")
    gf_types = Counter(circuit.cell_types[int(i)] for i in gf_idx)
    par_types = Counter(circuit.cell_types[int(i)] for i in par_idx)
    return CircuitFacts(
        n_neurons=circuit.n_neurons,
        n_connections=circuit.n_connections,
        n_gf=int(gf_idx.size),
        n_parallel=int(par_idx.size),
        has_parallel=bool(par_idx.size > 0),
        parallel_types=dict(sorted(par_types.items())),
        gf_types=dict(sorted(gf_types.items())),
    )


def grid_rates(n: int) -> NDArray[np.float64]:
    return 10 ** np.linspace(LOG10_RATE_MIN, LOG10_RATE_MAX, n)


@dataclass(frozen=True)
class SweepPoint:
    i: int
    j: int
    r_lc4: float
    r_lplc2: float
    outcome: str
    gf_ms: float | None
    parallel_ms: float | None
    steps: int


def sweep(sim: LIFSimulator, rates: NDArray[np.float64]) -> list[SweepPoint]:
    points: list[SweepPoint] = []
    for j in range(rates.shape[0]):
        for i in range(rates.shape[0]):
            r_lc4 = float(rates[i])
            r_lplc2 = float(rates[j])
            res = sim.first_spikes(Stimulus(r_lc4, r_lplc2))
            points.append(
                SweepPoint(
                    i=i,
                    j=j,
                    r_lc4=r_lc4,
                    r_lplc2=r_lplc2,
                    outcome=res.outcome,
                    gf_ms=res.gf_ms,
                    parallel_ms=res.parallel_ms,
                    steps=res.steps,
                )
            )
    return points


def outcome_grid(points: list[SweepPoint], n: int) -> NDArray[np.str_]:
    rows = [[""] * n for _ in range(n)]
    for p in points:
        rows[p.j][p.i] = p.outcome
    return np.array(rows, dtype=np.str_)


def _component_sizes(mask: NDArray[np.bool_]) -> list[int]:
    n_rows, n_cols = mask.shape
    seen = np.zeros(mask.shape, dtype=np.bool_)
    sizes: list[int] = []
    for r0 in range(n_rows):
        for c0 in range(n_cols):
            if not mask[r0, c0] or seen[r0, c0]:
                continue
            seen[r0, c0] = True
            queue: deque[tuple[int, int]] = deque([(r0, c0)])
            size = 0
            while queue:
                r, c = queue.popleft()
                size += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr = r + dr
                    cc = c + dc
                    if 0 <= rr < n_rows and 0 <= cc < n_cols and mask[rr, cc] and not seen[rr, cc]:
                        seen[rr, cc] = True
                        queue.append((rr, cc))
            sizes.append(size)
    return sizes


def regions(grid: NDArray[np.str_]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for outcome in OUTCOMES:
        mask = grid == outcome
        count = int(np.count_nonzero(mask))
        sizes = _component_sizes(mask)
        largest = max(sizes) if sizes else 0
        stats[outcome] = {
            "count": count,
            "fraction": count / grid.size,
            "n_regions": len(sizes),
            "largest": largest,
            "largest_share": largest / count if count else 0.0,
        }
    return stats


def boundary_length(grid: NDArray[np.str_]) -> int:
    horizontal = int(np.count_nonzero(grid[:, 1:] != grid[:, :-1]))
    vertical = int(np.count_nonzero(grid[1:, :] != grid[:-1, :]))
    return horizontal + vertical


def line_changes(grid: NDArray[np.str_]) -> dict[str, Any]:
    row_changes = np.count_nonzero(grid[:, 1:] != grid[:, :-1], axis=1)
    col_changes = np.count_nonzero(grid[1:, :] != grid[:-1, :], axis=0)
    n = grid.shape[0]
    all_changes = np.concatenate([row_changes, col_changes])
    n_lines = 2 * n
    n_over = int(np.count_nonzero(all_changes > A_MAX_CHANGES_PER_LINE))
    return {
        "row_changes": row_changes.tolist(),
        "col_changes": col_changes.tolist(),
        "max_changes": int(all_changes.max()),
        "n_lines": n_lines,
        "n_over": n_over,
        "fraction_over": n_over / n_lines,
    }


def merged_tie(grid: NDArray[np.str_]) -> NDArray[np.str_]:
    return np.where(grid == "tie", np.str_("parallel_first"), grid)


def edge_saturation(grid: NDArray[np.str_]) -> dict[str, Any]:
    edges = {
        "lc4_min": grid[:, 0],
        "lc4_max": grid[:, -1],
        "lplc2_min": grid[0, :],
        "lplc2_max": grid[-1, :],
    }
    result: dict[str, Any] = {}
    for name, cells in edges.items():
        outcomes = sorted(set(cells.tolist()))
        result[name] = {"single_outcome": len(outcomes) == 1, "outcomes": outcomes}
    result["capped"] = not all(result[name]["single_outcome"] for name in edges)
    return result


def dependence(grid: NDArray[np.str_]) -> dict[str, Any]:
    rows_varying = sum(1 for row in grid if len(set(row.tolist())) > 1)
    cols_varying = sum(1 for col in grid.T if len(set(col.tolist())) > 1)
    return {
        "rows_varying": rows_varying,
        "cols_varying": cols_varying,
        "depends_on_both": rows_varying > 0 and cols_varying > 0,
    }


def diagonal(points: list[SweepPoint], n: int) -> dict[str, Any]:
    diag = sorted((p for p in points if p.i == p.j), key=lambda p: p.i)
    diag = diag[:n]
    outcomes = [p.outcome for p in diag]
    first_gf = next((p for p in diag if p.outcome == "gf_first"), None)
    return {
        "outcomes": outcomes,
        "any_gf_first": first_gf is not None,
        "first_gf_rate_hz": first_gf.r_lc4 if first_gf is not None else None,
    }


def determinism_check(
    circuit: Circuit,
    rates: NDArray[np.float64],
    grid_points: list[SweepPoint],
    n_points: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    n = int(rates.shape[0])
    by_ij = {(p.i, p.j): p for p in grid_points}
    chosen = rng.choice(n * n, n_points, replace=False)
    fresh = LIFSimulator(circuit, dt_ms=DT_MS, window_ms=WINDOW_MS)
    n_match = 0
    for k in chosen.tolist():
        i = k % n
        j = k // n
        original = by_ij[(i, j)]
        again = fresh.first_spikes(Stimulus(float(rates[i]), float(rates[j])))
        if (
            again.outcome == original.outcome
            and again.gf_ms == original.gf_ms
            and again.parallel_ms == original.parallel_ms
            and again.steps == original.steps
        ):
            n_match += 1
    return {"n": n_points, "n_match": n_match, "all_match": n_match == n_points}


def lookup_index(log10_rate: NDArray[np.float64], n: int) -> NDArray[np.int64]:
    scaled = np.clip(log10_rate, LOG10_RATE_MIN, LOG10_RATE_MAX)
    span = LOG10_RATE_MAX - LOG10_RATE_MIN
    return np.rint(scaled / span * (n - 1)).astype(np.int64)


def lookup_agreement(
    sim: LIFSimulator,
    rates: NDArray[np.float64],
    grid: NDArray[np.str_],
    n_points: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    n = int(rates.shape[0])
    x = rng.uniform(LOG10_RATE_MIN, LOG10_RATE_MAX, (n_points, 2))
    idx = lookup_index(x, n)
    n_agree = 0
    for k in range(n_points):
        res = sim.first_spikes(Stimulus(float(10 ** x[k, 0]), float(10 ** x[k, 1])))
        looked_up = grid[int(idx[k, 1]), int(idx[k, 0])]
        if res.outcome == looked_up:
            n_agree += 1
    return {"n": n_points, "n_agree": n_agree, "fraction": n_agree / n_points}
