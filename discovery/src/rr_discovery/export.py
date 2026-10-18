"""Circuit export: writer-side spec, circuit counts, provenance details (M5, R7, R14-R15, R42)."""

import importlib.metadata
import platform
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import pandas as pd

from reflex_router.circuit import (
    ROLES,
    SHIU_PARAMS,
    CircuitSpec,
    Neuron,
    Provenance,
    Role,
    write_circuit,
)
from rr_discovery.config import (
    DiscoverConfig,
    DiscoveryConfig,
    discover_config_dict,
    require_shiu,
)
from rr_discovery.run import M2Verdict, StimSets

LICENSE_NOTE = (
    "Zenodo v783 record states CC BY 4.0; FlyWire Terms of Service (edits and annotations) and "
    "Principles state CC BY-NC 4.0; the Terms explicitly name only edits and annotations; "
    "unresolved; this project applies the stricter CC BY-NC 4.0"
)
SHIU_PAPER_DOI = "10.1038/s41586-024-07763-9"

CITATIONS: tuple[dict[str, str | None], ...] = (
    {
        "key": "dorkenwald2024",
        "text": "Dorkenwald et al. 2024, Nature 634:124-138 (FlyWire whole-brain connectome)",
        "doi": "10.1038/s41586-024-07558-y",
        "doi_status": "verified: research flywire-data-access C7 (Europe PMC record)",
    },
    {
        "key": "schlegel2024",
        "text": "Schlegel et al. 2024, Nature 634:139-152",
        "doi": "10.1038/s41586-024-07686-5",
        "doi_status": "charter R3",
    },
    {
        "key": "schlegel2023_preprint",
        "text": "Schlegel et al. 2023, bioRxiv (preprint)",
        "doi": "10.1101/2023.06.27.546055",
        "doi_status": "charter R3",
    },
    {
        "key": "flywire_v783_zenodo",
        "text": "FlyWire v783 release (Zenodo record)",
        "doi": None,
        "doi_status": "charter R42 (Zenodo DOI) / discovery.toml [zenodo]",
    },
    {
        "key": "eckstein_bates2024",
        "text": "Eckstein, Bates et al. 2024 (neurotransmitter predictions)",
        "doi": None,
        "doi_status": "unverified",
    },
    {
        "key": "codex",
        "text": "Codex (FlyWire connectome browser)",
        "doi": "10.13140/RG.2.2.35928.67844",
        "doi_status": "charter R42",
    },
    {
        "key": "shiu2024",
        "text": "Shiu et al. 2024, Nature 634:210-219 (Drosophila whole-brain LIF model)",
        "doi": SHIU_PAPER_DOI,
        "doi_status": "charter R40",
    },
)


class ExportError(Exception):
    pass


def citations(zenodo_doi: str) -> list[dict[str, str | None]]:
    out: list[dict[str, str | None]] = []
    for entry in CITATIONS:
        item = dict(entry)
        if item["key"] == "flywire_v783_zenodo":
            item["doi"] = zenodo_doi
        out.append(item)
    return out


def software_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": importlib.metadata.version("numpy"),
        "pandas": importlib.metadata.version("pandas"),
        "pyarrow": importlib.metadata.version("pyarrow"),
        "reflex_router_discovery": importlib.metadata.version("reflex-router-discovery"),
        "reflex_router": importlib.metadata.version("reflex-router"),
    }


def presynaptic_signs(connectivity: pd.DataFrame) -> pd.Series:
    signs = pd.Series(connectivity.groupby("Presynaptic_ID")["Excitatory"].first())
    if not bool(signs.isin([1, -1]).to_numpy().all()):
        raise ExportError("Excitatory must be 1 or -1 for every presynaptic neuron")
    return signs


def build_spec(
    *,
    stim: StimSets,
    members: np.ndarray,
    gf_ids: np.ndarray,
    parallel_ids: np.ndarray,
    edges: pd.DataFrame,
    signs: pd.Series,
    labels: pd.DataFrame,
) -> CircuitSpec:
    lc4 = {int(x) for x in stim.lc4.tolist()}
    lplc2 = {int(x) for x in stim.lplc2.tolist()}
    gf = {int(x) for x in np.asarray(gf_ids, dtype=np.int64).tolist()}
    par = {int(x) for x in np.asarray(parallel_ids, dtype=np.int64).tolist()}
    stimulated = lc4 | lplc2
    if gf & par:
        raise ExportError(f"output_gf and output_parallel overlap: {sorted(gf & par)[:10]}")
    if (gf | par) & stimulated:
        raise ExportError(
            f"output groups overlap stimulated neurons: {sorted((gf | par) & stimulated)[:10]}"
        )
    cell = {
        int(r): (str(c), str(s))
        for r, c, s in zip(
            labels["root_id"].tolist(),
            labels["cell_type"].tolist(),
            labels["side"].tolist(),
            strict=True,
        )
    }
    sign_ids: list[int] = signs.index.to_numpy(dtype=np.int64).tolist()
    sign_vals: list[int] = signs.to_numpy(dtype=np.int64).tolist()
    sign_of: dict[int, int] = dict(zip(sign_ids, sign_vals, strict=True))
    neurons: list[Neuron] = []
    for rid in sorted({int(x) for x in np.asarray(members, dtype=np.int64).tolist()}):
        role: Role
        if rid in lc4:
            role = "input_lc4"
        elif rid in lplc2:
            role = "input_lplc2"
        elif rid in gf:
            role = "output_gf"
        elif rid in par:
            role = "output_parallel"
        else:
            role = "inter"
        cell_type, side = cell.get(rid, ("", ""))
        neurons.append(
            Neuron(
                root_id=rid,
                role=role,
                sign=sign_of.get(rid, 1),
                cell_type=cell_type,
                side=side,
            )
        )
    pre_arr: list[int] = edges["pre"].to_numpy(dtype=np.int64).tolist()
    post_arr: list[int] = edges["post"].to_numpy(dtype=np.int64).tolist()
    syn_arr: list[int] = edges["syn"].to_numpy(dtype=np.int64).tolist()
    connections = tuple(
        sorted((p, q, s) for p, q, s in zip(pre_arr, post_arr, syn_arr, strict=True))
    )
    return CircuitSpec(neurons=tuple(neurons), connections=connections, params=SHIU_PARAMS)


def circuit_counts(spec: CircuitSpec) -> dict[str, Any]:
    incoming = {post for _, post, _ in spec.connections}
    outgoing = {pre for pre, _, _ in spec.connections}
    return {
        "n_neurons": len(spec.neurons),
        "n_edges": len(spec.connections),
        "n_synapses": int(sum(count for _, _, count in spec.connections)),
        "by_role": {r: sum(1 for n in spec.neurons if n.role == r) for r in ROLES},
        "n_no_incoming": sum(1 for n in spec.neurons if n.root_id not in incoming),
        "n_no_outgoing": sum(1 for n in spec.neurons if n.root_id not in outgoing),
    }


def build_details(
    *,
    cfg: DiscoveryConfig,
    dc: DiscoverConfig,
    input_hashes: Mapping[str, str],
    model_input_hashes: Mapping[str, str],
    annotation_sha256: str,
    vendored_code_sha256: str,
    condition_runner_sha256: str,
    m2: M2Verdict,
    run_result: Mapping[str, Any],
    n_lc4: int,
    n_lplc2: int,
) -> dict[str, Any]:
    shiu = require_shiu(cfg)
    seeds = list(run_result["seeds"])
    return {
        "schema": 1,
        "kind": "rr-discovery-circuit",
        "data": {
            "version": cfg.version,
            "zenodo_record": cfg.zenodo.record,
            "zenodo_doi": cfg.zenodo.doi,
            "inputs": dict(input_hashes),
            "model_input": dict(model_input_hashes),
        },
        "annotations": {
            "repo": cfg.annotations.repo,
            "tag": cfg.annotations.tag,
            "file": PurePosixPath(cfg.annotations.path).name,
            "sha256": annotation_sha256,
        },
        "shiu": {
            "paper_doi": SHIU_PAPER_DOI,
            "repo": shiu.repo,
            "commit": shiu.commit,
            "vendored_code_sha256": vendored_code_sha256,
            "condition_runner_sha256": condition_runner_sha256,
        },
        "citations": citations(cfg.zenodo.doi),
        "license": {"label": dc.license_label, "note": LICENSE_NOTE},
        "m2": {"verdict": m2.verdict, "sim_env": m2.sim_env},
        "stimulus": {
            "config": discover_config_dict(dc),
            "n_lc4": n_lc4,
            "n_lplc2": n_lplc2,
            "seed_scheme": "seed_base + trial_index",
            "seeds": seeds,
            "n_trials": len(seeds),
            "t_run_s": run_result["t_run_s"],
            "shiu_params": run_result["params"],
        },
        "spikes": dict(run_result["spikes"]),
        "software": {
            "simulation": dict(run_result["env"]),
            "postprocess": software_versions(),
        },
    }


def write_artifact(
    out_dir: Path,
    spec: CircuitSpec,
    details: Mapping[str, Any],
    *,
    data_version: str,
    license_label: str,
) -> str:
    provenance = Provenance(
        data_version,
        f"{license_label} (derived from FlyWire {data_version}; see NOTICE.md)",
        "FlyWire LC4/LPLC2 discovery circuit (rr-discover discover); provenance in details",
        details,
    )
    return write_circuit(out_dir, spec, provenance)
