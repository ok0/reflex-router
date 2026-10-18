import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_DIRS = [ROOT / "src", ROOT / "discovery/src"]
SANITY = ROOT / "discovery/src/rr_discovery/sanity.py"
ROOT_ID_RE = re.compile(r"(?<![\d_])\d(?:_?\d){17}(?![\d_])")
CORE_SRC = ROOT / "src" / "reflex_router"


def test_root_id_literal_only_in_sanity_module() -> None:
    hits: list[tuple[Path, str]] = []
    for src in SRC_DIRS:
        if not src.exists():
            continue
        for path in src.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for m in ROOT_ID_RE.finditer(text):
                hits.append((path, m.group(0)))
    offending = [p for p, _ in hits if p != SANITY]
    assert not offending, "root-ID literal found outside sanity.py: " + ", ".join(
        str(p) for p in offending
    )
    sanity_hits = [h for h in hits if h[0] == SANITY]
    assert len(sanity_hits) == 1, (
        f"expected exactly one root-ID literal in sanity.py, found {len(sanity_hits)}"
    )


def test_root_license_mit_excludes_circuit_data() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in text
    assert "circuit-data/" in text


def test_circuit_data_license_cc_by_nc() -> None:
    text = (ROOT / "circuit-data/LICENSE").read_text(encoding="utf-8")
    assert "Attribution-NonCommercial 4.0 International" in text


def test_notice_stub_contents() -> None:
    text = (ROOT / "circuit-data/NOTICE.md").read_text(encoding="utf-8")
    for needle in (
        "Dorkenwald",
        "10.5281/zenodo.10676866",
        "derived",
        "CC BY 4.0",
        "CC BY-NC 4.0",
        "stricter",
    ):
        assert needle in text, f"NOTICE.md missing {needle!r}"


def test_notice_m5_contents() -> None:
    text = (ROOT / "circuit-data/NOTICE.md").read_text(encoding="utf-8")
    for needle in (
        "Schlegel",
        "10.1038/s41586-024-07686-5",
        "Shiu",
        "10.13140/RG.2.2.35928.67844",
        "Eckstein",
        "M5",
    ):
        assert needle in text, f"NOTICE.md missing {needle!r}"


def test_m5_docs_filter_attribution() -> None:
    text = (ROOT / "discovery/README.md").read_text(encoding="utf-8")
    for needle in (
        "10.1101/2023.06.27.546055",
        "Codex's default threshold is 5 synapses",
        "Deviations from the stated rule",
    ):
        assert needle in text, f"discovery/README.md missing {needle!r}"


def test_gitignore_raw_ignored_reports_tracked() -> None:
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        pytest.skip("not a git checkout")

    raw_dir = ROOT / "circuit-data/v783/raw"
    reports_dir = ROOT / "circuit-data/v783/reports"
    raw_existed = raw_dir.exists()
    raw_file = raw_dir / "_rr_dummy.feather"
    report_file = reports_dir / "_rr_dummy_report.md"
    try:
        raw_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        raw_file.write_bytes(b"dummy")
        report_file.write_text("dummy\n", encoding="utf-8")

        raw_rc = subprocess.run(["git", "check-ignore", "-q", str(raw_file)], cwd=ROOT).returncode
        report_rc = subprocess.run(
            ["git", "check-ignore", "-q", str(report_file)], cwd=ROOT
        ).returncode
        assert raw_rc == 0, "raw data file is not git-ignored"
        assert report_rc == 1, "reports file is git-ignored"
    finally:
        for p in (raw_file, report_file):
            if p.exists():
                p.unlink()
        if not raw_existed and raw_dir.exists():
            raw_dir.rmdir()


def test_gitignore_m2_outputs() -> None:
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        pytest.skip("not a git checkout")

    dirs = [
        ROOT / "circuit-data/shiu",
        ROOT / "circuit-data/shiu/raw",
        ROOT / "circuit-data/v783",
        ROOT / "circuit-data/v783/model_input",
        ROOT / "circuit-data/v783/regress",
    ]
    existed = {d for d in dirs if d.exists()}
    dummies = [
        ROOT / "circuit-data/v783/model_input/_rr_dummy.parquet",
        ROOT / "circuit-data/v783/regress/_rr_dummy.json",
        ROOT / "circuit-data/shiu/raw/_rr_dummy.csv",
    ]
    golden = ROOT / "circuit-data/v783/reports/regress_golden.json"
    try:
        for p in dummies:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"dummy")
        for p in dummies:
            rc = subprocess.run(["git", "check-ignore", "-q", str(p)], cwd=ROOT).returncode
            assert rc == 0, f"{p.relative_to(ROOT)} is not git-ignored"
        golden_rc = subprocess.run(["git", "check-ignore", "-q", str(golden)], cwd=ROOT).returncode
        assert golden_rc == 1, "regress_golden.json is git-ignored"
    finally:
        for p in dummies:
            if p.exists():
                p.unlink()
        for d in sorted(dirs, key=lambda x: len(x.parts), reverse=True):
            if d not in existed:
                try:
                    d.rmdir()
                except OSError:
                    pass


def test_gitignore_m5_outputs() -> None:
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        pytest.skip("not a git checkout")

    discover_dir = ROOT / "circuit-data/v783/discover"
    discover_existed = discover_dir.exists()
    dummy = discover_dir / "_rr_dummy.tsv"
    tracked = (
        ROOT / "circuit-data/v783/circuit.json",
        ROOT / "circuit-data/v783/metadata.json",
        ROOT / "circuit-data/v783/reports/parallel_dn_candidates.md",
    )
    try:
        discover_dir.mkdir(parents=True, exist_ok=True)
        dummy.write_bytes(b"dummy")
        rc = subprocess.run(["git", "check-ignore", "-q", str(dummy)], cwd=ROOT).returncode
        assert rc == 0, "circuit-data/v783/discover/ file is not git-ignored"
        for p in tracked:
            rc = subprocess.run(["git", "check-ignore", "-q", str(p)], cwd=ROOT).returncode
            assert rc == 1, f"{p.relative_to(ROOT)} is git-ignored"
    finally:
        if dummy.exists():
            dummy.unlink()
        if not discover_existed and discover_dir.exists():
            discover_dir.rmdir()


def test_core_imports_only_stdlib_numpy_self() -> None:
    allowed = sys.stdlib_module_names | {"numpy", "reflex_router"}
    offending: list[str] = []
    for path in sorted(CORE_SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
                modules = [node.module]
            else:
                continue
            for name in modules:
                if name.split(".")[0] not in allowed:
                    offending.append(f"{path.relative_to(ROOT)}:{node.lineno}:{name}")
    assert not offending, "non-stdlib/numpy/self imports in core: " + ", ".join(offending)


def _is_taskgroup_call(expr: ast.expr) -> bool:
    if not isinstance(expr, ast.Call):
        return False
    func = expr.func
    if isinstance(func, ast.Attribute):
        return func.attr.endswith("TaskGroup")
    if isinstance(func, ast.Name):
        return func.id.endswith("TaskGroup")
    return False


def test_no_taskgroup_cancel_in_core() -> None:
    for path in sorted(CORE_SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "TaskGroup.cancel" not in text, f"TaskGroup.cancel found in {path.relative_to(ROOT)}"
        tree = ast.parse(text, filename=str(path))
        tg_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if isinstance(item.optional_vars, ast.Name) and _is_taskgroup_call(
                        item.context_expr
                    ):
                        tg_names.add(item.optional_vars.id)
            elif isinstance(node, ast.Assign) and _is_taskgroup_call(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        tg_names.add(target.id)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "cancel"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in tg_names
            ):
                raise AssertionError(
                    f"TaskGroup cancel call at {path.relative_to(ROOT)}:{node.lineno}"
                )
