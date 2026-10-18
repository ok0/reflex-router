"""Measure CircuitGate decision overhead on synthetic circuits (no FlyWire data).

Writes gate_overhead_m4.json and gate_overhead_m4.md to --out-dir.
Report only: PAC6 is judged in M11.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from reflex_router.gate.circuit_gate import CircuitGate
from reflex_router.testing.circuits import demo_mapping, random_spec, write_and_load

LABEL = (
    "M4 gate decision overhead on synthetic circuits (no FlyWire data); "
    "report only, PAC6 judged in M11"
)
DT_MS = 0.1
WINDOW_MS = 100.0
MEMO_QUANTUM_HZ = 1.0


def _pairs(samples: int) -> list[tuple[float, float]]:
    return [(10.0 + i, 150.0 - i) for i in range(samples)]


def _percentiles(values: list[float]) -> dict[str, float]:
    p50, p95 = np.percentile(np.asarray(values, dtype=np.float64), [50, 95])
    return {"p50": float(p50), "p95": float(p95)}


def _measure(size: int, seed: int, samples: int) -> dict[str, Any]:
    spec = random_spec(size, seed=seed)
    pairs = _pairs(samples)
    with tempfile.TemporaryDirectory(prefix="rr-overhead-") as tmp:
        circuit = write_and_load(Path(tmp) / "circuit", spec)
        gate = CircuitGate(
            circuit,
            mapping=demo_mapping,
            dt_ms=DT_MS,
            window_ms=WINDOW_MS,
            memo_quantum_hz=MEMO_QUANTUM_HZ,
        )
        cold: list[float] = []
        outcomes: dict[str, int] = {}
        for r1, r2 in pairs:
            d = gate.decide_rates(r1, r2)
            assert d.memo_hit is False
            cold.append(d.overhead_us)
            outcomes[d.reason] = outcomes.get(d.reason, 0) + 1
        warm: list[float] = []
        for r1, r2 in pairs:
            d = gate.decide_rates(r1, r2)
            assert d.memo_hit is True
            warm.append(d.overhead_us)
    return {
        "n_neurons": size,
        "n_connections": len(spec.connections),
        "cold_us": _percentiles(cold),
        "warm_us": _percentiles(warm),
        "outcomes": dict(sorted(outcomes.items())),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['label']}",
        "",
        f"- python: {report['python']}",
        f"- numpy: {report['numpy']}",
        f"- platform: {report['platform']}",
        f"- machine: {report['machine']}",
        f"- processor: {report['processor']}",
        f"- dt_ms: {report['dt_ms']}, window_ms: {report['window_ms']}, "
        f"memo_quantum_hz: {report['memo_quantum_hz']}",
        f"- samples: {report['samples']}, seed: {report['seed']}",
        "",
        "| neurons | connections | cold p50 (us) | cold p95 (us) | warm p50 (us) | "
        "warm p95 (us) | outcomes |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for c in report["circuits"]:
        outcomes = ", ".join(f"{k}: {v}" for k, v in c["outcomes"].items())
        lines.append(
            f"| {c['n_neurons']} | {c['n_connections']} | {c['cold_us']['p50']:.1f} | "
            f"{c['cold_us']['p95']:.1f} | {c['warm_us']['p50']:.1f} | "
            f"{c['warm_us']['p95']:.1f} | {outcomes} |"
        )
    return "\n".join(lines) + "\n"


def _positive_samples(text: str) -> int:
    value = int(text)
    if not 1 <= value <= 100:
        raise argparse.ArgumentTypeError(f"--samples must be between 1 and 100, got {value}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=LABEL)
    parser.add_argument("--out-dir", type=Path, default=Path("reports"))
    parser.add_argument("--sizes", type=int, nargs="+", default=[1000, 5000])
    parser.add_argument("--samples", type=_positive_samples, default=40)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    circuits = [_measure(size, args.seed, args.samples) for size in args.sizes]
    report: dict[str, Any] = {
        "label": LABEL,
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "dt_ms": DT_MS,
        "window_ms": WINDOW_MS,
        "memo_quantum_hz": MEMO_QUANTUM_HZ,
        "samples": args.samples,
        "seed": args.seed,
        "circuits": circuits,
    }
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "gate_overhead_m4.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "gate_overhead_m4.md").write_text(_markdown(report), encoding="utf-8")
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
