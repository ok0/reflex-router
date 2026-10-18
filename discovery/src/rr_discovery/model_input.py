import json
import platform
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather
import pyarrow.parquet as pq

from rr_discovery.data import IntegrityError, sha256_file

NT_COLS = ("gaba_avg", "ach_avg", "glut_avg", "oct_avg", "ser_avg", "da_avg")
INHIBITORY_COLS = ("gaba_avg", "glut_avg")
CONN_COLS = (
    "Presynaptic_ID",
    "Postsynaptic_ID",
    "Presynaptic_Index",
    "Postsynaptic_Index",
    "Connectivity",
    "Excitatory",
    "Excitatory x Connectivity",
)
SIGN_RULE = (
    "presynaptic neuron inhibitory iff sum(syn_count*(gaba_avg+glut_avg)) / "
    "sum(syn_count*sum(NT_COLS)) > 0.5 over its rows with no NaN NT value; "
    "neurons with no such rows are excitatory"
)


@dataclass(frozen=True)
class ModelInputPaths:
    completeness: Path
    connectivity: Path
    input_totals: Path
    meta: Path


def output_paths(out_dir: Path, version: str) -> ModelInputPaths:
    return ModelInputPaths(
        completeness=out_dir / f"completeness_{version}.csv",
        connectivity=out_dir / f"connectivity_{version}.parquet",
        input_totals=out_dir / f"input_totals_{version}.parquet",
        meta=out_dir / f"model_input_{version}.json",
    )


@dataclass(frozen=True)
class BuildStats:
    n_rows: int
    n_neurons: int
    n_pairs: int
    n_pre: int
    n_pre_inhibitory: int
    n_pre_missing_nt: int
    n_targets: int


def load_connections(path: Path) -> pd.DataFrame:
    return pyarrow.feather.read_table(
        path,
        columns=["pre_pt_root_id", "post_pt_root_id", "syn_count", *NT_COLS],
        memory_map=True,
    ).to_pandas()


def presynaptic_signs(df: pd.DataFrame) -> tuple[pd.Series, int]:
    valid = df[list(NT_COLS)].notna().all(axis=1)
    v = df.loc[valid]
    w = v["syn_count"].astype("float64")
    num = w * (v["gaba_avg"] + v["glut_avg"])
    den = w * v[list(NT_COLS)].sum(axis=1)
    num_by_pre = num.groupby(v["pre_pt_root_id"].to_numpy()).sum()
    den_by_pre = den.groupby(v["pre_pt_root_id"].to_numpy()).sum()

    all_pre = np.unique(df["pre_pt_root_id"].to_numpy()).astype(np.int64)
    num_arr = num_by_pre.reindex(all_pre, fill_value=0.0).to_numpy(dtype="float64")
    den_arr = den_by_pre.reindex(all_pre, fill_value=0.0).to_numpy(dtype="float64")

    has_den = den_arr > 0
    ratio = np.zeros_like(num_arr)
    np.divide(num_arr, den_arr, out=ratio, where=has_den)
    inhibitory = has_den & (ratio > 0.5)

    signs = pd.Series(
        np.where(inhibitory, -1, 1).astype(np.int64),
        index=pd.Index(all_pre, name="pre_pt_root_id"),
        name="Excitatory",
    )
    n_missing = int((~has_den).sum())
    return signs, n_missing


def aggregate_pairs(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(["pre_pt_root_id", "post_pt_root_id"], sort=True).agg(
        syn=("syn_count", "sum")
    )
    return pd.DataFrame(
        {
            "pre": np.asarray(grouped.index.get_level_values(0), dtype=np.int64),
            "post": np.asarray(grouped.index.get_level_values(1), dtype=np.int64),
            "syn": np.asarray(grouped["syn"], dtype=np.int64),
        }
    )


def input_totals(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("post_pt_root_id", sort=True).agg(input_total=("syn_count", "sum"))
    return pd.DataFrame(
        {
            "root_id": np.asarray(grouped.index, dtype=np.int64),
            "input_total": np.asarray(grouped["input_total"], dtype=np.int64),
        }
    )


def build_tables(df: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame, BuildStats]:
    ids = np.unique(
        np.concatenate([df["pre_pt_root_id"].to_numpy(), df["post_pt_root_id"].to_numpy()])
    ).astype(np.int64)
    signs, n_missing = presynaptic_signs(df)
    pairs = aggregate_pairs(df)
    pre = pairs["pre"].to_numpy(dtype=np.int64)
    post = pairs["post"].to_numpy(dtype=np.int64)
    syn = pairs["syn"].to_numpy(dtype=np.int64)
    exc = signs.reindex(pre).to_numpy(dtype=np.int64)

    conn = pd.DataFrame(
        {
            "Presynaptic_ID": pre,
            "Postsynaptic_ID": post,
            "Presynaptic_Index": np.searchsorted(ids, pre).astype(np.int64),
            "Postsynaptic_Index": np.searchsorted(ids, post).astype(np.int64),
            "Connectivity": syn,
            "Excitatory": exc,
            "Excitatory x Connectivity": exc * syn,
        },
        columns=list(CONN_COLS),
    )
    conn = conn.sort_values(["Presynaptic_Index", "Postsynaptic_Index"], kind="stable").reset_index(
        drop=True
    )

    totals = input_totals(df)
    stats = BuildStats(
        n_rows=len(df),
        n_neurons=len(ids),
        n_pairs=len(pairs),
        n_pre=len(signs),
        n_pre_inhibitory=int((signs == -1).sum()),
        n_pre_missing_nt=n_missing,
        n_targets=len(totals),
    )
    return ids, conn, totals, stats


def build(connections: Path, out_dir: Path, *, version: str) -> tuple[ModelInputPaths, BuildStats]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = output_paths(out_dir, version)
    df = load_connections(connections)
    ids, conn, totals, stats = build_tables(df)

    completeness_text = ",Completed\n" + "".join(f"{i},True\n" for i in ids.tolist())
    paths.completeness.write_bytes(completeness_text.encode("utf-8"))
    pq.write_table(
        pa.Table.from_pandas(conn, preserve_index=False),
        paths.connectivity,
        compression="snappy",
    )
    pq.write_table(
        pa.Table.from_pandas(totals, preserve_index=False),
        paths.input_totals,
        compression="snappy",
    )

    meta: dict[str, Any] = {
        "schema": 1,
        "data_version": version,
        "sign_rule": SIGN_RULE,
        "inputs": {
            "connections": {"file": connections.name, "sha256": sha256_file(connections)},
        },
        "outputs": {
            key: {"file": path.name, "sha256": sha256_file(path)}
            for key, path in (
                ("completeness", paths.completeness),
                ("connectivity", paths.connectivity),
                ("input_totals", paths.input_totals),
            )
        },
        "stats": asdict(stats),
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "pyarrow": pa.__version__,
        },
    }
    paths.meta.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return paths, stats


def verify_outputs(paths: ModelInputPaths) -> dict[str, Any]:
    if not paths.meta.exists():
        raise IntegrityError(f"{paths.meta} not found; run 'rr-discover model-input' first")
    meta: dict[str, Any] = json.loads(paths.meta.read_text(encoding="utf-8"))
    for key, path in (
        ("completeness", paths.completeness),
        ("connectivity", paths.connectivity),
        ("input_totals", paths.input_totals),
    ):
        if not path.exists():
            raise IntegrityError(f"{path} missing; run 'rr-discover model-input' first")
        expected = meta["outputs"][key]["sha256"]
        actual = sha256_file(path)
        if actual != expected:
            raise IntegrityError(f"{path} sha256 mismatch: expected {expected}, got {actual}")
    return meta
