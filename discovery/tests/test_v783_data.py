import numpy as np
import pytest
from rr_discovery import sanity
from rr_discovery.annotations import (
    descending_ids,
    ids_by_cell_type,
    load_annotations,
    load_root_ids,
)
from rr_discovery.data import read_manifest, sha256_file

pytestmark = pytest.mark.flywire


def test_lookups_nonempty_and_within_rootlist(v783_paths) -> None:
    _, paths = v783_paths
    ann = load_annotations(paths.annotations)
    root_ids = load_root_ids(paths.root_ids)
    sets = {t: ids_by_cell_type(ann, t, valid_ids=root_ids) for t in ("LC4", "LPLC2", "DNp01")}
    for ids in sets.values():
        assert ids.size > 0
        assert np.isin(ids, root_ids).all()
    desc = descending_ids(ann, valid_ids=root_ids)
    assert desc.size > 0
    assert np.isin(sets["DNp01"], desc).all()


def test_left_dnp01_sanity(v783_paths) -> None:
    _, paths = v783_paths
    ann = load_annotations(paths.annotations)
    root_ids = load_root_ids(paths.root_ids)
    sanity.check_left_dnp01(ids_by_cell_type(ann, "DNp01", valid_ids=root_ids))


def test_manifest_pins_match_files(v783_paths) -> None:
    cfg, _ = v783_paths
    manifest = read_manifest(cfg.manifest)
    assert len(manifest) == 3
    for name, entry in manifest.items():
        assert sha256_file(cfg.data_dir / name) == entry.sha256
