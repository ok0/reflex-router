import numpy as np
import pandas as pd
import pytest
from rr_discovery.model_input import CONN_COLS
from rr_discovery.retention import (
    core_metrics,
    direct_input_ids,
    edge_metrics,
    gf_identity,
    parallel_identity,
    persistence,
    spearman,
)


def test_core_metrics_basic():
    m = core_metrics(
        base_core=np.array([1, 2, 3, 4, 5]),
        base_rel={2: 0.9, 3: 0.5, 4: 0.1},
        cond_responsive=np.array([2, 3, 4, 6, 7]),
        cond_rel={2: 0.8, 3: 0.2, 4: 0.4},
        cond_stimulated=np.array([5, 9]),
    )
    assert m.n_stimulated == 2
    assert m.n_core_excluded == 1
    assert m.reference_size == 4
    assert m.retained == 3
    assert m.core_retention == pytest.approx(0.75)
    assert m.jaccard == pytest.approx(0.5)
    assert m.n_new == 2
    assert m.n_both == 3
    assert m.spearman == pytest.approx(0.5)


def test_core_metrics_edge_cases():
    empty = core_metrics(
        base_core=np.array([], dtype=np.int64),
        base_rel={},
        cond_responsive=np.array([], dtype=np.int64),
        cond_rel={},
        cond_stimulated=np.array([], dtype=np.int64),
    )
    assert empty.reference_size == 0
    assert empty.core_retention is None
    assert empty.jaccard is None
    assert empty.n_new == 0
    same = core_metrics(
        base_core=np.array([1, 2]),
        base_rel={1: 0.1, 2: 0.2},
        cond_responsive=np.array([1, 2]),
        cond_rel={1: 0.1, 2: 0.2},
        cond_stimulated=np.array([], dtype=np.int64),
    )
    assert same.core_retention == 1.0
    assert same.jaccard == 1.0
    disjoint = core_metrics(
        base_core=np.array([1, 2]),
        base_rel={1: 0.1, 2: 0.2},
        cond_responsive=np.array([3]),
        cond_rel={3: 0.3},
        cond_stimulated=np.array([], dtype=np.int64),
    )
    assert disjoint.core_retention == 0.0
    assert disjoint.jaccard == 0.0
    assert disjoint.n_new == 1


def test_spearman():
    assert spearman([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)
    assert spearman([1, 1, 2], [1, 2, 3]) == pytest.approx(0.8660254, abs=1e-7)
    assert spearman([1.0], [2.0]) is None
    assert spearman([1, 1, 1], [1, 2, 3]) is None


def test_edge_metrics():
    base = pd.DataFrame({"pre": [1, 2, 3], "post": [2, 3, 4], "syn": [5, 5, 5]})
    cond = pd.DataFrame({"pre": [1, 3, 4], "post": [2, 4, 5], "syn": [5, 5, 5]})
    m = edge_metrics(base_edges=base, cond_members=np.array([1, 2, 3, 4, 5]), cond_edges=cond)
    assert m.n_edges_shared == 2
    assert m.edge_jaccard == pytest.approx(0.5)
    empty = pd.DataFrame({"pre": [], "post": [], "syn": []}).astype("int64")
    none = edge_metrics(
        base_edges=empty, cond_members=np.array([], dtype=np.int64), cond_edges=empty
    )
    assert none.edge_jaccard is None


def _stats(rows: list[tuple[int, bool, float, float, float, int]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=["root_id", "responsive", "rate_hz", "rel_rate", "trial_frac", "rank"],
    )


def test_gf_identity_cases():
    gf_type = np.array([301, 302], dtype=np.int64)
    base = np.array([301, 302], dtype=np.int64)
    both = _stats([(301, True, 5.0, 1.0, 1.0, 1), (302, True, 4.0, 0.8, 1.0, 2)])
    eq = gf_identity(gf_type_ids=gf_type, base_gf_ids=base, cond_stats=both)
    assert eq.equals_baseline is True
    one = _stats([(301, True, 5.0, 1.0, 1.0, 1), (302, False, 0.5, 0.1, 0.25, 0)])
    partial = gf_identity(gf_type_ids=gf_type, base_gf_ids=base, cond_stats=one)
    assert partial.ids == (301,)
    assert partial.equals_baseline is False
    assert [m.root_id for m in partial.missing] == [302]
    assert partial.missing[0].rank is None
    none = gf_identity(gf_type_ids=gf_type, base_gf_ids=base, cond_stats=_stats([]))
    assert none.ids == ()
    assert [m.rate_hz for m in none.missing] == [0.0, 0.0]


def test_parallel_identity_cases():
    cell_type_of = {401: "DNp02", 402: "DNp03", 403: "DNp04", 404: "DNx99"}
    tracked = ["DNp02", "DNp03", "DNp04", "DNx99"]
    eligible = np.array([401, 402, 404], dtype=np.int64)
    base = np.array([401, 402], dtype=np.int64)
    everyone = np.array([401, 402, 403, 404], dtype=np.int64)

    kept = parallel_identity(
        base_parallel_ids=base,
        eligible_ids=eligible,
        cell_type_of=cell_type_of,
        tracked_types=tracked,
        cond_responsive=np.array([401, 402], dtype=np.int64),
        cond_members=np.array([401, 402], dtype=np.int64),
        cond_stimulated=np.array([], dtype=np.int64),
    )
    assert kept.equals_baseline is True
    assert kept.baseline_has_parallel is True

    partly = parallel_identity(
        base_parallel_ids=base,
        eligible_ids=eligible,
        cell_type_of=cell_type_of,
        tracked_types=tracked,
        cond_responsive=np.array([401], dtype=np.int64),
        cond_members=np.array([401], dtype=np.int64),
        cond_stimulated=np.array([], dtype=np.int64),
    )
    assert partly.lost == ((402, "DNp03", False, False),)

    new = parallel_identity(
        base_parallel_ids=base,
        eligible_ids=eligible,
        cell_type_of=cell_type_of,
        tracked_types=tracked,
        cond_responsive=everyone,
        cond_members=everyone,
        cond_stimulated=np.array([], dtype=np.int64),
    )
    assert new.new_ids == (404,)
    assert new.new_cell_types == ("DNx99",)
    assert 403 not in new.condition_ids

    empty = parallel_identity(
        base_parallel_ids=np.array([], dtype=np.int64),
        eligible_ids=eligible,
        cell_type_of=cell_type_of,
        tracked_types=tracked,
        cond_responsive=everyone,
        cond_members=everyone,
        cond_stimulated=np.array([], dtype=np.int64),
    )
    assert empty.baseline_has_parallel is False
    assert all(row.n_baseline == 0 for row in empty.per_type)


def test_direct_input_ids():
    conn = pd.DataFrame(
        [
            (1, 401, 1, 401, 50, 1, 50),
            (1, 402, 1, 402, 2, 1, 2),
            (9, 402, 9, 402, 998, 1, 998),
        ],
        columns=list(CONN_COLS),
    )
    totals = pd.DataFrame({"root_id": [401, 402], "input_total": [1000, 1000]})
    got = direct_input_ids(
        conn,
        totals,
        stim_all=np.array([1], dtype=np.int64),
        candidate_ids=np.array([401, 402], dtype=np.int64),
    )
    assert got.tolist() == [401]


def test_persistence_bins():
    records = [
        ("A", "rate", np.array([1, 2]), np.array([], dtype=np.int64)),
        ("B", "rate", np.array([1]), np.array([], dtype=np.int64)),
        ("C", "subset_side", np.array([1, 3]), np.array([2])),
    ]
    out = persistence(records, roles={})
    assert out["n_conditions"] == 3
    neurons = {n["root_id"]: n for n in out["neurons"]}
    assert (neurons[1]["n_responsive"], neurons[1]["n_eligible"]) == (3, 3)
    assert (neurons[2]["n_responsive"], neurons[2]["n_eligible"]) == (1, 2)
    assert (neurons[3]["n_responsive"], neurons[3]["n_eligible"]) == (1, 3)
    counts = {b["label"]: b["count"] for b in out["bins"]}
    assert counts == {"100%": 1, ">=90%": 1, ">=75%": 1, ">=50%": 2}
    assert neurons[1]["per_family"]["rate"] == [2, 2]
    assert neurons[2]["per_family"]["rate"] == [1, 2]
    assert neurons[2]["per_family"]["subset_side"] == [0, 0]
