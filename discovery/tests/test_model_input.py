import math
from pathlib import Path

import pandas as pd
import pyarrow.feather
import pytest
from rr_discovery.data import IntegrityError, sha256_file
from rr_discovery.model_input import (
    CONN_COLS,
    BuildStats,
    build,
    build_tables,
    load_connections,
    output_paths,
    presynaptic_signs,
    verify_outputs,
)

NAN = math.nan

ROWS = [
    (101, 102, "A", 3, 0.1, 0.8, 0.1),
    (101, 102, "B", 2, 0.1, 0.8, 0.1),
    (101, 103, "A", 5, 0.2, 0.7, 0.1),
    (102, 103, "A", 4, 0.6, 0.2, 0.2),
    (102, 104, "B", 1, 0.1, 0.8, 0.1),
    (103, 104, "A", 6, NAN, NAN, NAN),
    (103, 105, "A", 1, NAN, NAN, NAN),
    (104, 101, "A", 2, 0.25, 0.5, 0.25),
]


def _feather(tmp_path: Path, rows: list, name: str = "conn.feather") -> Path:
    records = []
    for pre, post, neuropil, syn, gaba, ach, glut in rows:
        if math.isnan(gaba):
            nt = [NAN] * 6
        else:
            nt = [gaba, ach, glut, 0.0, 0.0, 0.0]
        records.append((pre, post, neuropil, syn, *nt))
    df = pd.DataFrame(
        records,
        columns=[
            "pre_pt_root_id",
            "post_pt_root_id",
            "neuropil",
            "syn_count",
            "gaba_avg",
            "ach_avg",
            "glut_avg",
            "oct_avg",
            "ser_avg",
            "da_avg",
        ],
    ).astype(
        {
            "pre_pt_root_id": "int64",
            "post_pt_root_id": "int64",
            "syn_count": "int64",
            "gaba_avg": "float64",
            "ach_avg": "float64",
            "glut_avg": "float64",
            "oct_avg": "float64",
            "ser_avg": "float64",
            "da_avg": "float64",
        }
    )
    path = tmp_path / name
    pyarrow.feather.write_feather(df, path)
    return path


def test_pair_aggregation(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    conn = build_tables(load_connections(f))[1]
    assert conn.columns.tolist() == list(CONN_COLS)
    pairs = [
        tuple(int(x) for x in r)
        for r in conn[["Presynaptic_ID", "Postsynaptic_ID", "Connectivity"]].itertuples(
            index=False, name=None
        )
    ]
    assert pairs == [
        (101, 102, 5),
        (101, 103, 5),
        (102, 103, 4),
        (102, 104, 1),
        (103, 104, 6),
        (103, 105, 1),
        (104, 101, 2),
    ]
    idx = [
        tuple(int(x) for x in r)
        for r in conn[["Presynaptic_Index", "Postsynaptic_Index"]].itertuples(
            index=False, name=None
        )
    ]
    assert idx == [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 0)]


def test_sign_rule(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    signs, n_missing = presynaptic_signs(load_connections(f))
    assert signs.loc[101] == 1
    assert signs.loc[102] == -1
    assert signs.loc[103] == 1
    assert signs.loc[104] == 1
    assert n_missing == 1
    conn = build_tables(load_connections(f))[1]
    assert conn["Excitatory x Connectivity"].tolist() == [5, 5, -4, -1, 6, 1, 2]
    stats = build_tables(load_connections(f))[3]
    assert stats.n_pre_inhibitory == 1
    assert stats.n_pre_missing_nt == 1


def test_input_totals(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    _, _, totals, stats = build_tables(load_connections(f))
    got = dict(zip(totals["root_id"].tolist(), totals["input_total"].tolist(), strict=True))
    assert got == {101: 2, 102: 5, 103: 9, 104: 7, 105: 1}
    assert stats.n_targets == 5


def test_completeness_bytes(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    paths, _ = build(f, tmp_path / "o", version="t")
    assert paths.completeness.read_bytes() == (
        b",Completed\n101,True\n102,True\n103,True\n104,True\n105,True\n"
    )


def test_stats(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    stats = build_tables(load_connections(f))[3]
    assert stats == BuildStats(
        n_rows=8,
        n_neurons=5,
        n_pairs=7,
        n_pre=4,
        n_pre_inhibitory=1,
        n_pre_missing_nt=1,
        n_targets=5,
    )


def test_deterministic(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    p1, _ = build(f, tmp_path / "out1", version="t")
    p2, _ = build(f, tmp_path / "out2", version="t")
    for a, b in (
        (p1.completeness, p2.completeness),
        (p1.connectivity, p2.connectivity),
        (p1.input_totals, p2.input_totals),
        (p1.meta, p2.meta),
    ):
        assert a.read_bytes() == b.read_bytes()

    shuffled = _feather(tmp_path, list(reversed(ROWS)), name="shuffled.feather")
    p3, _ = build(shuffled, tmp_path / "out3", version="t")
    assert p1.completeness.read_bytes() == p3.completeness.read_bytes()
    assert p1.connectivity.read_bytes() == p3.connectivity.read_bytes()
    assert p1.input_totals.read_bytes() == p3.input_totals.read_bytes()

    meta = verify_outputs(p1)
    assert meta["inputs"]["connections"]["sha256"] == sha256_file(f)


def test_verify_outputs_detects_tamper(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    paths, _ = build(f, tmp_path / "o", version="t")
    verify_outputs(paths)
    with paths.connectivity.open("ab") as fh:
        fh.write(b"\x00")
    with pytest.raises(IntegrityError):
        verify_outputs(paths)


def test_verify_outputs_missing_meta(tmp_path: Path) -> None:
    paths = output_paths(tmp_path / "empty", "t")
    with pytest.raises(IntegrityError, match="rr-discover model-input"):
        verify_outputs(paths)


def test_readable_like_shiu(tmp_path: Path) -> None:
    f = _feather(tmp_path, ROWS)
    paths, _ = build(f, tmp_path / "o", version="t")
    assert pd.read_csv(paths.completeness, index_col=0).index.tolist() == [101, 102, 103, 104, 105]
    assert pd.read_parquet(paths.connectivity).columns.tolist() == list(CONN_COLS)
