import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, TextIO

import numpy as np
import pandas as pd

from rr_discovery.config import (
    DiscoveryConfig,
    RegressConfig,
    StimSet,
    require_model_input,
    require_regress,
)
from rr_discovery.data import IntegrityError
from rr_discovery.model_input import output_paths, verify_outputs
from rr_discovery.vendor import (
    RUNNER,
    V630Status,
    read_vendor_record,
    v630_status,
    vendored_code_hash,
    vendored_problems,
)


class RegressError(Exception):
    pass


@dataclass(frozen=True)
class SweepRow:
    frequency_hz: float
    mean_hz: float
    sd_hz: float
    n_trials: int
    wall_s: float


@dataclass(frozen=True)
class SweepTable:
    rows: tuple[SweepRow, ...]

    @property
    def by_freq(self) -> dict[float, SweepRow]:
        return {row.frequency_hz: row for row in self.rows}


@dataclass(frozen=True)
class CheckOutcome:
    ok: bool
    detail: str


@dataclass(frozen=True)
class RegressionResult:
    monotonic: CheckOutcome
    ratio: CheckOutcome
    equivalence: CheckOutcome
    ratio_v630: CheckOutcome | None
    v630_status: str
    verdict: Literal["PASS", "FAIL"]
    sim_env: Literal["py314", "fallback", "undecided"]
    notes: tuple[str, ...]


UNDECIDED_NOTE = (
    "environments are equivalent; failure is not environment-caused; "
    "user decision required before M5"
)


def table_from_result(result: Mapping[str, Any]) -> SweepTable:
    t_run_s = float(result["t_run_s"])
    rows: list[SweepRow] = []
    for condition in result["conditions"]:
        rates = np.asarray(condition["readout_spikes"], dtype=float) / t_run_s
        rows.append(
            SweepRow(
                frequency_hz=float(condition["frequency_hz"]),
                mean_hz=float(rates.mean()),
                sd_hz=float(rates.std(ddof=0)),
                n_trials=len(rates),
                wall_s=float(condition["wall_s"]),
            )
        )
    rows.sort(key=lambda row: row.frequency_hz)
    return SweepTable(rows=tuple(rows))


def check_monotonic(t: SweepTable) -> CheckOutcome:
    for a, b in zip(t.rows, t.rows[1:], strict=False):
        if b.mean_hz < a.mean_hz - max(a.sd_hz, b.sd_hz):
            return CheckOutcome(
                False,
                f"{a.frequency_hz:g} Hz {a.mean_hz:.3f} -> "
                f"{b.frequency_hz:g} Hz {b.mean_hz:.3f} drops by more than 1 SD "
                f"(sd {a.sd_hz:.3f}, {b.sd_hz:.3f})",
            )
    return CheckOutcome(True, "non-decreasing within 1 SD")


def check_ratio(
    t: SweepTable, *, at_hz: float = 100.0, lo: float = 0.7, hi: float = 0.9
) -> CheckOutcome:
    by_freq = t.by_freq
    if at_hz not in by_freq:
        return CheckOutcome(False, f"no {at_hz:g} Hz row")
    mx = max(row.mean_hz for row in t.rows)
    if mx <= 0:
        return CheckOutcome(False, "max mean is 0")
    ratio = by_freq[at_hz].mean_hz / mx
    return CheckOutcome(
        lo <= ratio <= hi,
        f"R100/max = {ratio:.3f} (allowed [{lo}, {hi}])",
    )


def check_equivalence(
    t: SweepTable, golden: SweepTable, *, n_sd: float = 2.0, rel: float = 0.15
) -> CheckOutcome:
    current = t.by_freq
    reference = golden.by_freq
    if set(current) != set(reference):
        return CheckOutcome(False, "frequency grids differ")
    failures: list[str] = []
    for freq in sorted(reference):
        g = reference[freq]
        m = current[freq].mean_hz
        tol = max(n_sd * g.sd_hz, rel * abs(g.mean_hz))
        if abs(m - g.mean_hz) > tol:
            failures.append(f"{freq:g} Hz: {m:.3f} vs golden {g.mean_hz:.3f} (tol {tol:.3f})")
    if failures:
        return CheckOutcome(False, "; ".join(failures))
    return CheckOutcome(True, "all frequencies within tolerance")


def check(table: SweepTable, golden: SweepTable) -> tuple[CheckOutcome, CheckOutcome, CheckOutcome]:
    return check_monotonic(table), check_ratio(table), check_equivalence(table, golden)


def decide(
    mono: CheckOutcome,
    ratio: CheckOutcome,
    equiv: CheckOutcome,
    *,
    ratio_v630: CheckOutcome | None,
    v630_status: str,
) -> RegressionResult:
    def result(
        verdict: Literal["PASS", "FAIL"],
        sim_env: Literal["py314", "fallback", "undecided"],
        notes: tuple[str, ...],
    ) -> RegressionResult:
        return RegressionResult(
            monotonic=mono,
            ratio=ratio,
            equivalence=equiv,
            ratio_v630=ratio_v630,
            v630_status=v630_status,
            verdict=verdict,
            sim_env=sim_env,
            notes=notes,
        )

    if not equiv.ok:
        return result(
            "FAIL",
            "fallback",
            ("environment not equivalent (ADR-14 c): simulation stage uses the fallback env",),
        )
    if mono.ok and ratio.ok:
        return result("PASS", "py314", ())
    if not ratio.ok:
        if ratio_v630 is None:
            return result(
                "FAIL",
                "undecided",
                (
                    f"ratio failed on v783; v630 rerun not possible: {v630_status}",
                    UNDECIDED_NOTE,
                ),
            )
        if ratio_v630.ok and mono.ok:
            return result(
                "PASS",
                "py314",
                ("ratio failed on v783 but holds on v630 (connectome-version effect, ADR-14)",),
            )
        return result("FAIL", "undecided", (UNDECIDED_NOTE,))
    return result("FAIL", "undecided", (UNDECIDED_NOTE,))


SweepFn = Callable[[Path, Path, Path], dict[str, Any]]
CheckFn = Callable[[Path], dict[str, Any]]
CompilerFn = Callable[[], bool]
Mode = Literal["regress", "capture", "smoke"]
ENV_KEYS = ("python", "brian2", "numpy", "pandas", "pyarrow", "joblib")


def run_runner(python: Path, job: Path, out: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [str(python), str(RUNNER), "sweep", "--job", str(job), "--out", str(out)], check=False
    )
    if proc.returncode != 0:
        raise RegressError(f"runner failed (exit {proc.returncode}) under {python}")
    result: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))
    return result


def runner_check(python: Path) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [str(python), str(RUNNER), "check"],
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        raise RegressError(f"runner check failed under {python}: {err}") from err
    lines = proc.stdout.strip().splitlines()
    if proc.returncode != 0 or not lines:
        raise RegressError(
            f"runner check failed (exit {proc.returncode}) under {python}: {proc.stderr.strip()}"
        )
    try:
        check: dict[str, Any] = json.loads(lines[-1])
    except json.JSONDecodeError as err:
        raise RegressError(f"runner check printed no JSON under {python}") from err
    return check


def cython_available() -> bool:
    from brian2.codegen.runtime.cython_rt import CythonCodeObject

    return bool(CythonCodeObject.is_available())


def make_job(
    *,
    label: str,
    completeness: Path,
    connectivity: Path,
    stim: StimSet,
    rc: RegressConfig,
    frequencies: tuple[float, ...] | None = None,
    n_trials: int | None = None,
    n_proc: int | None = None,
) -> dict[str, Any]:
    return {
        "schema": 1,
        "label": label,
        "completeness": str(completeness),
        "connectivity": str(connectivity),
        "stim_ids": list(stim.sugar_grn_ids),
        "readout_id": stim.mn9_id,
        "frequencies_hz": list(rc.frequencies_hz if frequencies is None else frequencies),
        "n_trials": rc.n_trials if n_trials is None else n_trials,
        "seed_base": rc.seed_base,
        "n_proc": rc.n_proc if n_proc is None else n_proc,
    }


def golden_document(
    table: SweepTable,
    run: Mapping[str, Any],
    *,
    input_hashes: Mapping[str, str],
    code_hash: str,
    rc: RegressConfig,
    data_version: str,
) -> dict[str, Any]:
    conditions = run["conditions"]
    return {
        "schema": 1,
        "kind": "rr-regress-golden",
        "data_version": data_version,
        "input_hashes": dict(input_hashes),
        "vendored_code_hash": code_hash,
        "env": run["env"],
        "host": run["host"],
        "frequencies_hz": list(rc.frequencies_hz),
        "n_trials": rc.n_trials,
        "seed_base": rc.seed_base,
        "seed_scheme": "seed_base + 1000*frequency_index + trial_index",
        "seeds": {f"{c['frequency_hz']:g}": c["seeds"] for c in conditions},
        "stim": {
            "sugar_grn_ids": list(rc.v783.sugar_grn_ids),
            "mn9_id": rc.v783.mn9_id,
            "source": rc.stim_source,
        },
        "rows": [asdict(row) for row in table.rows],
        "timing": {
            "total_wall_s": run["total_wall_s"],
            "per_condition_wall_s": {f"{c['frequency_hz']:g}": c["wall_s"] for c in conditions},
        },
        "peak_rss": run["peak_rss"],
    }


def load_golden(path: Path) -> tuple[SweepTable, dict[str, Any]]:
    doc: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    rows = tuple(SweepRow(**row) for row in doc["rows"])
    return SweepTable(rows=rows), doc


def _input_hashes(meta: Mapping[str, Any]) -> dict[str, str]:
    return {
        "completeness": meta["outputs"]["completeness"]["sha256"],
        "connectivity": meta["outputs"]["connectivity"]["sha256"],
    }


def _golden_mismatches(
    golden: Mapping[str, Any],
    *,
    rc: RegressConfig,
    input_hashes: Mapping[str, str],
    code_hash: str,
) -> list[str]:
    stim = golden.get("stim", {})
    checks = (
        ("input hashes", golden.get("input_hashes") == dict(input_hashes)),
        ("code hash", golden.get("vendored_code_hash") == code_hash),
        ("frequencies", golden.get("frequencies_hz") == list(rc.frequencies_hz)),
        ("n_trials", golden.get("n_trials") == rc.n_trials),
        ("seed_base", golden.get("seed_base") == rc.seed_base),
        (
            "stim",
            stim.get("sugar_grn_ids") == list(rc.v783.sugar_grn_ids)
            and stim.get("mn9_id") == rc.v783.mn9_id,
        ),
    )
    return [
        f"golden was captured with different {name}; recapture with --capture-golden --force"
        for name, ok in checks
        if not ok
    ]


def _capture_problems(rc: RegressConfig, python: Path, force: bool, check_fn: CheckFn) -> list[str]:
    problems: list[str] = []
    if not (python.is_file() and os.access(python, os.X_OK)):
        problems.append(f"--python {python} is not an executable file")
    else:
        env = check_fn(python)
        py = str(env.get("python", "unknown"))
        brian2 = str(env.get("brian2", "unknown"))
        cython = bool(env.get("cython_available", False))
        if not py.startswith("3.10.") or brian2 != "2.5.1" or not cython:
            problems.append(
                "fallback env must be python 3.10.* with brian2 2.5.1 and Cython available; "
                f"{python} reports python {py}, brian2 {brian2}, cython_available {cython}"
            )
    if rc.golden.exists() and not force:
        problems.append("golden exists; pass --force to recapture")
    return problems


def preflight(
    cfg: DiscoveryConfig,
    *,
    mode: Mode,
    python: Path | None,
    force: bool,
    compiler_ok: CompilerFn,
    check_fn: CheckFn,
) -> list[str]:
    rc = require_regress(cfg)
    mi = require_model_input(cfg)
    paths = output_paths(mi.out_dir, cfg.version)
    try:
        meta = verify_outputs(paths)
    except IntegrityError as err:
        return [f"model input missing or modified: {err}; run 'rr-discover model-input'"]

    problems = vendored_problems(read_vendor_record())
    if problems:
        return problems

    index = set(pd.read_csv(paths.completeness, index_col=0).index.tolist())
    missing = sorted(i for i in (*rc.v783.sugar_grn_ids, rc.v783.mn9_id) if i not in index)
    if missing:
        return [f"stimulus or readout ids not in completeness: {missing}"]

    if mode == "capture":
        if python is None:
            return ["--capture-golden needs --python <path to fallback env python>"]
        return _capture_problems(rc, python, force, check_fn)

    problems = []
    if mode in ("regress", "smoke") and not compiler_ok():
        problems.append("no working C/C++ compiler for brian2 Cython (see discovery/README.md)")
    if mode == "regress":
        if not rc.golden.is_file():
            problems.append(
                f"golden file {rc.golden} missing; capture it once with "
                "'rr-discover regress --capture-golden --python <fallback python>'"
            )
        else:
            golden: dict[str, Any] = json.loads(rc.golden.read_text(encoding="utf-8"))
            problems.extend(
                _golden_mismatches(
                    golden,
                    rc=rc,
                    input_hashes=_input_hashes(meta),
                    code_hash=vendored_code_hash(),
                )
            )
    return problems


def _sweep(
    label: str,
    *,
    python: Path,
    completeness: Path,
    connectivity: Path,
    stim: StimSet,
    rc: RegressConfig,
    sweep_fn: SweepFn,
    frequencies: tuple[float, ...] | None = None,
    n_trials: int | None = None,
    n_proc: int | None = None,
) -> dict[str, Any]:
    job_path = rc.work_dir / f"{label}.job.json"
    out_path = rc.work_dir / f"{label}.result.json"
    job = make_job(
        label=label,
        completeness=completeness,
        connectivity=connectivity,
        stim=stim,
        rc=rc,
        frequencies=frequencies,
        n_trials=n_trials,
        n_proc=n_proc,
    )
    job_path.write_text(json.dumps(job, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return sweep_fn(python, job_path, out_path)


def _word(outcome: CheckOutcome) -> str:
    return "PASS" if outcome.ok else "FAIL"


def _mib(n: Any) -> str:
    return f"{float(n) / 2**20:.0f}"


def _env_line(env: Mapping[str, Any]) -> str:
    return ", ".join(f"{k} {env.get(k, 'n/a')}" for k in ENV_KEYS)


def _summary_run(run: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "env": run["env"],
        "host": run["host"],
        "peak_rss": run["peak_rss"],
        "per_condition": {f"{c['frequency_hz']:g}": float(c["wall_s"]) for c in run["conditions"]},
        "total": float(run["total_wall_s"]),
    }


def _summary_golden(doc: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "env": doc["env"],
        "host": doc["host"],
        "peak_rss": doc["peak_rss"],
        "per_condition": doc["timing"]["per_condition_wall_s"],
        "total": doc["timing"]["total_wall_s"],
    }


def _table_md(title: str, table: SweepTable) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "| frequency | mean Hz | SD | trials | wall s |",
        "|---|---|---|---|---|",
    ]
    for row in table.rows:
        lines.append(
            f"| {row.frequency_hz:g} | {row.mean_hz:.3f} | {row.sd_hz:.3f} | "
            f"{row.n_trials} | {row.wall_s:.1f} |"
        )
    return [*lines, ""]


def _timing_line(label: str, s: Mapping[str, Any]) -> str:
    per = list(s["per_condition"].values())
    mean = sum(per) / len(per) if per else 0.0
    per_hour = f"{3600 / mean:.1f}" if mean > 0 else "n/a"
    detail = ", ".join(f"{k} Hz {v:.1f} s" for k, v in s["per_condition"].items())
    return (
        f"- {label}: total {s['total']:.1f} s; per condition: {detail}; "
        f"mean {mean:.1f} s; conditions/hour {per_hour}"
    )


def _peak_line(label: str, s: Mapping[str, Any]) -> str:
    p = s["peak_rss"]
    return (
        f"- {label}: parent {_mib(p['parent_bytes'])} MiB, "
        f"max worker {_mib(p['max_worker_bytes'])} MiB, n_workers {p['n_workers']}, "
        f"sum of worker peaks {_mib(p['sum_worker_peak_bytes'])} MiB"
    )


def render_report(
    *,
    result: RegressionResult,
    table: SweepTable,
    golden_table: SweepTable,
    golden_doc: Mapping[str, Any],
    run: Mapping[str, Any],
    table630: SweepTable | None,
    run630: Mapping[str, Any] | None,
    st: V630Status,
    rc: RegressConfig,
    input_hashes: Mapping[str, str],
    code_hash: str,
) -> str:
    current = _summary_run(run)
    golden = _summary_golden(golden_doc)
    summaries: list[tuple[str, dict[str, Any]]] = [("3.14 (current)", current), ("golden", golden)]
    lines: list[str] = [
        "# M2 Shiu regression check",
        "",
        "## Verdict",
        "",
        f"**{result.verdict}**",
        "",
    ]

    lines += ["## Checks", ""]
    lines.append(f"- monotonic: {_word(result.monotonic)} ({result.monotonic.detail})")
    lines.append(f"- ratio: {_word(result.ratio)} ({result.ratio.detail})")
    lines.append(f"- equivalence: {_word(result.equivalence)} ({result.equivalence.detail})")
    if result.ratio_v630 is not None:
        lines.append(f"- ratio (v630): {_word(result.ratio_v630)} ({result.ratio_v630.detail})")
    lines.append("")

    lines += ["## Simulation environment for M5/M6", "", f"- sim_env: {result.sim_env}"]
    lines += [f"- note: {note}" for note in result.notes]
    lines.append("")

    lines += ["## Sweep tables", ""]
    lines += _table_md("3.14 (current)", table)
    lines += _table_md("golden", golden_table)
    if table630 is not None and run630 is not None:
        lines += _table_md("v630", table630)
        summaries.append(("v630", _summary_run(run630)))

    lines += ["## Environments", ""]
    for label, summary in summaries:
        lines.append(f"- {label}: {_env_line(summary['env'])}")
    lines.append("")

    lines += ["## Host", ""]
    for label, summary in summaries:
        host = ", ".join(f"{k} {v}" for k, v in summary["host"].items())
        lines.append(f"- {label}: {host}")
    lines.append("")

    lines += ["## Timing", ""]
    lines += [_timing_line(label, summary) for label, summary in summaries]
    lines.append("")

    lines += ["## Peak memory", ""]
    lines += [_peak_line(label, summary) for label, summary in summaries]
    lines.append("")

    lines += ["## v630 availability", "", f"- {st.detail}", ""]

    lines += ["## Inputs", ""]
    for name, sha in input_hashes.items():
        lines.append(f"- {name} sha256: {sha}")
    lines.append(f"- vendored code hash: {code_hash}")
    lines.append(f"- stim source: {rc.stim_source}")
    lines.append("")
    return "\n".join(lines)


def execute(
    cfg: DiscoveryConfig,
    *,
    mode: Mode,
    python: Path | None = None,
    force: bool = False,
    sweep_fn: SweepFn = run_runner,
    check_fn: CheckFn = runner_check,
    compiler_ok: CompilerFn = cython_available,
    out: TextIO | None = None,
) -> int:
    stream: TextIO = sys.stdout if out is None else out
    try:
        problems = preflight(
            cfg,
            mode=mode,
            python=python,
            force=force,
            compiler_ok=compiler_ok,
            check_fn=check_fn,
        )
        if problems:
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
            return 1

        rc = require_regress(cfg)
        paths = output_paths(require_model_input(cfg).out_dir, cfg.version)
        meta = verify_outputs(paths)
        input_hashes = _input_hashes(meta)
        code_hash = vendored_code_hash()
        rc.work_dir.mkdir(parents=True, exist_ok=True)
        this_python = Path(sys.executable)

        if mode == "smoke":
            run = _sweep(
                "smoke-v783",
                python=this_python,
                completeness=paths.completeness,
                connectivity=paths.connectivity,
                stim=rc.v783,
                rc=rc,
                sweep_fn=sweep_fn,
                frequencies=(100.0,),
                n_trials=1,
                n_proc=1,
            )
            cond = run["conditions"][0]
            peak = max(run["peak_rss"]["parent_bytes"], run["peak_rss"]["max_worker_bytes"])
            print(
                f"smoke: 1 trial at 100 Hz: {cond['wall_s']:.1f} s, "
                f"MN9 spikes {cond['readout_spikes'][0]}, peak RSS {_mib(peak)} MiB",
                file=stream,
            )
            return 0

        if mode == "capture":
            if python is None:
                raise RegressError("--capture-golden needs --python <path to fallback env python>")
            run = _sweep(
                "golden-v783",
                python=python,
                completeness=paths.completeness,
                connectivity=paths.connectivity,
                stim=rc.v783,
                rc=rc,
                sweep_fn=sweep_fn,
            )
            doc = golden_document(
                table_from_result(run),
                run,
                input_hashes=input_hashes,
                code_hash=code_hash,
                rc=rc,
                data_version=cfg.version,
            )
            rc.golden.parent.mkdir(parents=True, exist_ok=True)
            rc.golden.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            print(f"golden: {rc.golden}", file=stream)
            return 0

        run = _sweep(
            "regress-v783",
            python=this_python,
            completeness=paths.completeness,
            connectivity=paths.connectivity,
            stim=rc.v783,
            rc=rc,
            sweep_fn=sweep_fn,
        )
        table = table_from_result(run)
        golden_table, golden_doc = load_golden(rc.golden)
        mono, ratio, equiv = check(table, golden_table)

        st = v630_status(cfg)
        ratio_v630: CheckOutcome | None = None
        table630: SweepTable | None = None
        run630: dict[str, Any] | None = None
        if (
            equiv.ok
            and not ratio.ok
            and st.available
            and st.completeness is not None
            and st.connectivity is not None
        ):
            run630 = _sweep(
                "regress-v630",
                python=this_python,
                completeness=st.completeness,
                connectivity=st.connectivity,
                stim=rc.v630,
                rc=rc,
                sweep_fn=sweep_fn,
            )
            table630 = table_from_result(run630)
            ratio_v630 = check_ratio(table630)

        result = decide(mono, ratio, equiv, ratio_v630=ratio_v630, v630_status=st.detail)
        report_text = render_report(
            result=result,
            table=table,
            golden_table=golden_table,
            golden_doc=golden_doc,
            run=run,
            table630=table630,
            run630=run630,
            st=st,
            rc=rc,
            input_hashes=input_hashes,
            code_hash=code_hash,
        )
        rc.report.parent.mkdir(parents=True, exist_ok=True)
        rc.report.write_text(report_text, encoding="utf-8")

        print(f"monotonic: {_word(mono)}  {mono.detail}", file=stream)
        print(f"ratio: {_word(ratio)}  {ratio.detail}", file=stream)
        print(f"equivalence: {_word(equiv)}  {equiv.detail}", file=stream)
        if ratio_v630 is not None:
            print(f"ratio (v630): {_word(ratio_v630)}  {ratio_v630.detail}", file=stream)
        print(f"v630 inputs: {st.detail}", file=stream)
        print(f"verdict: {result.verdict}", file=stream)
        print(f"simulation env for M5/M6: {result.sim_env}", file=stream)
        print(f"report: {rc.report}", file=stream)
        return 0 if result.verdict == "PASS" else 1
    except RegressError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
