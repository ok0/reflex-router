import hashlib
import io
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from rr_discovery.annotations import ids_by_cell_type, load_annotations, load_root_ids
from rr_discovery.config import (
    DiscoverConfig,
    DiscoveryConfig,
    require_discover,
    require_model_input,
)
from rr_discovery.data import paths_from_config
from rr_discovery.model_input import output_paths, verify_outputs
from rr_discovery.vendor import SHIU_DIR

CONDITION_RUNNER = SHIU_DIR / "condition_runner.py"
ROBUSTNESS_RUNNER = SHIU_DIR / "robustness_runner.py"
SPIKES_HEADER = "trial\troot_id\tn_spikes"
_VERDICT_RE = re.compile(r"^\*\*(PASS|FAIL)\*\*\s*$", re.MULTILINE)
_SIM_ENV_RE = re.compile(r"^- sim_env: (\S+)\s*$", re.MULTILINE)


class RunError(Exception):
    pass


@dataclass(frozen=True)
class StimSets:
    lc4: np.ndarray
    lplc2: np.ndarray

    @property
    def all(self) -> np.ndarray:
        return np.union1d(self.lc4, self.lplc2).astype(np.int64)


@dataclass(frozen=True)
class M2Verdict:
    verdict: str
    sim_env: str


ConditionFn = Callable[[Path, Path, Path, Path], dict[str, Any]]


def _exact_ids(
    ann: pd.DataFrame, cell_type: str, expected: int, valid_ids: np.ndarray
) -> np.ndarray:
    ids = ids_by_cell_type(ann, cell_type, valid_ids=valid_ids)
    if ids.size != expected:
        raise RunError(
            f"{cell_type} count {ids.size} != expected {expected} (annotation lookup); aborting"
        )
    return ids


def stimulated_sets(ann: pd.DataFrame, valid_ids: np.ndarray, dc: DiscoverConfig) -> StimSets:
    lc4 = _exact_ids(ann, dc.lc4_cell_type, dc.expected_lc4, valid_ids)
    lplc2 = _exact_ids(ann, dc.lplc2_cell_type, dc.expected_lplc2, valid_ids)
    overlap = np.intersect1d(lc4, lplc2)
    if overlap.size:
        raise RunError(f"LC4 and LPLC2 stimulated sets overlap: {overlap.tolist()[:10]}")
    return StimSets(lc4=lc4, lplc2=lplc2)


def read_m2_verdict(report: Path) -> M2Verdict:
    if not report.is_file():
        raise RunError(f"M2 report not found: {report}")
    text = report.read_text(encoding="utf-8")
    verdict = _VERDICT_RE.search(text)
    if verdict is None:
        raise RunError(f"no **PASS** or **FAIL** verdict line in {report}")
    sim_env = _SIM_ENV_RE.search(text)
    if sim_env is None:
        raise RunError(f"no '- sim_env:' line in {report}")
    return M2Verdict(verdict=verdict.group(1), sim_env=sim_env.group(1))


def make_condition_job(
    *,
    label: str,
    completeness: Path,
    connectivity: Path,
    stim_ids: np.ndarray,
    dc: DiscoverConfig,
    n_proc: int,
) -> dict[str, Any]:
    return {
        "schema": 1,
        "label": label,
        "completeness": str(completeness),
        "connectivity": str(connectivity),
        "stim_ids": [int(i) for i in np.asarray(stim_ids, dtype=np.int64).tolist()],
        "r_poi_hz": float(dc.rate_hz),
        "n_trials": int(dc.n_trials),
        "seed_base": int(dc.seed_base),
        "n_proc": int(n_proc),
    }


def run_condition_runner(
    python: Path, job: Path, spikes: Path, out: Path, *, runner: Path = CONDITION_RUNNER
) -> dict[str, Any]:
    proc = subprocess.run(
        [
            str(python),
            str(runner),
            "condition",
            "--job",
            str(job),
            "--spikes",
            str(spikes),
            "--out",
            str(out),
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise RunError(f"condition runner exited with status {proc.returncode}")
    parsed: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
    return parsed


def run_paths(dc: DiscoverConfig, version: str) -> tuple[Path, Path, Path]:
    return (
        dc.work_dir / f"condition_{version}.job.json",
        dc.work_dir / f"spikes_{version}.tsv",
        dc.work_dir / f"run_{version}.json",
    )


def read_spike_counts(path: Path, *, expected_sha256: str) -> pd.DataFrame:
    if not path.is_file():
        raise RunError(f"spike counts file not found: {path}")
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        raise RunError(f"{path} sha256 mismatch: expected {expected_sha256}, got {actual}")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as err:
        raise RunError(f"{path} is not ASCII: {err}") from err
    header = text.split("\n", 1)[0]
    if header != SPIKES_HEADER:
        raise RunError(f"{path} header is {header!r}, expected {SPIKES_HEADER!r}")
    frame = pd.read_csv(io.StringIO(text), sep="\t")
    return pd.DataFrame(frame[["trial", "root_id", "n_spikes"]]).astype(np.int64)


def write_run_log(work_dir: Path, step: str, entry: Mapping[str, Any]) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    path = work_dir / "run_log.json"
    log: dict[str, Any] = {}
    if path.is_file():
        log = json.loads(path.read_text(encoding="utf-8"))
    log[step] = dict(entry)
    path.write_text(json.dumps(log, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def run_stage(
    cfg: DiscoveryConfig,
    *,
    python: Path | None,
    n_proc: int | None,
    condition_fn: ConditionFn = run_condition_runner,
) -> Path:
    dc = require_discover(cfg)
    verdict = read_m2_verdict(dc.m2_report)
    if verdict.verdict != "PASS":
        raise RunError(f"M2 verdict is {verdict.verdict}; the whole-brain run requires PASS")
    if python is None:
        if verdict.sim_env != "py314":
            raise RunError(f"M2 sim_env is {verdict.sim_env}; pass --python <fallback python>")
        python = Path(sys.executable)
    effective_n_proc = dc.n_proc if n_proc is None else n_proc

    mi = output_paths(require_model_input(cfg).out_dir, cfg.version)
    verify_outputs(mi)
    paths = paths_from_config(cfg)
    ann = load_annotations(paths.annotations)
    valid = load_root_ids(paths.root_ids)
    stim = stimulated_sets(ann, valid, dc)

    job_path, spikes_path, out_path = run_paths(dc, cfg.version)
    job = make_condition_job(
        label=cfg.version,
        completeness=mi.completeness,
        connectivity=mi.connectivity,
        stim_ids=stim.all,
        dc=dc,
        n_proc=effective_n_proc,
    )
    dc.work_dir.mkdir(parents=True, exist_ok=True)
    job_path.write_text(json.dumps(job, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    started = datetime.now(UTC)
    t0 = time.monotonic()
    result = condition_fn(python, job_path, spikes_path, out_path)
    wall_s = time.monotonic() - t0

    write_run_log(
        dc.work_dir,
        "run",
        {
            "started_utc": started.isoformat(timespec="seconds"),
            "wall_s": wall_s,
            "python": str(python),
            "n_proc": effective_n_proc,
            "host": result["host"],
            "total_wall_s": result["total_wall_s"],
            "trial_wall_s": result["trial_wall_s"],
            "peak_rss": result["peak_rss"],
        },
    )
    return out_path
