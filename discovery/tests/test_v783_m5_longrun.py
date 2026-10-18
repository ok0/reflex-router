import hashlib
import json
import os
from pathlib import Path

import pytest
from rr_discovery import pipeline, run
from rr_discovery.config import DiscoverConfig, load_config, require_discover
from rr_discovery.identify import LIMITATION

from reflex_router.circuit import Stimulus, load_circuit
from reflex_router.gate import CircuitGate, GateDecision

REPO = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.longrun,
    pytest.mark.flywire,
    pytest.mark.skipif(
        os.environ.get("RR_LONGRUN") != "1",
        reason="M5 whole-brain simulation; set RR_LONGRUN=1 to run",
    ),
]


def _capture(dc: DiscoverConfig) -> dict[str, object]:
    circuit = (dc.out_dir / "circuit.json").read_bytes()
    return {
        "circuit_sha256": hashlib.sha256(circuit).hexdigest(),
        "metadata": (dc.out_dir / "metadata.json").read_bytes(),
        "report": dc.candidates_report.read_bytes(),
        "table": dc.responsive_table.read_bytes(),
    }


def test_end_to_end_reproducible() -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    dc = require_discover(cfg)
    rounds: list[dict[str, object]] = []
    for _ in range(2):
        run.run_stage(cfg, python=None, n_proc=None)
        assert pipeline.post_stage(cfg) == 0
        rounds.append(_capture(dc))
    assert rounds[0] == rounds[1]


def test_real_circuit_gate() -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    dc = require_discover(cfg)
    c = load_circuit(dc.out_dir)
    for arr in c.arrays().values():
        assert not arr.flags.writeable

    gate = CircuitGate(c, mapping=lambda x: Stimulus(0.0, 0.0))
    for lc4_hz, lplc2_hz in ((0.0, 0.0), (50.0, 50.0), (150.0, 0.0), (0.0, 150.0), (150.0, 150.0)):
        assert isinstance(gate.decide_rates(lc4_hz, lplc2_hz), GateDecision)

    details = json.loads((dc.out_dir / "metadata.json").read_text(encoding="utf-8"))["details"]
    report = dc.candidates_report.read_text(encoding="utf-8")
    table_rows = sum(1 for line in report.splitlines() if "| output_parallel |" in line)
    n_parallel = details["circuit"]["by_role"]["output_parallel"]
    assert table_rows == n_parallel == c.role_indices("output_parallel").size
    if n_parallel == 0:
        assert LIMITATION in report
        assert details["parallel_output"] == "none"
    assert details["software"]["simulation"]["brian2"] == "2.10.1"
