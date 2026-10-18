import numpy as np
import pandas as pd
import pytest
from rr_discovery import annotations, extract, sanity
from rr_discovery.identify import LIMITATION, outputs, render_report
from rr_discovery.run import StimSets

ANN = pd.DataFrame(
    {
        "root_id": [101, 102, 201, 202, 301, 302, 401, 402, 403, 404, 405, 406, 407, 501],
        "cell_type": [
            "LC4",
            "LC4",
            "LPLC2",
            "LPLC2",
            "DNp01",
            "DNp01",
            "DNp02",
            "DNp03",
            "DNp04",
            "DNp03",
            "DNp11",
            "DNx99",
            "DNx98",
            "T4",
        ],
        "super_class": [
            "optic",
            "optic",
            "optic",
            "optic",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "optic",
        ],
        "side": [
            "left",
            "left",
            "left",
            "left",
            "left",
            "right",
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
        ],
    }
)
VALID = ANN["root_id"].to_numpy(dtype=np.int64)
MEMBERS = np.array([101, 102, 201, 202, 301, 401, 402, 403, 405, 406, 501], dtype=np.int64)
STIM = StimSets(
    lc4=np.array([101, 102], dtype=np.int64), lplc2=np.array([201, 202], dtype=np.int64)
)
PRIOR = ("DNp02", "DNp03", "DNp04", "DNp06")
REPORTED = ("DNp11",)


def _stats(gf_responsive: bool = True) -> pd.DataFrame:
    root = [301, 401, 403, 404, 405, 406, 501, 302, 402]
    responsive = [True] * 7 + [False, False]
    if not gf_responsive:
        responsive[0] = False
    rate = [5.0] * 7 + [0.1, 0.1]
    return pd.DataFrame(
        {
            "root_id": np.array(root, dtype=np.int64),
            "total_spikes": np.array([10] * 7 + [1, 1], dtype=np.int64),
            "trials_fired": np.array([4] * 7 + [1, 1], dtype=np.int64),
            "rate_hz": np.array(rate, dtype=np.float64),
            "rel_rate": np.array([r / 5.0 for r in rate], dtype=np.float64),
            "trial_frac": np.array([1.0] * 7 + [0.25, 0.25], dtype=np.float64),
            "responsive": np.array(responsive, dtype=bool),
            "rank": np.array([1, 2, 3, 4, 5, 6, 7, 0, 0], dtype=np.int64),
        }
    )


def _connectivity(drop_post: tuple[int, ...] = ()) -> pd.DataFrame:
    rows = [
        (101, 401, 20),
        (201, 402, 20),
        (101, 403, 5),
        (202, 404, 15),
        (202, 405, 12),
        (201, 406, 30),
        (101, 301, 50),
    ]
    rows = [r for r in rows if r[1] not in drop_post]
    return pd.DataFrame(
        {
            "Presynaptic_ID": np.array([r[0] for r in rows], dtype=np.int64),
            "Postsynaptic_ID": np.array([r[1] for r in rows], dtype=np.int64),
            "Connectivity": np.array([r[2] for r in rows], dtype=np.int64),
            "Excitatory": np.ones(len(rows), dtype=np.int64),
        }
    )


def _totals() -> pd.DataFrame:
    posts = [301, 401, 402, 403, 404, 405, 406]
    return pd.DataFrame(
        {
            "root_id": np.array(posts, dtype=np.int64),
            "input_total": np.full(len(posts), 1000, dtype=np.int64),
        }
    )


def _run(
    *,
    stats: pd.DataFrame | None = None,
    connectivity: pd.DataFrame | None = None,
):
    return outputs(
        ann=ANN,
        valid_ids=VALID,
        stats=_stats() if stats is None else stats,
        members=MEMBERS,
        stim=STIM,
        connectivity=_connectivity() if connectivity is None else connectivity,
        input_totals=_totals(),
        gf_cell_type="DNp01",
        prior_cell_types=PRIOR,
        reported_cell_types=REPORTED,
    )


def test_roles_follow_adr15() -> None:
    out = _run()
    by_id = {c.root_id: c for c in out.candidates}

    assert by_id[401].role == "output_parallel"
    assert by_id[401].label == "prior"
    assert by_id[401].evidence == "LOW"

    assert by_id[402].role == "inter"
    assert (by_id[402].check_i, by_id[402].check_ii, by_id[402].check_iii) == (False, True, True)

    assert by_id[403].role == "inter"
    assert (by_id[403].check_i, by_id[403].check_ii, by_id[403].check_iii) == (True, False, True)

    assert by_id[404].role == "not in circuit"
    assert (by_id[404].check_i, by_id[404].check_ii, by_id[404].check_iii) == (True, True, False)

    assert by_id[405].role == "output_parallel"
    assert by_id[405].label == "reported"
    assert by_id[405].evidence == "data-driven"

    assert by_id[406].role == "output_parallel"
    assert by_id[406].label == "data-driven"

    assert 407 not in by_id
    assert 302 not in by_id
    assert out.gf_ids.tolist() == [301]
    assert ("DNp06", "no neurons of this cell type in the v783 annotations") in out.absent_types
    assert out.parallel_output == "present"
    assert [r.root_id for r in out.gf_rows] == [301, 302]
    assert [r.responsive for r in out.gf_rows] == [True, False]
    assert [r.side for r in out.gf_rows] == [
        str(ANN.loc[ANN["root_id"] == 301, "side"].iloc[0]),
        str(ANN.loc[ANN["root_id"] == 302, "side"].iloc[0]),
    ]
    assert "DNp06" in out.prior_cell_types
    assert out.parallel_reason == "3 candidate(s) passed ADR-15 checks (i)-(iii)"

    assert (by_id[403].lc4_raw, by_id[403].lc4_kept) == (5, 0)
    assert (by_id[401].lc4_raw, by_id[401].lc4_kept) == (20, 20)


def test_report_content() -> None:
    out = _run()
    rule = extract.ResponsiveRule()
    text = render_report(out, data_version="v783", rule=rule, gf_cell_type="DNp01", summary=None)
    assert (
        "| cell_type | root_id | side | label | evidence | responsive | rate Hz | rel rate | "
        "trial frac | LC4 syn raw | LC4 syn kept | LPLC2 syn raw | LPLC2 syn kept | "
        "(i) | (ii) | (iii) | role |"
    ) in text
    assert "DNp06" in text
    assert "DNp11" in text
    assert "LOW" in text
    assert "No candidate is literature-confirmed in M5" in text
    assert "literature-confirmed |" not in text
    side301 = str(ANN.loc[ANN["root_id"] == 301, "side"].iloc[0])
    side302 = str(ANN.loc[ANN["root_id"] == 302, "side"].iloc[0])
    assert "## Giant fiber (DNp01)" in text
    assert "| root_id | side | responsive | rate Hz | rel rate | trial frac |" in text
    assert any(line.startswith(f"| 301 | {side301} | yes | ") for line in text.splitlines())
    assert any(line.startswith(f"| 302 | {side302} | no | ") for line in text.splitlines())
    assert "prior set {DNp02, DNp03, DNp04, DNp06}" in text
    assert text == render_report(
        out, data_version="v783", rule=rule, gf_cell_type="DNp01", summary=None
    )


def test_no_parallel_reason() -> None:
    out = _run(connectivity=_connectivity(drop_post=(401, 405, 406)))
    assert out.parallel_output == "none"
    text = render_report(
        out,
        data_version="v783",
        rule=extract.ResponsiveRule(),
        gf_cell_type="DNp01",
        summary=None,
    )
    assert LIMITATION in text


def test_gf_not_responsive_gives_empty_gf() -> None:
    out = _run(stats=_stats(gf_responsive=False))
    assert out.gf_ids.size == 0


def test_labels_helper() -> None:
    labels = annotations.labels(ANN, np.array([999, 101]))
    row = labels.set_index("root_id")
    assert row.loc[999, "cell_type"] == ""
    assert row.loc[101, "cell_type"] == "LC4"


def test_check_gf_in_circuit_raises() -> None:
    with pytest.raises(sanity.SanityError):
        sanity.check_gf_in_circuit(np.array([1]), np.array([1]))
