import json
import os
from pathlib import Path

import pytest
from rr_discovery import cli, robust_report, robustness
from rr_discovery.config import (
    DiscoverConfig,
    DiscoveryConfig,
    load_config,
    require_discover,
    require_robustness,
)

pytestmark = [
    pytest.mark.longrun,
    pytest.mark.flywire,
    pytest.mark.skipif(
        os.environ.get("RR_M6_LONGRUN") != "1",
        reason="M6 full grid (~2 h); set RR_M6_LONGRUN=1",
    ),
]

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "discovery/discovery.toml"


def _m5_bytes(dc: DiscoverConfig) -> dict[str, bytes]:
    return {
        "circuit": (dc.out_dir / "circuit.json").read_bytes(),
        "metadata": (dc.out_dir / "metadata.json").read_bytes(),
        "parallel": dc.candidates_report.read_bytes(),
        "responsive": dc.responsive_table.read_bytes(),
    }


def test_full_grid() -> None:
    cfg: DiscoveryConfig = load_config(CONFIG, base_dir=REPO)
    dc = require_discover(cfg)
    rc = require_robustness(cfg)
    before = _m5_bytes(dc)

    assert cli.main(["robustness", "--config", str(CONFIG)]) == 0

    results = json.loads(rc.results.read_text(encoding="utf-8"))
    conditions = results["conditions"]
    assert len(conditions) == 40
    assert {c["family"] for c in conditions} >= {"random_set", "shuffle"}
    assert "chance" in results
    assert "persistence" in results
    for cond in conditions:
        assert cond["status"] in {"completed", "failed", "dropped"}

    report_text = rc.report.read_text(encoding="utf-8")
    assert robust_report.STATEMENT in report_text
    assert robust_report.FORBIDDEN.search(report_text.replace(robust_report.STATEMENT, "")) is None

    report_before = rc.report.read_bytes()
    results_before = rc.results.read_bytes()
    robustness.report_stage(cfg)
    assert rc.report.read_bytes() == report_before
    assert rc.results.read_bytes() == results_before

    summary = robustness.run_stage(cfg, python=None, n_proc=None)
    assert summary.n_run == 0

    assert _m5_bytes(dc) == before

    log = json.loads((rc.work_dir / "run_log.json").read_text(encoding="utf-8"))
    assert any(key.startswith("run:") for key in log)
    assert "run_total" in log
