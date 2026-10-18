import math

from rr_discovery.regress import (
    CheckOutcome,
    SweepRow,
    SweepTable,
    check,
    check_equivalence,
    check_monotonic,
    check_ratio,
    decide,
    table_from_result,
)


def _t(means, sds, freqs=(10, 20, 50, 100, 200)) -> SweepTable:
    rows = tuple(
        SweepRow(
            frequency_hz=float(f),
            mean_hz=float(m),
            sd_hz=float(s),
            n_trials=30,
            wall_s=0.0,
        )
        for f, m, s in zip(freqs, means, sds, strict=True)
    )
    return SweepTable(rows=rows)


G = _t([5, 20, 50, 80, 100], [2, 4, 5, 6, 5])
OK = CheckOutcome(True, "ok")
BAD = CheckOutcome(False, "bad")


def test_all_pass():
    outcomes = check(G, G)
    assert all(o.ok for o in outcomes)
    assert "0.800" in outcomes[1].detail


def test_non_monotonic():
    t = _t([5, 20, 50, 80, 60], [1] * 5)
    assert not check_monotonic(t).ok


def test_monotonic_within_sd():
    t = _t([5, 20, 50, 80, 79.5], [1] * 5)
    assert check_monotonic(t).ok


def test_ratio_below():
    assert not check_ratio(_t([5, 20, 50, 60, 100], [1] * 5)).ok


def test_ratio_above():
    assert not check_ratio(_t([5, 20, 50, 95, 100], [1] * 5)).ok


def test_ratio_bounds_inclusive():
    assert check_ratio(_t([5, 20, 50, 70, 100], [1] * 5)).ok
    assert check_ratio(_t([5, 20, 50, 90, 100], [1] * 5)).ok


def test_ratio_no_max():
    outcome = check_ratio(_t([0, 0, 0, 0, 0], [0] * 5))
    assert not outcome.ok
    assert "max mean is 0" in outcome.detail


def test_equivalence_outside():
    golden = _t([5, 20, 50, 80, 100], [2, 4, 5, 6, 10])
    current = _t([5, 20, 50, 80, 121], [2, 4, 5, 6, 1])
    assert not check_equivalence(current, golden).ok


def test_equivalence_boundary_sd_wider():
    golden = _t([5, 20, 50, 80, 100], [2, 4, 5, 6, 10])
    assert check_equivalence(_t([5, 20, 50, 80, 120.0], [1] * 5), golden).ok
    assert not check_equivalence(_t([5, 20, 50, 80, 120.5], [1] * 5), golden).ok


def test_equivalence_boundary_rel_wider():
    golden = _t([5, 20, 50, 80, 100], [2, 4, 5, 6, 5])
    assert check_equivalence(_t([5, 20, 50, 80, 115.0], [1] * 5), golden).ok
    assert not check_equivalence(_t([5, 20, 50, 80, 115.5], [1] * 5), golden).ok
    assert check_equivalence(_t([5, 20, 50, 80, 112.0], [1] * 5), golden).ok


def test_equivalence_grid_mismatch():
    current = _t([5, 20, 50, 80], [1] * 4, freqs=(10, 20, 50, 100))
    outcome = check_equivalence(current, G)
    assert not outcome.ok
    assert "frequency grids differ" in outcome.detail


def test_table_from_result():
    result = {
        "t_run_s": 1.0,
        "conditions": [
            {"frequency_hz": 100.0, "readout_spikes": [1, 2, 3], "wall_s": 2.5},
            {"frequency_hz": 10.0, "readout_spikes": [0, 0], "wall_s": 1.0},
        ],
    }
    table = table_from_result(result)
    assert [row.frequency_hz for row in table.rows] == [10.0, 100.0]
    row = table.by_freq[100.0]
    assert row.mean_hz == 2.0
    assert math.isclose(row.sd_hz, math.sqrt(2 / 3))
    assert row.n_trials == 3
    assert row.wall_s == 2.5


def test_decide_pass():
    result = decide(OK, OK, OK, ratio_v630=None, v630_status="unused")
    assert result.verdict == "PASS"
    assert result.sim_env == "py314"
    assert result.notes == ()


def test_decide_equivalence_fails_fallback():
    result = decide(OK, OK, BAD, ratio_v630=None, v630_status="unused")
    assert result.verdict == "FAIL"
    assert result.sim_env == "fallback"
    assert "fallback env" in result.notes[0]


def test_decide_ratio_fails_v630_unavailable():
    result = decide(OK, BAD, OK, ratio_v630=None, v630_status="unavailable: missing")
    assert result.verdict == "FAIL"
    assert result.sim_env == "undecided"
    assert "v630 rerun not possible" in result.notes[0]
    assert "user decision required before M5" in result.notes[-1]


def test_decide_ratio_fails_v630_holds():
    result = decide(OK, BAD, OK, ratio_v630=OK, v630_status="available: x")
    assert result.verdict == "PASS"
    assert result.sim_env == "py314"
    assert "holds on v630" in result.notes[0]


def test_decide_ratio_fails_v630_also_fails():
    result = decide(OK, BAD, OK, ratio_v630=BAD, v630_status="available: x")
    assert result.verdict == "FAIL"
    assert result.sim_env == "undecided"
    assert "user decision required before M5" in result.notes[-1]


def test_decide_monotonic_fails_ratio_ok():
    result = decide(BAD, OK, OK, ratio_v630=None, v630_status="unused")
    assert result.verdict == "FAIL"
    assert result.sim_env == "undecided"
    assert "user decision required before M5" in result.notes[-1]
