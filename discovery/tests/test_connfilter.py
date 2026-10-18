import numpy as np
import pandas as pd
import pytest
from rr_discovery.connfilter import ConnFilterError, keep


def _edges(rows: list[tuple[int, int, int]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["pre", "post", "syn"]).astype("int64")


def _totals(rows: list[tuple[int, int]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["root_id", "input_total"]).astype("int64")


def test_absolute_threshold():
    mask = keep(_edges([(1, 100, 10), (2, 100, 11)]), _totals([(100, 10_000)]))
    assert isinstance(mask, np.ndarray)
    assert mask.dtype == bool
    assert mask.tolist() == [False, True]


def test_relative_threshold():
    kept = keep(_edges([(3, 200, 5)]), _totals([(200, 400)]))
    dropped = keep(_edges([(3, 300, 5)]), _totals([(300, 600)]))
    assert kept.tolist() == [True]
    assert dropped.tolist() == [False]


def test_exactly_one_percent_dropped():
    mask = keep(_edges([(4, 400, 4)]), _totals([(400, 400)]))
    assert mask.tolist() == [False]


def test_totals_before_restriction():
    totals = _totals([(500, 2000), (999, 50)])
    edges = _edges([(5, 500, 15), (6, 500, 12), (7, 500, 8)])
    mask = keep(edges, totals)
    assert mask.tolist() == [True, True, False]


def test_missing_target_raises():
    with pytest.raises(ConnFilterError):
        keep(_edges([(1, 777, 20)]), _totals([(100, 1000)]))


def test_duplicate_pair_raises():
    with pytest.raises(ConnFilterError):
        keep(_edges([(1, 100, 20), (1, 100, 3)]), _totals([(100, 1000)]))
