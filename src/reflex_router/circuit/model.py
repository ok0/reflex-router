"""Circuit model: LIF parameters, writer-side spec, read-only loaded circuit, on-disk format.

On-disk format (version 1), one directory per circuit:
- circuit.json: canonical JSON object {"format": "reflex-router-circuit", "format_version": 1,
  "params": {9 LIF fields as repr(float) strings}, "neurons": [{"root_id", "role", "sign",
  "cell_type", "side"} sorted by root_id], "connections": [[pre_root_id, post_root_id, syn_count]
  sorted by (pre, post)]}. Canonical: sort_keys, compact separators, ASCII, one trailing newline.
- metadata.json: {"circuit_sha256", "data_version", "license", "notes"} with the SHA-256 of the
  exact circuit.json bytes, plus an optional "details" JSON object (provenance details, written
  by discovery). The output_parallel group may be empty (ADR-15).

LIF parameter source: Shiu et al. 2024, philshiu/Drosophila_brain_model @ 91bdd1e7, model.py
default_params. Per-parameter references: v_th (Shiu et al. 2024), t_mbr (Kakaria & de Bivort 2017),
tau (Jürgensen et al.), t_rfc (Lazar et al.), t_dly (Paul et al. 2015), w_syn (free parameter),
f_poi (Poisson-input scale).
"""

import dataclasses
import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

Role = Literal["input_lc4", "input_lplc2", "output_gf", "output_parallel", "inter"]
ROLES: tuple[Role, ...] = ("input_lc4", "input_lplc2", "output_gf", "output_parallel", "inter")

FORMAT_NAME = "reflex-router-circuit"
FORMAT_VERSION = 1
CIRCUIT_FILE = "circuit.json"
METADATA_FILE = "metadata.json"

_MAX_ROOT_ID = 2**63 - 1
_SIGNS = (1, -1)
_HEX64 = re.compile(r"[0-9a-f]{64}")


class CircuitError(ValueError):
    pass


class CircuitFormatError(CircuitError):
    pass


class CircuitHashMismatch(CircuitError):
    pass


@dataclass(frozen=True, slots=True)
class LIFParams:
    v_0_mv: float
    v_rst_mv: float
    v_th_mv: float
    t_mbr_ms: float
    tau_ms: float
    t_rfc_ms: float
    t_dly_ms: float
    w_syn_mv: float
    f_poi: float

    def __post_init__(self) -> None:
        values = (
            self.v_0_mv,
            self.v_rst_mv,
            self.v_th_mv,
            self.t_mbr_ms,
            self.tau_ms,
            self.t_rfc_ms,
            self.t_dly_ms,
            self.w_syn_mv,
            self.f_poi,
        )
        if not all(math.isfinite(v) for v in values):
            raise ValueError("LIF parameters must all be finite")
        if not self.t_mbr_ms > 0:
            raise ValueError(f"t_mbr_ms must be > 0, got {self.t_mbr_ms}")
        if not self.tau_ms > 0:
            raise ValueError(f"tau_ms must be > 0, got {self.tau_ms}")
        if self.tau_ms == self.t_mbr_ms:
            raise ValueError(f"tau_ms must differ from t_mbr_ms, both are {self.tau_ms}")
        if not self.t_rfc_ms >= 0:
            raise ValueError(f"t_rfc_ms must be >= 0, got {self.t_rfc_ms}")
        if not self.t_dly_ms > 0:
            raise ValueError(f"t_dly_ms must be > 0, got {self.t_dly_ms}")
        if not self.v_th_mv > self.v_0_mv:
            raise ValueError(f"v_th_mv must exceed v_0_mv, got {self.v_th_mv} <= {self.v_0_mv}")
        if not self.v_th_mv > self.v_rst_mv:
            raise ValueError(f"v_th_mv must exceed v_rst_mv, got {self.v_th_mv} <= {self.v_rst_mv}")
        if not self.w_syn_mv > 0:
            raise ValueError(f"w_syn_mv must be > 0, got {self.w_syn_mv}")
        if not self.f_poi > 0:
            raise ValueError(f"f_poi must be > 0, got {self.f_poi}")


SHIU_PARAMS = LIFParams(
    v_0_mv=-52.0,  # resting potential, Shiu et al. 2024 default_params
    v_rst_mv=-52.0,  # reset potential, Shiu et al. 2024 default_params
    v_th_mv=-45.0,  # firing threshold, Shiu et al. 2024 default_params
    t_mbr_ms=20.0,  # membrane time constant, Kakaria & de Bivort 2017
    tau_ms=5.0,  # synaptic conductance time constant, Jürgensen et al.
    t_rfc_ms=2.2,  # refractory period, Lazar et al.
    t_dly_ms=1.8,  # synaptic delay, Paul et al. 2015
    w_syn_mv=0.275,  # per-synapse weight (free parameter)
    f_poi=250.0,  # Poisson-input scale (free parameter)
)

_PARAM_NAMES = tuple(f.name for f in dataclasses.fields(LIFParams))
_NEURON_KEYS = frozenset({"root_id", "role", "sign", "cell_type", "side"})
_DOC_KEYS = frozenset({"format", "format_version", "params", "neurons", "connections"})
_META_KEYS = frozenset({"circuit_sha256", "data_version", "license", "notes"})
_META_OPTIONAL = frozenset({"details"})


@dataclass(frozen=True, slots=True)
class Neuron:
    root_id: int
    role: Role
    sign: int
    cell_type: str
    side: str


@dataclass(frozen=True, slots=True)
class CircuitSpec:
    neurons: tuple[Neuron, ...]
    connections: tuple[tuple[int, int, int], ...]
    params: LIFParams


@dataclass(frozen=True, slots=True)
class Provenance:
    data_version: str
    license: str
    notes: str = ""
    details: Mapping[str, Any] | None = field(default=None, hash=False)


def _frozen(a: ArrayLike, dtype: DTypeLike) -> NDArray[Any]:
    return np.frombuffer(np.ascontiguousarray(a, dtype=dtype).tobytes(), dtype=dtype)


@dataclass(frozen=True, eq=False)
class Circuit:
    root_ids: NDArray[np.int64]
    role_codes: NDArray[np.int8]
    signs: NDArray[np.int8]
    cell_types: tuple[str, ...]
    sides: tuple[str, ...]
    indptr: NDArray[np.int64]
    indices: NDArray[np.int64]
    syn_count: NDArray[np.int64]
    params: LIFParams
    sha256: str
    provenance: Provenance

    @property
    def n_neurons(self) -> int:
        return int(self.root_ids.shape[0])

    @property
    def n_connections(self) -> int:
        return int(self.indices.shape[0])

    def role_indices(self, role: Role) -> NDArray[np.int64]:
        code = ROLES.index(role)
        return _frozen(np.flatnonzero(self.role_codes == code), np.int64)

    def arrays(self) -> dict[str, NDArray[Any]]:
        return {
            "root_ids": self.root_ids,
            "role_codes": self.role_codes,
            "signs": self.signs,
            "indptr": self.indptr,
            "indices": self.indices,
            "syn_count": self.syn_count,
        }

    def to_spec(self) -> CircuitSpec:
        n = self.n_neurons
        ids = self.root_ids.tolist()
        neurons = tuple(
            Neuron(
                root_id=ids[i],
                role=ROLES[int(self.role_codes[i])],
                sign=int(self.signs[i]),
                cell_type=self.cell_types[i],
                side=self.sides[i],
            )
            for i in range(n)
        )
        pre_of_edge = np.repeat(np.arange(n), np.diff(self.indptr)).tolist()
        connections = tuple(
            (ids[p], ids[post], count)
            for p, post, count in zip(
                pre_of_edge, self.indices.tolist(), self.syn_count.tolist(), strict=True
            )
        )
        return CircuitSpec(neurons=neurons, connections=connections, params=self.params)


def _dumps(obj: object) -> bytes:
    text = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return text.encode("ascii") + b"\n"


def _is_int(x: object) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _validate_doc(doc: object) -> CircuitSpec:
    if not isinstance(doc, dict):
        raise CircuitFormatError("circuit document must be a JSON object")
    if set(doc) != _DOC_KEYS:
        raise CircuitFormatError(f"circuit document keys must be {sorted(_DOC_KEYS)}")
    if doc["format"] != FORMAT_NAME or not _is_int(doc["format_version"]):
        raise CircuitFormatError(
            f"unsupported format {doc['format']!r} / {doc['format_version']!r}"
        )
    if doc["format_version"] != FORMAT_VERSION:
        raise CircuitFormatError(f"unsupported format_version {doc['format_version']!r}")

    raw_params = doc["params"]
    if not isinstance(raw_params, dict) or set(raw_params) != set(_PARAM_NAMES):
        raise CircuitFormatError(f"params keys must be {sorted(_PARAM_NAMES)}")
    param_values: dict[str, float] = {}
    for name in _PARAM_NAMES:
        text = raw_params[name]
        if not isinstance(text, str):
            raise CircuitFormatError(f"param {name} must be a string")
        try:
            param_values[name] = float(text)
        except ValueError as exc:
            raise CircuitFormatError(f"param {name} is not a float: {text!r}") from exc
    try:
        params = LIFParams(**param_values)
    except ValueError as exc:
        raise CircuitFormatError(f"invalid LIF parameters: {exc}") from exc

    raw_neurons = doc["neurons"]
    if not isinstance(raw_neurons, list):
        raise CircuitFormatError("neurons must be a list")
    neurons: list[Neuron] = []
    seen: set[int] = set()
    for item in raw_neurons:
        if not isinstance(item, dict) or set(item) != _NEURON_KEYS:
            raise CircuitFormatError(f"neuron must be an object with keys {sorted(_NEURON_KEYS)}")
        root_id = item["root_id"]
        if not _is_int(root_id) or not 0 <= root_id <= _MAX_ROOT_ID:
            raise CircuitFormatError(f"root_id must be an int in [0, 2**63-1], got {root_id!r}")
        role = item["role"]
        if role not in ROLES:
            raise CircuitFormatError(f"unknown role {role!r}")
        sign = item["sign"]
        if not _is_int(sign) or sign not in _SIGNS:
            raise CircuitFormatError(f"sign must be 1 or -1, got {sign!r}")
        if not isinstance(item["cell_type"], str) or not isinstance(item["side"], str):
            raise CircuitFormatError("cell_type and side must be strings")
        if root_id in seen:
            raise CircuitFormatError(f"duplicate neuron id {root_id}")
        if neurons and root_id < neurons[-1].root_id:
            raise CircuitFormatError("neurons not sorted by root_id")
        seen.add(root_id)
        neurons.append(
            Neuron(
                root_id=root_id,
                role=role,
                sign=sign,
                cell_type=item["cell_type"],
                side=item["side"],
            )
        )

    raw_connections = doc["connections"]
    if not isinstance(raw_connections, list):
        raise CircuitFormatError("connections must be a list")
    connections: list[tuple[int, int, int]] = []
    edges: set[tuple[int, int]] = set()
    for item in raw_connections:
        if not isinstance(item, list) or len(item) != 3 or not all(_is_int(x) for x in item):
            raise CircuitFormatError(f"connection must be a 3-list of ints, got {item!r}")
        pre, post, count = item
        if pre not in seen or post not in seen:
            raise CircuitFormatError(f"dangling connection {pre} -> {post}")
        if count <= 0:
            raise CircuitFormatError(f"non-positive synapse count {count} for {pre} -> {post}")
        if (pre, post) in edges:
            raise CircuitFormatError(f"duplicate connection {pre} -> {post}")
        if connections and (pre, post) < (connections[-1][0], connections[-1][1]):
            raise CircuitFormatError("connections not sorted by (pre, post)")
        edges.add((pre, post))
        connections.append((pre, post, count))

    roles = {n.role for n in neurons}
    if "output_gf" not in roles:
        raise CircuitFormatError("missing output group: need output_gf")
    if "input_lc4" not in roles or "input_lplc2" not in roles:
        raise CircuitFormatError("missing input group: need input_lc4 and input_lplc2")

    return CircuitSpec(neurons=tuple(neurons), connections=tuple(connections), params=params)


def encode_circuit(spec: CircuitSpec) -> bytes:
    neurons = sorted(spec.neurons, key=lambda n: n.root_id)
    connections = sorted(spec.connections, key=lambda c: (c[0], c[1]))
    doc: dict[str, Any] = {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "params": {name: repr(float(getattr(spec.params, name))) for name in _PARAM_NAMES},
        "neurons": [
            {
                "root_id": n.root_id,
                "role": n.role,
                "sign": n.sign,
                "cell_type": n.cell_type,
                "side": n.side,
            }
            for n in neurons
        ],
        "connections": [[pre, post, count] for pre, post, count in connections],
    }
    _validate_doc(doc)
    return _dumps(doc)


def write_circuit(directory: str | PathLike[str], spec: CircuitSpec, provenance: Provenance) -> str:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    data = encode_circuit(spec)
    sha = hashlib.sha256(data).hexdigest()
    metadata: dict[str, Any] = {
        "circuit_sha256": sha,
        "data_version": provenance.data_version,
        "license": provenance.license,
        "notes": provenance.notes,
    }
    if provenance.details is not None:
        metadata["details"] = dict(provenance.details)
    meta_bytes = _dumps(metadata)
    (path / CIRCUIT_FILE).write_bytes(data)
    (path / METADATA_FILE).write_bytes(meta_bytes)
    return sha


def load_circuit(directory: str | PathLike[str]) -> Circuit:
    path = Path(directory)
    try:
        raw = (path / CIRCUIT_FILE).read_bytes()
        meta_raw = (path / METADATA_FILE).read_bytes()
    except OSError as exc:
        raise CircuitFormatError(f"cannot read circuit files in {path}: {exc}") from exc

    try:
        meta: object = json.loads(meta_raw)
    except ValueError as exc:
        raise CircuitFormatError(f"metadata.json is not valid JSON: {exc}") from exc
    if not isinstance(meta, dict) or not (_META_KEYS <= set(meta) <= _META_KEYS | _META_OPTIONAL):
        raise CircuitFormatError(
            f"metadata keys must be {sorted(_META_KEYS)} plus optional {sorted(_META_OPTIONAL)}"
        )
    if not all(isinstance(meta[k], str) for k in _META_KEYS):
        raise CircuitFormatError("metadata values must be strings")
    if "details" in meta and not isinstance(meta["details"], dict):
        raise CircuitFormatError("metadata details must be a JSON object")
    expected = meta["circuit_sha256"]
    if not isinstance(expected, str) or not _HEX64.fullmatch(expected):
        raise CircuitFormatError("circuit_sha256 must be 64 lowercase hex characters")

    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise CircuitHashMismatch(f"circuit.json sha256 {actual} != metadata {expected}")

    try:
        doc: object = json.loads(raw)
    except ValueError as exc:
        raise CircuitFormatError(f"circuit.json is not valid JSON: {exc}") from exc
    spec = _validate_doc(doc)
    if _dumps(doc) != raw:
        raise CircuitFormatError("circuit.json is not in canonical form")

    neurons = sorted(spec.neurons, key=lambda n: n.root_id)
    index = {n.root_id: i for i, n in enumerate(neurons)}
    n_count = len(neurons)
    pre_idx = np.array([index[pre] for pre, _, _ in spec.connections], dtype=np.int64)
    post_idx = np.array([index[post] for _, post, _ in spec.connections], dtype=np.int64)
    counts = np.array([count for _, _, count in spec.connections], dtype=np.int64)
    order = np.argsort(pre_idx, kind="stable")
    indptr = np.zeros(n_count + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(np.bincount(pre_idx, minlength=n_count))

    return Circuit(
        root_ids=_frozen(np.array([n.root_id for n in neurons], dtype=np.int64), np.int64),
        role_codes=_frozen(
            np.array([ROLES.index(n.role) for n in neurons], dtype=np.int8), np.int8
        ),
        signs=_frozen(np.array([n.sign for n in neurons], dtype=np.int8), np.int8),
        cell_types=tuple(n.cell_type for n in neurons),
        sides=tuple(n.side for n in neurons),
        indptr=_frozen(indptr, np.int64),
        indices=_frozen(post_idx[order], np.int64),
        syn_count=_frozen(counts[order], np.int64),
        params=spec.params,
        sha256=actual,
        provenance=Provenance(
            data_version=meta["data_version"],
            license=meta["license"],
            notes=meta["notes"],
            details=MappingProxyType(meta["details"]) if "details" in meta else None,
        ),
    )
