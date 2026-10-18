"""Shared value types: the request risk class."""

from typing import Literal

RiskClass = Literal["low", "medium", "high"]
RISK_CLASSES: tuple[RiskClass, ...] = ("low", "medium", "high")
