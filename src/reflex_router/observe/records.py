"""Shared literal type for gate decisions.

`Winner` names the path a gate selects: "reflex" or "deliberate".
"""

from typing import Literal

Winner = Literal["reflex", "deliberate"]
