import ast
import json
import re
import tomllib
from pathlib import Path

from rr_discovery.data import read_manifest
from rr_discovery.vendor import SHIU_DIR, read_vendor_record, vendored_code_hash, vendored_problems

REPO = Path(__file__).resolve().parents[2]
ALLOWED_RUNNER_IMPORTS = {
    "argparse",
    "importlib",
    "json",
    "os",
    "platform",
    "resource",
    "subprocess",
    "sys",
    "time",
    "pathlib",
    "typing",
    "numpy",
    "pandas",
    "joblib",
    "brian2",
}


def test_vendor_record_and_hashes() -> None:
    record = read_vendor_record()
    assert re.fullmatch(r"[0-9a-f]{40}", record.commit)
    assert vendored_problems(record) == []
    for name, (upstream_sha, vendored_sha) in record.files.items():
        assert vendored_sha == upstream_sha, name


def test_license_mit_credit() -> None:
    text = (SHIU_DIR / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in text
    assert "Philip Shiu" in text


def test_py310_syntax() -> None:
    for name in ("runner.py", "model.py", "utils.py"):
        src = (SHIU_DIR / name).read_text(encoding="utf-8")
        ast.parse(src, filename=name, feature_version=(3, 10))


def test_runner_import_allowlist() -> None:
    tree = ast.parse((SHIU_DIR / "runner.py").read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module.split(".")[0])
    assert modules <= ALLOWED_RUNNER_IMPORTS, modules - ALLOWED_RUNNER_IMPORTS


def test_condition_runner_py310_and_imports() -> None:
    src = (SHIU_DIR / "condition_runner.py").read_text(encoding="utf-8")
    ast.parse(src, filename="condition_runner.py", feature_version=(3, 10))
    tree = ast.parse(src)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module.split(".")[0])
    assert modules <= ALLOWED_RUNNER_IMPORTS | {"hashlib"}, modules - ALLOWED_RUNNER_IMPORTS


def test_vendored_code_hash_matches_golden() -> None:
    golden = json.loads(Path(REPO / "circuit-data/v783/reports/regress_golden.json").read_text())
    assert vendored_code_hash() == golden["vendored_code_hash"]


def test_shiu_manifest_pins() -> None:
    manifest = read_manifest(REPO / "discovery" / "shiu_manifest.toml")
    assert set(manifest) == {
        "LICENSE",
        "model.py",
        "utils.py",
        "Completeness_783.csv",
        "Connectivity_783.parquet",
        "2023_03_23_completeness_630_final.csv",
        "2023_03_23_connectivity_630_final.parquet",
    }
    with (SHIU_DIR / "VENDOR.toml").open("rb") as fh:
        vendor = tomllib.load(fh)
    assert manifest["model.py"].sha256 == vendor["files"]["model.py"]["upstream_sha256"]
