import numpy as np
import pandas as pd
import pytest
from rr_discovery.controls import (
    ControlsError,
    chance_reference,
    check_shuffle,
    condition_stim,
    degree_preserving_shuffle,
    random_set,
    shuffle_tables,
    side_labels,
    side_sets,
)
from rr_discovery.model_input import CONN_COLS
from rr_discovery.run import StimSets

N = 30
KS = (1, 2, 5, 11)


def _graph() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    pre = np.array([i for k in KS for i in range(N)], dtype=np.int64)
    post = np.array([(i + k) % N for k in KS for i in range(N)], dtype=np.int64)
    syn = np.array([1 + (7 * i + k) % 13 for k in KS for i in range(N)], dtype=np.int64)
    sign_by_pre = np.array([-1 if i % 3 == 0 else 1 for i in range(N)], dtype=np.int64)
    return pre, post, syn, sign_by_pre


def _all_true(checks: dict[str, int | bool]) -> bool:
    return all(v for v in checks.values() if isinstance(v, bool))


def test_shuffle_preserves_degrees_and_counts():
    pre, post, syn, sign_by_pre = _graph()
    sign = sign_by_pre[pre]
    res = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    checks = check_shuffle(pre, post, syn, sign, pre, res.post_idx, syn, sign, n_nodes=N)
    assert _all_true(checks)
    assert res.self_loops_after == 0
    assert res.n_changed_edges > 0
    assert res.n_accepted > 0


def _shuffled_checks(
    pre_after: np.ndarray,
    post_after: np.ndarray,
    syn_after: np.ndarray,
    sign_after: np.ndarray,
) -> dict[str, int | bool]:
    pre, post, syn, sign_by_pre = _graph()
    sign = sign_by_pre[pre]
    return check_shuffle(
        pre, post, syn, sign, pre_after, post_after, syn_after, sign_after, n_nodes=N
    )


def test_check_shuffle_detects_out_degree():
    pre, post, syn, sign_by_pre = _graph()
    sign = sign_by_pre[pre]
    res = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    bad_pre = pre.copy()
    bad_pre[0] = (bad_pre[0] + 1) % N
    checks = _shuffled_checks(bad_pre, res.post_idx, syn, sign)
    assert checks["out_degree_equal"] is False


def test_check_shuffle_detects_in_degree():
    pre, post, syn, sign_by_pre = _graph()
    sign = sign_by_pre[pre]
    res = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    bad_post = res.post_idx.copy()
    bad_post[0] = (bad_post[0] + 1) % N
    checks = _shuffled_checks(pre, bad_post, syn, sign)
    assert checks["in_degree_equal"] is False


def test_check_shuffle_detects_syn_multiset():
    pre, post, syn, sign_by_pre = _graph()
    sign = sign_by_pre[pre]
    res = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    bad_syn = syn.copy()
    bad_syn[0] += 1
    checks = _shuffled_checks(pre, res.post_idx, bad_syn, sign)
    assert checks["syn_multiset_equal"] is False


def test_check_shuffle_detects_signs():
    pre, post, syn, sign_by_pre = _graph()
    sign = sign_by_pre[pre]
    res = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    bad_sign = sign.copy()
    bad_sign[0] = -bad_sign[0]
    checks = _shuffled_checks(pre, res.post_idx, syn, bad_sign)
    assert checks["signs_follow_pre"] is False


def test_shuffle_deterministic():
    pre, post, _, _ = _graph()
    a = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    b = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    c = degree_preserving_shuffle(pre, post, n_nodes=N, seed=2, rounds=5)
    assert np.array_equal(a.post_idx, b.post_idx)
    assert not np.array_equal(a.post_idx, c.post_idx)


def test_shuffle_no_new_self_loops():
    pre, post, syn, sign_by_pre = _graph()
    pre = np.append(pre, 3)
    post = np.append(post, 3)
    syn = np.append(syn, 4)
    sign = sign_by_pre[pre]
    res = degree_preserving_shuffle(pre, post, n_nodes=N, seed=1, rounds=5)
    checks = check_shuffle(pre, post, syn, sign, pre, res.post_idx, syn, sign, n_nodes=N)
    assert res.self_loops_after <= 1
    assert checks["no_duplicates"] is True
    assert checks["no_new_self_loops"] is True


def test_shuffle_tables_recompute_totals():
    rows = []
    for a in range(4):
        for b in range(4):
            if a == b:
                continue
            syn = 1 + (3 * a + b) % 5
            exc = 1 if a % 2 == 0 else 0
            rows.append(
                {
                    "Presynaptic_ID": 1000 + a,
                    "Postsynaptic_ID": 1000 + b,
                    "Presynaptic_Index": a,
                    "Postsynaptic_Index": b,
                    "Connectivity": syn,
                    "Excitatory": exc,
                    "Excitatory x Connectivity": syn if exc else -syn,
                }
            )
    conn = pd.DataFrame(rows, columns=list(CONN_COLS))
    pre = conn["Presynaptic_Index"].to_numpy(dtype=np.int64)
    post = conn["Postsynaptic_Index"].to_numpy(dtype=np.int64)
    res = degree_preserving_shuffle(pre, post, n_nodes=4, seed=3, rounds=4)
    out, totals = shuffle_tables(conn, res)
    assert list(out.columns) == list(CONN_COLS)
    sums: dict[int, int] = {}
    for root, value in zip(
        out["Postsynaptic_ID"].tolist(), out["Connectivity"].tolist(), strict=True
    ):
        sums[int(root)] = sums.get(int(root), 0) + int(value)
    assert totals["root_id"].tolist() == sorted(sums)
    assert totals["input_total"].tolist() == [sums[r] for r in totals["root_id"].tolist()]
    per_pre = out.groupby("Presynaptic_ID")["Excitatory"].nunique()
    assert (per_pre == 1).all()


def _ann() -> pd.DataFrame:
    rows = [
        (101, "LC4", "left"),
        (102, "LC4", "right"),
        (103, "LC4", "na"),
        (201, "LPLC2", "left"),
        (202, "LPLC2", "right"),
    ]
    return pd.DataFrame(rows, columns=["root_id", "cell_type", "side"])


def test_side_sets_and_condition_stim():
    stim = StimSets(
        lc4=np.array([101, 102, 103], dtype=np.int64),
        lplc2=np.array([201, 202], dtype=np.int64),
    )
    sides = side_sets(_ann(), stim, left_label="left", right_label="right")
    assert sides.lc4["left"].tolist() == [101]
    assert sides.lc4["right"].tolist() == [102]
    assert sides.lc4["unlabeled"].tolist() == [103]
    counts = sides.counts()
    assert counts["lc4"] == {"left": 1, "right": 1, "unlabeled": 1}
    assert counts["lplc2"] == {"left": 1, "right": 1, "unlabeled": 0}
    assert condition_stim(sides, ["lc4"], "left").all.tolist() == [101]
    bilateral = condition_stim(sides, ["lc4", "lplc2"], "bilateral")
    assert bilateral.all.tolist() == [101, 102, 103, 201, 202]
    assert 103 not in condition_stim(sides, ["lc4"], "left").all.tolist()
    assert 103 not in condition_stim(sides, ["lc4"], "right").all.tolist()


def test_random_set_split_and_exclusions():
    left = list(range(501, 507))
    right = list(range(601, 607))
    center = [701, 702]
    special = [101, 102, 201, 202, 301]
    ids = np.array(sorted(left + right + center + special), dtype=np.int64)
    rows = []
    for rid in left:
        rows.append((rid, "T4", "left"))
    for rid in right:
        rows.append((rid, "T4", "right"))
    for rid in center:
        rows.append((rid, "T4", "center"))
    rows += [
        (101, "LC4", "left"),
        (102, "LC4", "right"),
        (201, "LPLC2", "left"),
        (202, "LPLC2", "right"),
        (301, "DNp01", "left"),
    ]
    ann = pd.DataFrame(rows, columns=["root_id", "cell_type", "side"])
    exclude = np.array([101, 102, 201, 202, 301], dtype=np.int64)
    kwargs = {
        "exclude": exclude,
        "n_left": 2,
        "n_right": 3,
        "n_unlabeled": 1,
        "left_label": "left",
        "right_label": "right",
    }
    draw = random_set(ann, ids, seed=5, **kwargs)
    assert draw.size == 6
    labels = side_labels(ann, draw, left_label="left", right_label="right").tolist()
    assert labels.count("left") == 2
    assert labels.count("right") == 3
    assert labels.count("unlabeled") == 1
    assert not set(draw.tolist()) & set(exclude.tolist())
    assert np.array_equal(draw, random_set(ann, ids, seed=5, **kwargs))
    assert not np.array_equal(draw, random_set(ann, ids, seed=6, **kwargs))
    with pytest.raises(ControlsError):
        random_set(ann, ids, seed=5, **{**kwargs, "n_left": 7})


def test_chance_reference():
    core = np.arange(1, 11, dtype=np.int64)
    same = chance_reference(core, core, n_draws=50, seed=1)
    assert same.retention_mean == 1.0
    assert same.retention_sd == 0.0
    assert same.jaccard_mean == 1.0
    assert same.jaccard_sd == 0.0
    population = np.arange(1, 1001, dtype=np.int64)
    core_big = np.arange(1, 101, dtype=np.int64)
    ref = chance_reference(core_big, population, n_draws=2000, seed=3)
    assert abs(ref.retention_mean - 0.1) < 0.01
    assert ref.to_dict() == chance_reference(core_big, population, n_draws=2000, seed=3).to_dict()
