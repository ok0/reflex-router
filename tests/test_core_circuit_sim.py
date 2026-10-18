import math
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

from reflex_router.circuit import Circuit, LIFParams, LIFSimulator, Role, Stimulus
from reflex_router.testing.circuits import build_spec, demo_race_spec, write_and_load

BASE_NEURONS: list[tuple[int, Role, int]] = [
    (1, "input_lc4", 1),
    (2, "input_lplc2", 1),
    (3, "output_gf", 1),
    (4, "output_parallel", 1),
]


def _kick_steps(g0: float, p: LIFParams, dt: float) -> int:
    threshold = p.v_th_mv - p.v_0_mv
    for k in range(1, 100_000):
        drive = (
            g0
            * p.tau_ms
            / (p.tau_ms - p.t_mbr_ms)
            * (math.exp(-k * dt / p.tau_ms) - math.exp(-k * dt / p.t_mbr_ms))
        )
        if drive > threshold:
            return k
    raise AssertionError(f"conductance {g0} never reaches threshold")


def _load(
    tmp_path: Path,
    name: str,
    neurons: Sequence[tuple[int, Role, int]],
    connections: Sequence[tuple[int, int, int]],
) -> Circuit:
    return write_and_load(tmp_path / name, build_spec(neurons, connections))


@pytest.mark.parametrize("dt", [0.1, 0.05])
def test_delay_analytic(tmp_path: Path, dt: float) -> None:
    c = _load(tmp_path, "delay", BASE_NEURONS, [(2, 3, 200)])
    p = c.params
    sim = LIFSimulator(c, dt_ms=dt)
    stim = Stimulus(0.0, 1.0)
    st = sim.spike_times(stim)
    lplc2 = int(c.role_indices("input_lplc2")[0])
    gf = int(c.role_indices("output_gf")[0])
    assert st[lplc2], "lplc2 input never spiked"
    assert st[gf], "GF never spiked"

    k_in = _kick_steps(p.w_syn_mv * p.f_poi, p, dt)
    t_in = st[lplc2][0]
    assert abs(t_in - k_in * dt) <= dt + 1e-9

    t_out = st[gf][0]
    assert t_out - t_in >= p.t_dly_ms - 1e-9
    k_gf = _kick_steps(200 * p.w_syn_mv, p, dt)
    assert abs(t_out - (t_in + p.t_dly_ms + k_gf * dt)) <= 0.1 + 1e-9

    fs = sim.first_spikes(stim)
    assert fs.gf_ms == t_out
    assert fs.parallel_ms is None


@pytest.mark.parametrize("dt", [0.1, 0.05])
def test_refractory(tmp_path: Path, dt: float) -> None:
    neurons: list[tuple[int, Role, int]] = [
        (1, "input_lc4", 1),
        *[(11 + i, "input_lplc2", 1) for i in range(10)],
        (3, "output_gf", 1),
        (4, "output_parallel", 1),
    ]
    connections = [(11 + i, 3, 5000) for i in range(10)]
    c = _load(tmp_path, "refr", neurons, connections)
    sim = LIFSimulator(c, dt_ms=dt, window_ms=30.0)
    spikes = sim.spike_times(Stimulus(0.0, 1000.0))
    gf = int(c.role_indices("output_gf")[0])
    times = spikes[gf]
    assert len(times) >= 2
    min_interval = min(b - a for a, b in zip(times, times[1:], strict=False))
    assert min_interval >= c.params.t_rfc_ms - 1e-9
    assert min_interval <= c.params.t_rfc_ms + 0.1 + 1e-9


def test_inhibition_suppresses(tmp_path: Path) -> None:
    base = _load(tmp_path, "base", BASE_NEURONS, [(2, 3, 200)])
    assert LIFSimulator(base).first_spikes(Stimulus(1.0, 1.0)).gf_ms is not None

    inhibited_neurons: list[tuple[int, Role, int]] = [
        (1, "input_lc4", -1),
        (2, "input_lplc2", 1),
        (3, "output_gf", 1),
        (4, "output_parallel", 1),
    ]
    inhibited = _load(tmp_path, "inh", inhibited_neurons, [(2, 3, 200), (1, 3, 200)])
    fs = LIFSimulator(inhibited).first_spikes(Stimulus(1.0, 1.0))
    assert fs.gf_ms is None


def test_synapse_count_scales_weight(tmp_path: Path) -> None:
    neurons: list[tuple[int, Role, int]] = [
        (1, "input_lc4", -1),
        (2, "input_lplc2", 1),
        (3, "output_gf", 1),
        (4, "output_parallel", 1),
    ]
    probe = _load(tmp_path, "probe", neurons, [(1, 3, 50), (2, 3, 200)])
    w = probe.params.w_syn_mv
    expected = np.array([50 * -1 * w, 200 * 1 * w], dtype=np.float64)
    np.testing.assert_array_equal(LIFSimulator(probe).weights, expected)

    fire_times: list[float] = []
    for count in (100, 200, 300, 400):
        c = _load(tmp_path, f"count{count}", neurons, [(2, 3, count)])
        gf_ms = LIFSimulator(c).first_spikes(Stimulus(0.0, 1.0)).gf_ms
        if count == 100:
            assert gf_ms is None
        else:
            assert gf_ms is not None
            fire_times.append(gf_ms)
    assert all(a > b for a, b in zip(fire_times, fire_times[1:], strict=False))


def test_dt_agreement(tmp_path: Path) -> None:
    delay = _load(tmp_path, "agree_delay", BASE_NEURONS, [(2, 3, 200)])
    inhibition = _load(
        tmp_path,
        "agree_inh",
        [
            (1, "input_lc4", -1),
            (2, "input_lplc2", 1),
            (3, "output_gf", 1),
            (4, "output_parallel", 1),
        ],
        [(2, 3, 200), (1, 3, 200)],
    )
    tie = _load(tmp_path, "agree_tie", BASE_NEURONS, [(2, 3, 200), (2, 4, 200)])
    demo = write_and_load(tmp_path / "agree_demo", demo_race_spec())
    cases = [
        (delay, Stimulus(0.0, 1.0)),
        (inhibition, Stimulus(1.0, 1.0)),
        (tie, Stimulus(0.0, 1.0)),
        (demo, Stimulus(50.0, 142.5)),
        (demo, Stimulus(50.0, 30.0)),
    ]
    for circuit, stim in cases:
        coarse = LIFSimulator(circuit, dt_ms=0.1).first_spikes(stim)
        fine = LIFSimulator(circuit, dt_ms=0.05).first_spikes(stim)
        assert coarse.outcome == fine.outcome
        for a, b in ((coarse.gf_ms, fine.gf_ms), (coarse.parallel_ms, fine.parallel_ms)):
            if a is None or b is None:
                assert a is None and b is None
            else:
                assert abs(a - b) <= 0.1 + 1e-9


@pytest.mark.parametrize("dt", [0.2, 0.07, 0.0, -0.1])
def test_dt_rejected(tmp_path: Path, dt: float) -> None:
    c = _load(tmp_path, "dt", BASE_NEURONS, [(2, 3, 200)])
    with pytest.raises(ValueError):
        LIFSimulator(c, dt_ms=dt)


def test_window_zero_rejected(tmp_path: Path) -> None:
    c = _load(tmp_path, "win", BASE_NEURONS, [(2, 3, 200)])
    with pytest.raises(ValueError):
        LIFSimulator(c, window_ms=0.0)


def test_rate_zero_no_input_and_no_fire(tmp_path: Path) -> None:
    c = _load(tmp_path, "zero", BASE_NEURONS, [(2, 3, 200)])
    sim = LIFSimulator(c)
    stim = Stimulus(0.0, 0.0)
    fs = sim.first_spikes(stim)
    assert fs.outcome == "no_fire"
    assert fs.steps == sim.n_steps
    st = sim.spike_times(stim)
    assert len(st) == c.n_neurons
    assert all(len(t) == 0 for t in st)


def test_stimulus_schedule_staggered(tmp_path: Path) -> None:
    neurons: list[tuple[int, Role, int]] = [
        (1, "input_lc4", 1),
        (11, "input_lplc2", 1),
        (12, "input_lplc2", 1),
        (13, "input_lplc2", 1),
        (14, "input_lplc2", 1),
        (3, "output_gf", 1),
        (4, "output_parallel", 1),
    ]
    c = _load(tmp_path, "sched", neurons, [(11, 3, 200)])
    sim = LIFSimulator(c)
    dt = sim.dt_ms
    steps, idx = sim._schedule(Stimulus(0.0, 100.0))
    for j, neuron in enumerate(c.role_indices("input_lplc2").tolist()):
        s = steps[idx == neuron].tolist()
        assert s[0] == math.floor(j * 2.5 / dt + 1e-9)
        assert all(b - a == 100 for a, b in zip(s, s[1:], strict=False))


def test_tie(tmp_path: Path) -> None:
    c = _load(tmp_path, "tie", BASE_NEURONS, [(2, 3, 200), (2, 4, 200)])
    fs = LIFSimulator(c).first_spikes(Stimulus(0.0, 1.0))
    assert fs.gf_ms is not None
    assert fs.gf_ms == fs.parallel_ms
    assert fs.outcome == "tie"


def test_early_stop_steps(tmp_path: Path) -> None:
    c = _load(tmp_path, "early", BASE_NEURONS, [(2, 3, 200)])
    sim = LIFSimulator(c)
    assert sim.first_spikes(Stimulus(0.0, 1.0)).steps < sim.first_spikes(Stimulus(0.0, 0.0)).steps
    assert sim.first_spikes(Stimulus(0.0, 0.0)).steps == sim.n_steps


def test_determinism_repeat_fresh_threads(tmp_path: Path) -> None:
    c = write_and_load(tmp_path / "det", demo_race_spec())
    stim = Stimulus(50.0, 142.5)
    sim = LIFSimulator(c)
    first = sim.first_spikes(stim)
    for _ in range(50):
        assert sim.first_spikes(stim) == first
    assert LIFSimulator(c).first_spikes(stim) == first
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _i: sim.first_spikes(stim), range(64)))
    assert all(r == first for r in results)


@pytest.mark.parametrize(
    ("rate_lc4", "rate_lplc2"),
    [(-1.0, 0.0), (float("nan"), 0.0), (float("inf"), 0.0), (0.0, 1000.1)],
)
def test_stimulus_validation(rate_lc4: float, rate_lplc2: float) -> None:
    with pytest.raises(ValueError):
        Stimulus(rate_lc4, rate_lplc2)
