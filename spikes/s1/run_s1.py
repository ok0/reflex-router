"""S1 driver: network guard, Part A sweep, Part B gate comparison, tables and report."""

import argparse
import dataclasses
import hashlib
import json
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import s1_frozen as fz
from numpy.typing import NDArray
from s1_gates import (
    choose_threshold,
    const_escalate,
    const_reflex,
    fit_circuit,
    fit_formula,
    fit_mlp,
    matched_threshold,
    metrics,
    oracle,
    train_cost,
)
from s1_part_a import (
    CircuitFacts,
    SweepPoint,
    boundary_length,
    circuit_facts,
    dependence,
    determinism_check,
    diagonal,
    edge_saturation,
    grid_rates,
    line_changes,
    lookup_agreement,
    merged_tie,
    outcome_grid,
    regions,
    sweep,
)
from s1_report import render
from s1_synth import (
    c1_offset,
    c1_theta,
    circuit_features,
    features,
    make_dataset,
    mapping_outcomes,
    signal_summary,
)
from s1_verdict import (
    combined,
    compare,
    effective_label,
    nonlinearity_available,
    part_a_verdict,
    part_b_verdict,
    v1,
    v2,
    v3,
    validity,
)

from reflex_router.circuit import Circuit, LIFSimulator, load_circuit

NETWORK_ATTEMPTS: list[str] = []
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / ".ensemble" / "milestones" / "S1"
REPRO_FILES = ("part_a_map.csv", "part_a_stats.json", "part_b_results.csv", "part_b_summary.json")
WALL_CLOCK_TARGET_S = 1800.0
EXIT_SHA_MISMATCH = 2
MODEL_VARIANTS: tuple[tuple[str, str], ...] = (
    ("circuit", "free"),
    ("circuit", "matched"),
    ("formula", "free"),
    ("formula", "matched"),
    ("mlp", "free"),
    ("mlp", "matched"),
    ("oracle", "free"),
    ("const_reflex", "free"),
    ("const_escalate", "free"),
)
ROW_FIELDS = (
    "scenario",
    "noise",
    "P",
    "seed",
    "model",
    "variant",
    "cost",
    "false_reflex",
    "share",
    "decision_acc",
    "train_cost",
    "fit_evals",
    "feasible",
)
MAP_FIELDS = ("i", "j", "r_lc4_hz", "r_lplc2_hz", "outcome", "gf_ms", "parallel_ms", "steps")


def _install_network_guard() -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        NETWORK_ATTEMPTS.append("attempt")
        raise RuntimeError("network disabled in S1")

    socket_cls: Any = socket.socket
    socket_mod: Any = socket
    socket_cls.connect = _blocked
    socket_mod.create_connection = _blocked


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return format(value, ".17g")
    return str(value)


def _csv(header: tuple[str, ...], rows: list[list[Any]]) -> str:
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(_cell(v) for v in row))
    return "\n".join(lines) + "\n"


def _json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def _mean(values: NDArray[np.float64]) -> float:
    finite = values[~np.isnan(values)]
    return float(np.mean(finite)) if finite.size else float("nan")


def _run_part_a(circuit: Circuit, sim: LIFSimulator) -> tuple[CircuitFacts, dict[str, Any]]:
    facts = circuit_facts(circuit)
    rates = grid_rates(fz.GRID_N)
    points: list[SweepPoint] = sweep(sim, rates)
    grid = outcome_grid(points, fz.GRID_N)
    stats: dict[str, Any] = {
        "regions": regions(grid),
        "boundary_length": boundary_length(grid),
        "line_changes": line_changes(grid),
        "edge_saturation": edge_saturation(grid),
        "dependence": dependence(grid),
        "diagonal": diagonal(points, fz.GRID_N),
    }
    verdict = part_a_verdict(stats, facts.has_parallel)
    merged_grid = merged_tie(grid)
    merged: dict[str, Any] = {
        "regions": regions(merged_grid),
        "boundary_length": boundary_length(merged_grid),
        "line_changes": line_changes(merged_grid),
    }
    det = determinism_check(
        circuit,
        rates,
        points,
        fz.N_DETERMINISM_POINTS,
        np.random.default_rng([fz.ROOT_SEED, fz.RNG_DET_CHECK]),
    )
    look = lookup_agreement(
        sim,
        rates,
        grid,
        fz.N_LOOKUP_AGREEMENT_POINTS,
        np.random.default_rng([fz.ROOT_SEED, fz.RNG_LOOKUP_CHECK]),
    )
    part_a: dict[str, Any] = {
        "stats": stats,
        "merged": merged,
        "determinism": det,
        "lookup": look,
        "verdict": verdict,
        "grid": grid,
        "rates": rates,
        "points": points,
    }
    return facts, part_a


def _map_csv(points: list[SweepPoint]) -> str:
    rows: list[list[Any]] = [
        [p.i, p.j, p.r_lc4, p.r_lplc2, p.outcome, p.gf_ms, p.parallel_ms, p.steps]
        for p in sorted(points, key=lambda p: (p.j, p.i))
    ]
    return _csv(MAP_FIELDS, rows)


def _c1_lookup(grid: NDArray[np.str_], offset: float) -> Any:
    theta = c1_theta(offset)

    def lookup(sig: dict[str, NDArray[Any]]) -> NDArray[np.str_]:
        return mapping_outcomes(theta, circuit_features(sig), grid, fz.GRID_N)

    return lookup


def _row_sort_key(r: dict[str, Any]) -> tuple[int, int, float, int, int]:
    return (
        fz.SCENARIOS.index(r["scenario"]),
        fz.NOISES.index(r["noise"]),
        float(r["P"]),
        int(r["seed"]),
        MODEL_VARIANTS.index((r["model"], r["variant"])),
    )


def _row(
    base: dict[str, Any],
    *,
    model: str,
    variant: str,
    acc_te: NDArray[np.bool_],
    acc_tr: NDArray[np.bool_],
    p_te: NDArray[np.float64],
    y: NDArray[np.int8],
    oracle_te: NDArray[np.bool_],
    fit_evals: int,
    feasible: bool | None,
) -> dict[str, Any]:
    P = float(base["P"])
    m = metrics(acc_te, p_te, P, oracle_te)
    return {
        **base,
        "model": model,
        "variant": variant,
        "cost": m["cost"],
        "false_reflex": m["false_reflex"],
        "share": m["share"],
        "decision_acc": m["decision_acc"],
        "train_cost": train_cost(acc_tr, y, P),
        "fit_evals": fit_evals,
        "feasible": feasible,
    }


def _run_part_b(
    grid: NDArray[np.str_], c1_offset_value: float
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    lookup = _c1_lookup(grid, c1_offset_value)
    rows: list[dict[str, Any]] = []
    formula_budgets: list[int] = []
    signals_info: dict[str, Any] = {}
    for scen_idx, scen in enumerate(fz.SCENARIOS):
        for noise_idx, noise in enumerate(fz.NOISES):
            for seed in range(fz.N_SEEDS):
                ds = make_dataset(scen, noise, seed, lookup)
                if scen == "N0" and noise == "base" and seed == 0:
                    signals_info = {
                        "train": signal_summary(ds.train_sig),
                        "test": signal_summary(ds.test_sig),
                    }
                y = ds.y_train
                X_tr = features(ds.train_sig)
                X_te = features(ds.test_sig)
                fc_tr = circuit_features(ds.train_sig)
                fc_te = circuit_features(ds.test_sig)
                mlp = fit_mlp(
                    fc_tr,
                    y,
                    np.random.default_rng([fz.ROOT_SEED, fz.RNG_MLP, scen_idx, noise_idx, seed]),
                )
                mlp_tr = mlp.predict(fc_tr)
                mlp_te = mlp.predict(fc_te)
                t_mlp_matched = matched_threshold(mlp_tr)
                for p_idx, P in enumerate(fz.P_VALUES):
                    base: dict[str, Any] = {"scenario": scen, "noise": noise, "P": P, "seed": seed}
                    oracle_te = oracle(ds.p_test, P)
                    oracle_tr = oracle(ds.p_train, P)
                    n_test = len(ds.p_test)
                    n_train = len(y)
                    for matched in (False, True):
                        key = [
                            fz.ROOT_SEED,
                            fz.RNG_CIRCUIT_FIT,
                            scen_idx,
                            noise_idx,
                            p_idx,
                            seed,
                            int(matched),
                        ]
                        fit_c = fit_circuit(fc_tr, y, P, grid, fz.GRID_N, key, matched)
                        acc_te = mapping_outcomes(fit_c.theta, fc_te, grid, fz.GRID_N) == "gf_first"
                        acc_tr = mapping_outcomes(fit_c.theta, fc_tr, grid, fz.GRID_N) == "gf_first"
                        rows.append(
                            _row(
                                base,
                                model="circuit",
                                variant="matched" if matched else "free",
                                acc_te=acc_te,
                                acc_tr=acc_tr,
                                p_te=ds.p_test,
                                y=y,
                                oracle_te=oracle_te,
                                fit_evals=fit_c.evals,
                                feasible=fit_c.feasible if matched else None,
                            )
                        )
                    fit_f = fit_formula(X_tr, y, P)
                    formula_budgets.append(fit_f.budget)
                    sc_tr = X_tr @ fit_f.w
                    sc_te = X_te @ fit_f.w
                    for variant, thr in (("free", fit_f.t), ("matched", fit_f.t_matched)):
                        rows.append(
                            _row(
                                base,
                                model="formula",
                                variant=variant,
                                acc_te=sc_te > thr,
                                acc_tr=sc_tr > thr,
                                p_te=ds.p_test,
                                y=y,
                                oracle_te=oracle_te,
                                fit_evals=fit_f.budget,
                                feasible=None,
                            )
                        )
                    t_mlp, _ = choose_threshold(mlp_tr, y, P)
                    for variant, thr in (("free", t_mlp), ("matched", t_mlp_matched)):
                        rows.append(
                            _row(
                                base,
                                model="mlp",
                                variant=variant,
                                acc_te=mlp_te > thr,
                                acc_tr=mlp_tr > thr,
                                p_te=ds.p_test,
                                y=y,
                                oracle_te=oracle_te,
                                fit_evals=fz.MLP_STEPS,
                                feasible=None,
                            )
                        )
                    rows.append(
                        _row(
                            base,
                            model="oracle",
                            variant="free",
                            acc_te=oracle_te,
                            acc_tr=oracle_tr,
                            p_te=ds.p_test,
                            y=y,
                            oracle_te=oracle_te,
                            fit_evals=0,
                            feasible=None,
                        )
                    )
                    rows.append(
                        _row(
                            base,
                            model="const_reflex",
                            variant="free",
                            acc_te=const_reflex(n_test),
                            acc_tr=const_reflex(n_train),
                            p_te=ds.p_test,
                            y=y,
                            oracle_te=oracle_te,
                            fit_evals=0,
                            feasible=None,
                        )
                    )
                    rows.append(
                        _row(
                            base,
                            model="const_escalate",
                            variant="free",
                            acc_te=const_escalate(n_test),
                            acc_tr=const_escalate(n_train),
                            p_te=ds.p_test,
                            y=y,
                            oracle_te=oracle_te,
                            fit_evals=0,
                            feasible=None,
                        )
                    )
    rows.sort(key=_row_sort_key)
    return rows, signals_info, max(formula_budgets)


def _vals(
    groups: dict[tuple[str, str, float, str, str], list[dict[str, Any]]],
    scen: str,
    noise: str,
    P: float,
    model: str,
    variant: str,
    field: str,
) -> NDArray[np.float64]:
    group = groups[(scen, noise, P, model, variant)]
    return np.array([float(r[field]) for r in group], dtype=np.float64)


def _summarize_part_b(
    rows: list[dict[str, Any]],
    signals_info: dict[str, Any],
    c1_info: dict[str, Any],
    formula_max: int,
    part_a_label: str,
) -> dict[str, Any]:
    groups: dict[tuple[str, str, float, str, str], list[dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault((r["scenario"], r["noise"], float(r["P"]), r["model"], r["variant"]), [])
        groups[(r["scenario"], r["noise"], float(r["P"]), r["model"], r["variant"])].append(r)

    def cost(scen: str, noise: str, P: float, model: str, variant: str) -> NDArray[np.float64]:
        return _vals(groups, scen, noise, P, model, variant, "cost")

    cmp_all: dict[tuple[str, str, float], dict[str, Any]] = {}
    for scen_idx, scen in enumerate(fz.SCENARIOS):
        for noise_idx, noise in enumerate(fz.NOISES):
            for p_idx, P in enumerate(fz.P_VALUES):
                res = compare(
                    cost(scen, noise, P, "circuit", "free"),
                    cost(scen, noise, P, "formula", "free"),
                    np.random.default_rng([fz.ROOT_SEED, fz.RNG_BOOT, scen_idx, noise_idx, p_idx]),
                )
                cmp_all[(scen, noise, P)] = {
                    "mean_diff": float(res["mean_diff"]),
                    "rel": float(res["rel"]),
                    "ci_lo": float(res["ci_lo"]),
                    "ci_hi": float(res["ci_hi"]),
                    "label": str(res["label"]),
                }

    flags: dict[str, bool] = {}
    for scen in fz.SCENARIOS:
        flags[scen] = bool(
            nonlinearity_available(
                cost(scen, "base", fz.P_BASE, "mlp", "free"),
                cost(scen, "base", fz.P_BASE, "formula", "free"),
            )
        )

    labels: dict[str, dict[str, dict[str, Any]]] = {}
    for scen in fz.SCENARIOS:
        labels[scen] = {}
        for noise in fz.NOISES:
            c3 = cmp_all[(scen, noise, 3.0)]
            c10 = cmp_all[(scen, noise, 10.0)]
            c30 = cmp_all[(scen, noise, 30.0)]
            labels[scen][noise] = {
                "P3": c3["label"],
                "P10": c10["label"],
                "P30": c30["label"],
                "effective_p10": effective_label(
                    c10["label"], c3["mean_diff"], c30["mean_diff"], scen, flags[scen]
                ),
            }

    agg: dict[str, Any] = {}
    for scen in fz.SCENARIOS:
        agg[scen] = {}
        for noise in fz.NOISES:
            agg[scen][noise] = {}
            for P in fz.P_VALUES:
                means: dict[str, dict[str, float]] = {}
                for model, variant in MODEL_VARIANTS:
                    means[f"{model}|{variant}"] = {
                        field: _mean(_vals(groups, scen, noise, P, model, variant, field))
                        for field in ("cost", "false_reflex", "share", "decision_acc")
                    }
                feasible_count = sum(
                    1 for r in groups[(scen, noise, P, "circuit", "matched")] if r["feasible"]
                )
                agg[scen][noise][f"{P:g}"] = {
                    "means": means,
                    "compare": cmp_all[(scen, noise, P)],
                    "circuit_feasible_matched": feasible_count,
                }

    c_gate_means: dict[tuple[float, str], dict[str, float]] = {}
    c_best_const_means: dict[tuple[float, str], float] = {}
    for P in fz.P_VALUES:
        for noise in fz.NOISES:
            c_gate_means[(P, noise)] = {
                "circuit": _mean(cost("N0", noise, P, "circuit", "free")),
                "formula": _mean(cost("N0", noise, P, "formula", "free")),
            }
            c_best_const_means[(P, noise)] = min(
                _mean(cost("N0", noise, P, "const_reflex", "free")),
                _mean(cost("N0", noise, P, "const_escalate", "free")),
            )
    v1_ok = bool(v1(c_gate_means, c_best_const_means))
    c1_label = labels["C1"]["base"]["P10"]
    v2_ok = bool(v2(c1_label))
    v3_ok = bool(
        v3(
            cost("L1", "base", fz.P_BASE, "formula", "free"),
            cost("L1", "base", fz.P_BASE, "oracle", "free"),
        )
    )
    valid = bool(validity(v1_ok, v2_ok, v3_ok))

    eff_base = {sc: labels[sc]["base"]["effective_p10"] for sc in ("L1", "L2", "X1", "X2")}
    part_b_v = part_b_verdict(eff_base)
    c1_circuit_win = labels["C1"]["base"]["P10"] == "circuit_win"
    combined_v, cell_text = combined(part_a_label, part_b_v, valid, c1_circuit_win)

    circuit_evals = fz.CIRCUIT_RESTARTS * fz.CIRCUIT_ITERS_PER_RESTART
    return {
        "signals": signals_info,
        "c1": c1_info,
        "budgets": {
            "formula_max": formula_max,
            "circuit_evals": circuit_evals,
            "ok": bool(circuit_evals >= formula_max),
        },
        "flags": flags,
        "labels": labels,
        "aggregates": agg,
        "v": {"v1": v1_ok, "v2": v2_ok, "v3": v3_ok},
        "valid": valid,
        "verdict": {
            "part_a": part_a_label,
            "part_b": part_b_v,
            "combined": combined_v,
            "cell_text": cell_text,
        },
    }


def _part_b_tables(rows: list[dict[str, Any]]) -> str:
    return _csv(ROW_FIELDS, [[r[f] for f in ROW_FIELDS] for r in rows])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the S1 go/no-go spike.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--repro-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    out_dir: Path = args.out_dir
    repro_dir: Path | None = args.repro_dir

    _install_network_guard()
    t0 = time.perf_counter()
    commit = _git("rev-parse", "HEAD")
    porcelain = _git("status", "--porcelain", "--", "spikes/s1")

    circuit_dir = REPO_ROOT / fz.CIRCUIT_DIR
    sha_before = _sha256(circuit_dir / "circuit.json")
    if sha_before != fz.EXPECTED_CIRCUIT_SHA256:
        print(
            f"circuit.json sha256 {sha_before} != expected {fz.EXPECTED_CIRCUIT_SHA256}",
            file=sys.stderr,
        )
        return EXIT_SHA_MISMATCH

    circuit = load_circuit(circuit_dir)
    sim = LIFSimulator(circuit, dt_ms=fz.DT_MS, window_ms=fz.WINDOW_MS)
    facts, part_a = _run_part_a(circuit, sim)

    grid = part_a["grid"]
    offset, share, degenerate = c1_offset(grid, fz.GRID_N)
    c1_info = {"offset": offset, "share": share, "degenerate": degenerate}
    rows, signals_info, formula_max = _run_part_b(grid, offset)
    part_b = _summarize_part_b(rows, signals_info, c1_info, formula_max, part_a["verdict"])

    sha_after = _sha256(circuit_dir / "circuit.json")
    brian2_imported = "brian2" in sys.modules
    wall = time.perf_counter() - t0

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "part_a_map.csv").write_text(_map_csv(part_a["points"]))
    part_a_json = {
        "facts": dataclasses.asdict(facts),
        "stats": part_a["stats"],
        "verdict": part_a["verdict"],
        "supplementary_tie_merged": part_a["merged"],
        "determinism": part_a["determinism"],
        "lookup_agreement": part_a["lookup"],
        "grid": {
            "n": fz.GRID_N,
            "log10_rate_min": fz.LOG10_RATE_MIN,
            "log10_rate_max": fz.LOG10_RATE_MAX,
            "dt_ms": fz.DT_MS,
            "window_ms": fz.WINDOW_MS,
        },
    }
    (out_dir / "part_a_stats.json").write_text(_json(part_a_json))
    (out_dir / "part_b_results.csv").write_text(_part_b_tables(rows))
    (out_dir / "part_b_summary.json").write_text(_json(part_b))

    deviations: list[dict[str, Any]] = []
    if porcelain:
        deviations.append({"text": "spike files uncommitted at run time", "touches_frozen": False})
    if not part_b["budgets"]["ok"]:
        deviations.append(
            {
                "text": "circuit fitting budget below the formula maximum (recorded)",
                "touches_frozen": True,
            }
        )

    repro: dict[str, bool] | None = None
    if repro_dir is not None:
        repro = {}
        for name in REPRO_FILES:
            other = repro_dir / name
            repro[name] = other.is_file() and other.read_bytes() == (out_dir / name).read_bytes()

    meta: dict[str, Any] = {
        "commit": commit,
        "git_status_porcelain": porcelain,
        "sha256_before": sha_before,
        "sha256_after": sha_after,
        "sha256_identical": sha_before == sha_after,
        "expected_sha256": fz.EXPECTED_CIRCUIT_SHA256,
        "wall_clock_s": wall,
        "wall_clock_target_s": WALL_CLOCK_TARGET_S,
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "brian2_imported": brian2_imported,
        "network_attempts": len(NETWORK_ATTEMPTS),
        "deviations": deviations,
        "repro": repro,
    }
    (out_dir / "run_meta.json").write_text(_json(meta))

    report = render(facts, part_a, part_b, meta)
    (out_dir / "report.md").write_text(report)
    print(f"S1 done: {part_b['verdict']['combined']} ({part_b['verdict']['cell_text']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
