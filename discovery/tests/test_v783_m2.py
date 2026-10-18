import pandas as pd
import pytest
from rr_discovery.config import require_model_input, require_shiu
from rr_discovery.data import paths_from_config, read_manifest, sha256_file
from rr_discovery.model_input import output_paths, verify_outputs
from rr_discovery.vendor import SHIU_DIR, reference_paths, v630_status

pytestmark = pytest.mark.flywire

COMPLETENESS_783_SHA256 = "bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311"
TOTALS_TARGETS = 137_090


@pytest.fixture
def m2(v783_paths):
    cfg, _ = v783_paths
    mi = output_paths(require_model_input(cfg).out_dir, cfg.version)
    if not mi.meta.exists():
        pytest.skip("model input not built; run 'uv run rr-discover model-input'")
    return cfg, mi


def test_model_input_meta_and_hashes(m2) -> None:
    cfg, mi = m2
    meta = verify_outputs(mi)
    feather = paths_from_config(cfg).connections.name
    pin = read_manifest(cfg.manifest)[feather].sha256
    assert meta["inputs"]["connections"]["sha256"] == pin


def test_input_totals_cover_all_targets(m2) -> None:
    _, mi = m2
    totals = pd.read_parquet(mi.input_totals)
    conn = pd.read_parquet(mi.connectivity, columns=["Postsynaptic_ID"])
    assert len(totals) == TOTALS_TARGETS
    assert set(totals["root_id"].tolist()) == set(conn["Postsynaptic_ID"].tolist())


def test_completeness_matches_shiu(m2) -> None:
    cfg, mi = m2
    shiu_csv = require_shiu(cfg).raw_dir / "Completeness_783.csv"
    if not shiu_csv.exists():
        pytest.skip("Shiu raw Completeness_783.csv absent; run 'uv run rr-discover shiu-fetch'")
    assert sha256_file(mi.completeness) == COMPLETENESS_783_SHA256


def test_pairs_match_shiu(m2) -> None:
    cfg, mi = m2
    _, shiu_con = reference_paths(cfg)
    if not shiu_con.exists():
        pytest.skip("Shiu raw Connectivity_783.parquet absent; run 'uv run rr-discover shiu-fetch'")
    cols = ["Presynaptic_ID", "Postsynaptic_ID", "Connectivity"]
    ours = pd.read_parquet(mi.connectivity, columns=cols).sort_values(cols[:2])
    theirs = pd.read_parquet(shiu_con, columns=cols).sort_values(cols[:2])
    assert ours[cols].to_numpy().tolist() == theirs[cols].to_numpy().tolist()


def test_sign_agreement_with_shiu(m2) -> None:
    cfg, mi = m2
    _, shiu_con = reference_paths(cfg)
    if not shiu_con.exists():
        pytest.skip("Shiu raw Connectivity_783.parquet absent; run 'uv run rr-discover shiu-fetch'")
    cols = ["Presynaptic_ID", "Excitatory"]
    ours = pd.read_parquet(mi.connectivity, columns=cols).groupby("Presynaptic_ID")["Excitatory"]
    theirs = pd.read_parquet(shiu_con, columns=cols).groupby("Presynaptic_ID")["Excitatory"]
    joined = pd.concat([ours.first(), theirs.first()], axis=1, keys=["ours", "shiu"], join="inner")
    disagree = int((joined["ours"] != joined["shiu"]).sum())
    agreement = 1.0 - disagree / len(joined)
    print(f"sign agreement with Shiu v783: {agreement:.5f} ({disagree} of {len(joined)} differ)")
    assert agreement >= 0.965


def test_vendored_equals_fetched(v783_paths) -> None:
    cfg, _ = v783_paths
    raw = require_shiu(cfg).raw_dir
    if not (raw / "model.py").exists():
        pytest.skip("Shiu raw files absent; run 'uv run rr-discover shiu-fetch'")
    for name in ("model.py", "utils.py", "LICENSE"):
        assert (raw / name).read_bytes() == (SHIU_DIR / name).read_bytes()


def test_v630_available(v783_paths) -> None:
    cfg, _ = v783_paths
    status = v630_status(cfg)
    if not status.available:
        pytest.skip(status.detail)
    assert status.available
