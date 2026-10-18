import hashlib
from pathlib import Path

import pytest
from rr_discovery.config import load_config
from rr_discovery.data import (
    FileSpec,
    IntegrityError,
    ManifestEntry,
    fetch_file,
    paths_from_config,
    read_manifest,
    write_manifest,
)

PAYLOAD = b"hello v783" * 1000


@pytest.fixture
def source(tmp_path: Path) -> Path:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    p = src_dir / "a.bin"
    p.write_bytes(PAYLOAD)
    return p


@pytest.fixture
def digests() -> tuple[str, str]:
    return hashlib.sha256(PAYLOAD).hexdigest(), hashlib.md5(PAYLOAD).hexdigest()


def test_download_verified(tmp_path: Path, source: Path, digests: tuple[str, str]) -> None:
    sha, _ = digests
    dest = tmp_path / "dest"
    res = fetch_file(FileSpec("a.bin", source.as_uri(), sha), dest, record=False)
    assert res.action == "downloaded"
    assert (dest / "a.bin").read_bytes() == PAYLOAD
    assert not list(dest.glob("*.part"))


def test_second_run_idempotent(tmp_path: Path, source: Path, digests: tuple[str, str]) -> None:
    sha, _ = digests
    dest = tmp_path / "dest"
    spec = FileSpec("a.bin", source.as_uri(), sha)
    fetch_file(spec, dest, record=False)
    source.unlink()
    res = fetch_file(spec, dest, record=False)
    assert res.action == "cached"


def test_corrupted_existing_file_detected(
    tmp_path: Path, source: Path, digests: tuple[str, str]
) -> None:
    sha, _ = digests
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "a.bin").write_bytes(b"different bytes")
    with pytest.raises(IntegrityError, match="sha256 mismatch for a.bin"):
        fetch_file(FileSpec("a.bin", source.as_uri(), sha), dest, record=False)


def test_download_hash_mismatch(tmp_path: Path, source: Path) -> None:
    dest = tmp_path / "dest"
    with pytest.raises(IntegrityError):
        fetch_file(FileSpec("a.bin", source.as_uri(), "0" * 64), dest, record=False)
    assert not (dest / "a.bin").exists()
    assert not (dest / "a.bin.part").exists()


def test_md5_mismatch(tmp_path: Path, source: Path, digests: tuple[str, str]) -> None:
    sha, _ = digests
    dest = tmp_path / "dest"
    with pytest.raises(IntegrityError):
        fetch_file(FileSpec("a.bin", source.as_uri(), sha, md5="0" * 32), dest, record=False)


def test_unpinned_requires_record(tmp_path: Path, source: Path, digests: tuple[str, str]) -> None:
    sha, _ = digests
    dest = tmp_path / "dest"
    spec = FileSpec("a.bin", source.as_uri(), None)
    with pytest.raises(IntegrityError, match="--record-hashes"):
        fetch_file(spec, dest, record=False)
    res = fetch_file(spec, dest, record=True)
    assert res.action == "recorded"
    assert res.sha256 == sha


def test_manifest_roundtrip(tmp_path: Path) -> None:
    entries = {
        "b.npy": ManifestEntry(sha256="b" * 64, size=2, source="https://example.org/b.npy"),
        "a.feather": ManifestEntry(sha256="a" * 64, size=1, source="https://example.org/a.feather"),
    }
    path = tmp_path / "manifest.toml"
    write_manifest(path, entries)
    assert read_manifest(path) == entries
    text = path.read_text(encoding="utf-8")
    assert text.index("a.feather") < text.index("b.npy")
    first = path.read_bytes()
    write_manifest(path, entries)
    assert path.read_bytes() == first


def test_paths_from_config(tmp_path: Path) -> None:
    p = tmp_path / "discovery.toml"
    p.write_text(
        """\
[data]
version = "v783"
data_dir = "circuit-data/v783/raw"
reports_dir = "circuit-data/v783/reports"
manifest = "discovery/data_manifest.toml"

[zenodo]
record = "10676866"
doi = "10.5281/zenodo.10676866"
files = ["proofread_connections_783.feather", "proofread_root_ids_783.npy"]

[annotations]
repo = "flyconnectome/flywire_annotations"
tag = "v3.2.0"
path = "supplemental_files/Supplemental_file1_neuron_annotations.tsv"
""",
        encoding="utf-8",
    )
    cfg = load_config(p, base_dir=tmp_path)
    paths = paths_from_config(cfg)
    assert paths.connections.name == "proofread_connections_783.feather"
    assert paths.root_ids.name == "proofread_root_ids_783.npy"
    assert paths.annotations.name == "Supplemental_file1_neuron_annotations.tsv"
