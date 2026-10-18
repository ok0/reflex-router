import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from reflex_router.circuit import (
    CircuitFormatError,
    CircuitSpec,
    Provenance,
    encode_circuit,
    load_circuit,
    write_circuit,
)
from reflex_router.circuit.sim import LIFSimulator, Stimulus
from reflex_router.gate.circuit_gate import CircuitGate
from reflex_router.testing.circuits import (
    SYNTHETIC_PROVENANCE,
    build_spec,
    demo_race_spec,
    write_and_load,
)


def _np_spec() -> CircuitSpec:
    return build_spec(
        [(1, "input_lc4", 1), (2, "input_lplc2", 1), (3, "output_gf", 1), (4, "inter", 1)],
        [(2, 3, 200), (1, 4, 50)],
    )


def _canon(obj: object) -> bytes:
    text = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return text.encode("ascii") + b"\n"


def _write_raw(directory: Path, doc: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    data = _canon(doc)
    (directory / "circuit.json").write_bytes(data)
    meta = {
        "circuit_sha256": hashlib.sha256(data).hexdigest(),
        "data_version": SYNTHETIC_PROVENANCE.data_version,
        "license": SYNTHETIC_PROVENANCE.license,
        "notes": SYNTHETIC_PROVENANCE.notes,
    }
    (directory / "metadata.json").write_bytes(_canon(meta))


def _drop_neuron(doc: dict[str, Any], root_id: int) -> dict[str, Any]:
    doc["neurons"] = [n for n in doc["neurons"] if n["root_id"] != root_id]
    doc["connections"] = [c for c in doc["connections"] if root_id not in (c[0], c[1])]
    return doc


def test_no_parallel_loads_hash_readonly(tmp_path: Path) -> None:
    dir1 = tmp_path / "a"
    c = write_and_load(dir1, _np_spec())
    assert c.role_indices("output_parallel").size == 0
    assert c.sha256 == hashlib.sha256((dir1 / "circuit.json").read_bytes()).hexdigest()
    for array in c.arrays().values():
        assert array.flags.writeable is False

    dir2 = tmp_path / "b"
    write_circuit(dir2, c.to_spec(), c.provenance)
    assert (dir1 / "circuit.json").read_bytes() == (dir2 / "circuit.json").read_bytes()
    assert (dir1 / "metadata.json").read_bytes() == (dir2 / "metadata.json").read_bytes()


def test_no_parallel_sim(tmp_path: Path) -> None:
    c = write_and_load(tmp_path, _np_spec())
    sim = LIFSimulator(c)
    assert sim.has_parallel is False
    fs = sim.first_spikes(Stimulus(0.0, 150.0))
    assert fs.gf_ms is not None
    assert fs.parallel_ms is None
    assert fs.outcome == "gf_first"
    assert sim.first_spikes(Stimulus(0.0, 0.0)).outcome == "no_fire"


def test_no_parallel_gate(tmp_path: Path) -> None:
    c = write_and_load(tmp_path, _np_spec())
    gate = CircuitGate(c, mapping=lambda x: Stimulus(0.0, 0.0))
    fire = gate.decide_rates(0.0, 150.0)
    assert fire.winner == "reflex"
    assert fire.reason == "gf_first_no_parallel_group"
    silent = gate.decide_rates(0.0, 0.0)
    assert silent.winner == "deliberate"
    assert silent.reason == "no_fire_no_parallel_group"

    demo_dir = tmp_path / "demo"
    demo = write_and_load(demo_dir, demo_race_spec())
    assert CircuitGate(demo, mapping=lambda x: Stimulus(0.0, 0.0)).simulator.has_parallel is True


def test_still_rejects_missing_gf_or_input(tmp_path: Path) -> None:
    base: dict[str, Any] = json.loads(encode_circuit(_np_spec()))

    no_gf = json.loads(json.dumps(base))
    _write_raw(tmp_path / "no_gf", _drop_neuron(no_gf, 3))
    with pytest.raises(CircuitFormatError, match="missing output group"):
        load_circuit(tmp_path / "no_gf")

    no_lc4 = json.loads(json.dumps(base))
    _write_raw(tmp_path / "no_lc4", _drop_neuron(no_lc4, 1))
    with pytest.raises(CircuitFormatError, match="missing input group"):
        load_circuit(tmp_path / "no_lc4")


def test_details_roundtrip(tmp_path: Path) -> None:
    details = {"b": {"c": [1, 2]}, "a": "x"}
    dir1 = tmp_path / "a"
    write_circuit(
        dir1,
        _np_spec(),
        Provenance("synthetic", "MIT", "n", details=details),
    )
    c = load_circuit(dir1)
    assert c.provenance.details is not None
    assert dict(c.provenance.details) == {"b": {"c": [1, 2]}, "a": "x"}
    with pytest.raises(TypeError):
        c.provenance.details["a"] = 1  # type: ignore[index]

    dir2 = tmp_path / "b"
    write_circuit(dir2, c.to_spec(), c.provenance)
    assert (dir1 / "metadata.json").read_bytes() == (dir2 / "metadata.json").read_bytes()


def test_legacy_metadata_unchanged(tmp_path: Path) -> None:
    write_circuit(tmp_path, _np_spec(), SYNTHETIC_PROVENANCE)
    meta = json.loads((tmp_path / "metadata.json").read_bytes())
    assert set(meta) == {"circuit_sha256", "data_version", "license", "notes"}
    assert load_circuit(tmp_path).provenance.details is None


def test_details_invalid_rejected(tmp_path: Path) -> None:
    write_circuit(tmp_path, _np_spec(), SYNTHETIC_PROVENANCE)
    base_meta = json.loads((tmp_path / "metadata.json").read_bytes())

    bad_details = dict(base_meta, details=[1])
    (tmp_path / "metadata.json").write_bytes(_canon(bad_details))
    with pytest.raises(CircuitFormatError, match="details must be a JSON object"):
        load_circuit(tmp_path)

    extra_key = dict(base_meta, foo="x")
    (tmp_path / "metadata.json").write_bytes(_canon(extra_key))
    with pytest.raises(CircuitFormatError, match="metadata keys"):
        load_circuit(tmp_path)
