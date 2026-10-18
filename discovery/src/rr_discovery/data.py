import hashlib
import json
import os
import sys
import tomllib
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.error import URLError

from rr_discovery.config import AnnotationsConfig, ConfigError, DiscoveryConfig


class IntegrityError(Exception):
    pass


@dataclass(frozen=True)
class FileSpec:
    name: str
    url: str
    sha256: str | None
    md5: str | None = None


@dataclass(frozen=True)
class ManifestEntry:
    sha256: str
    size: int
    source: str


@dataclass(frozen=True)
class FetchResult:
    name: str
    path: Path
    sha256: str
    size: int
    action: Literal["cached", "downloaded", "recorded"]


@dataclass(frozen=True)
class Paths:
    connections: Path
    root_ids: Path
    annotations: Path


CHUNK = 1 << 20
PROGRESS_STEP = 64 << 20
MANIFEST_HEADER = (
    "# sha256 pins for raw data in data.data_dir. Trust-on-first-use: filled by "
    "`rr-discover fetch --record-hashes`, then committed. Do not edit by hand.\n"
)


def zenodo_url(record: str, name: str) -> str:
    return f"https://zenodo.org/records/{record}/files/{name}?download=1"


def annotations_url(cfg: AnnotationsConfig) -> str:
    return f"https://raw.githubusercontent.com/{cfg.repo}/{cfg.tag}/{cfg.path}"


def paths_from_config(cfg: DiscoveryConfig) -> Paths:
    feathers = [n for n in cfg.zenodo.files if n.endswith(".feather")]
    npys = [n for n in cfg.zenodo.files if n.endswith(".npy")]
    if len(feathers) != 1:
        raise ConfigError(f"zenodo.files must contain exactly one .feather file, found {feathers}")
    if len(npys) != 1:
        raise ConfigError(f"zenodo.files must contain exactly one .npy file, found {npys}")
    return Paths(
        connections=cfg.data_dir / feathers[0],
        root_ids=cfg.data_dir / npys[0],
        annotations=cfg.data_dir / PurePosixPath(cfg.annotations.path).name,
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _digests_file(path: Path) -> tuple[str, str]:
    sha = hashlib.sha256()
    md = hashlib.md5()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK):
            sha.update(chunk)
            md.update(chunk)
    return sha.hexdigest(), md.hexdigest()


def read_manifest(path: Path) -> dict[str, ManifestEntry]:
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        raw = tomllib.load(fh)
    files = raw.get("files", {})
    entries: dict[str, ManifestEntry] = {}
    for name, table in files.items():
        sha = table.get("sha256", "")
        if not sha:
            continue
        entries[name] = ManifestEntry(
            sha256=sha,
            size=int(table["size"]),
            source=str(table["source"]),
        )
    return entries


def write_manifest(path: Path, entries: Mapping[str, ManifestEntry]) -> None:
    parts = [MANIFEST_HEADER, "\n[files]\n"]
    for name in sorted(entries):
        e = entries[name]
        parts.append(
            f'\n[files."{name}"]\nsha256 = "{e.sha256}"\nsize = {e.size}\nsource = "{e.source}"\n'
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(parts), encoding="utf-8")


def zenodo_md5(record: str, timeout_s: float = 30.0) -> dict[str, str]:
    url = f"https://zenodo.org/api/records/{record}"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        out: dict[str, str] = {}
        for f in payload["files"]:
            checksum = f["checksum"]
            if checksum.startswith("md5:"):
                out[f["key"]] = checksum[4:]
        return out
    except (URLError, TimeoutError, ValueError, KeyError) as err:
        print(
            f"warning: Zenodo checksums unavailable ({err}); relying on pinned sha256 only",
            file=sys.stderr,
        )
        return {}


def fetch_file(spec: FileSpec, dest_dir: Path, *, record: bool) -> FetchResult:
    dest = dest_dir / spec.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    if spec.sha256 is None and not record:
        raise IntegrityError(
            f"no pinned sha256 for {spec.name}; run 'rr-discover fetch --record-hashes' "
            "to pin it on first use"
        )

    if dest.exists():
        sha, md = _digests_file(dest)
        if spec.sha256 is not None:
            if sha == spec.sha256:
                return FetchResult(spec.name, dest, sha, dest.stat().st_size, "cached")
            raise IntegrityError(
                f"sha256 mismatch for {spec.name} at {dest}: expected {spec.sha256}, got {sha}. "
                "Delete the file to re-download."
            )
        if spec.md5 is not None and md != spec.md5:
            raise IntegrityError(
                f"md5 mismatch for {spec.name} at {dest}: expected {spec.md5}, got {md}. "
                "Delete the file to re-download."
            )
        return FetchResult(spec.name, dest, sha, dest.stat().st_size, "recorded")

    part = dest.with_name(dest.name + ".part")
    sha_h = hashlib.sha256()
    md_h = hashlib.md5()
    size = 0
    next_report = PROGRESS_STEP
    try:
        with urllib.request.urlopen(spec.url, timeout=60) as resp, part.open("wb") as out:
            while chunk := resp.read(CHUNK):
                out.write(chunk)
                sha_h.update(chunk)
                md_h.update(chunk)
                size += len(chunk)
                if size >= next_report:
                    print(f"  {spec.name}: {size >> 20} MiB", file=sys.stderr)
                    next_report += PROGRESS_STEP
    except BaseException:
        part.unlink(missing_ok=True)
        raise

    sha = sha_h.hexdigest()
    md = md_h.hexdigest()
    if spec.sha256 is not None and sha != spec.sha256:
        part.unlink(missing_ok=True)
        raise IntegrityError(f"sha256 mismatch for {spec.name}: expected {spec.sha256}, got {sha}")
    if spec.md5 is not None and md != spec.md5:
        part.unlink(missing_ok=True)
        raise IntegrityError(f"md5 mismatch for {spec.name}: expected {spec.md5}, got {md}")
    os.replace(part, dest)
    action: Literal["downloaded", "recorded"] = (
        "downloaded" if spec.sha256 is not None else "recorded"
    )
    return FetchResult(spec.name, dest, sha, size, action)


def fetch(cfg: DiscoveryConfig, *, record_hashes: bool = False) -> tuple[Paths, list[FetchResult]]:
    manifest = read_manifest(cfg.manifest)
    md5s = zenodo_md5(cfg.zenodo.record)

    def pinned(name: str) -> str | None:
        entry = manifest.get(name)
        return entry.sha256 if entry is not None else None

    specs: list[FileSpec] = [
        FileSpec(
            name=name,
            url=zenodo_url(cfg.zenodo.record, name),
            sha256=pinned(name),
            md5=md5s.get(name),
        )
        for name in cfg.zenodo.files
    ]
    ann_name = PurePosixPath(cfg.annotations.path).name
    specs.append(
        FileSpec(
            name=ann_name,
            url=annotations_url(cfg.annotations),
            sha256=pinned(ann_name),
            md5=None,
        )
    )

    results: list[FetchResult] = []
    for spec in specs:
        result = fetch_file(spec, cfg.data_dir, record=record_hashes)
        print(f"{result.action}  {result.name}  sha256={result.sha256}")
        results.append(result)

    if record_hashes and any(r.action == "recorded" for r in results):
        urls = {spec.name: spec.url for spec in specs}
        merged = dict(manifest)
        for r in results:
            if r.action == "recorded":
                merged[r.name] = ManifestEntry(sha256=r.sha256, size=r.size, source=urls[r.name])
        write_manifest(cfg.manifest, merged)

    return paths_from_config(cfg), results
