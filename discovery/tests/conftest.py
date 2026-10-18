from pathlib import Path

import pytest
from rr_discovery.config import DiscoveryConfig, load_config
from rr_discovery.data import Paths, paths_from_config

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v783_paths() -> tuple[DiscoveryConfig, Paths]:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=REPO)
    paths = paths_from_config(cfg)
    if not all(p.exists() for p in (paths.connections, paths.root_ids, paths.annotations)):
        pytest.skip("FlyWire v783 data not present; run 'uv run rr-discover fetch' first")
    return cfg, paths
