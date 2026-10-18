"""Pin the published S1 artifacts in reports/s1/. Does not rerun S1; no network or data."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
S1_DIR = ROOT / "reports" / "s1"
REPRO_FILES = ("part_a_map.csv", "part_a_stats.json", "part_b_results.csv", "part_b_summary.json")
EXPECTED_SHA256 = {
    "part_a_map.csv": "58205c4892908bbb266c4e758138a67057eef04f92965ea9577fdffa61dda5e0",
    "part_a_stats.json": "1106855f140e4b7668558975210b5a5fa7a848c8e8bee659270d284065f5f45c",
    "part_b_results.csv": "27442c1452904175fd0375d06672763f7e0c82b03292011724986ef23866b192",
    "part_b_summary.json": "9def0edd4c4d1304853aa6345ce4cefc2359c53f80149b1cff4e41ac1eac0b68",
}
FROZEN_SHA256 = {
    "spikes/s1/s1_frozen.py": "dfb343f672dca9c5623bb6e0a9b2c1df49ea22c83a6bddd1143e978e445db9c2",
    "spikes/s1/s1_verdict.py": "f1da24d117d0e74f91457373b518e924aed107a67445bbe0f5e124487d1a6f01",
}
CIRCUIT_SHA256 = "4ca62284d2831f01228e2d0f8a71fdfce78a0b26674cb1bbccf537f487263d91"
FORBIDDEN = ("does not work", "circuit works")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_sums(directory: Path) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    return sums


def hash_mismatches(directory: Path) -> list[str]:
    sums = _read_sums(directory)
    return [n for n in REPRO_FILES if sums.get(n) != _sha256(directory / n)]


def _load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((S1_DIR / name).read_text(encoding="utf-8"))
    return data


def test_sha256sums_lists_exactly_the_repro_files() -> None:
    lines = [
        line
        for line in (S1_DIR / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 4
    assert set(_read_sums(S1_DIR)) == set(REPRO_FILES)


def test_repro_files_match_sha256sums() -> None:
    assert hash_mismatches(S1_DIR) == []


def test_sha256sums_pinned() -> None:
    assert _read_sums(S1_DIR) == EXPECTED_SHA256


def test_hash_check_detects_altered_byte(tmp_path: Path) -> None:
    for name in (*REPRO_FILES, "SHA256SUMS"):
        shutil.copyfile(S1_DIR / name, tmp_path / name)
    assert hash_mismatches(tmp_path) == []
    data = bytearray((tmp_path / "part_a_stats.json").read_bytes())
    data[0] ^= 0x01
    (tmp_path / "part_a_stats.json").write_bytes(bytes(data))
    assert hash_mismatches(tmp_path) == ["part_a_stats.json"]


def test_part_a_verdict_is_a_fail() -> None:
    assert _load("part_a_stats.json")["verdict"] == "A_FAIL"


def test_part_b_and_combined_verdicts() -> None:
    v = _load("part_b_summary.json")["verdict"]
    assert v["part_a"] == "A_FAIL"
    assert v["part_b"] == "B_TIE"
    assert v["combined"] == "STOP"


def test_frozen_files_match_recorded_sha256() -> None:
    for rel, digest in FROZEN_SHA256.items():
        assert _sha256(ROOT / rel) == digest


def test_run_meta_records_frozen_files() -> None:
    m = _load("run_meta.json")
    assert m["frozen_files_sha256"] == FROZEN_SHA256
    assert m["deviations"] == []
    assert m["network_attempts"] == 0
    assert m["sha256_identical"] is True
    assert m["sha256_before"] == CIRCUIT_SHA256
    assert set(m["repro"]) == set(REPRO_FILES)
    assert all(m["repro"].values())


def test_report_records_frozen_files() -> None:
    text = (S1_DIR / "report.md").read_text(encoding="utf-8")
    for rel, digest in FROZEN_SHA256.items():
        assert f"`{rel}` {digest}" in text
    assert "Combined cell: **STOP**" in text
    assert "Deviations: no deviations" in text


def test_preregistration_header() -> None:
    text = (S1_DIR / "preregistration.md").read_text(encoding="utf-8")
    for rel, digest in FROZEN_SHA256.items():
        assert rel in text
        assert digest in text
    assert "Deviations: no deviations." in text


def test_verification_keeps_sensitivity_notes() -> None:
    text = (S1_DIR / "verification.md").read_text(encoding="utf-8")
    assert "5% coverage" in text
    assert "effective_label" in text
    assert "no benefit of the circuit gate over the formula gate is established" in text


def test_no_forbidden_wording() -> None:
    offenders: list[str] = []
    for path in sorted(S1_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").lower()
        offenders.extend(f"{path.name}:{phrase}" for phrase in FORBIDDEN if phrase in text)
    assert offenders == []


def test_circuit_json_matches_metadata() -> None:
    assert _sha256(ROOT / "circuit-data/v783/circuit.json") == CIRCUIT_SHA256
    metadata = json.loads((ROOT / "circuit-data/v783/metadata.json").read_text(encoding="utf-8"))
    assert metadata["circuit_sha256"] == CIRCUIT_SHA256
