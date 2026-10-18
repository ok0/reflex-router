import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyarrow.feather

from rr_discovery.annotations import (
    descending_ids,
    ids_by_cell_type,
    load_annotations,
    load_root_ids,
    near_matches,
    root_id_column,
)
from rr_discovery.config import DiscoveryConfig
from rr_discovery.data import Paths, read_manifest
from rr_discovery.sanity import SanityError, check_left_dnp01

PRE_COLS = ("pre_pt_root_id", "pre_root_id", "pre")
POST_COLS = ("post_pt_root_id", "post_root_id", "post")
SYN_COLS = ("syn_count", "syn_cnt", "count", "synapse_count")
NT_RE = re.compile(r"(^nt_|_nt$|nt_type|gaba|ach|glut|oct|ser|da_avg|dop)", re.I)
LOOKUP_TYPES = ("LC4", "LPLC2", "DNp01")


@dataclass
class SchemaReport:
    conn_columns: list[tuple[str, str]] = field(default_factory=list)
    conn_rows: int = 0
    pre_col: str | None = None
    post_col: str | None = None
    syn_col: str | None = None
    min_syn_row: int | None = None
    min_syn_pair: int | None = None
    n_pairs: int = 0
    pairs_lt5: int = 0
    pairs_le10: int = 0
    threshold_verdict: str = ""
    nt_columns: list[str] = field(default_factory=list)
    input_totals_derivable: bool = False
    n_targets: int = 0
    n_root_ids: int = 0
    n_conn_ids: int = 0
    conn_ids_in_rootlist: int = 0
    conn_ids_not_in_rootlist: int = 0
    ann_columns: list[tuple[str, str]] = field(default_factory=list)
    ann_root_col: str | None = None
    n_ann_ids: int = 0
    rootlist_in_ann: int = 0
    rootlist_not_in_ann: int = 0
    conn_ids_in_ann: int = 0
    lookups: dict[str, int] = field(default_factory=dict)
    near: dict[str, list[str]] = field(default_factory=dict)
    sanity_left_dnp01: bool | None = None
    file_hashes: dict[str, str] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unresolved and self.sanity_left_dnp01 is True


def _resolve(names: list[str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _verdict(min_syn_row: int | None) -> str:
    if min_syn_row is None:
        return "UNRESOLVED: no synapse-count column"
    if min_syn_row == 1:
        return "NOT thresholded: minimum syn_count per row is 1"
    if min_syn_row > 1:
        return (
            f"Already thresholded: minimum syn_count per row is {min_syn_row} "
            f"(rows below {min_syn_row} absent)"
        )
    return f"UNRESOLVED: minimum syn_count per row is {min_syn_row}"


def inspect(paths: Paths, cfg: DiscoveryConfig) -> SchemaReport:
    report = SchemaReport()

    table = pyarrow.feather.read_table(paths.connections, memory_map=True)
    report.conn_columns = [(f.name, str(f.type)) for f in table.schema]
    report.conn_rows = table.num_rows
    names = [name for name, _ in report.conn_columns]
    df = table.to_pandas()

    report.pre_col = _resolve(names, PRE_COLS)
    report.post_col = _resolve(names, POST_COLS)
    report.syn_col = _resolve(names, SYN_COLS)
    if report.pre_col is None:
        report.unresolved.append("pre-synaptic root-ID column not found")
    if report.post_col is None:
        report.unresolved.append("post-synaptic root-ID column not found")
    if report.syn_col is None:
        report.unresolved.append("synapse-count column not found")

    if report.syn_col is not None:
        report.min_syn_row = int(df[report.syn_col].min())
    report.threshold_verdict = _verdict(report.min_syn_row)

    if report.pre_col and report.post_col and report.syn_col:
        pair_sums = df.groupby([report.pre_col, report.post_col])[report.syn_col].sum()
        report.n_pairs = int(len(pair_sums))
        report.min_syn_pair = int(pair_sums.min())
        report.pairs_lt5 = int((pair_sums < 5).sum())
        report.pairs_le10 = int((pair_sums <= 10).sum())
        report.n_targets = int(df[report.post_col].nunique())
        report.input_totals_derivable = True

    report.nt_columns = [name for name in names if NT_RE.search(name)]

    root_ids = load_root_ids(paths.root_ids)
    report.n_root_ids = int(root_ids.size)
    if report.pre_col and report.post_col:
        conn_ids = np.unique(
            np.concatenate([df[report.pre_col].to_numpy(), df[report.post_col].to_numpy()])
        ).astype(np.int64)
    else:
        conn_ids = np.empty(0, dtype=np.int64)
    report.n_conn_ids = int(conn_ids.size)
    conn_in_root = int(np.isin(conn_ids, root_ids).sum())
    report.conn_ids_in_rootlist = conn_in_root
    report.conn_ids_not_in_rootlist = report.n_conn_ids - conn_in_root

    ann = load_annotations(paths.annotations)
    report.ann_columns = [(str(col), str(dtype)) for col, dtype in ann.dtypes.items()]
    try:
        root_col: str | None = root_id_column(ann)
    except KeyError as e:
        report.unresolved.append(str(e.args[0]))
        root_col = None
    report.ann_root_col = root_col

    if root_col is not None:
        ann_ids = np.unique(ann[root_col].dropna().to_numpy().astype(np.int64))
        report.n_ann_ids = int(ann_ids.size)
        root_in_ann = int(np.isin(root_ids, ann_ids).sum())
        report.rootlist_in_ann = root_in_ann
        report.rootlist_not_in_ann = report.n_root_ids - root_in_ann
        report.conn_ids_in_ann = int(np.isin(conn_ids, ann_ids).sum())

        dnp01: np.ndarray | None = None
        for cell_type in LOOKUP_TYPES:
            ids = ids_by_cell_type(ann, cell_type, valid_ids=root_ids)
            report.lookups[cell_type] = int(ids.size)
            if cell_type == "DNp01":
                dnp01 = ids
            if ids.size == 0:
                report.near[cell_type] = near_matches(ann, cell_type)
                report.unresolved.append(f"cell_type '{cell_type}' not found (see near matches)")
        report.lookups["descending"] = int(descending_ids(ann, valid_ids=root_ids).size)

        if dnp01 is not None:
            report.sanity_left_dnp01 = True
            try:
                check_left_dnp01(dnp01)
            except SanityError as e:
                report.sanity_left_dnp01 = False
                report.unresolved.append(str(e))

    report.file_hashes = {name: entry.sha256 for name, entry in read_manifest(cfg.manifest).items()}
    return report


def _or_unresolved(value: str | None) -> str:
    return value if value is not None else "unresolved"


def render(report: SchemaReport, cfg: DiscoveryConfig) -> str:
    lines: list[str] = []
    add = lines.append

    add(f"# Schema report — FlyWire {cfg.version}")
    add("")
    add("## Sources")
    add("")
    add(f"- Zenodo DOI: {cfg.zenodo.doi} (record {cfg.zenodo.record})")
    add(f"- Annotations: {cfg.annotations.repo}@{cfg.annotations.tag}, path {cfg.annotations.path}")
    add("")
    add("| File | sha256 |")
    add("| --- | --- |")
    for name, sha in report.file_hashes.items():
        add(f"| {name} | {sha} |")
    add("")

    add("## Connection table")
    add("")
    add(f"- Rows: {report.conn_rows}")
    add("")
    add("| Column | Type |")
    add("| --- | --- |")
    for name, dtype in report.conn_columns:
        add(f"| {name} | {dtype} |")
    add("")
    add(f"- Pre-synaptic column: {_or_unresolved(report.pre_col)}")
    add(f"- Post-synaptic column: {_or_unresolved(report.post_col)}")
    add(f"- Synapse-count column: {_or_unresolved(report.syn_col)}")
    add("")

    add("## Threshold")
    add("")
    add(
        "- Minimum syn_count per row: "
        f"{report.min_syn_row if report.min_syn_row is not None else 'unresolved'}"
    )
    add(
        "- Minimum syn_count per (pre, post) pair after summing neuropils: "
        f"{report.min_syn_pair if report.min_syn_pair is not None else 'unresolved'}"
    )
    add(f"- Pairs < 5: {report.pairs_lt5} (of {report.n_pairs})")
    add(f"- Pairs ≤ 10: {report.pairs_le10} (of {report.n_pairs})")
    add("")
    add(f"**Verdict:** {report.threshold_verdict}")
    add("")

    add("## Neurotransmitter fields")
    add("")
    if report.nt_columns:
        for name in report.nt_columns:
            add(f"- {name}")
    else:
        add("none found")
    add("")

    add("## Per-target input totals")
    add("")
    add(f"- derivable: {'yes' if report.input_totals_derivable else 'no'}")
    add(f"- Number of targets: {report.n_targets}")
    add("- Note: sums over proofread connections only.")
    add("")

    add("## Root-ID coverage")
    add("")
    add("| Measure | Count |")
    add("| --- | --- |")
    add(f"| Root-ID list size | {report.n_root_ids} |")
    add(f"| Connection-table IDs | {report.n_conn_ids} |")
    add(f"| Connection IDs in root list | {report.conn_ids_in_rootlist} |")
    add(f"| Connection IDs not in root list | {report.conn_ids_not_in_rootlist} |")
    add(f"| Annotation IDs | {report.n_ann_ids} |")
    add(f"| Annotation root column used | {_or_unresolved(report.ann_root_col)} |")
    add(f"| Root list in annotations | {report.rootlist_in_ann} |")
    add(f"| Root list not in annotations | {report.rootlist_not_in_ann} |")
    add(f"| Connection IDs in annotations | {report.conn_ids_in_ann} |")
    add("")

    add("## Annotation table")
    add("")
    if report.ann_columns:
        add("| Column | Type |")
        add("| --- | --- |")
        for name, dtype in report.ann_columns:
            add(f"| {name} | {dtype} |")
    else:
        add("not loaded")
    add("")

    add("## Cell-type lookups (restricted to root-ID list)")
    add("")
    for key in ("LC4", "LPLC2", "DNp01", "descending"):
        if key in report.lookups:
            add(f"- {key}: {report.lookups[key]}")
    add("- Naming mapping used: exact case-sensitive match")
    if report.near:
        add("")
        add("Near matches for zero-count types:")
        for key, values in report.near.items():
            add(f"- {key}: {', '.join(values) if values else 'none'}")
    add("")

    add("## Sanity check")
    add("")
    if report.sanity_left_dnp01 is True:
        add("- left DNp01 present: PASS")
    elif report.sanity_left_dnp01 is False:
        add("- left DNp01 present: FAIL")
    else:
        add("- left DNp01 present: not run")
    add("")

    add("## Unresolved")
    add("")
    if report.unresolved:
        for item in report.unresolved:
            add(f"- {item}")
    else:
        add("none")

    return "\n".join(lines) + "\n"


def write_report(report: SchemaReport, reports_dir: Path, cfg: DiscoveryConfig) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / "schema_report.md"
    out.write_text(render(report, cfg), encoding="utf-8")
    return out
