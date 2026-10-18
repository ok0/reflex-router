from pathlib import Path

import pyarrow.parquet as pq
import pytest
from rr_discovery.annotations import load_annotations, load_root_ids
from rr_discovery.config import DiscoveryConfig, require_discover, require_model_input
from rr_discovery.data import Paths
from rr_discovery.model_input import output_paths
from rr_discovery.run import stimulated_sets
from rr_discovery.sanity import check_gf_in_circuit

from reflex_router.circuit import load_circuit

pytestmark = pytest.mark.flywire

REPO = Path(__file__).resolve().parents[2]


def test_stim_counts_v783(v783_paths: tuple[DiscoveryConfig, Paths]) -> None:
    cfg, paths = v783_paths
    dc = require_discover(cfg)
    ann = load_annotations(paths.annotations)
    valid = load_root_ids(paths.root_ids)
    stim = stimulated_sets(ann, valid, dc)
    assert len(stim.lc4) == 104
    assert len(stim.lplc2) == 210


def test_input_totals_cover_all_targets(v783_paths: tuple[DiscoveryConfig, Paths]) -> None:
    cfg, _ = v783_paths
    mi = output_paths(require_model_input(cfg).out_dir, cfg.version)
    if not (mi.meta.exists() and mi.connectivity.exists() and mi.input_totals.exists()):
        pytest.skip("model input not built; run 'uv run rr-discover model-input'")
    totals = pq.read_table(mi.input_totals, columns=["root_id"]).to_pandas()
    targets = pq.read_table(mi.connectivity, columns=["Postsynaptic_ID"]).to_pandas()
    assert set(targets["Postsynaptic_ID"].unique().tolist()) <= set(
        totals["root_id"].unique().tolist()
    )


def test_left_dnp01_in_gf_and_circuit() -> None:
    circuit_dir = REPO / "circuit-data/v783"
    if not (circuit_dir / "circuit.json").exists():
        pytest.skip("circuit.json not built; run 'uv run rr-discover discover'")
    c = load_circuit(circuit_dir)
    check_gf_in_circuit(c.root_ids[c.role_indices("output_gf")], c.root_ids)
