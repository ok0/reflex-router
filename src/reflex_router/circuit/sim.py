"""Deterministic LIF simulator over a loaded circuit.

Units: time in ms, voltage in mV, rate in Hz. Each step runs in order: membrane and conductance
update (refractory neurons held), threshold detection, delivery of synaptic input due this step,
reset. Spikes at step n are delivered to their targets at step n + delay_steps. Input neurons
(Poisson targets) have no refractory period. No randomness: stimulus events are a fixed
staggered schedule. The circuit arrays are read-only; every run keeps its state locally.
An empty output_parallel group is valid; parallel_ms is then always None.
"""

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from reflex_router.circuit.model import Circuit

MAX_RATE_HZ = 1000.0
MAX_DT_MS = 0.1
DEFAULT_DT_MS = 0.1
DEFAULT_WINDOW_MS = 100.0

_TOL = 1e-6
_NEVER = -(2**40)


@dataclass(frozen=True, slots=True)
class Stimulus:
    rate_lc4_hz: float
    rate_lplc2_hz: float

    def __post_init__(self) -> None:
        for name, rate in (
            ("rate_lc4_hz", self.rate_lc4_hz),
            ("rate_lplc2_hz", self.rate_lplc2_hz),
        ):
            if not math.isfinite(rate) or not 0.0 <= rate <= MAX_RATE_HZ:
                raise ValueError(f"{name} must be finite and in [0, {MAX_RATE_HZ}], got {rate}")


Outcome = Literal["gf_first", "parallel_first", "tie", "no_fire"]


@dataclass(frozen=True, slots=True)
class FirstSpikes:
    gf_ms: float | None
    parallel_ms: float | None
    steps: int

    @property
    def outcome(self) -> Outcome:
        if self.gf_ms is not None and self.parallel_ms is not None:
            return "tie"
        if self.gf_ms is not None:
            return "gf_first"
        if self.parallel_ms is not None:
            return "parallel_first"
        return "no_fire"


def _readonly[T: np.generic](a: NDArray[T]) -> NDArray[T]:
    a.setflags(write=False)
    return a


class LIFSimulator:
    def __init__(
        self,
        circuit: Circuit,
        *,
        dt_ms: float = DEFAULT_DT_MS,
        window_ms: float = DEFAULT_WINDOW_MS,
    ) -> None:
        if dt_ms > MAX_DT_MS:
            raise ValueError(
                f"dt_ms too coarse to resolve synaptic delay and refractory period: "
                f"{dt_ms} > {MAX_DT_MS}"
            )
        if not 0.0 < dt_ms:
            raise ValueError(f"dt_ms must be > 0, got {dt_ms}")
        if not (math.isfinite(window_ms) and window_ms > 0):
            raise ValueError(f"window_ms must be finite and > 0, got {window_ms}")

        p = circuit.params
        delay_steps = round(p.t_dly_ms / dt_ms)
        refractory_steps = round(p.t_rfc_ms / dt_ms)
        n_steps = round(window_ms / dt_ms)
        if abs(p.t_dly_ms / dt_ms - delay_steps) > _TOL:
            raise ValueError(f"t_dly_ms={p.t_dly_ms} is not a multiple of dt_ms={dt_ms}")
        if abs(p.t_rfc_ms / dt_ms - refractory_steps) > _TOL:
            raise ValueError(f"t_rfc_ms={p.t_rfc_ms} is not a multiple of dt_ms={dt_ms}")
        if delay_steps < 1:
            raise ValueError(f"synaptic delay must be at least one step, got {delay_steps}")
        if abs(window_ms / dt_ms - n_steps) > _TOL:
            raise ValueError(f"window_ms={window_ms} is not a multiple of dt_ms={dt_ms}")

        n = circuit.n_neurons
        pre_of_edge = np.repeat(np.arange(n, dtype=np.int64), np.diff(circuit.indptr))
        weights = (
            circuit.syn_count.astype(np.float64)
            * circuit.signs[pre_of_edge].astype(np.float64)
            * p.w_syn_mv
        )

        refr = np.full(n, refractory_steps, dtype=np.int64)
        lc4_idx = circuit.role_indices("input_lc4")
        lplc2_idx = circuit.role_indices("input_lplc2")
        gf_idx = circuit.role_indices("output_gf")
        par_idx = circuit.role_indices("output_parallel")
        refr[lc4_idx] = 0
        refr[lplc2_idx] = 0
        is_gf = np.zeros(n, dtype=bool)
        is_gf[gf_idx] = True
        is_par = np.zeros(n, dtype=bool)
        is_par[par_idx] = True

        self._circuit = circuit
        self._has_parallel = bool(par_idx.size > 0)
        self._dt_ms = dt_ms
        self._window_ms = window_ms
        self._n_steps = n_steps
        self._delay_steps = delay_steps
        self._refractory_steps = refractory_steps
        self._n = n
        self._v_0 = p.v_0_mv
        self._v_rst = p.v_rst_mv
        self._v_th = p.v_th_mv
        self._decay_v = math.exp(-dt_ms / p.t_mbr_ms)
        self._decay_g = math.exp(-dt_ms / p.tau_ms)
        self._couple = p.tau_ms / (p.tau_ms - p.t_mbr_ms) * (self._decay_g - self._decay_v)
        self._w_in = p.w_syn_mv * p.f_poi
        self._weights = _readonly(weights)
        self._refr = _readonly(refr)
        self._lc4_idx = _readonly(lc4_idx)
        self._lplc2_idx = _readonly(lplc2_idx)
        self._is_gf = _readonly(is_gf)
        self._is_par = _readonly(is_par)

    @property
    def circuit(self) -> Circuit:
        return self._circuit

    @property
    def has_parallel(self) -> bool:
        return self._has_parallel

    @property
    def dt_ms(self) -> float:
        return self._dt_ms

    @property
    def window_ms(self) -> float:
        return self._window_ms

    @property
    def n_steps(self) -> int:
        return self._n_steps

    @property
    def delay_steps(self) -> int:
        return self._delay_steps

    @property
    def refractory_steps(self) -> int:
        return self._refractory_steps

    @property
    def weights(self) -> NDArray[np.float64]:
        return self._weights

    def _schedule(self, stim: Stimulus) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
        times: list[float] = []
        targets: list[int] = []
        groups = (
            (self._lc4_idx, stim.rate_lc4_hz),
            (self._lplc2_idx, stim.rate_lplc2_hz),
        )
        for idx, rate in groups:
            if rate <= 0 or idx.size == 0:
                continue
            period = 1000.0 / rate
            count = int(idx.size)
            for j, neuron in enumerate(idx.tolist()):
                t = j * period / count
                while t < self._window_ms:
                    times.append(t)
                    targets.append(neuron)
                    t += period
        steps = np.floor(np.asarray(times, dtype=np.float64) / self._dt_ms + 1e-9).astype(np.int64)
        idx_arr = np.asarray(targets, dtype=np.int64)
        order = np.lexsort((idx_arr, steps))
        return steps[order], idx_arr[order]

    def _run(
        self, stim: Stimulus, *, stop_early: bool, record: bool
    ) -> tuple[FirstSpikes, list[list[float]]]:
        n = self._n
        d = self._delay_steps
        dt = self._dt_ms
        v_0 = self._v_0
        v_th = self._v_th
        decay_v = self._decay_v
        decay_g = self._decay_g
        couple = self._couple
        refr = self._refr
        weights = self._weights
        indptr = self._circuit.indptr
        indices = self._circuit.indices
        is_gf = self._is_gf
        is_par = self._is_par

        v = np.full(n, v_0, dtype=np.float64)
        g = np.zeros(n, dtype=np.float64)
        last = np.full(n, _NEVER, dtype=np.int64)
        ring = np.zeros((d, n), dtype=np.float64)
        ev_steps, ev_idx = self._schedule(stim)
        n_ev = int(ev_steps.shape[0])
        ptr = 0
        recorded: list[list[float]] = [[] for _ in range(n if record else 0)]

        for step in range(self._n_steps):
            active = (step - last) >= refr
            v = np.where(active, v_0 + (v - v_0) * decay_v + g * couple, v)
            g = np.where(active, g * decay_g, g)
            spk = np.flatnonzero(active & (v > v_th))
            slot = step % d
            g += ring[slot]
            ring[slot] = 0.0
            start = ptr
            while ptr < n_ev and int(ev_steps[ptr]) == step:
                ptr += 1
            if ptr > start:
                np.add.at(g, ev_idx[start:ptr], self._w_in)
            for i in spk.tolist():
                a = int(indptr[i])
                b = int(indptr[i + 1])
                np.add.at(ring[slot], indices[a:b], weights[a:b])
            v[spk] = self._v_rst
            g[spk] = 0.0
            last[spk] = step
            if record:
                t_now = step * dt
                for i in spk.tolist():
                    recorded[i].append(t_now)
            if stop_early:
                gf_hit = bool(is_gf[spk].any())
                par_hit = bool(is_par[spk].any())
                if gf_hit or par_hit:
                    return (
                        FirstSpikes(
                            gf_ms=step * dt if gf_hit else None,
                            parallel_ms=step * dt if par_hit else None,
                            steps=step + 1,
                        ),
                        recorded,
                    )
        return FirstSpikes(gf_ms=None, parallel_ms=None, steps=self._n_steps), recorded

    def first_spikes(self, stim: Stimulus) -> FirstSpikes:
        result, _ = self._run(stim, stop_early=True, record=False)
        return result

    def spike_times(self, stim: Stimulus) -> tuple[tuple[float, ...], ...]:
        _, recorded = self._run(stim, stop_early=False, record=True)
        return tuple(tuple(times) for times in recorded)
