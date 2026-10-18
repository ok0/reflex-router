import copy
import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from reflex_router.circuit import (
    SHIU_PARAMS,
    CircuitFormatError,
    CircuitHashMismatch,
    CircuitSpec,
    LIFParams,
    encode_circuit,
    load_circuit,
    write_circuit,
)
from reflex_router.testing.circuits import SYNTHETIC_PROVENANCE, build_spec, write_and_load


def _tiny_spec() -> CircuitSpec:
    return build_spec(
        [
            (1, "input_lc4", 1),
            (2, "input_lplc2", 1),
            (3, "output_gf", 1),
            (4, "output_parallel", 1),
        ],
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


def _base_doc() -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(encode_circuit(_tiny_spec()))
    return doc


def _neuron(doc: dict[str, Any], root_id: int) -> dict[str, Any]:
    for item in doc["neurons"]:
        if item["root_id"] == root_id:
            return cast(dict[str, Any], item)
    raise AssertionError(f"no neuron {root_id}")


def _drop_neuron(doc: dict[str, Any], root_id: int) -> dict[str, Any]:
    doc["neurons"] = [n for n in doc["neurons"] if n["root_id"] != root_id]
    doc["connections"] = [c for c in doc["connections"] if root_id not in (c[0], c[1])]
    return doc


def test_write_load_write_identical_bytes(tmp_path: Path) -> None:
    dir1 = tmp_path / "a"
    write_circuit(dir1, _tiny_spec(), SYNTHETIC_PROVENANCE)
    c = load_circuit(dir1)

    dir2 = tmp_path / "b"
    write_circuit(dir2, c.to_spec(), c.provenance)
    assert (dir1 / "circuit.json").read_bytes() == (dir2 / "circuit.json").read_bytes()
    assert (dir1 / "metadata.json").read_bytes() == (dir2 / "metadata.json").read_bytes()

    spec = _tiny_spec()
    reversed_spec = CircuitSpec(
        neurons=tuple(reversed(spec.neurons)),
        connections=tuple(reversed(spec.connections)),
        params=spec.params,
    )
    dir3 = tmp_path / "c"
    write_circuit(dir3, reversed_spec, SYNTHETIC_PROVENANCE)
    assert (dir1 / "circuit.json").read_bytes() == (dir3 / "circuit.json").read_bytes()
    assert (dir1 / "metadata.json").read_bytes() == (dir3 / "metadata.json").read_bytes()


def test_hash_exposed_and_matches_file(tmp_path: Path) -> None:
    sha = write_circuit(tmp_path, _tiny_spec(), SYNTHETIC_PROVENANCE)
    data = (tmp_path / "circuit.json").read_bytes()
    c = load_circuit(tmp_path)
    assert c.sha256 == hashlib.sha256(data).hexdigest()
    assert c.sha256 == sha


def test_one_byte_change_rejected(tmp_path: Path) -> None:
    write_and_load(tmp_path, _tiny_spec())
    path = tmp_path / "circuit.json"
    data = path.read_bytes()
    mutated = data.replace(b'"root_id":1', b'"root_id":5', 1)
    assert mutated != data
    assert len(mutated) == len(data)
    path.write_bytes(mutated)
    with pytest.raises(CircuitHashMismatch):
        load_circuit(tmp_path)


def _mut_role(doc: dict[str, Any]) -> dict[str, Any]:
    _neuron(doc, 1)["role"] = "bogus"
    return doc


def _mut_dup_neuron(doc: dict[str, Any]) -> dict[str, Any]:
    doc["neurons"].append(copy.deepcopy(_neuron(doc, 1)))
    return doc


def _mut_dangling(doc: dict[str, Any]) -> dict[str, Any]:
    doc["connections"].append([2, 99, 5])
    return doc


def _mut_count_zero(doc: dict[str, Any]) -> dict[str, Any]:
    doc["connections"][0][2] = 0
    return doc


def _mut_count_negative(doc: dict[str, Any]) -> dict[str, Any]:
    doc["connections"][0][2] = -3
    return doc


def _mut_drop_gf(doc: dict[str, Any]) -> dict[str, Any]:
    return _drop_neuron(doc, 3)


def _mut_drop_lc4(doc: dict[str, Any]) -> dict[str, Any]:
    return _drop_neuron(doc, 1)


def _mut_drop_lplc2(doc: dict[str, Any]) -> dict[str, Any]:
    return _drop_neuron(doc, 2)


@pytest.mark.parametrize(
    ("mutate", "substring"),
    [
        (_mut_role, "unknown role"),
        (_mut_dup_neuron, "duplicate neuron id"),
        (_mut_dangling, "dangling connection"),
        (_mut_count_zero, "non-positive synapse count"),
        (_mut_count_negative, "non-positive synapse count"),
        (_mut_drop_gf, "missing output group"),
        (_mut_drop_lc4, "missing input group"),
        (_mut_drop_lplc2, "missing input group"),
    ],
)
def test_structural_invalid_rejected(tmp_path: Path, mutate: Any, substring: str) -> None:
    doc = mutate(_base_doc())
    _write_raw(tmp_path, doc)
    with pytest.raises(CircuitFormatError, match=substring):
        load_circuit(tmp_path)


def test_encode_rejects_invalid_spec() -> None:
    spec = build_spec(
        [
            (1, "input_lc4", 1),
            (2, "input_lplc2", 1),
            (3, "output_gf", 1),
            (4, "output_parallel", 1),
        ],
        [(2, 99, 200)],
    )
    with pytest.raises(CircuitFormatError, match="dangling connection"):
        encode_circuit(spec)


def test_non_canonical_rejected(tmp_path: Path) -> None:
    doc = _base_doc()
    doc["neurons"] = list(reversed(doc["neurons"]))
    _write_raw(tmp_path, doc)
    with pytest.raises(CircuitFormatError):
        load_circuit(tmp_path)


def test_arrays_read_only(tmp_path: Path) -> None:
    c = write_and_load(tmp_path, _tiny_spec())
    for array in c.arrays().values():
        assert array.flags.writeable is False
        if array.size:
            with pytest.raises(ValueError):
                array[...] = 0
        with pytest.raises(ValueError):
            array.setflags(write=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cast(Any, c).sha256 = "x"


def test_shiu_params_values() -> None:
    assert SHIU_PARAMS == LIFParams(
        v_0_mv=-52.0,
        v_rst_mv=-52.0,
        v_th_mv=-45.0,
        t_mbr_ms=20.0,
        tau_ms=5.0,
        t_rfc_ms=2.2,
        t_dly_ms=1.8,
        w_syn_mv=0.275,
        f_poi=250.0,
    )
    with pytest.raises(ValueError):
        LIFParams(
            v_0_mv=-52.0,
            v_rst_mv=-52.0,
            v_th_mv=-45.0,
            t_mbr_ms=20.0,
            tau_ms=20.0,
            t_rfc_ms=2.2,
            t_dly_ms=1.8,
            w_syn_mv=0.275,
            f_poi=250.0,
        )
