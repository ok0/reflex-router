"""Gate contract: the input a gate sees, the decision it returns, and the Protocol itself."""

from dataclasses import dataclass, field
from typing import Protocol

from reflex_router.circuit.sim import Stimulus
from reflex_router.observe.records import Winner
from reflex_router.types import RiskClass


@dataclass(frozen=True, slots=True)
class GateInput:
    arc: str
    evidence: float
    latency_budget_ms: float | None
    risk: RiskClass
    intent: str | None = None


@dataclass(frozen=True)
class GateDecision:
    winner: Winner
    reason: str
    score: float | None = None
    gf_ms: float | None = None
    parallel_ms: float | None = None
    overhead_us: float = field(default=0.0, compare=False)
    stimulus: Stimulus | None = None
    memo_hit: bool | None = field(default=None, compare=False)


class Gate(Protocol):
    def decide(self, x: GateInput) -> GateDecision: ...
