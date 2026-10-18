import hashlib
import json
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

from reflex_router.circuit import Role
from reflex_router.gate.base import GateInput
from reflex_router.gate.circuit_gate import CircuitGate
from reflex_router.testing.circuits import build_spec, demo_mapping, demo_race_spec, write_and_load

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "gate_overhead_m4.json"

TIE_NEURONS: list[tuple[int, Role, int]] = [
    (1, "input_lc4", 1),
    (2, "input_lplc2", 1),
    (3, "output_gf", 1),
    (4, "output_parallel", 1),
]


@pytest.fixture
def demo_dir(tmp_path: Path) -> Path:
    path = tmp_path / "demo"
    write_and_load(path, demo_race_spec())
    return path


def _gate(path: Path, *, quantum: float = 1.0, memo_size: int = 65536) -> CircuitGate:
    return CircuitGate.from_dir(
        path, mapping=demo_mapping, memo_quantum_hz=quantum, memo_size=memo_size
    )


def test_four_outcomes(tmp_path: Path, demo_dir: Path) -> None:
    gate = _gate(demo_dir)
    reflex = gate.decide_rates(50.0, 142.5)
    assert reflex.winner == "reflex"
    assert reflex.reason == "gf_first"
    assert reflex.gf_ms is not None

    parallel = gate.decide_rates(50.0, 30.0)
    assert parallel.winner == "deliberate"
    assert parallel.reason == "parallel_first"

    tie_path = tmp_path / "tie"
    write_and_load(tie_path, build_spec(TIE_NEURONS, [(2, 3, 200), (2, 4, 200)]))
    tie = _gate(tie_path).decide_rates(0.0, 1.0)
    assert tie.winner == "deliberate"
    assert tie.reason == "tie"

    none = gate.decide_rates(0.0, 0.0)
    assert none.winner == "deliberate"
    assert none.reason == "no_fire"

    reasons = {reflex.reason, parallel.reason, tie.reason, none.reason}
    assert len(reasons) == 4
    for d, (r1, r2) in zip(
        [reflex, parallel, tie, none],
        [(50.0, 142.5), (50.0, 30.0), (0.0, 1.0), (0.0, 0.0)],
        strict=True,
    ):
        assert d.overhead_us > 0
        assert d.stimulus is not None
        assert d.stimulus.rate_lc4_hz == float(gate.quantize(r1))
        assert d.stimulus.rate_lplc2_hz == float(gate.quantize(r2))


def test_memo_hit_equals_cold(demo_dir: Path) -> None:
    gate = _gate(demo_dir)
    d1 = gate.decide_rates(50.0, 142.5)
    d2 = gate.decide_rates(50.0, 142.5)
    assert d1.memo_hit is False
    assert d2.memo_hit is True
    assert d1 == d2
    cold = _gate(demo_dir).decide_rates(50.0, 142.5)
    assert cold.memo_hit is False
    assert cold.gf_ms == d1.gf_ms
    assert cold.parallel_ms == d1.parallel_ms
    assert cold.stimulus == d1.stimulus
    assert cold == d1


def test_quantization(demo_dir: Path) -> None:
    gate = _gate(demo_dir)
    d1 = gate.decide_rates(50.3, 142.4)
    d2 = gate.decide_rates(50.0, 142.0)
    assert d1 == d2
    assert d2.memo_hit is True

    coarse = _gate(demo_dir, quantum=5.0)
    assert coarse.quantize(142.4) == 28
    stim = coarse.decide_rates(50.0, 142.4).stimulus
    assert stim is not None
    assert stim.rate_lplc2_hz == 140.0


def test_lru_eviction(demo_dir: Path) -> None:
    gate = _gate(demo_dir, memo_size=2)
    gate.decide_rates(1.0, 1.0)
    gate.decide_rates(2.0, 2.0)
    assert gate.decide_rates(1.0, 1.0).memo_hit is True
    gate.decide_rates(3.0, 3.0)
    assert gate.memo_keys() == ((1, 1), (3, 3))
    assert gate.decide_rates(2.0, 2.0).memo_hit is False
    for i in range(20):
        gate.decide_rates(float(10 + i), float(10 + i))
        assert gate.memo_info().size <= 2


def test_concurrent_equals_sequential(demo_dir: Path) -> None:
    pairs = [(50.0, 3.5 * i) for i in range(40)] * 3
    random.Random(0).shuffle(pairs)
    gate = _gate(demo_dir, memo_size=16)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda p: gate.decide_rates(p[0], p[1]), pairs))
    reference = _gate(demo_dir)
    expected = {p: reference.decide_rates(p[0], p[1]) for p in set(pairs)}
    for pair, got in zip(pairs, results, strict=True):
        assert got == expected[pair]
    assert gate.memo_info().size <= 16


def test_invalid_args(demo_dir: Path) -> None:
    with pytest.raises(ValueError):
        _gate(demo_dir, memo_size=0)
    with pytest.raises(ValueError):
        _gate(demo_dir, quantum=0.0)
    with pytest.raises(ValueError):
        _gate(demo_dir).decide_rates(-1.0, 0.0)


def test_circuit_unchanged_after_1000_decisions(demo_dir: Path) -> None:
    gate = _gate(demo_dir)
    file_sha = hashlib.sha256((demo_dir / "circuit.json").read_bytes()).hexdigest()
    before = {k: a.copy() for k, a in gate.circuit.arrays().items()}
    for i in range(1000):
        gate.decide(GateInput("a", (i % 50) / 50, None, "low"))
    after = gate.circuit.arrays()
    assert before.keys() == after.keys()
    for k in before:
        np.testing.assert_array_equal(before[k], after[k])
    assert gate.circuit.sha256 == file_sha
    assert hashlib.sha256((demo_dir / "circuit.json").read_bytes()).hexdigest() == file_sha


def test_overhead_tool_smoke(tmp_path: Path) -> None:
    script = ROOT / "scripts" / "gate_overhead.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--out-dir",
            str(tmp_path),
            "--sizes",
            "300",
            "--samples",
            "5",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads((tmp_path / "gate_overhead_m4.json").read_text(encoding="utf-8"))
    assert (tmp_path / "gate_overhead_m4.md").exists()
    assert report["samples"] == 5
    assert report["seed"] == 0
    assert report["label"].startswith("M4 gate decision overhead")
    assert "python" in report and "numpy" in report and "platform" in report
    assert "machine" in report and "processor" in report
    assert len(report["circuits"]) == 1
    circuit = report["circuits"][0]
    assert circuit["n_neurons"] == 300
    assert circuit["n_connections"] > 0
    for key in ("cold_us", "warm_us"):
        assert 0 < circuit[key]["p50"] <= circuit[key]["p95"]
    assert sum(circuit["outcomes"].values()) == 5


def test_committed_overhead_report() -> None:
    assert REPORT.exists()
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    circuits = report["circuits"]
    assert {c["n_neurons"] for c in circuits} >= {1000, 5000}
    for c in circuits:
        assert c["n_connections"] > 0
        for key in ("cold_us", "warm_us"):
            assert c[key]["p50"] > 0
            assert c[key]["p50"] <= c[key]["p95"]
    for field in ("python", "numpy", "machine"):
        assert report[field]
    assert "synthetic" in report["label"]
