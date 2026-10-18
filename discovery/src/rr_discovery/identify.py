from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from rr_discovery import annotations, connfilter, extract
from rr_discovery.annotations import descending_ids, ids_by_cell_type
from rr_discovery.run import StimSets

Label = Literal["prior", "reported", "data-driven"]
Role = Literal["output_parallel", "inter", "not in circuit"]

LABEL_ORDER: tuple[str, ...] = ("prior", "reported", "data-driven")
LIMITATION = (
    "Limitation: no candidate passed ADR-15 checks (i)-(iii), so the circuit has no "
    "output_parallel neurons and the release cannot claim a parallel-escape output "
    "(charter R5)."
)
NO_TYPE_REASON = "no neurons of this cell type in the v783 annotations"
NO_PASS_REASON = "present but no neuron passed (i)-(iii)"
REPORT_HEADER = (
    "| cell_type | root_id | side | label | evidence | responsive | rate Hz | rel rate | "
    "trial frac | LC4 syn raw | LC4 syn kept | LPLC2 syn raw | LPLC2 syn kept | "
    "(i) | (ii) | (iii) | role |"
)


class IdentifyError(Exception):
    pass


@dataclass(frozen=True)
class Candidate:
    root_id: int
    cell_type: str
    side: str
    label: Label
    evidence: str
    responsive: bool
    rate_hz: float
    rel_rate: float
    trial_frac: float
    lc4_raw: int
    lc4_kept: int
    lplc2_raw: int
    lplc2_kept: int
    check_i: bool
    check_ii: bool
    check_iii: bool
    role: Role


@dataclass(frozen=True)
class GFRow:
    root_id: int
    side: str
    responsive: bool
    rate_hz: float
    rel_rate: float
    trial_frac: float


@dataclass(frozen=True)
class Outputs:
    gf_type_ids: np.ndarray
    gf_ids: np.ndarray
    gf_rows: tuple[GFRow, ...]
    prior_cell_types: tuple[str, ...]
    parallel_ids: np.ndarray
    candidates: tuple[Candidate, ...]
    absent_types: tuple[tuple[str, str], ...]
    parallel_output: Literal["present", "none"]
    parallel_reason: str


def _sums_by_post(edges: pd.DataFrame, pre_ids: np.ndarray) -> dict[int, int]:
    pre = edges["pre"].to_numpy(dtype=np.int64)
    sub = edges.loc[np.isin(pre, pre_ids)]
    grouped = sub.groupby("post")["syn"].sum()
    return {int(post): int(total) for post, total in grouped.items()}


def outputs(
    *,
    ann: pd.DataFrame,
    valid_ids: np.ndarray,
    stats: pd.DataFrame,
    members: np.ndarray,
    stim: StimSets,
    connectivity: pd.DataFrame,
    input_totals: pd.DataFrame,
    gf_cell_type: str,
    prior_cell_types: Sequence[str],
    reported_cell_types: Sequence[str],
) -> Outputs:
    gf_type_ids = ids_by_cell_type(ann, gf_cell_type, valid_ids=valid_ids)
    responsive_all = np.asarray(stats["responsive"], dtype=bool)
    responsive_ids = np.asarray(stats["root_id"], dtype=np.int64)[responsive_all]
    gf_ids = np.intersect1d(gf_type_ids, responsive_ids)
    gf_set = set(gf_type_ids.tolist())

    assigned: dict[int, Label] = {}

    def claim(label: Label, ids: np.ndarray) -> None:
        for rid in np.asarray(ids, dtype=np.int64).tolist():
            if rid in gf_set or rid in assigned:
                continue
            assigned[rid] = label

    prior_types = {t: ids_by_cell_type(ann, t, valid_ids=valid_ids) for t in prior_cell_types}
    reported_types = {t: ids_by_cell_type(ann, t, valid_ids=valid_ids) for t in reported_cell_types}
    for ids in prior_types.values():
        claim("prior", ids)
    for ids in reported_types.values():
        claim("reported", ids)
    claim(
        "data-driven",
        np.intersect1d(descending_ids(ann, valid_ids=valid_ids), responsive_ids),
    )

    candidate_ids = np.array(sorted(assigned), dtype=np.int64)
    names = annotations.labels(ann, candidate_ids)
    names_by_root = {
        int(r): (str(c), str(s))
        for r, c, s in zip(
            names["root_id"].tolist(),
            names["cell_type"].tolist(),
            names["side"].tolist(),
            strict=True,
        )
    }

    pre_col = connectivity["Presynaptic_ID"].to_numpy(dtype=np.int64)
    post_col = connectivity["Postsynaptic_ID"].to_numpy(dtype=np.int64)
    syn_col = connectivity["Connectivity"].to_numpy(dtype=np.int64)
    sel = np.isin(pre_col, stim.all) & np.isin(post_col, candidate_ids)
    edges = pd.DataFrame(
        {"pre": pre_col[sel], "post": post_col[sel], "syn": syn_col[sel]},
    )
    kept = connfilter.keep(edges, input_totals)
    kept_edges = edges.loc[kept]

    lc4_raw = _sums_by_post(edges, stim.lc4)
    lc4_kept = _sums_by_post(kept_edges, stim.lc4)
    lplc2_raw = _sums_by_post(edges, stim.lplc2)
    lplc2_kept = _sums_by_post(kept_edges, stim.lplc2)

    stat_by_root = {
        int(r): (float(rate), float(rel), float(frac), bool(resp))
        for r, rate, rel, frac, resp in zip(
            np.asarray(stats["root_id"], dtype=np.int64).tolist(),
            np.asarray(stats["rate_hz"], dtype=np.float64).tolist(),
            np.asarray(stats["rel_rate"], dtype=np.float64).tolist(),
            np.asarray(stats["trial_frac"], dtype=np.float64).tolist(),
            responsive_all.tolist(),
            strict=True,
        )
    }
    member_set = set(np.asarray(members, dtype=np.int64).tolist())

    gf_labels = annotations.labels(ann, gf_type_ids)
    gf_side_by_root = {
        int(r): str(s)
        for r, s in zip(
            gf_labels["root_id"].tolist(),
            gf_labels["side"].tolist(),
            strict=True,
        )
    }
    gf_responsive = set(gf_ids.tolist())
    gf_rows = tuple(
        GFRow(
            root_id=rid,
            side=gf_side_by_root.get(rid, ""),
            responsive=rid in gf_responsive,
            rate_hz=stat_by_root.get(rid, (0.0, 0.0, 0.0, False))[0],
            rel_rate=stat_by_root.get(rid, (0.0, 0.0, 0.0, False))[1],
            trial_frac=stat_by_root.get(rid, (0.0, 0.0, 0.0, False))[2],
        )
        for rid in sorted(int(r) for r in gf_type_ids.tolist())
    )

    candidates: list[Candidate] = []
    for rid in candidate_ids.tolist():
        label = assigned[rid]
        cell_type, side = names_by_root.get(rid, ("", ""))
        rate, rel, frac, resp = stat_by_root.get(rid, (0.0, 0.0, 0.0, False))
        l4_raw = lc4_raw.get(rid, 0)
        l4_kept = lc4_kept.get(rid, 0)
        lp_raw = lplc2_raw.get(rid, 0)
        lp_kept = lplc2_kept.get(rid, 0)
        check_i = resp
        check_ii = l4_kept + lp_kept > 0
        check_iii = rid in member_set
        if check_i and check_ii and check_iii:
            role: Role = "output_parallel"
        elif check_iii:
            role = "inter"
        else:
            role = "not in circuit"
        candidates.append(
            Candidate(
                root_id=rid,
                cell_type=cell_type,
                side=side,
                label=label,
                evidence="LOW" if label == "prior" else "data-driven",
                responsive=resp,
                rate_hz=rate,
                rel_rate=rel,
                trial_frac=frac,
                lc4_raw=l4_raw,
                lc4_kept=l4_kept,
                lplc2_raw=lp_raw,
                lplc2_kept=lp_kept,
                check_i=check_i,
                check_ii=check_ii,
                check_iii=check_iii,
                role=role,
            )
        )

    candidates.sort(key=lambda c: (LABEL_ORDER.index(c.label), c.cell_type, -c.rel_rate, c.root_id))
    tuple_candidates = tuple(candidates)

    absent: list[tuple[str, str]] = []
    for t in (*prior_cell_types, *reported_cell_types):
        type_ids = prior_types[t] if t in prior_types else reported_types[t]
        if type_ids.size == 0:
            absent.append((t, NO_TYPE_REASON))
        elif not any(c.cell_type == t and c.role == "output_parallel" for c in tuple_candidates):
            absent.append((t, NO_PASS_REASON))

    parallel = sorted(c.root_id for c in tuple_candidates if c.role == "output_parallel")
    parallel_ids = np.array(parallel, dtype=np.int64)
    if parallel:
        parallel_output: Literal["present", "none"] = "present"
        parallel_reason = f"{len(parallel)} candidate(s) passed ADR-15 checks (i)-(iii)"
    else:
        parallel_output = "none"
        n_cand = len(tuple_candidates)
        n_resp = sum(1 for c in tuple_candidates if c.responsive)
        n_input = sum(1 for c in tuple_candidates if c.check_ii)
        parallel_reason = (
            f"no candidate passed ADR-15 checks (i)-(iii): {n_cand} candidates, "
            f"{n_resp} responsive, {n_input} with filtered direct LC4/LPLC2 input"
        )

    return Outputs(
        gf_type_ids=gf_type_ids,
        gf_ids=gf_ids,
        gf_rows=gf_rows,
        prior_cell_types=tuple(prior_cell_types),
        parallel_ids=parallel_ids,
        candidates=tuple_candidates,
        absent_types=tuple(absent),
        parallel_output=parallel_output,
        parallel_reason=parallel_reason,
    )


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"


def _pf(flag: bool) -> str:
    return "pass" if flag else "fail"


def render_report(
    out: Outputs,
    *,
    data_version: str,
    rule: extract.ResponsiveRule,
    gf_cell_type: str,
    summary: Mapping[str, int] | None,
) -> str:
    prior_set = sorted(out.prior_cell_types)
    gf_lines: list[str] = [f"## Giant fiber ({gf_cell_type})", ""]
    if out.gf_rows:
        gf_lines += [
            "| root_id | side | responsive | rate Hz | rel rate | trial frac |",
            "|---|---|---|---|---|---|",
        ]
        gf_lines += [
            f"| {r.root_id} | {r.side} | {_yes(r.responsive)} | {r.rate_hz:.3f} | "
            f"{r.rel_rate:.4f} | {r.trial_frac:.3f} |"
            for r in out.gf_rows
        ]
    else:
        gf_lines.append(f"No {gf_cell_type} neurons in the annotations.")
    gf_lines.append("")
    lines: list[str] = [
        f"# Parallel DN candidates ({data_version})",
        "",
        f"Responsive rule (min_rate_hz={rule.min_rate_hz}, "
        f"min_trial_frac={rule.min_trial_frac}): {extract.RULE_TEXT}",
        "",
        f"Connection filter: {connfilter.RULE_TEXT}",
        "",
        f"Evidence: prior set {{{', '.join(prior_set)}}} is LOW evidence (ADR-15); "
        "others are data-driven. No candidate is literature-confirmed in M5.",
        "",
        *gf_lines,
        "## Candidates",
        "",
        REPORT_HEADER,
        "|" + "---|" * 17,
    ]
    for c in out.candidates:
        lines.append(
            f"| {c.cell_type} | {c.root_id} | {c.side} | {c.label} | {c.evidence} | "
            f"{_yes(c.responsive)} | {c.rate_hz:.3f} | {c.rel_rate:.4f} | {c.trial_frac:.3f} | "
            f"{c.lc4_raw} | {c.lc4_kept} | {c.lplc2_raw} | {c.lplc2_kept} | "
            f"{_pf(c.check_i)} | {_pf(c.check_ii)} | {_pf(c.check_iii)} | {c.role} |"
        )
    lines += ["", "## Absent or failing candidate types", ""]
    lines += [f"- {t}: {reason}" for t, reason in out.absent_types]
    lines += ["", "## Result", "", f"parallel_output: {out.parallel_output}", ""]
    lines.append(f"reason: {out.parallel_reason}")
    if out.parallel_output == "none":
        lines += ["", LIMITATION]
    if summary is not None:
        lines += ["", "## Circuit", ""]
        lines += [f"- {key}: {summary[key]}" for key in sorted(summary)]
    return "\n".join(lines) + "\n"
