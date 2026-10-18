from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather
import pytest
from rr_discovery import sanity
from rr_discovery.cli import main
from rr_discovery.config import DiscoveryConfig, load_config
from rr_discovery.data import Paths, paths_from_config
from rr_discovery.schema import inspect, render, write_report

LEFT = sanity.LEFT_DNP01_V783

DEFAULT_ANN_ROWS: tuple[tuple[int, str | None, str], ...] = (
    (1, "LC4", "optic"),
    (2, "LC4", "optic"),
    (3, "LPLC2", "optic"),
    (LEFT, "DNp01", "descending"),
    (20, None, "central"),
)
DEFAULT_ROOTS: tuple[int, ...] = (1, 2, 3, 10, LEFT)

CONFIG_TEXT = """\
[data]
version = "v783"
data_dir = "raw"
reports_dir = "reports"
manifest = "manifest.toml"

[zenodo]
record = "10676866"
doi = "10.5281/zenodo.10676866"
files = ["proofread_connections_783.feather", "proofread_root_ids_783.npy"]

[annotations]
repo = "flyconnectome/flywire_annotations"
tag = "v3.2.0"
path = "supplemental_files/Supplemental_file1_neuron_annotations.tsv"
"""


def _build(
    tmp_path: Path,
    *,
    pre: Sequence[int] = (1, 1, 2, 3),
    post: Sequence[int] = (10, 10, 10, 11),
    syn: Sequence[int] = (1, 2, 1, 3),
    neuropil: Sequence[str] = ("A", "B", "A", "A"),
    nt: Sequence[str] = ("ach", "gaba", "ach", "glut"),
    gaba: Sequence[float] = (0.1, 0.2, 0.3, 0.4),
    roots: Sequence[int] = DEFAULT_ROOTS,
    ann_rows: Sequence[tuple[int, str | None, str]] = DEFAULT_ANN_ROWS,
) -> tuple[DiscoveryConfig, Paths]:
    cfg_path = tmp_path / "discovery.toml"
    cfg_path.write_text(CONFIG_TEXT, encoding="utf-8")
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (tmp_path / "manifest.toml").write_text(
        f'[files."proofread_root_ids_783.npy"]\nsha256 = "{"a" * 64}"\nsize = 1\nsource = "x"\n',
        encoding="utf-8",
    )
    table = pa.table(
        {
            "pre_pt_root_id": pa.array(list(pre), type=pa.int64()),
            "post_pt_root_id": pa.array(list(post), type=pa.int64()),
            "neuropil": pa.array(list(neuropil), type=pa.string()),
            "syn_count": pa.array(list(syn), type=pa.int64()),
            "nt_type": pa.array(list(nt), type=pa.string()),
            "gaba_avg": pa.array(list(gaba), type=pa.float64()),
        }
    )
    pyarrow.feather.write_feather(table, raw / "proofread_connections_783.feather")
    np.save(raw / "proofread_root_ids_783.npy", np.array(list(roots), dtype=np.int64))
    pd.DataFrame(list(ann_rows), columns=["root_783", "cell_type", "super_class"]).to_csv(
        raw / "Supplemental_file1_neuron_annotations.tsv", sep="\t", index=False
    )
    cfg = load_config(cfg_path, base_dir=tmp_path)
    return cfg, paths_from_config(cfg)


def test_not_thresholded(tmp_path: Path) -> None:
    cfg, paths = _build(tmp_path)
    report = inspect(paths, cfg)
    assert report.threshold_verdict.startswith("NOT thresholded")
    assert report.min_syn_row == 1


def test_pair_sums_aggregate_across_neuropils(tmp_path: Path) -> None:
    cfg, paths = _build(
        tmp_path,
        pre=(1, 1, 2),
        post=(10, 10, 11),
        syn=(1, 2, 4),
        neuropil=("A", "B", "A"),
        nt=("ach", "gaba", "ach"),
        gaba=(0.1, 0.2, 0.3),
        roots=(1, 2, 10, 11, LEFT),
    )
    report = inspect(paths, cfg)
    assert report.min_syn_pair == 3


def test_thresholded(tmp_path: Path) -> None:
    cfg, paths = _build(
        tmp_path,
        pre=(1, 1, 2),
        post=(10, 10, 11),
        syn=(5, 6, 7),
        neuropil=("A", "B", "A"),
        nt=("ach", "gaba", "ach"),
        gaba=(0.1, 0.2, 0.3),
        roots=(1, 2, 10, 11, LEFT),
    )
    report = inspect(paths, cfg)
    assert report.threshold_verdict.startswith("Already thresholded")
    assert "5" in report.threshold_verdict


def test_nt_and_totals(tmp_path: Path) -> None:
    cfg, paths = _build(tmp_path)
    report = inspect(paths, cfg)
    assert report.nt_columns == ["nt_type", "gaba_avg"]
    assert report.input_totals_derivable is True
    assert report.n_targets == len({10, 11})


def test_coverage(tmp_path: Path) -> None:
    cfg, paths = _build(tmp_path)
    report = inspect(paths, cfg)
    assert report.conn_ids_not_in_rootlist == 1
    assert report.n_ann_ids == 5
    assert report.rootlist_in_ann == 4
    assert report.rootlist_not_in_ann == 1
    assert report.conn_ids_in_ann == 3


def test_report_rendered(tmp_path: Path) -> None:
    cfg, paths = _build(tmp_path)
    report = inspect(paths, cfg)
    out = write_report(report, cfg.reports_dir, cfg)
    assert out == cfg.reports_dir / "schema_report.md"
    text = out.read_text(encoding="utf-8")
    for heading in (
        "# Schema report — FlyWire v783",
        "## Sources",
        "## Connection table",
        "## Threshold",
        "## Neurotransmitter fields",
        "## Per-target input totals",
        "## Root-ID coverage",
        "## Annotation table",
        "## Cell-type lookups (restricted to root-ID list)",
        "## Sanity check",
        "## Unresolved",
    ):
        assert heading in text
    assert "Verdict" in text
    assert "nt_type" in text
    assert "int64" in text
    assert "left DNp01 present: PASS" in text
    assert str(LEFT) not in text
    assert report.ok is True


def test_sanity_fail_marks_not_ok(tmp_path: Path) -> None:
    cfg, paths = _build(
        tmp_path,
        roots=(1, 2, 3, 4, 10),
        ann_rows=(
            (1, "LC4", "optic"),
            (2, "LC4", "optic"),
            (3, "LPLC2", "optic"),
            (4, "DNp01", "descending"),
        ),
    )
    report = inspect(paths, cfg)
    assert report.sanity_left_dnp01 is False
    assert report.ok is False
    assert "FAIL" in render(report, cfg)


def test_cli_inspect_missing_data(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg_path = tmp_path / "discovery.toml"
    cfg_path.write_text(CONFIG_TEXT, encoding="utf-8")
    code = main(["inspect", "--config", str(cfg_path), "--data-dir", str(tmp_path / "none")])
    assert code == 1
    assert "run 'rr-discover fetch' first" in capsys.readouterr().err
