from typing import Any, cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from reflex_router.gate.base import GateInput
from reflex_router.gate.formula_gate import FormulaGate
from reflex_router.types import RISK_CLASSES, RiskClass


def _x(evidence: float, budget: float | None, risk: RiskClass, arc: str = "a") -> GateInput:
    return GateInput(arc=arc, evidence=evidence, latency_budget_ms=budget, risk=risk)


@pytest.mark.parametrize(
    ("evidence", "budget_ms", "risk", "expected_score", "expected_winner"),
    [
        (0.9, None, "low", 0.9, "reflex"),
        (0.5, None, "low", 0.5, "deliberate"),
        (0.7, 500.0, "low", 0.9, "reflex"),
        (0.7, 5000.0, "low", 0.72, "deliberate"),
        (0.9, None, "high", 0.55, "deliberate"),
        (0.9, None, "medium", 0.7, "deliberate"),
        (0.0, 50.0, "low", 0.2, "deliberate"),
    ],
)
def test_formula_gate_table(
    evidence: float,
    budget_ms: float | None,
    risk: RiskClass,
    expected_score: float,
    expected_winner: str,
) -> None:
    d = FormulaGate().decide(_x(evidence, budget_ms, risk))
    assert d.score == pytest.approx(expected_score)
    assert d.winner == expected_winner
    assert d.reason == "formula"
    assert d.overhead_us >= 0


def test_formula_gate_threshold_inclusive() -> None:
    gate = FormulaGate(w_e=1.0, w_u=0.0, w_r=0.0, theta=0.5)
    assert gate.decide(_x(0.5, None, "low")).winner == "reflex"


def test_no_budget_urgency_zero() -> None:
    _, u, _ = FormulaGate().features(_x(0.4, None, "low"))
    assert u == 0.0


@given(
    e=st.floats(0, 1),
    b1=st.floats(1, 1e5),
    b2=st.floats(1, 1e5),
    risk=st.sampled_from(RISK_CLASSES),
)
def test_tight_budget_scores_no_lower(e: float, b1: float, b2: float, risk: RiskClass) -> None:
    gate = FormulaGate()
    lo, hi = sorted((b1, b2))
    assert gate.score(_x(e, lo, risk)) >= gate.score(_x(e, hi, risk))


@given(e=st.floats(0, 1), budget=st.none() | st.floats(1, 1e5))
def test_high_risk_scores_no_higher(e: float, budget: float | None) -> None:
    gate = FormulaGate()
    high = gate.score(_x(e, budget, "high"))
    medium = gate.score(_x(e, budget, "medium"))
    low = gate.score(_x(e, budget, "low"))
    assert high <= medium <= low


def test_formula_gate_pure() -> None:
    gate = FormulaGate()
    x = _x(0.6, 800.0, "medium")
    first = gate.decide(x)
    for _ in range(50):
        assert gate.decide(x) == first


def test_formula_gate_param_validation() -> None:
    with pytest.raises(ValueError):
        FormulaGate(w_e=-1.0)
    with pytest.raises(ValueError):
        FormulaGate(urgency_ref_ms=0)
    with pytest.raises(ValueError):
        FormulaGate(risk_mult=cast(Any, {"low": 1.0, "medium": 0.6}))
    with pytest.raises(ValueError):
        FormulaGate(risk_mult={"low": 1.0, "medium": 0.6, "high": 1.5})
