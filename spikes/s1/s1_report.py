"""Markdown report renderer for S1 (pure function of the run results)."""

import math
from typing import Any

from numpy.typing import NDArray
from s1_frozen import (
    C1_LC4,
    C1_LPLC2,
    C1_LPLC2_OFFSET,
    CIRCUIT_ITERS_PER_RESTART,
    CIRCUIT_RESTARTS,
    COPULA_RHO,
    COST_ESCALATE,
    DT_MS,
    GRID_N,
    HIGH_NOISE_SHRINK,
    L1_COEF,
    L2_CUT,
    L2_LO,
    L2_SPAN,
    L2_STEEP,
    L2_U,
    LR_MAX_ITER,
    MLP_HIDDEN,
    MLP_STEPS,
    N0_P,
    N_SEEDS,
    N_TEST,
    N_TRAIN,
    NOISES,
    OUTCOME_CHAR,
    OUTCOMES,
    P_BASE,
    P_HIGH,
    P_LOW,
    P_VALUES,
    SCENARIOS,
    WINDOW_MS,
)
from s1_part_a import CircuitFacts

WALL_CLOCK_TARGET_S = 1800.0
MODEL_ORDER = ("circuit", "formula", "mlp", "const_reflex", "const_escalate", "oracle")

SCENARIO_DEFS: dict[str, str] = {
    "N0": f"Null: p = {N0_P} for every request, independent of the signals.",
    "L1": (
        f"Linear: logit p = {L1_COEF[0]} + {L1_COEF[1]}*(s-0.5) + {L1_COEF[2]}*(L-0.3)"
        f" + {L1_COEF[3]}*k + {L1_COEF[4]}*(b-0.5)."
    ),
    "L2": (
        f"Monotone saturating: u = {L2_U[0]}*s + {L2_U[1]}*L + {L2_U[2]}*k, "
        f"p = {L2_LO} + {L2_SPAN}*sigmoid({L2_STEEP}*(u-{L2_CUT}))."
    ),
    "X1": (
        f"Interaction (independent of the circuit): p = {P_HIGH} if s > 0.6 and (L < 0.35 or "
        f"k = 0), else {P_LOW}."
    ),
    "X2": (
        f"Band (independent of the circuit): for k = 0, p = {P_HIGH} if 0.3 < b < 0.7 and "
        f"s > 0.6; for k >= 1, p = {P_HIGH} if (s > 0.5) XOR (b > 0.5); otherwise {P_LOW}."
    ),
    "C1": (
        f"Circuit-native control: p = {P_HIGH} if the circuit map under the C1 mapping "
        f"(lc4 gains {C1_LC4}, lplc2 gains {C1_LPLC2}, lplc2 offset {C1_LPLC2_OFFSET}, "
        f"lc4 offset o*) gives gf_first, else {P_LOW}. Expected to favour the circuit; a "
        "harness check, not evidence for the hypothesis."
    ),
}

EXPECTED_TO_WIN: dict[str, str] = {
    "N0": "no",
    "L1": "no",
    "L2": "no",
    "X1": "yes, iff the nonlinearity flag is set",
    "X2": "yes, iff the nonlinearity flag is set",
    "C1": "control (expected to favour the circuit)",
}

PARAGRAPHS: dict[str, str] = {
    "GO": (
        "On these synthetic tests the circuit gate beat the formula gate where a nonlinear gate "
        "can plausibly help (X1 or X2, flagged) and did not lose where it cannot. The circuit "
        "map has distinct GF-first and parallel-first regions. This supports continuing the "
        "circuit gate. It is not evidence of a benefit on real traces."
    ),
    "REFRAME": (
        "The result does not support a clean go or stop. The circuit gate is not shown to add "
        "value over a formula gate on these synthetic tests, or the evidence is mixed or only "
        "partial. Use the per-scenario table and the cell text above to decide the framing; no "
        "consequence is applied here."
    ),
    "STOP": (
        "On these synthetic tests the circuit gate adds nothing over a formula gate in the "
        "scenarios where a nonlinear gate could help, and the circuit map does not give distinct, "
        "clean outcome regions. This is a negative result. Any cost-saving claim that depends on "
        "the circuit gate would need to be dropped, subject to the user's decision."
    ),
    "INVALID": (
        "A validity check (V1, V2 or V3) failed, so no verdict is issued. The harness must be "
        "fixed and rerun, with the rerun recorded as a deviation."
    ),
}

CONSEQUENCE: dict[str, str] = {
    "GO": (
        "Proposed, not applied: keep the circuit gate as a candidate; file an ADR-5 revision "
        "before relying on it (conditional if Part A is partial); confirm the mapping form (A5) "
        "on real traces before any claim."
    ),
    "REFRAME": (
        "Proposed, not applied: restate the circuit's role as an open question; do not make the "
        "cost-saving claim; decide the framing with the user before the next milestone."
    ),
    "STOP": (
        "Proposed, not applied: drop the cost-saving claim for the circuit gate and publish the "
        "negative result (P5); the race demotion (P-A) is a separate step after this verdict."
    ),
    "INVALID": "Proposed, not applied: none until the harness passes V1 to V3.",
}

A4_A5_LIMITS = (
    "Limits. A4: the labels are a synthetic proxy; a circuit WIN here is necessary but not "
    "sufficient evidence for a benefit on real benchmark traces (that stays with M11). A5: the "
    "stimulus mapping form is S1's own fixed-form gain and offset, not the project default "
    "(R8 / M9); a different mapping form could change the Part B results."
)


def _fmt(x: float | None, digits: int = 4) -> str:
    if x is None or math.isnan(x):
        return "n/a"
    return f"{x:.{digits}f}"


def _pct(x: float) -> str:
    return f"{100.0 * x:+.2f}%"


def _yn(flag: bool) -> str:
    return "yes" if flag else "no"


def _pf(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _map_lines(grid: NDArray[Any], rates: NDArray[Any]) -> list[str]:
    n = grid.shape[0]
    lines: list[str] = []
    for j in range(n - 1, -1, -1):
        chars = "".join(OUTCOME_CHAR[str(grid[j, i])] for i in range(n))
        label = f"{rates[j]:8.1f}" if (j % 8 == 0 or j == n - 1) else " " * 8
        lines.append(f"{label} |{chars}|")
    return lines


def _region_table(regions: dict[str, Any]) -> list[str]:
    rows = [
        "| outcome | count | fraction | regions | largest | largest share |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in OUTCOMES:
        r = regions[name]
        rows.append(
            f"| {name} | {r['count']} | {_fmt(r['fraction'])} | {r['n_regions']} | "
            f"{r['largest']} | {_fmt(r['largest_share'])} |"
        )
    return rows


def _verdict_section(facts: CircuitFacts, part_b: dict[str, Any]) -> list[str]:
    verdict = part_b["verdict"]
    v = part_b["v"]
    combined = verdict["combined"]
    lines = [
        "## 1 Verdict",
        "",
        f"Combined cell: **{combined}**",
        "",
        f"- Part A verdict (AC1 on the frozen grid): {verdict['part_a']}",
        f"- Part B verdict (AC1, base noise, P = 10): {verdict['part_b']}",
        f"- V1 (N0: neither gate beats the best constant by more than 1%): {_pf(v['v1'])}",
        f"- V2 (C1: circuit gate not a formula WIN): {_pf(v['v2'])}",
        f"- V3 (L1: formula within 2% of oracle cost): {_pf(v['v3'])}",
        f"- Validity: {'valid' if part_b['valid'] else 'INVALID (a check failed)'}",
        "",
        f"Cell text: {verdict['cell_text']}",
        "",
        PARAGRAPHS[combined],
        "",
        A4_A5_LIMITS,
        "",
    ]
    if not facts.has_parallel:
        lines += ["The parallel group is absent in this circuit (see section 4).", ""]
    return lines


def _prereg_section(meta: dict[str, Any]) -> list[str]:
    deviations = meta["deviations"]
    porcelain = meta["git_status_porcelain"]
    lines = [
        "## 2 Pre-registration",
        "",
        f"- Commit containing the frozen rule: {meta['commit']}",
        f"- Working tree of spikes/s1 at run time: "
        f"{'clean' if not porcelain else 'dirty: ' + porcelain}",
    ]
    if not deviations:
        lines.append("- Deviations: no deviations")
    else:
        lines.append("- Deviations:")
        for d in deviations:
            lines.append(f"  - {d['text']}")
        if any(d["touches_frozen"] for d in deviations):
            lines.append(
                "- A deviation touches a frozen constant: verdict non-binding until the user "
                "confirms."
            )
    lines.append("")
    return lines


def _setup_section(meta: dict[str, Any]) -> list[str]:
    wall = float(meta["wall_clock_s"])
    target_state = "within" if wall <= WALL_CLOCK_TARGET_S else "over"
    lines = [
        "## 3 Run setup",
        "",
        f"- circuit.json sha256 before: {meta['sha256_before']}",
        f"- circuit.json sha256 after: {meta['sha256_after']}",
        f"- Identical before and after: {_yn(meta['sha256_identical'])}",
        f"- Wall-clock: {wall:.1f} s (target at most {WALL_CLOCK_TARGET_S:.0f} s, "
        f"{target_state} target)",
        "- Env access in spikes/s1: none",
        f"- Network attempts: {meta['network_attempts']}",
        f"- brian2 imported: {_yn(meta['brian2_imported'])}",
        f"- Python: {meta['python']}",
        f"- numpy: {meta['numpy']}; platform: {meta['platform']}",
    ]
    repro = meta["repro"]
    if repro is None:
        lines.append("- Repro check: not requested in this run")
    else:
        lines.append("- Repro check against the earlier run (byte-identical):")
        for name, same in repro.items():
            lines.append(f"  - {name}: {'true' if same else 'false'}")
    lines.append("")
    return lines


def _facts_section(facts: CircuitFacts) -> list[str]:
    lines = [
        "## 4 Circuit facts",
        "",
        f"- Neurons: {facts.n_neurons}",
        f"- Connections: {facts.n_connections}",
        f"- output_gf group size: {facts.n_gf} (types {facts.gf_types})",
        f"- output_parallel group size: {facts.n_parallel}",
    ]
    if facts.has_parallel:
        lines.append(f"- Parallel DN types ({len(facts.parallel_types)}): {facts.parallel_types}")
    else:
        lines.append(
            "- The parallel group is absent: non-GF-first outcomes are no_fire plus any "
            "distinct simulator output."
        )
    lines.append("")
    return lines


def _part_a_section(part_a: dict[str, Any]) -> list[str]:
    stats = part_a["stats"]
    merged = part_a["merged"]
    grid = part_a["grid"]
    rates = part_a["rates"]
    lc = stats["line_changes"]
    mlc = merged["line_changes"]
    sat = stats["edge_saturation"]
    dep = stats["dependence"]
    diag = stats["diagonal"]
    det = part_a["determinism"]
    look = part_a["lookup"]
    diag_chars = "".join(OUTCOME_CHAR[o] for o in diag["outcomes"])
    if sat["capped"]:
        capped_text = "yes (the outer rows or columns are not all single-outcome)"
    else:
        capped_text = "no (each outer row and column shows a single stable outcome)"
    first_text = f" (first at {diag['first_gf_rate_hz']:.2f} Hz)" if diag["any_gf_first"] else ""
    lines = [
        "## 5 Part A map",
        "",
        f"Grid {GRID_N} x {GRID_N}, log-spaced rates from {rates[0]:.1f} Hz to "
        f"{rates[-1]:.1f} Hz on both axes. Rows are r_lplc2 (top = highest), columns are "
        "r_lc4 (left = lowest). Legend: G gf_first, P parallel_first, T tie, . no_fire.",
        "",
        "```",
        *_map_lines(grid, rates),
        "```",
        "",
        f"Part A verdict: {part_a['verdict']}",
        "",
        *_region_table(stats["regions"]),
        "",
        f"- Boundary length (adjacent pairs with different outcomes): {stats['boundary_length']}",
        f"- Max outcome changes on any row or column: {lc['max_changes']}",
        f"- Lines over 2 changes: {lc['n_over']} of {lc['n_lines']} "
        f"(fraction {_fmt(lc['fraction_over'])})",
        "",
        "Supplementary (tie merged into parallel_first; not used for the verdict):",
        "",
        *_region_table(merged["regions"]),
        "",
        f"- Boundary length (merged): {merged['boundary_length']}; max changes "
        f"{mlc['max_changes']}; fraction over 2 {_fmt(mlc['fraction_over'])}",
        "",
        f"- Edge saturation: lc4_min {sat['lc4_min']['outcomes']}, lc4_max "
        f"{sat['lc4_max']['outcomes']}, lplc2_min {sat['lplc2_min']['outcomes']}, lplc2_max "
        f"{sat['lplc2_max']['outcomes']}.",
        f"- Capped: {capped_text}",
        f"- Outcome depends on both inputs: {_yn(dep['depends_on_both'])} (rows varying along "
        f"r_lc4: {dep['rows_varying']}; columns varying along r_lplc2: {dep['cols_varying']})",
        f"- Diagonal (r_lc4 = r_lplc2) outcomes: {diag_chars}; GF-first on the diagonal "
        f"alone: {_yn(diag['any_gf_first'])}{first_text}",
        f"- Determinism spot-check: {det['n_match']} of {det['n']} re-simulated points match "
        f"exactly ({'all match' if det['all_match'] else 'mismatch'})",
        f"- Lookup agreement with direct simulation: {look['n_agree']} of {look['n']} "
        f"({_fmt(look['fraction'])})",
        "",
    ]
    return lines


def _part_b_setup_section(part_b: dict[str, Any]) -> list[str]:
    sig = part_b["signals"]
    c1 = part_b["c1"]
    budgets = part_b["budgets"]
    budget_text = (
        "the circuit budget is at least the formula budget"
        if budgets["ok"]
        else "the circuit budget is BELOW the formula budget (deviation recorded)"
    )
    lines = [
        "## 6 Part B setup",
        "",
        "Signals (R10): s = Gaussian-copula marginal in [0,1]; L = log-normal (mu log 400, "
        "sigma 1) clipped to [log 20, log 20000] and normalised to [0,1]; copula correlation "
        f"rho = {COPULA_RHO} between the Gaussian pair; k in {{0,1,2}} with probabilities "
        "(0.5, 0.3, 0.2); b uniform on [0,1]. The same signals are used across scenarios for a "
        "given seed.",
        "",
        f"Measured summary (seed 0, train n = {N_TRAIN}; test n = {N_TEST}):",
        "",
        f"- Train: mean s {_fmt(sig['train']['mean_s'])}, mean L {_fmt(sig['train']['mean_L'])}, "
        f"mean b {_fmt(sig['train']['mean_b'])}, k proportions "
        f"{[_fmt(x) for x in sig['train']['k_props']]}, corr(s, L) "
        f"{_fmt(sig['train']['corr_sL'])}",
        f"- Test: corr(s, L) {_fmt(sig['test']['corr_sL'])}, k proportions "
        f"{[_fmt(x) for x in sig['test']['k_props']]}",
        "",
        "Scenarios (R11). Base noise uses p as defined; high noise uses "
        f"p' = 0.5 + {HIGH_NOISE_SHRINK} * (p - 0.5) (pulled halfway to 0.5).",
        "",
    ]
    for scen in SCENARIOS:
        lines.append(f"- {scen}: {SCENARIO_DEFS[scen]}")
    lines += [
        "",
        "Cost model (R12): accept and correct = 1; accept and wrong = 1 + P; escalate = "
        f"{COST_ESCALATE:g}. Expected cost uses true p on the test set. P values {P_VALUES}, "
        f"base P = {P_BASE:g}. At P = 3 accepting the reflex is always cost-optimal "
        "(1 + 3 < 5), so every sensible gate converges to always-reflex; P = 3 is a "
        "sensitivity check only.",
        "",
        "Formula gate (R13): logistic regression with intercept (L2 1e-4 on the weights, "
        f"Newton-IRLS, at most {LR_MAX_ITER} iterations) on [s, L, k, b]. Threshold chosen on "
        "the training set by empirical cost (free) and as the median split of the training "
        "scores (matched: top half accepted). Budget = iterations + threshold candidates; "
        f"maximum over all fits: {budgets['formula_max']}.",
        "",
        "Circuit gate (R14): fixed circuit.json and LIFSimulator (dt "
        f"{DT_MS} ms, window {WINDOW_MS} ms). Mapping on fc = [s, L, k/2, b]: "
        "x1 = clip(theta[4] + fc . theta[0:4], 0, 3) for log10 r_lc4 and "
        "x2 = clip(theta[9] + fc . theta[5:9], 0, 3) for log10 r_lplc2; accept = gf_first, "
        "escalate otherwise, read from the 64 x 64 map (lookup, agreement in section 5). Fit: "
        f"(1+1)-ES with {CIRCUIT_RESTARTS} restarts x {CIRCUIT_ITERS_PER_RESTART} evaluations, "
        f"budget {budgets['circuit_evals']} candidate mappings. Restart 0 starts from the fixed "
        "start; the others from uniform random starts. Matched variant: objective penalised "
        "unless the accept share is within 2 points of 50%. The mapping is fit on training data "
        "only.",
        "",
        f"Budget comparison: circuit {budgets['circuit_evals']} vs formula maximum "
        f"{budgets['formula_max']}; {budget_text}.",
        "",
        f"Flexible learner (R15 ii): numpy MLP, one tanh hidden layer of {MLP_HIDDEN}, sigmoid "
        f"output, BCE with L2 1e-4, full-batch Adam (lr 0.01, betas 0.9/0.999, eps 1e-8), "
        f"{MLP_STEPS} steps, init N(0, 1/sqrt(fan_in)), on [s, L, k/2, b]. Thresholds are "
        "chosen as for the formula gate. The true-p oracle and the best constant policy "
        "(always reflex, always escalate) are reference models, not gates under test.",
        "",
        f"Sizes and seeds: train {N_TRAIN}, test {N_TEST}, {N_SEEDS} dataset seeds per scenario "
        "and noise level. Labels are Bernoulli draws from p on the training set only; test "
        "metrics use true p.",
        "",
        "C1 offset rule (frozen): among offsets -3.0 to 3.0 in steps of 0.1, pick the one whose "
        "gf_first share on 100000 reference signals is closest to 50%; ties to smaller |o|, "
        f"then smaller o. Result: o* = {c1['offset']:.1f}, gf_first share {_fmt(c1['share'])}, "
        f"degenerate: {_yn(c1['degenerate'])}"
        + (" (V2 is weak in this case)." if c1["degenerate"] else "."),
        "",
        "Nonlinearity flag (R16): set for a scenario when the MLP beats the formula gate by at "
        "least 2% relative expected cost at P = 10, base noise.",
        "",
        "| scenario | nonlinearity available | expected to be able to win |",
        "|---|---|---|",
    ]
    for scen in SCENARIOS:
        lines.append(f"| {scen} | {_yn(part_b['flags'][scen])} | {EXPECTED_TO_WIN[scen]} |")
    lines.append("")
    return lines


def _results_section(part_b: dict[str, Any]) -> list[str]:
    agg = part_b["aggregates"]
    labels = part_b["labels"]
    lines = [
        "## 7 Results",
        "",
        "Free variants unless stated; means over seeds. False-reflex is the share of accepted "
        "reflexes that are wrong (true p). The oracle and the constants have no fitted threshold "
        "and are recorded once under free.",
        "",
    ]
    for scen in SCENARIOS:
        for noise in NOISES:
            for P in P_VALUES:
                block = agg[scen][noise][f"{P:g}"]
                means = block["means"]
                cmp = block["compare"]
                lines += [
                    f"### {scen}, {noise} noise, P = {P:g}",
                    "",
                    "| model | expected cost | false-reflex | reflex share | decision acc |",
                    "|---|---:|---:|---:|---:|",
                ]
                for model in MODEL_ORDER:
                    m = means[f"{model}|free"]
                    lines.append(
                        f"| {model} | {_fmt(m['cost'])} | {_fmt(m['false_reflex'])} | "
                        f"{_fmt(m['share'])} | {_fmt(m['decision_acc'])} |"
                    )
                lines += [
                    "",
                    f"Circuit minus formula: mean diff {_fmt(cmp['mean_diff'])}, relative "
                    f"{_pct(cmp['rel'])}, 95% CI [{_fmt(cmp['ci_lo'])}, {_fmt(cmp['ci_hi'])}], "
                    f"raw label {cmp['label']}.",
                ]
                if P == P_BASE:
                    lines.append(
                        f"Effective label (P = 3 and P = 30 sign check, flag applied): "
                        f"{labels[scen][noise]['effective_p10']}."
                    )
                lines += [
                    "",
                    "Matched reflex share (each gate refit with the share within 2 points of 50%):",
                    "",
                    "| model | false-reflex | reflex share | circuit fit feasible (seeds) |",
                    "|---|---:|---:|---:|",
                ]
                for model in ("circuit", "formula", "mlp"):
                    m = means[f"{model}|matched"]
                    feas = (
                        f"{block['circuit_feasible_matched']}/{N_SEEDS}"
                        if model == "circuit"
                        else "n/a"
                    )
                    lines.append(
                        f"| {model} | {_fmt(m['false_reflex'])} | {_fmt(m['share'])} | {feas} |"
                    )
                lines.append("")
    return lines


def render(
    facts: CircuitFacts,
    part_a: dict[str, Any],
    part_b: dict[str, Any],
    meta: dict[str, Any],
) -> str:
    combined = part_b["verdict"]["combined"]
    lines: list[str] = ["# S1 go/no-go spike report", ""]
    lines += _verdict_section(facts, part_b)
    lines += _prereg_section(meta)
    lines += _setup_section(meta)
    lines += _facts_section(facts)
    lines += _part_a_section(part_a)
    lines += _part_b_setup_section(part_b)
    lines += _results_section(part_b)
    lines += ["## 8 Proposed consequence", "", CONSEQUENCE[combined], ""]
    return "\n".join(lines) + "\n"
