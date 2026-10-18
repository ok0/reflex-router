from __future__ import annotations

import json
import re
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

STATEMENT = (
    "Retention numbers in this report are published as measured. M6 sets no retention threshold "
    "and gives no pass/fail verdict on the circuit. The PAC2 threshold is set by the Verifier and "
    "finalized at Gate 1 (M11)."
)
FORBIDDEN = re.compile(r"(?i)\b(pass|passes|passed|fail|fails|verdict)\b")
STEP_TEXT = {
    "drop_interaction": "Step 1: the interaction family (R7) was dropped.",
    "controls_to": "Step 2: random-set and shuffle controls were cut to {n} draws each.",
    "trials_to": "Step 3: trials of non-baseline conditions not yet run were cut to {n}.",
}
RUN_COST_TEXT = (
    "Per-condition and total wall times are kept out of this file for byte reproducibility; "
    "they are in the git-ignored run log discover/robustness/run_log.json and summarized in "
    "discovery/README.md next to the pre-run estimate."
)
NO_ROLE = "not in baseline circuit"
NA = "n/a"


def _round(obj: Any) -> Any:
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, Mapping):
        return {str(k): _round(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v) for v in obj]
    return obj


def _yn(value: Any) -> str:
    return "yes" if value else "no"


def _f(value: Any) -> str:
    return NA if value is None else f"{float(value):.4f}"


def _n(value: Any) -> str:
    return NA if value is None else str(value)


def _ids(ids: Sequence[Any]) -> str:
    return ", ".join(str(i) for i in ids) or "none"


def _table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _ordered(conditions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(conditions, key=lambda c: bool(c["control"]))


def _grid_section(results: dict[str, Any]) -> list[str]:
    grid = results["grid"]
    lines = [
        "## Grid and configuration",
        "",
        f"Grid file: `{grid['file']}`",
        "",
        f"sha256: `{grid['sha256']}`",
        "",
        "```toml",
        grid["text"].rstrip("\n"),
        "```",
        "",
        "Deviations from the frozen grid:",
        "",
    ]
    if grid["deviations"]:
        lines += [f"- from `{d['from_sha256']}`: {d['reason']}" for d in grid["deviations"]]
    else:
        lines.append("None.")
    lines.append("")
    return lines


def _side_text(side_counts: dict[str, dict[str, int]]) -> str:
    parts = []
    for group in sorted(side_counts):
        sides = side_counts[group]
        parts.append(f"{group} " + ", ".join(f"{s} {sides[s]}" for s in sorted(sides)))
    return "; ".join(parts) or NA


def _baseline_section(results: dict[str, Any]) -> list[str]:
    base = results["baseline"]
    return [
        "## Baseline sanity",
        "",
        f"- source: {base['source']}",
        f"- spikes sha256: `{base['spikes_sha256']}`",
        f"- seed base {base['seed_base']}, {base['n_trials']} trials, "
        f"rate {_f(base['rate_hz'])} Hz",
        f"- responsive neurons {base['n_responsive']}, core size {base['core_size']}, "
        f"members {base['n_members']}, edges {base['n_edges']}",
        f"- side counts: {_side_text(base['side_counts'])}",
        f"- GF ids: {_ids(base['gf_ids'])}",
        f"- parallel ids: {_ids(base['parallel_ids'])}",
        f"- parallel cell types: {_ids(base['parallel_cell_types'])}",
        f"- circuit sha256: `{base['circuit_sha256']}`",
        f"- matches the committed M5 circuit: {_yn(base['matches_m5'])}",
        "",
    ]


def _retention_row(cond: dict[str, Any], base_trials: int) -> list[str]:
    core = cond["core"]
    circuit = cond["circuit"]
    gf = cond["gf"]
    par = cond["parallel"]
    trials = str(cond["params"]["n_trials"])
    if cond["reduced"]:
        trials = f"{base_trials}→{cond['params']['n_trials']}"
    if core is None:
        core_cells = [NA] * 6
    else:
        core_cells = [
            str(core["n_core_excluded"]),
            f"{core['retained']} / {core['reference_size']}",
            _f(core["core_retention"]),
            _f(core["jaccard"]),
            str(core["n_new"]),
            _f(core["spearman"]),
        ]
    if circuit is None:
        circuit_cells = [NA] * 3
    else:
        circuit_cells = [
            str(circuit["n_members"]),
            str(circuit["n_edges"]),
            _f(circuit["edge_jaccard"]),
        ]
    gf_cell = NA if gf is None else _yn(gf["equals_baseline"])
    par_cell = NA if par is None else _yn(par["equals_baseline"])
    return [
        cond["cid"],
        cond["family"],
        cond["status"],
        trials,
        _n(cond["n_stimulated"]),
        *core_cells,
        *circuit_cells,
        gf_cell,
        par_cell,
    ]


def _span(values: list[float]) -> tuple[str, str, str]:
    if not values:
        return NA, NA, NA
    return f"{min(values):.4f}", f"{max(values):.4f}", f"{statistics.median(values):.4f}"


def _retentions(conditions: list[dict[str, Any]], *, control: bool) -> list[float]:
    return [
        c["core"]["core_retention"]
        for c in conditions
        if c["status"] == "completed"
        and bool(c["control"]) == control
        and c["core"] is not None
        and c["core"]["core_retention"] is not None
    ]


def _retention_section(results: dict[str, Any]) -> list[str]:
    conditions = _ordered(results["conditions"])
    base_trials = results["baseline"]["n_trials"]
    header = [
        "condition",
        "family",
        "status",
        "trials",
        "stimulated",
        "core excluded",
        "retained / reference",
        "core retention",
        "Jaccard",
        "new",
        "Spearman",
        "members",
        "edges",
        "edge Jaccard",
        "GF set equal",
        "parallel set equal",
    ]
    rows = [_retention_row(c, base_trials) for c in conditions]
    grid_lo, grid_hi, grid_med = _span(_retentions(conditions, control=False))
    ctl_lo, ctl_hi, ctl_med = _span(_retentions(conditions, control=True))
    chance = results["chance"]
    chance_mean = NA if chance is None else _f(chance["retention_mean"])
    lines = ["## Retention", ""]
    lines += _table(header, rows)
    lines += [
        "",
        f"Core retention over completed grid conditions ranges from {grid_lo} to {grid_hi} "
        f"(median {grid_med}); over control conditions from {ctl_lo} to {ctl_hi} "
        f"(median {ctl_med}); the chance-level mean is {chance_mean}.",
        "",
    ]
    return lines


def _chance_section(results: dict[str, Any]) -> list[str]:
    ch = results["chance"]
    lines = ["## Chance-level reference", ""]
    if ch is None:
        lines += ["None.", ""]
        return lines
    lines += [
        f"Random sets of {ch['set_size']} neurons drawn from a population of "
        f"{ch['population_size']}: {ch['n_draws']} draws, seed {ch['seed']}.",
        "",
    ]
    lines += _table(
        ["metric", "mean", "sd", "min", "max"],
        [
            [
                "core retention",
                _f(ch["retention_mean"]),
                _f(ch["retention_sd"]),
                _f(ch["retention_min"]),
                _f(ch["retention_max"]),
            ],
            [
                "Jaccard",
                _f(ch["jaccard_mean"]),
                _f(ch["jaccard_sd"]),
                _f(ch["jaccard_min"]),
                _f(ch["jaccard_max"]),
            ],
        ],
    )
    lines.append("")
    return lines


def _random_rows(conditions: list[dict[str, Any]]) -> list[list[str]]:
    rows = []
    for c in conditions:
        if c["family"] != "random_set":
            continue
        draw = c["random_draw"] or {}
        sides = draw.get("side_counts") or {}
        ids = draw.get("ids")
        rows.append(
            [
                c["cid"],
                _n(draw.get("draw")),
                _n(sides.get("left")),
                _n(sides.get("right")),
                _n(sides.get("unlabeled")),
                NA if ids is None else str(len(ids)),
            ]
        )
    return rows


def _shuffle_rows(shuffles: list[dict[str, Any]], check_keys: list[str]) -> list[list[str]]:
    rows = []
    for s in shuffles:
        checks = s["checks"]
        rows.append(
            [
                _n(s["draw"]),
                _n(s["seed"]),
                _n(s["rounds"]),
                _n(s["n_attempted"]),
                _n(s["n_accepted"]),
                _n(s["n_changed_edges"]),
                _n(s["self_loops_before"]),
                _n(s["self_loops_after"]),
                *[_yn(checks[k]) for k in check_keys],
            ]
        )
    return rows


def _controls_section(results: dict[str, Any]) -> list[str]:
    conditions = _ordered(results["conditions"])
    shuffles = results["shuffles"]
    check_keys = sorted(
        {k for s in shuffles for k, v in s["checks"].items() if isinstance(v, bool)}
    )
    lines = ["## Negative controls", "", "### Random sets", ""]
    lines += _table(
        ["condition", "draw", "left", "right", "unlabeled", "ids"],
        _random_rows(conditions),
    )
    lines += ["", "### Shuffles", ""]
    lines += _table(
        [
            "draw",
            "seed",
            "rounds",
            "attempted",
            "accepted",
            "changed edges",
            "self-loops before",
            "self-loops after",
            *check_keys,
        ],
        _shuffle_rows(shuffles, check_keys),
    )
    lines.append("")
    return lines


def _missing_text(missing: list[dict[str, Any]]) -> str:
    if not missing:
        return "none"
    return "; ".join(
        f"{m['root_id']}: rate {_f(m['rate_hz'])} Hz, rel rate {_f(m['rel_rate'])}, "
        f"rank {_n(m['rank'])}, trial frac {_f(m['trial_frac'])}"
        for m in missing
    )


def _gf_section(results: dict[str, Any]) -> list[str]:
    conditions = _ordered(results["conditions"])
    rows = [
        [
            c["cid"],
            _ids(c["gf"]["ids"]),
            _yn(c["gf"]["equals_baseline"]),
            _missing_text(c["gf"]["missing"]),
        ]
        for c in conditions
        if c["gf"] is not None
    ]
    completed = [c for c in conditions if c["status"] == "completed"]
    k = sum(1 for c in completed if c["gf"] is not None and c["gf"]["equals_baseline"])
    lines = ["## GF identity", ""]
    lines += _table(["condition", "responsive GF ids", "equal to baseline", "missing GF"], rows)
    lines += [
        "",
        f"The GF set equals the baseline set in {k} of {len(completed)} completed conditions.",
        "",
    ]
    return lines


def _lost_text(lost: list[list[Any]]) -> str:
    if not lost:
        return "none"
    return "; ".join(
        f"{root} ({cell_type}, check (i) {_yn(ci)}, check (iii) {_yn(ciii)})"
        for root, cell_type, ci, ciii in lost
    )


def _parallel_section(results: dict[str, Any]) -> list[str]:
    conditions = _ordered(results["conditions"])
    tracked = list(results["tracked_types"])
    base = results["baseline"]
    lines = ["## Parallel identity", ""]
    lines += _table(
        ["root_id", "cell type", "check (ii)"],
        [[str(r["root_id"]), r["cell_type"], _yn(r["check_ii"])] for r in results["check_ii"]],
    )
    lines.append("")
    if not base["parallel_ids"]:
        lines += ["The baseline has no parallel group; only candidate cell types are tracked.", ""]
    rows = []
    matrix = []
    for c in conditions:
        par = c["parallel"]
        if par is None:
            continue
        baseline_total = sum(t["n_baseline"] for t in par["per_type"])
        rows.append(
            [
                c["cid"],
                _yn(par["equals_baseline"]),
                f"{len(par['retained_ids'])} / {baseline_total}",
                _lost_text(par["lost"]),
                _ids(par["new_ids"]),
                ", ".join(par["new_cell_types"]) or "none",
            ]
        )
        by_type = {t["cell_type"]: t for t in par["per_type"]}
        cells = []
        for ct in tracked:
            t = by_type.get(ct)
            if t is None:
                cells.append("0 / 0 (+0)")
            else:
                cells.append(
                    f"{t['n_retained']} / {t['n_baseline']} (+{t['n_condition'] - t['n_retained']})"
                )
        matrix.append([c["cid"], *cells])
    lines += _table(
        [
            "condition",
            "parallel set equal",
            "retained / baseline",
            "lost",
            "new neurons",
            "new cell types",
        ],
        rows,
    )
    lines += [
        "",
        "Tracked cell types (cell: retained / baseline (+ condition minus retained)):",
        "",
    ]
    lines += _table(["condition", *tracked], matrix)
    lines.append("")
    return lines


def _persistence_section(results: dict[str, Any]) -> list[str]:
    pers = results["persistence"]
    roles = sorted(pers["by_role"])
    lines = [
        "## Persistence",
        "",
        "Persistence of a neuron is the fraction of completed non-control conditions in which "
        "the neuron was not stimulated and was responsive. The denominator counts only the "
        "conditions in which the neuron was not stimulated. Bins are cumulative.",
        "",
        f"Completed non-control conditions: {pers['n_conditions']}.",
        "",
    ]
    bin_rows = []
    for i, b in enumerate(pers["bins"]):
        bin_rows.append([b["label"], str(b["count"])] + [str(pers["by_role"][r][i]) for r in roles])
    lines += _table(["bin", "all", *roles], bin_rows)
    lines.append("")
    neuron_rows = []
    for n in pers["neurons"]:
        if n["role"] == NO_ROLE:
            continue
        per_family = "; ".join(
            f"{fam} {pair[0]} / {pair[1]}" for fam, pair in sorted(n["per_family"].items())
        )
        neuron_rows.append(
            [
                str(n["root_id"]),
                n["role"],
                f"{n['n_responsive']} / {n['n_eligible']}",
                per_family or "none",
            ]
        )
    if neuron_rows:
        lines += _table(["root_id", "role", "responsive / eligible", "per family"], neuron_rows)
    else:
        lines.append("None.")
    lines.append("")
    return lines


def _issues_section(results: dict[str, Any]) -> list[str]:
    reductions = results["reductions"]
    items: list[str] = []
    for step in reductions["steps"]:
        code = step["code"]
        if code in STEP_TEXT:
            items.append(STEP_TEXT[code].format(n=step["n"]))
        else:
            items.append(f"Step: {code} ({step['n']})")
    if reductions["dropped"]:
        items.append("Dropped: " + ", ".join(reductions["dropped"]))
    for cid in sorted(reductions["reduced"]):
        items.append(f"Reduced: {cid} to {reductions['reduced'][cid]} trials")
    for c in _ordered(results["conditions"]):
        if c["status"] == "failed":
            items.append(f"Failed: {c['cid']}: {c['reason']}")
    lines = ["## Failed, dropped or reduced conditions", ""]
    if items:
        lines += [f"- {item}" for item in items]
    else:
        lines.append("None.")
    lines.append("")
    return lines


def render(results: Mapping[str, Any]) -> str:
    data: dict[str, Any] = dict(results)
    lines = [
        "# Robustness of the v783 LC4/LPLC2 escape circuit (M6)",
        "",
        f"> {STATEMENT}",
        "",
    ]
    lines += _grid_section(data)
    lines += _baseline_section(data)
    lines += _retention_section(data)
    lines += _chance_section(data)
    lines += _controls_section(data)
    lines += _gf_section(data)
    lines += _parallel_section(data)
    lines += _persistence_section(data)
    lines += _issues_section(data)
    lines += ["## Run cost", "", RUN_COST_TEXT, ""]
    return "\n".join(lines) + "\n"


def write(results: Mapping[str, Any], *, report: Path, results_path: Path) -> None:
    json_text = json.dumps(_round(results), sort_keys=True, indent=2) + "\n"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json_text, encoding="utf-8")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render(json.loads(json_text)), encoding="utf-8")
