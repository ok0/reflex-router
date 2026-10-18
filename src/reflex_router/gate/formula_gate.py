"""Formula gate: a linear score over evidence, urgency and risk, compared to a threshold.

score = w_e * e + w_u * u - w_r * (1 - m)
    e: evidence clipped to [0, 1]
    u: urgency = min(max(urgency_ref_ms / latency_budget_ms, 0), 1); 0 when no budget,
       1 when the budget is <= 0
    m: risk multiplier from risk_mult for the request's risk class
Winner is "reflex" when score >= theta, otherwise "deliberate".
Defaults: w_e=1.0, w_u=0.2, w_r=0.5, theta=0.8, urgency_ref_ms=500.0,
risk_mult={"low": 1.0, "medium": 0.6, "high": 0.3}.
The gate keeps no state; intent is ignored (policy is added in M9).
"""

import math
import time
from collections.abc import Mapping
from types import MappingProxyType

from reflex_router.gate.base import GateDecision, GateInput
from reflex_router.types import RISK_CLASSES, RiskClass

DEFAULT_RISK_MULT: Mapping[RiskClass, float] = MappingProxyType(
    {"low": 1.0, "medium": 0.6, "high": 0.3}
)


class FormulaGate:
    def __init__(
        self,
        *,
        w_e: float = 1.0,
        w_u: float = 0.2,
        w_r: float = 0.5,
        theta: float = 0.8,
        urgency_ref_ms: float = 500.0,
        risk_mult: Mapping[RiskClass, float] | None = None,
    ) -> None:
        for name, value in (("w_e", w_e), ("w_u", w_u), ("w_r", w_r)):
            if not (math.isfinite(value) and value >= 0):
                raise ValueError(f"{name} must be finite and >= 0, got {value!r}")
        if not math.isfinite(theta):
            raise ValueError(f"theta must be finite, got {theta!r}")
        if not (urgency_ref_ms > 0):
            raise ValueError(f"urgency_ref_ms must be > 0, got {urgency_ref_ms!r}")
        if risk_mult is None:
            mult: Mapping[RiskClass, float] = DEFAULT_RISK_MULT
        else:
            if set(risk_mult.keys()) != set(RISK_CLASSES):
                raise ValueError(f"risk_mult keys must be exactly {RISK_CLASSES}")
            for key, value in risk_mult.items():
                if not (0.0 <= value <= 1.0):
                    raise ValueError(f"risk_mult[{key!r}] must be in [0, 1], got {value!r}")
            mult = MappingProxyType(dict(risk_mult))
        self.w_e = w_e
        self.w_u = w_u
        self.w_r = w_r
        self.theta = theta
        self.urgency_ref_ms = urgency_ref_ms
        self.risk_mult: Mapping[RiskClass, float] = mult

    def features(self, x: GateInput) -> tuple[float, float, float]:
        e = min(max(x.evidence, 0.0), 1.0)
        if x.latency_budget_ms is None:
            u = 0.0
        elif x.latency_budget_ms <= 0:
            u = 1.0
        else:
            u = min(max(self.urgency_ref_ms / x.latency_budget_ms, 0.0), 1.0)
        m = self.risk_mult[x.risk]
        return (e, u, m)

    def score(self, x: GateInput) -> float:
        e, u, m = self.features(x)
        return self.w_e * e + self.w_u * u - self.w_r * (1.0 - m)

    def decide(self, x: GateInput) -> GateDecision:
        t0 = time.perf_counter_ns()
        s = self.score(x)
        winner = "reflex" if s >= self.theta else "deliberate"
        return GateDecision(
            winner=winner,
            reason="formula",
            score=s,
            overhead_us=(time.perf_counter_ns() - t0) / 1000.0,
        )
