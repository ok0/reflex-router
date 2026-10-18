"""Repository hygiene checks (charter R46, PAC8).

Scans the file set reported by `git ls-files --cached --others --exclude-standard`,
so uncommitted files are covered too. The checks need no network, no data files,
no commit, and no clean working tree.

This file is excluded from the secret and personal-path content scans because it
contains the patterns it detects (spec R13). Size exemptions are documented at
SIZE_EXEMPT.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SELF = "tests/test_repo_hygiene.py"
MAX_BYTES = 5 * 1024 * 1024

# M6 robustness results, published unchanged (docs/report.md section 6), covered by
# circuit-data/LICENSE; pinned by sha256 so any change or growth fails;
# see M10 Flags (user decision).
SIZE_EXEMPT: dict[str, str] = {
    "circuit-data/v783/reports/robustness_results.json": (
        "8d17110ebdd44dbc7307566708ee968cd8a08de5eba5c819640a44919754b013"
    ),
}

SECRET_PATTERNS: list[tuple[str, re.Pattern[bytes]]] = [
    ("anthropic key", re.compile(rb"sk-ant-[A-Za-z0-9_-]{10,}")),
    ("sk- key", re.compile(rb"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}")),
    ("github token", re.compile(rb"ghp_[A-Za-z0-9]{20,}")),
    ("aws key id", re.compile(rb"AKIA[0-9A-Z]{16}")),
    (
        "api key assignment",
        re.compile(rb"[A-Za-z0-9_]*_API_KEY[ \t]*=[ \t]*[\"']?[^\s\"'#]+"),
    ),
]
PERSONAL_PATH = re.compile(rb"/(?:Users|home)/")
CIRCUIT_DATA_ROOT_FILES = frozenset({"circuit-data/LICENSE", "circuit-data/NOTICE.md"})
# directories named in the Scope section of circuit-data/NOTICE.md;
# a new data directory needs an entry here and in NOTICE.
COVERED_DIRS = ("circuit-data/v783/",)


def _repo_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except FileNotFoundError, subprocess.CalledProcessError:
        pytest.skip("not a git checkout")
    return sorted(
        {p for p in result.stdout.decode("utf-8").split("\0") if p and (ROOT / p).is_file()}
    )


def _line_of(data: bytes, pos: int) -> int:
    return data.count(b"\n", 0, pos) + 1


def _secret_hits(rel: str, data: bytes) -> list[str]:
    hits: list[str] = []
    for name, pat in SECRET_PATTERNS:
        for m in pat.finditer(data):
            hits.append(f"{rel}:{_line_of(data, m.start())}: {name}")
    return hits


def _path_hits(rel: str, data: bytes) -> list[str]:
    return [
        f"{rel}:{_line_of(data, m.start())}: personal path" for m in PERSONAL_PATH.finditer(data)
    ]


def _size_hit(rel: str, path: Path) -> str | None:
    size = path.stat().st_size
    if size <= MAX_BYTES:
        return None
    if rel in SIZE_EXEMPT and hashlib.sha256(path.read_bytes()).hexdigest() == SIZE_EXEMPT[rel]:
        return None
    return f"{rel}: {size} bytes > {MAX_BYTES}"


def _coverage_hit(rel: str) -> str | None:
    if not rel.startswith("circuit-data/"):
        return None
    if rel in CIRCUIT_DATA_ROOT_FILES:
        return None
    if Path(rel).name.upper().startswith(("LICENSE", "COPYING")):
        return f"{rel}: nested license file under circuit-data/"
    if rel.startswith(COVERED_DIRS):
        return None
    return f"{rel}: not covered by circuit-data/LICENSE (not in COVERED_DIRS)"


def test_file_set_includes_untracked_files() -> None:
    files = _repo_files()
    assert SELF in files


def test_no_secret_patterns() -> None:
    hits: list[str] = []
    for rel in _repo_files():
        if rel == SELF:
            continue
        hits.extend(_secret_hits(rel, (ROOT / rel).read_bytes()))
    assert not hits, "\n".join(hits)


def test_no_personal_paths() -> None:
    hits: list[str] = []
    for rel in _repo_files():
        if rel == SELF:
            continue
        hits.extend(_path_hits(rel, (ROOT / rel).read_bytes()))
    assert not hits, "\n".join(hits)


def test_no_large_files() -> None:
    hits: list[str] = []
    for rel in _repo_files():
        hit = _size_hit(rel, ROOT / rel)
        if hit is not None:
            hits.append(hit)
    assert not hits, "\n".join(hits)


def test_size_exemptions_are_licensed() -> None:
    for key in SIZE_EXEMPT:
        assert _coverage_hit(key) is None and key.startswith(COVERED_DIRS), key


def test_circuit_data_files_covered() -> None:
    license_text = (ROOT / "circuit-data/LICENSE").read_text(encoding="utf-8")
    assert "Attribution-NonCommercial 4.0 International" in license_text
    notice = (ROOT / "circuit-data/NOTICE.md").read_text(encoding="utf-8")
    for d in COVERED_DIRS:
        assert f"`{d}`" in notice, d
    hits: list[str] = []
    for rel in _repo_files():
        hit = _coverage_hit(rel)
        if hit is not None:
            hits.append(hit)
    assert not hits, "\n".join(hits)


def test_detectors_flag_samples(tmp_path: Path) -> None:
    key = ("sk" + "-ant-" + "A" * 24).encode()
    gh = ("gh" + "p_" + "B" * 24).encode()
    aws = ("AK" + "IA" + "C" * 16).encode()
    assign = ("OPENAI" + "_API_KEY" + "=abc123").encode()
    home = ("/" + "Users" + "/someone/x").encode()

    secret = _secret_hits("x", b"a\n" + key)
    assert secret and secret[0].endswith(":2: anthropic key")
    assert _secret_hits("x", gh)
    assert _secret_hits("x", aws)
    assert _secret_hits("x", assign)
    assert _secret_hits("x", b"risk-class task-list") == []
    assert _path_hits("x", home)

    p = tmp_path / "big.bin"
    p.write_bytes(b"\0" * (MAX_BYTES + 1))
    assert _size_hit("big.bin", p) is not None

    assert _coverage_hit("circuit-data/other/x.csv") is not None
    assert _coverage_hit("circuit-data/v783/LICENSE.txt") is not None
    assert _coverage_hit("circuit-data/v783/circuit.json") is None
    assert _coverage_hit("docs/x.md") is None
