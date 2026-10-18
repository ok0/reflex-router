"""Circuit gate: decides reflex versus deliberate from the first spikes of a loaded circuit.

Decision order: map the input to input rates (injected mapping), quantize the rates to a grid of
memo_quantum_hz, look up the quantized rate pair in an LRU memo, simulate on a miss, then map the
simulated outcome to a decision. The quantum is an accuracy/speed trade-off: coarser quanta mean
more memo hits and faster decisions, but rates that differ by less than a quantum share one result.
The mapping is injected: it is M4 test scaffolding, and the real encoder arrives in M9.
The circuit is read only; every simulation keeps its state locally, and the memo is guarded
by a lock. When the circuit has no parallel group, the reasons are gf_first_no_parallel_group
(reflex) and no_fire_no_parallel_group (deliberate).
"""

import math
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from os import PathLike

from reflex_router.circuit.model import Circuit, load_circuit
from reflex_router.circuit.sim import FirstSpikes, LIFSimulator, Stimulus
from reflex_router.gate.base import GateDecision, GateInput
from reflex_router.observe.records import Winner

RateMapping = Callable[[GateInput], Stimulus]

NO_PARALLEL_SUFFIX = "_no_parallel_group"


@dataclass(frozen=True, slots=True)
class MemoInfo:
    hits: int
    misses: int
    size: int
    maxsize: int


class CircuitGate:
    def __init__(
        self,
        circuit: Circuit,
        *,
        mapping: RateMapping,
        dt_ms: float = 0.1,
        window_ms: float = 100.0,
        memo_quantum_hz: float = 1.0,
        memo_size: int = 65536,
    ) -> None:
        if not (math.isfinite(memo_quantum_hz) and memo_quantum_hz > 0):
            raise ValueError(f"memo_quantum_hz must be finite and > 0, got {memo_quantum_hz}")
        if memo_size < 1:
            raise ValueError(f"memo_size must be >= 1, got {memo_size}")
        self._sim = LIFSimulator(circuit, dt_ms=dt_ms, window_ms=window_ms)
        self._mapping = mapping
        self._q = memo_quantum_hz
        self._memo_size = memo_size
        self._memo: OrderedDict[tuple[int, int], FirstSpikes] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    @classmethod
    def from_dir(
        cls,
        path: str | PathLike[str],
        *,
        mapping: RateMapping,
        dt_ms: float = 0.1,
        window_ms: float = 100.0,
        memo_quantum_hz: float = 1.0,
        memo_size: int = 65536,
    ) -> CircuitGate:
        return cls(
            load_circuit(path),
            mapping=mapping,
            dt_ms=dt_ms,
            window_ms=window_ms,
            memo_quantum_hz=memo_quantum_hz,
            memo_size=memo_size,
        )

    @property
    def circuit(self) -> Circuit:
        return self._sim.circuit

    @property
    def simulator(self) -> LIFSimulator:
        return self._sim

    @property
    def memo_quantum_hz(self) -> float:
        return self._q

    def quantize(self, rate_hz: float) -> int:
        if not (math.isfinite(rate_hz) and rate_hz >= 0):
            raise ValueError(f"rate must be finite and >= 0, got {rate_hz}")
        return math.floor(rate_hz / self._q + 0.5)

    def decide_rates(self, rate_lc4_hz: float, rate_lplc2_hz: float) -> GateDecision:
        t0 = time.perf_counter_ns()
        return self._decide(t0, rate_lc4_hz, rate_lplc2_hz)

    def decide(self, x: GateInput) -> GateDecision:
        t0 = time.perf_counter_ns()
        s = self._mapping(x)
        return self._decide(t0, s.rate_lc4_hz, s.rate_lplc2_hz)

    def _decide(self, t0: int, rate_lc4_hz: float, rate_lplc2_hz: float) -> GateDecision:
        key = (self.quantize(rate_lc4_hz), self.quantize(rate_lplc2_hz))
        stim = Stimulus(key[0] * self._q, key[1] * self._q)
        hit = False
        with self._lock:
            cached = self._memo.get(key)
            if cached is not None:
                self._memo.move_to_end(key)
                self._hits += 1
                hit = True
        if cached is not None:
            fs = cached
        else:
            fs = self._sim.first_spikes(stim)
            with self._lock:
                if key not in self._memo:
                    self._memo[key] = fs
                while len(self._memo) > self._memo_size:
                    self._memo.popitem(last=False)
                self._misses += 1
        outcome = fs.outcome
        winner: Winner = "reflex" if outcome == "gf_first" else "deliberate"
        reason = outcome if self._sim.has_parallel else outcome + NO_PARALLEL_SUFFIX
        return GateDecision(
            winner=winner,
            reason=reason,
            score=None,
            gf_ms=fs.gf_ms,
            parallel_ms=fs.parallel_ms,
            overhead_us=(time.perf_counter_ns() - t0) / 1000.0,
            stimulus=stim,
            memo_hit=hit,
        )

    def memo_info(self) -> MemoInfo:
        with self._lock:
            return MemoInfo(
                hits=self._hits,
                misses=self._misses,
                size=len(self._memo),
                maxsize=self._memo_size,
            )

    def memo_keys(self) -> tuple[tuple[int, int], ...]:
        with self._lock:
            return tuple(self._memo.keys())
