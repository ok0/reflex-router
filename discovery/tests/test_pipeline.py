import dataclasses
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from rr_discovery import export, identify
from rr_discovery.cli import main
from rr_discovery.config import DiscoverConfig, DiscoveryConfig, load_config, require_discover
from rr_discovery.identify import IdentifyError
from rr_discovery.pipeline import PostInputs, PostResult, postprocess
from rr_discovery.run import M2Verdict, RunError

from reflex_router.circuit import load_circuit

REPO = Path(__file__).resolve().parents[2]

ANN = pd.DataFrame(
    {
        "root_id": [101, 102, 201, 202, 301, 302, 401, 402, 403, 404, 405, 406, 407, 501],
        "cell_type": [
            "LC4",
            "LC4",
            "LPLC2",
            "LPLC2",
            "DNp01",
            "DNp01",
            "DNp02",
            "DNp03",
            "DNp04",
            "DNp03",
            "DNp11",
            "DNx99",
            "DNx98",
            "T4",
        ],
        "super_class": [
            "optic",
            "optic",
            "optic",
            "optic",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "descending",
            "optic",
        ],
        "side": [
            "left",
            "left",
            "left",
            "left",
            "left",
            "right",
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
        ],
    }
)
VALID = ANN["root_id"].to_numpy(dtype=np.int64)

_EDGES: tuple[tuple[int, int, int, int], ...] = (
    (101, 401, 20, 1),
    (201, 402, 20, 1),
    (101, 403, 5, 1),
    (202, 404, 15, 1),
    (202, 405, 12, 1),
    (201, 406, 30, 1),
    (101, 301, 50, 1),
    (401, 501, 12, 1),
    (501, 301, 11, -1),
    (403, 501, 3, 1),
    (501, 999, 10, -1),
)
STIM_EDGES: tuple[tuple[int, int], ...] = ((101, 401), (202, 404), (202, 405), (201, 406))


def _counts() -> pd.DataFrame:
    rows: list[tuple[int, int, int]] = []
    for trial in range(4):
        for rid in (101, 102, 201, 202):
            rows.append((trial, rid, 100))
        for rid in (301, 401, 403, 404, 405, 406, 501):
            rows.append((trial, rid, 3))
    rows += [(0, 302, 1), (0, 402, 1)]
    return pd.DataFrame(rows, columns=["trial", "root_id", "n_spikes"]).astype(np.int64)


def _connectivity(drop: tuple[tuple[int, int], ...] = ()) -> pd.DataFrame:
    rows = [r for r in _EDGES if (r[0], r[1]) not in drop]
    return pd.DataFrame(
        {
            "Presynaptic_ID": np.array([r[0] for r in rows], dtype=np.int64),
            "Postsynaptic_ID": np.array([r[1] for r in rows], dtype=np.int64),
            "Connectivity": np.array([r[2] for r in rows], dtype=np.int64),
            "Excitatory": np.array([r[3] for r in rows], dtype=np.int64),
        }
    )


def _totals() -> pd.DataFrame:
    posts = [301, 401, 402, 403, 404, 405, 406, 501, 999]
    return pd.DataFrame(
        {
            "root_id": np.array(posts, dtype=np.int64),
            "input_total": np.full(len(posts), 1000, dtype=np.int64),
        }
    )


def _setup(tmp_path: Path, **overrides: Any) -> tuple[DiscoveryConfig, DiscoverConfig]:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=tmp_path)
    values: dict[str, Any] = {"expected_lc4": 2, "expected_lplc2": 2, **overrides}
    return cfg, dataclasses.replace(require_discover(cfg), **values)


def _details(cfg: DiscoveryConfig, dc: DiscoverConfig) -> dict[str, Any]:
    run_result: dict[str, Any] = {
        "seeds": [1, 2, 3, 4],
        "t_run_s": 1.0,
        "params": {"r_poi": "150. Hz"},
        "spikes": {"file": "spikes_v783.tsv", "sha256": "0" * 64, "n_rows": 10},
        "env": {
            "python": "3.14.8",
            "brian2": "2.10.1",
            "numpy": "x",
            "pandas": "x",
            "pyarrow": "x",
            "joblib": "x",
        },
        "host": {"cpu": "SECRET-HOST"},
        "total_wall_s": 9.9,
        "job": {"completeness": str(dc.out_dir)},
    }
    return export.build_details(
        cfg=cfg,
        dc=dc,
        input_hashes={"fake.feather": "0" * 64},
        model_input_hashes={"completeness": "0" * 64},
        annotation_sha256="0" * 64,
        vendored_code_sha256="0" * 64,
        condition_runner_sha256="0" * 64,
        m2=M2Verdict("PASS", "py314"),
        run_result=run_result,
        n_lc4=2,
        n_lplc2=2,
    )


def _run(
    cfg: DiscoveryConfig,
    dc: DiscoverConfig,
    *,
    counts: pd.DataFrame | None = None,
    connectivity: pd.DataFrame | None = None,
) -> PostResult:
    inp = PostInputs(
        counts=_counts() if counts is None else counts,
        n_trials=4,
        t_run_s=1.0,
        ann=ANN,
        valid_ids=VALID,
        connectivity=_connectivity() if connectivity is None else connectivity,
        input_totals=_totals(),
        details_base=_details(cfg, dc),
    )
    return postprocess(inp, dc, data_version="v783", gf_sanity=lambda gf, members: None)


def _meta(dc: DiscoverConfig) -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads((dc.out_dir / "metadata.json").read_text("utf-8"))
    return parsed


def _all_keys(obj: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            keys.add(str(k))
            keys |= _all_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            keys |= _all_keys(v)
    return keys


def _artifact_bytes(dc: DiscoverConfig) -> dict[str, bytes]:
    return {
        "circuit": (dc.out_dir / "circuit.json").read_bytes(),
        "metadata": (dc.out_dir / "metadata.json").read_bytes(),
        "report": dc.candidates_report.read_bytes(),
        "table": dc.responsive_table.read_bytes(),
    }


def test_pipeline_expected_circuit(tmp_path: Path) -> None:
    cfg, dc = _setup(tmp_path)
    result = _run(cfg, dc)
    assert result.outputs.gf_ids.tolist() == [301]

    c = load_circuit(dc.out_dir)
    spec = c.to_spec()
    roles = {n.root_id: n.role for n in spec.neurons}
    signs = {n.root_id: n.sign for n in spec.neurons}
    assert set(roles) == {101, 102, 201, 202, 301, 401, 403, 404, 405, 406, 501}
    assert roles[101] == "input_lc4"
    assert roles[102] == "input_lc4"
    assert roles[201] == "input_lplc2"
    assert roles[202] == "input_lplc2"
    assert roles[301] == "output_gf"
    assert roles[401] == "output_parallel"
    assert roles[404] == "output_parallel"
    assert roles[405] == "output_parallel"
    assert roles[406] == "output_parallel"
    assert roles[403] == "inter"
    assert roles[501] == "inter"
    assert signs[501] == -1
    assert all(s == 1 for rid, s in signs.items() if rid != 501)
    assert set(spec.connections) == {
        (101, 301, 50),
        (101, 401, 20),
        (201, 406, 30),
        (202, 404, 15),
        (202, 405, 12),
        (401, 501, 12),
        (501, 301, 11),
    }

    meta = _meta(dc)
    assert meta["details"]["circuit"] == export.circuit_counts(spec)

    report = dc.candidates_report.read_text(encoding="utf-8")
    assert "## Giant fiber (DNp01)" in report
    assert any(line.startswith("| 301 | ") and "| yes |" in line for line in report.splitlines())


def test_pipeline_bytes_identical(tmp_path: Path) -> None:
    cfg_a, dc_a = _setup(tmp_path / "a")
    cfg_b, dc_b = _setup(tmp_path / "b")
    _run(cfg_a, dc_a)
    _run(cfg_b, dc_b)
    assert _artifact_bytes(dc_a) == _artifact_bytes(dc_b)


def test_no_volatile_strings(tmp_path: Path) -> None:
    cfg, dc = _setup(tmp_path)
    _run(cfg, dc)
    blobs = _artifact_bytes(dc)
    for name, blob in blobs.items():
        for needle in (str(tmp_path), str(Path.home()), "SECRET-HOST", "9.9"):
            assert needle.encode() not in blob, (name, needle)
    forbidden = {
        "host",
        "wall_s",
        "total_wall_s",
        "peak_rss",
        "pid",
        "maxrss_bytes",
        "started_utc",
        "job",
        "n_proc",
    }
    assert not (_all_keys(_meta(dc)) & forbidden)


def test_metadata_r15_fields(tmp_path: Path) -> None:
    cfg, dc = _setup(tmp_path)
    _run(cfg, dc)
    meta = _meta(dc)
    d = meta["details"]
    assert meta["data_version"] == "v783"
    for dotted in (
        "data.version",
        "data.zenodo_record",
        "data.zenodo_doi",
        "data.inputs",
        "annotations.tag",
        "annotations.sha256",
        "shiu.paper_doi",
        "shiu.repo",
        "shiu.commit",
        "responsive_rule.min_rate_hz",
        "responsive_rule.min_trial_frac",
        "connection_filter.rule",
        "stimulus.config",
        "stimulus.seeds",
        "stimulus.n_trials",
        "spikes.sha256",
        "circuit.by_role",
        "parallel_output",
        "license.label",
        "license.note",
        "m2.sim_env",
        "software.simulation.brian2",
        "software.postprocess.reflex_router_discovery",
    ):
        node: Any = d
        for part in dotted.split("."):
            assert part in node, dotted
            node = node[part]
    keys = {c["key"] for c in d["citations"]}
    assert keys >= {
        "dorkenwald2024",
        "schlegel2024",
        "schlegel2023_preprint",
        "flywire_v783_zenodo",
        "eckstein_bates2024",
        "codex",
        "shiu2024",
    }
    eckstein = next(c for c in d["citations"] if c["key"] == "eckstein_bates2024")
    assert eckstein["doi_status"] == "unverified"


def test_no_parallel_exports(tmp_path: Path) -> None:
    cfg, dc = _setup(tmp_path)
    _run(cfg, dc, connectivity=_connectivity(drop=STIM_EDGES))
    meta = _meta(dc)
    assert meta["details"]["parallel_output"] == "none"
    report = dc.candidates_report.read_text(encoding="utf-8")
    assert identify.LIMITATION in report
    c = load_circuit(dc.out_dir)
    assert export.circuit_counts(c.to_spec())["by_role"]["output_parallel"] == 0


def test_gf_not_responsive_fails_without_circuit(tmp_path: Path) -> None:
    cfg, dc = _setup(tmp_path)
    counts = _counts().query("root_id != 301").reset_index(drop=True)
    with pytest.raises(IdentifyError):
        _run(cfg, dc, counts=counts)
    assert not (dc.out_dir / "circuit.json").exists()
    assert dc.candidates_report.exists()


def test_stim_count_mismatch_aborts(tmp_path: Path) -> None:
    cfg, dc = _setup(tmp_path, expected_lc4=3)
    with pytest.raises(RunError, match="LC4 count 2 != expected 3"):
        _run(cfg, dc)


def test_cli_discover_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["discover", "--help"])
    assert exc.value.code == 0
    assert "--step" in capsys.readouterr().out
