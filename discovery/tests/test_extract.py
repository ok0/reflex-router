import numpy as np
import pandas as pd
import pytest
from rr_discovery.extract import ResponsiveRule, neuron_stats, render_responsive_table, responsive

N_TRIALS = 10
T_RUN_S = 1.0
STIM = np.array([900], dtype=np.int64)


def _counts() -> pd.DataFrame:
    rows: list[tuple[int, int, int]] = []

    def add(root: int, per_trial: list[tuple[int, int]]) -> None:
        rows.extend((trial, root, n) for trial, n in per_trial)

    add(1, [(t, 4) for t in range(5)])
    add(2, [(0, 4), (1, 4), (2, 4), (3, 4), (4, 3)])
    add(3, [(0, 8), (1, 8), (2, 7), (3, 7)])
    add(4, [(0, 500)])
    add(5, [(3, 1)])
    add(6, [(t, 10) for t in range(N_TRIALS)])
    add(900, [(0, 1000), (1, 1000)])
    return pd.DataFrame(rows, columns=["trial", "root_id", "n_spikes"]).astype("int64")


def _out() -> pd.DataFrame:
    return responsive(
        _counts(), ResponsiveRule(), n_trials=N_TRIALS, t_run_s=T_RUN_S, stimulated=STIM
    )


def test_thresholds_exact():
    out = _out()
    flags = dict(zip(out["root_id"].tolist(), out["responsive"].tolist(), strict=True))
    assert flags == {1: True, 2: False, 3: False, 4: False, 5: False, 6: True}
    assert 900 not in set(out["root_id"].tolist())


def test_ranking_by_rel_rate():
    out = _out().set_index("root_id")
    assert out.loc[6, "rank"] == 1
    assert out.loc[1, "rank"] == 2
    assert out.loc[6, "rel_rate"] == pytest.approx(10 / 50)
    assert out.loc[1, "rel_rate"] == pytest.approx(2 / 50)


def test_rel_rate_uses_max_over_nonstimulated():
    out = _out().set_index("root_id")
    assert out.loc[4, "rate_hz"] == pytest.approx(50.0)
    assert out.loc[6, "rel_rate"] == pytest.approx(10 / 50)


def test_rule_validation():
    with pytest.raises(ValueError):
        ResponsiveRule(0, 0.5)
    with pytest.raises(ValueError):
        ResponsiveRule(2, 1.5)


def test_neuron_stats_columns_and_types():
    stats = neuron_stats(_counts(), n_trials=N_TRIALS, t_run_s=T_RUN_S)
    assert list(stats.columns) == [
        "root_id",
        "total_spikes",
        "trials_fired",
        "rate_hz",
        "trial_frac",
    ]
    assert stats["root_id"].dtype == np.int64
    assert stats["total_spikes"].dtype == np.int64
    assert stats["rate_hz"].dtype == np.float64


def test_render_responsive_table():
    out = _out()
    labels = pd.DataFrame(
        {"root_id": [1, 6], "cell_type": ["DNp02", "DNp03"], "side": ["left", "right"]}
    )
    text = render_responsive_table(out, labels)
    lines = text.splitlines()
    assert lines[0] == (
        "rank\troot_id\tcell_type\tside\trate_hz\trel_rate\ttrial_frac\ttotal_spikes\ttrials_fired"
    )
    assert len(lines) == 3
    assert text.endswith("\n")
    assert lines[1].split("\t")[1] == "6"
    assert lines[2].split("\t")[1] == "1"
    assert render_responsive_table(out, labels) == text
