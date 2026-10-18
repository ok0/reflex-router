"""Post-processing: responsive set, member edges, output identification, circuit export (M5)."""

import json
import platform
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from reflex_router.circuit import CircuitSpec
from rr_discovery import annotations, connfilter, export, extract, identify, sanity
from rr_discovery.config import (
    DiscoverConfig,
    DiscoveryConfig,
    require_discover,
    require_model_input,
)
from rr_discovery.data import paths_from_config, sha256_file
from rr_discovery.identify import Outputs
from rr_discovery.model_input import output_paths, verify_outputs
from rr_discovery.run import (
    CONDITION_RUNNER,
    RunError,
    StimSets,
    read_m2_verdict,
    read_spike_counts,
    run_paths,
    stimulated_sets,
    write_run_log,
)
from rr_discovery.vendor import vendored_code_hash

_CONNECTIVITY_COLUMNS = ["Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory"]
_MODEL_INPUT_KEYS = ("completeness", "connectivity", "input_totals")


@dataclass(frozen=True)
class PostInputs:
    counts: pd.DataFrame
    n_trials: int
    t_run_s: float
    ann: pd.DataFrame
    valid_ids: np.ndarray
    connectivity: pd.DataFrame
    input_totals: pd.DataFrame
    details_base: Mapping[str, Any]


@dataclass(frozen=True)
class PostResult:
    circuit_sha256: str
    outputs: Outputs
    counts: dict[str, Any]


@dataclass(frozen=True)
class Derived:
    stats: pd.DataFrame
    responsive_ids: np.ndarray
    members: np.ndarray
    n_member_pairs: int
    n_kept: int
    edges: pd.DataFrame


def derive(
    counts: pd.DataFrame,
    *,
    n_trials: int,
    t_run_s: float,
    stimulated: np.ndarray,
    connectivity: pd.DataFrame,
    input_totals: pd.DataFrame,
    rule: extract.ResponsiveRule,
) -> Derived:
    stats = extract.responsive(
        counts,
        rule,
        n_trials=n_trials,
        t_run_s=t_run_s,
        stimulated=stimulated,
    )
    responsive_mask = np.asarray(stats["responsive"], dtype=bool)
    responsive_ids = np.asarray(stats["root_id"], dtype=np.int64)[responsive_mask]
    members = np.union1d(stimulated, responsive_ids).astype(np.int64)

    pre_col = connectivity["Presynaptic_ID"].to_numpy(dtype=np.int64)
    post_col = connectivity["Postsynaptic_ID"].to_numpy(dtype=np.int64)
    syn_col = connectivity["Connectivity"].to_numpy(dtype=np.int64)
    sel = np.isin(pre_col, members) & np.isin(post_col, members)
    member_edges = pd.DataFrame(
        {"pre": pre_col[sel], "post": post_col[sel], "syn": syn_col[sel]},
    )
    kept = connfilter.keep(member_edges, input_totals)
    edges = member_edges.loc[kept].reset_index(drop=True)
    return Derived(
        stats=stats,
        responsive_ids=responsive_ids,
        members=members,
        n_member_pairs=int(sel.sum()),
        n_kept=int(kept.sum()),
        edges=edges,
    )


def circuit_labels(ann: pd.DataFrame, members: np.ndarray, out: Outputs) -> pd.DataFrame:
    candidate_ids = np.array([c.root_id for c in out.candidates], dtype=np.int64)
    label_ids = np.union1d(np.union1d(members, candidate_ids), out.gf_type_ids).astype(np.int64)
    return annotations.labels(ann, label_ids)


def circuit_spec(
    *,
    stim: StimSets,
    d: Derived,
    out: Outputs,
    labels: pd.DataFrame,
    connectivity: pd.DataFrame,
) -> CircuitSpec:
    signs = export.presynaptic_signs(connectivity)
    return export.build_spec(
        stim=stim,
        members=d.members,
        gf_ids=out.gf_ids,
        parallel_ids=out.parallel_ids,
        edges=d.edges,
        signs=signs,
        labels=labels,
    )


def postprocess(
    inp: PostInputs,
    dc: DiscoverConfig,
    *,
    data_version: str,
    gf_sanity: Callable[[np.ndarray, np.ndarray], None],
) -> PostResult:
    stim = stimulated_sets(inp.ann, inp.valid_ids, dc)
    rule = extract.ResponsiveRule(dc.min_rate_hz, dc.min_trial_frac)
    d = derive(
        inp.counts,
        n_trials=inp.n_trials,
        t_run_s=inp.t_run_s,
        stimulated=stim.all,
        connectivity=inp.connectivity,
        input_totals=inp.input_totals,
        rule=rule,
    )

    out = identify.outputs(
        ann=inp.ann,
        valid_ids=inp.valid_ids,
        stats=d.stats,
        members=d.members,
        stim=stim,
        connectivity=inp.connectivity,
        input_totals=inp.input_totals,
        gf_cell_type=dc.gf_cell_type,
        prior_cell_types=dc.prior_cell_types,
        reported_cell_types=dc.reported_cell_types,
    )
    labels = circuit_labels(inp.ann, d.members, out)

    dc.responsive_table.parent.mkdir(parents=True, exist_ok=True)
    dc.responsive_table.write_text(
        extract.render_responsive_table(d.stats, labels), encoding="utf-8"
    )
    dc.candidates_report.parent.mkdir(parents=True, exist_ok=True)
    dc.candidates_report.write_text(
        identify.render_report(
            out,
            data_version=data_version,
            rule=rule,
            gf_cell_type=dc.gf_cell_type,
            summary=None,
        ),
        encoding="utf-8",
    )

    if out.gf_ids.size == 0:
        raise identify.IdentifyError(
            f"no responsive {dc.gf_cell_type} neuron; circuit.json not written; "
            f"see {dc.candidates_report.name}"
        )
    gf_sanity(out.gf_ids, d.members)

    spec = circuit_spec(
        stim=stim,
        d=d,
        out=out,
        labels=labels,
        connectivity=inp.connectivity,
    )
    counts = export.circuit_counts(spec)
    summary: dict[str, int] = {
        key: int(counts[key])
        for key in ("n_neurons", "n_edges", "n_synapses", "n_no_incoming", "n_no_outgoing")
    }
    summary.update({f"by_role.{role}": int(n) for role, n in counts["by_role"].items()})
    dc.candidates_report.write_text(
        identify.render_report(
            out,
            data_version=data_version,
            rule=rule,
            gf_cell_type=dc.gf_cell_type,
            summary=summary,
        ),
        encoding="utf-8",
    )

    details: dict[str, Any] = {
        **dict(inp.details_base),
        "responsive_rule": {
            "min_rate_hz": rule.min_rate_hz,
            "min_trial_frac": rule.min_trial_frac,
            "text": extract.RULE_TEXT,
            "n_responsive": int(d.responsive_ids.size),
        },
        "connection_filter": {
            "rule": connfilter.RULE_TEXT,
            "citation": connfilter.CITATION,
            "codex_note": connfilter.CODEX_NOTE,
            "n_member_pairs": d.n_member_pairs,
            "n_kept": d.n_kept,
        },
        "outputs": {
            "gf_cell_type": dc.gf_cell_type,
            "gf_ids": sorted(int(x) for x in out.gf_ids.tolist()),
            "parallel_ids": sorted(int(x) for x in out.parallel_ids.tolist()),
            "parallel_cell_types": sorted(
                {c.cell_type for c in out.candidates if c.role == "output_parallel"}
            ),
        },
        "circuit": counts,
        "parallel_output": out.parallel_output,
        "parallel_output_reason": out.parallel_reason,
    }
    sha = export.write_artifact(
        dc.out_dir,
        spec,
        details,
        data_version=data_version,
        license_label=dc.license_label,
    )
    return PostResult(circuit_sha256=sha, outputs=out, counts=counts)


def post_stage(cfg: DiscoveryConfig) -> int:
    dc = require_discover(cfg)
    _, spikes_path, run_path = run_paths(dc, cfg.version)
    if not run_path.is_file():
        raise RunError("run step output missing; run 'rr-discover discover --step run' first")
    run_result: dict[str, Any] = json.loads(run_path.read_text(encoding="utf-8"))
    counts = read_spike_counts(spikes_path, expected_sha256=str(run_result["spikes"]["sha256"]))

    mi = output_paths(require_model_input(cfg).out_dir, cfg.version)
    model_meta = verify_outputs(mi)
    paths = paths_from_config(cfg)
    ann = annotations.load_annotations(paths.annotations)
    valid = annotations.load_root_ids(paths.root_ids)
    stim = stimulated_sets(ann, valid, dc)
    connectivity = pq.read_table(mi.connectivity, columns=_CONNECTIVITY_COLUMNS).to_pandas()
    input_totals = pq.read_table(mi.input_totals).to_pandas()

    raw_files = (paths.connections, paths.root_ids, paths.annotations)
    input_hashes = {p.name: sha256_file(p) for p in raw_files}
    model_input_hashes = {k: str(model_meta["outputs"][k]["sha256"]) for k in _MODEL_INPUT_KEYS}

    details_base = export.build_details(
        cfg=cfg,
        dc=dc,
        input_hashes=input_hashes,
        model_input_hashes=model_input_hashes,
        annotation_sha256=input_hashes[paths.annotations.name],
        vendored_code_sha256=vendored_code_hash(),
        condition_runner_sha256=sha256_file(CONDITION_RUNNER),
        m2=read_m2_verdict(dc.m2_report),
        run_result=run_result,
        n_lc4=int(stim.lc4.size),
        n_lplc2=int(stim.lplc2.size),
    )

    started = datetime.now(UTC)
    t0 = time.monotonic()
    result = postprocess(
        PostInputs(
            counts=counts,
            n_trials=len(run_result["seeds"]),
            t_run_s=float(run_result["t_run_s"]),
            ann=ann,
            valid_ids=valid,
            connectivity=connectivity,
            input_totals=input_totals,
            details_base=details_base,
        ),
        dc,
        data_version=cfg.version,
        gf_sanity=sanity.check_gf_in_circuit,
    )
    write_run_log(
        dc.work_dir,
        "post",
        {
            "started_utc": started.isoformat(timespec="seconds"),
            "wall_s": time.monotonic() - t0,
            "host": platform.node(),
        },
    )
    print(dc.out_dir)
    print(result.circuit_sha256)
    print(json.dumps(result.counts, sort_keys=True))
    print(result.outputs.parallel_output)
    print(dc.candidates_report)
    return 0
