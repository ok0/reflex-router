"""Tests for the S1 spike: map statistics, verdict logic, statistics, synthetic data and gates."""

from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from s1_frozen import (
    NOISES,
    OUTCOME_CHAR,
    OUTCOMES,
    P_VALUES,
    RNG_BOOT,
    RNG_CIRCUIT_FIT,
    RNG_DET_CHECK,
    RNG_MLP,
    ROOT_SEED,
    SCENARIOS,
)
from s1_gates import (
    choose_threshold,
    const_escalate,
    const_reflex,
    fit_circuit,
    fit_formula,
    fit_mlp,
    metrics,
    oracle,
)
from s1_part_a import (
    boundary_length,
    determinism_check,
    grid_rates,
    line_changes,
    regions,
    sweep,
)
from s1_synth import (
    apply_noise,
    circuit_features,
    features,
    make_dataset,
    mapping_outcomes,
    p_true,
    signals,
)
from s1_verdict import (
    combined,
    compare,
    effective_label,
    part_a_verdict,
    part_b_verdict,
)

from reflex_router.circuit import LIFSimulator
from reflex_router.testing.circuits import demo_race_spec, write_and_load

INV_OUTCOME_CHAR = {char: outcome for outcome, char in OUTCOME_CHAR.items()}


def _grid(rows: list[str]) -> NDArray[np.str_]:
    return np.array([[INV_OUTCOME_CHAR[ch] for ch in row] for row in rows], dtype=np.str_)


def _region_stats(
    gf_fraction: float,
    gf_count: int,
    gf_n_regions: int,
    gf_largest_share: float,
    pf_fraction: float,
    pf_count: int,
    pf_largest_share: float,
    ns_fraction: float,
    ns_n_regions: int,
) -> dict[str, Any]:
    return {
        "regions": {
            "gf_first": {
                "count": gf_count,
                "fraction": gf_fraction,
                "n_regions": gf_n_regions,
                "largest": 0,
                "largest_share": gf_largest_share,
            },
            "parallel_first": {
                "count": pf_count,
                "fraction": pf_fraction,
                "n_regions": 1,
                "largest": 0,
                "largest_share": pf_largest_share,
            },
            "tie": {
                "count": 0,
                "fraction": 0.0,
                "n_regions": 0,
                "largest": 0,
                "largest_share": 0.0,
            },
            "no_fire": {
                "count": int(ns_fraction * 4096),
                "fraction": ns_fraction,
                "n_regions": ns_n_regions,
                "largest": 0,
                "largest_share": 1.0,
            },
        },
        "line_changes": {"fraction_over": 0.0},
    }


def _passing_stats() -> dict[str, Any]:
    return _region_stats(
        gf_fraction=0.5,
        gf_count=2048,
        gf_n_regions=1,
        gf_largest_share=1.0,
        pf_fraction=0.3,
        pf_count=1228,
        pf_largest_share=1.0,
        ns_fraction=0.2,
        ns_n_regions=1,
    )


def _c1_stub(sig: dict[str, NDArray[Any]]) -> NDArray[np.str_]:
    return np.where(sig["s"] > 0.5, "gf_first", "parallel_first")


def _truth_lookup(theta: NDArray[np.float64], grid: NDArray[np.str_], n: int) -> Any:
    def lookup(sig: dict[str, NDArray[Any]]) -> NDArray[np.str_]:
        return mapping_outcomes(theta, circuit_features(sig), grid, n)

    return lookup


def _l1_costs(P: float) -> dict[str, float]:
    scen_idx = SCENARIOS.index("L1")
    noise_idx = NOISES.index("base")
    seed = 0
    ds = make_dataset("L1", "base", seed, None)
    p = ds.p_test
    oracle_acc = oracle(p, P)
    n = len(p)

    fit = fit_formula(features(ds.train_sig), ds.y_train, P)
    formula_acc = features(ds.test_sig) @ fit.w > fit.t

    mlp = fit_mlp(
        circuit_features(ds.train_sig),
        ds.y_train,
        np.random.default_rng([ROOT_SEED, RNG_MLP, scen_idx, noise_idx, seed]),
    )
    t_mlp, _ = choose_threshold(mlp.predict(circuit_features(ds.train_sig)), ds.y_train, P)
    mlp_acc = mlp.predict(circuit_features(ds.test_sig)) > t_mlp

    return {
        "oracle": metrics(oracle_acc, p, P, oracle_acc)["cost"],
        "formula": metrics(formula_acc, p, P, oracle_acc)["cost"],
        "mlp": metrics(mlp_acc, p, P, oracle_acc)["cost"],
        "const_reflex": metrics(const_reflex(n), p, P, oracle_acc)["cost"],
        "const_escalate": metrics(const_escalate(n), p, P, oracle_acc)["cost"],
    }


def test_regions_boundary_changes() -> None:
    grid = _grid(["GGP", "GTP", "..P"])
    stats = regions(grid)
    assert stats["gf_first"]["count"] == 3
    assert stats["gf_first"]["n_regions"] == 1
    assert stats["gf_first"]["largest"] == 3
    assert stats["parallel_first"]["count"] == 3
    assert stats["parallel_first"]["n_regions"] == 1
    assert stats["tie"]["count"] == 1
    assert stats["no_fire"]["count"] == 2
    assert stats["no_fire"]["n_regions"] == 1
    assert boundary_length(grid) == 7
    changes = line_changes(grid)
    assert changes["row_changes"] == [1, 2, 1]
    assert changes["col_changes"] == [1, 2, 0]
    assert changes["max_changes"] == 2
    assert changes["n_over"] == 0


def test_two_regions() -> None:
    grid = _grid(["G.G"] * 3)
    gf = regions(grid)["gf_first"]
    assert gf["n_regions"] == 2
    assert gf["largest_share"] == 0.5


def test_part_a_verdict() -> None:
    assert part_a_verdict(_passing_stats(), has_parallel=True) == "A_PASS"

    small_parallel = _region_stats(
        gf_fraction=0.5,
        gf_count=2048,
        gf_n_regions=1,
        gf_largest_share=1.0,
        pf_fraction=0.03,
        pf_count=123,
        pf_largest_share=1.0,
        ns_fraction=0.2,
        ns_n_regions=1,
    )
    assert part_a_verdict(small_parallel, has_parallel=True) == "A_PARTIAL"

    over = _passing_stats()
    over["line_changes"]["fraction_over"] = 0.25
    assert part_a_verdict(over, has_parallel=True) == "A_PARTIAL"

    no_parallel = _region_stats(
        gf_fraction=0.5,
        gf_count=2048,
        gf_n_regions=1,
        gf_largest_share=1.0,
        pf_fraction=0.0,
        pf_count=0,
        pf_largest_share=0.0,
        ns_fraction=0.5,
        ns_n_regions=1,
    )
    assert part_a_verdict(no_parallel, has_parallel=True) == "A_FAIL"

    no_parallel_group = _region_stats(
        gf_fraction=0.5,
        gf_count=2048,
        gf_n_regions=1,
        gf_largest_share=1.0,
        pf_fraction=0.0,
        pf_count=0,
        pf_largest_share=0.0,
        ns_fraction=0.2,
        ns_n_regions=1,
    )
    assert part_a_verdict(no_parallel_group, has_parallel=False) == "A_PARTIAL"

    all_no_fire = _region_stats(
        gf_fraction=0.0,
        gf_count=0,
        gf_n_regions=0,
        gf_largest_share=0.0,
        pf_fraction=0.0,
        pf_count=0,
        pf_largest_share=0.0,
        ns_fraction=1.0,
        ns_n_regions=1,
    )
    assert part_a_verdict(all_no_fire, has_parallel=False) == "A_FAIL"


def test_part_b_verdict_and_normalisation() -> None:
    base = {"L1": "tie", "L2": "tie", "X1": "tie", "X2": "tie"}
    assert part_b_verdict({**base, "X1": "circuit_win"}) == "B_WIN"
    assert part_b_verdict({**base, "X1": "circuit_win", "L1": "formula_win"}) == "B_MIXED"
    assert part_b_verdict({**base, "X2": "formula_win"}) == "B_LOSE"
    assert part_b_verdict(base) == "B_TIE"

    assert effective_label("circuit_win", 0.01, -0.1, "X1", True) == "tie"
    assert effective_label("circuit_win", 0.0, -0.1, "X1", False) == "tie"
    assert effective_label("circuit_win", 0.0, -0.1, "L1", True) == "tie"
    assert effective_label("circuit_win", 0.0, -0.1, "X1", True) == "circuit_win"


def test_combined() -> None:
    assert combined("A_PASS", "B_WIN", True, False)[0] == "GO"
    conditional = combined("A_PARTIAL", "B_WIN", True, False)
    assert conditional[0] == "GO"
    assert "conditional" in conditional[1]
    assert combined("A_FAIL", "B_WIN", True, False)[0] == "REFRAME"
    assert combined("A_FAIL", "B_TIE", True, True)[0] == "STOP"
    assert combined("A_PASS", "B_TIE", True, False)[0] == "REFRAME"
    assert combined("A_PASS", "B_WIN", False, False)[0] == "INVALID"


def test_compare_labels_and_bootstrap_deterministic() -> None:
    c_formula = np.full(100, 5.0)
    assert compare(c_formula - 0.5, c_formula, np.random.default_rng(0))["label"] == "circuit_win"
    assert compare(c_formula + 0.5, c_formula, np.random.default_rng(0))["label"] == "formula_win"
    alternating = np.tile(np.array([0.01, -0.01]), 50)
    assert compare(c_formula + alternating, c_formula, np.random.default_rng(0))["label"] == "tie"

    noisy = np.random.default_rng(1).normal(4.0, 1.0, 100)
    first = compare(noisy, c_formula, np.random.default_rng([ROOT_SEED, RNG_BOOT, 0, 0, 0]))
    second = compare(noisy, c_formula, np.random.default_rng([ROOT_SEED, RNG_BOOT, 0, 0, 0]))
    assert first["ci_lo"] == second["ci_lo"]
    assert first["ci_hi"] == second["ci_hi"]


def test_signals_distribution() -> None:
    sig = signals(np.random.default_rng(0), 200_000)
    assert np.all((sig["s"] >= 0.0) & (sig["s"] <= 1.0))
    assert np.all((sig["L"] >= 0.0) & (sig["L"] <= 1.0))
    for value, expected in zip((0, 1, 2), (0.5, 0.3, 0.2), strict=True):
        assert abs(float(np.mean(sig["k"] == value)) - expected) <= 0.01
    corr = float(np.corrcoef(sig["s"], sig["L"])[0, 1])
    assert -0.35 <= corr <= -0.25
    assert abs(float(np.mean(sig["b"])) - 0.5) <= 0.01


def test_p_true_ranges_and_noise() -> None:
    sig = signals(np.random.default_rng(0), 1000)
    for scenario in SCENARIOS:
        p = p_true(scenario, sig, c1_lookup=_c1_stub)
        assert np.all((p >= 0.0) & (p <= 1.0)), scenario
    assert np.all(p_true("N0", sig, c1_lookup=None) == 0.7)
    p = p_true("L1", sig, c1_lookup=None)
    np.testing.assert_allclose(apply_noise(p, "high"), 0.5 + 0.5 * (p - 0.5))


def test_oracle_is_lower_bound() -> None:
    costs = _l1_costs(10.0)
    for name in ("formula", "mlp", "const_reflex", "const_escalate"):
        assert costs["oracle"] <= costs[name], name


def test_formula_fits_linear() -> None:
    costs = _l1_costs(10.0)
    assert (costs["formula"] - costs["oracle"]) / costs["oracle"] <= 0.03


def test_circuit_fit_recovers_native_rule() -> None:
    n = 64
    grid = np.empty((n, n), dtype=np.str_)
    for j in range(n):
        for i in range(n):
            grid[j, i] = "gf_first" if i > j else "parallel_first"
    theta_true = np.array([1.0, -0.5, 0.0, 0.5, 1.0, -0.5, 0.5, 0.0, 0.5, 1.0])
    ds = make_dataset("C1", "base", 0, _truth_lookup(theta_true, grid, n))
    p_idx = P_VALUES.index(10.0)
    rng_key = [
        ROOT_SEED,
        RNG_CIRCUIT_FIT,
        SCENARIOS.index("C1"),
        NOISES.index("base"),
        p_idx,
        0,
        0,
    ]
    fit = fit_circuit(circuit_features(ds.train_sig), ds.y_train, 10.0, grid, n, rng_key, False)
    assert fit.evals == 4000
    again = fit_circuit(circuit_features(ds.train_sig), ds.y_train, 10.0, grid, n, rng_key, False)
    np.testing.assert_array_equal(fit.theta, again.theta)

    oracle_acc = oracle(ds.p_test, 10.0)
    acc = mapping_outcomes(fit.theta, circuit_features(ds.test_sig), grid, n) == "gf_first"
    cost = metrics(acc, ds.p_test, 10.0, oracle_acc)["cost"]
    oracle_cost = metrics(oracle_acc, ds.p_test, 10.0, oracle_acc)["cost"]
    assert cost <= 1.05 * oracle_cost


def test_sweep_deterministic_tiny(tmp_path: Path) -> None:
    circuit = write_and_load(tmp_path, demo_race_spec())
    sim = LIFSimulator(circuit)
    rates = grid_rates(5)
    first = sweep(sim, rates)
    second = sweep(sim, rates)
    assert first == second
    assert all(point.outcome in OUTCOMES for point in first)
    check = determinism_check(
        circuit,
        rates,
        first,
        5,
        np.random.default_rng([ROOT_SEED, RNG_DET_CHECK]),
    )
    assert check["all_match"]
