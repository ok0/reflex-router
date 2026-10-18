import hashlib
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError

from rr_discovery.config import DiscoveryConfig, require_shiu
from rr_discovery.data import (
    FetchResult,
    FileSpec,
    IntegrityError,
    ManifestEntry,
    fetch_file,
    read_manifest,
    sha256_file,
    write_manifest,
)

SHIU_DIR = Path(__file__).resolve().parent / "shiu"
VENDOR_RECORD = SHIU_DIR / "VENDOR.toml"
RUNNER = SHIU_DIR / "runner.py"
CODE_FILES = ("model.py", "runner.py", "utils.py")


@dataclass(frozen=True)
class VendorRecord:
    repo: str
    commit: str
    files: dict[str, tuple[str, str]]


@dataclass(frozen=True)
class V630Status:
    available: bool
    detail: str
    completeness: Path | None
    connectivity: Path | None


def shiu_url(repo: str, commit: str, name: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{commit}/{name}"


def fetch_shiu(cfg: DiscoveryConfig, *, record_hashes: bool = False) -> list[FetchResult]:
    sc = require_shiu(cfg)
    manifest = read_manifest(sc.manifest)

    def pinned(name: str) -> str | None:
        entry = manifest.get(name)
        return entry.sha256 if entry is not None else None

    urls: dict[str, str] = {}
    results: list[FetchResult] = []
    for name in (*sc.vendor_files, *sc.reference_files):
        urls[name] = shiu_url(sc.repo, sc.commit, name)
        result = fetch_file(
            FileSpec(name, urls[name], pinned(name)), sc.raw_dir, record=record_hashes
        )
        print(f"{result.action}  {result.name}  sha256={result.sha256}")
        results.append(result)

    for name in sc.v630_files:
        urls[name] = shiu_url(sc.repo, sc.commit, name)
        try:
            result = fetch_file(
                FileSpec(name, urls[name], pinned(name)), sc.raw_dir, record=record_hashes
            )
        except (URLError, TimeoutError, IntegrityError) as err:
            print(f"warning: v630 file {name} unavailable: {err}", file=sys.stderr)
            continue
        print(f"{result.action}  {result.name}  sha256={result.sha256}")
        results.append(result)

    if record_hashes and any(r.action == "recorded" for r in results):
        merged = dict(manifest)
        for r in results:
            if r.action == "recorded":
                merged[r.name] = ManifestEntry(sha256=r.sha256, size=r.size, source=urls[r.name])
        write_manifest(sc.manifest, merged)

    return results


def read_vendor_record(path: Path = VENDOR_RECORD) -> VendorRecord:
    with path.open("rb") as fh:
        raw = tomllib.load(fh)
    try:
        upstream = raw["upstream"]
        files = {
            name: (tbl["upstream_sha256"], tbl["vendored_sha256"])
            for name, tbl in raw["files"].items()
        }
        return VendorRecord(repo=upstream["repo"], commit=upstream["commit"], files=files)
    except KeyError as err:
        raise IntegrityError(f"{path} is missing key {err}") from err


def vendored_problems(record: VendorRecord, shiu_dir: Path = SHIU_DIR) -> list[str]:
    problems: list[str] = []
    for name, (_, vendored_sha) in sorted(record.files.items()):
        path = shiu_dir / name
        if not path.is_file():
            problems.append(f"missing vendored file {name}")
            continue
        sha = sha256_file(path)
        if sha != vendored_sha:
            problems.append(f"{name}: sha256 {sha} != VENDOR.toml vendored_sha256 {vendored_sha}")
    if not (shiu_dir / "PATCHES.md").is_file():
        problems.append("missing PATCHES.md")
    return problems


def vendored_code_hash(shiu_dir: Path = SHIU_DIR) -> str:
    text = "".join(f"{n} {sha256_file(shiu_dir / n)}\n" for n in CODE_FILES)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _by_suffix(names: tuple[str, ...], suffix: str) -> str | None:
    matches = [n for n in names if n.endswith(suffix)]
    return matches[0] if matches else None


def v630_status(cfg: DiscoveryConfig) -> V630Status:
    sc = require_shiu(cfg)
    manifest = read_manifest(sc.manifest)
    csv_name = _by_suffix(sc.v630_files, ".csv")
    pq_name = _by_suffix(sc.v630_files, ".parquet")
    if csv_name is None or pq_name is None:
        reason = "v630_files must list one .csv and one .parquet file"
        return V630Status(
            False,
            f"unavailable: {reason}; run 'rr-discover shiu-fetch' "
            "(alt. source: Edmond doi 10.17617/3.CZODIW)",
            None,
            None,
        )

    reasons: list[str] = []
    for name in (csv_name, pq_name):
        path = sc.raw_dir / name
        entry = manifest.get(name)
        if not path.is_file():
            reasons.append(f"{name} not found in {sc.raw_dir}")
        elif entry is None:
            reasons.append(f"{name} has no pin in {sc.manifest}")
        elif sha256_file(path) != entry.sha256:
            reasons.append(f"{name} sha256 differs from pin")

    if reasons:
        return V630Status(
            False,
            f"unavailable: {'; '.join(reasons)}; run 'rr-discover shiu-fetch' "
            "(alt. source: Edmond doi 10.17617/3.CZODIW)",
            None,
            None,
        )
    return V630Status(
        True,
        f"available: Shiu repo {sc.repo}@{sc.commit[:7]} ({csv_name}, {pq_name})",
        sc.raw_dir / csv_name,
        sc.raw_dir / pq_name,
    )


def reference_paths(cfg: DiscoveryConfig) -> tuple[Path, Path]:
    sc = require_shiu(cfg)
    csv_name = _by_suffix(sc.reference_files, ".csv")
    pq_name = _by_suffix(sc.reference_files, ".parquet")
    if csv_name is None or pq_name is None:
        raise IntegrityError("reference_files must list one .csv and one .parquet file")
    return sc.raw_dir / csv_name, sc.raw_dir / pq_name
