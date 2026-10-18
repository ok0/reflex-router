"""Sugar-GRN to MN9 sweep runner for the Shiu whole-brain model (MIT, this project's code).

Drives Shiu's vendored model.run_trial once per trial with an explicit brian2.seed,
because run_exp sets no seed. default_params are unchanged except r_poi, which is set
per sweep frequency as in Shiu's example.ipynb. Must run on Python 3.10 and 3.14.
"""

import argparse
import importlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast

import brian2
import joblib
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent


def _load_model() -> Any:
    sys.path.insert(0, str(_HERE))
    return importlib.import_module("model")


def _version(name: str) -> str:
    return str(importlib.import_module(name).__version__)


def _cython_available() -> bool:
    try:
        from brian2.codegen.runtime.cython_rt import CythonCodeObject

        return bool(CythonCodeObject.is_available())
    except Exception:
        return False


def _check() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "brian2": brian2.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "pyarrow": _version("pyarrow"),
        "joblib": joblib.__version__,
        "cython_available": _cython_available(),
    }


def _maxrss() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * (
        1 if sys.platform == "darwin" else 1024
    )


def _try(fn: Any) -> Any:
    try:
        return fn()
    except Exception:
        return None


def _sysctl(key: str) -> str:
    out = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _cpu() -> str | None:
    if sys.platform == "darwin":
        return _try(lambda: _sysctl("machdep.cpu.brand_string"))
    if sys.platform.startswith("linux"):

        def _linux_cpu() -> str | None:
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
            return None

        found = _try(_linux_cpu)
        if found is not None:
            return found
    return _try(platform.processor)


def _ram_bytes() -> int | None:
    if sys.platform == "darwin":
        return _try(lambda: int(_sysctl("hw.memsize")))
    return _try(lambda: os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))


def _host() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": _cpu(),
        "n_cpu": os.cpu_count(),
        "ram_bytes": _ram_bytes(),
    }


def _trial(
    seed: int,
    exc: list[int],
    ro: int,
    comp: str,
    conn: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    model = _load_model()
    brian2.seed(seed)
    t = time.perf_counter()
    spk = model.run_trial(exc, [], [], Path(comp), Path(conn), params)
    wall = time.perf_counter() - t
    return {
        "seed": seed,
        "readout_spikes": len(spk.get(ro, [])),
        "wall_s": wall,
        "pid": os.getpid(),
        "maxrss_bytes": _maxrss(),
    }


def _sweep(job_path: Path, out_path: Path) -> int:
    job = json.loads(job_path.read_text())
    model = _load_model()
    comp = job["completeness"]
    conn = job["connectivity"]
    stim_ids = [int(i) for i in job["stim_ids"]]
    readout_id = int(job["readout_id"])
    n_trials = int(job["n_trials"])
    seed_base = int(job["seed_base"])
    n_proc = int(job["n_proc"])
    label = job["label"]

    flyid2i = {int(fid): i for i, fid in enumerate(pd.read_csv(comp, index_col=0).index)}
    missing = sorted({i for i in [*stim_ids, readout_id] if i not in flyid2i})
    if missing:
        print(f"error: ids not in completeness: {missing}", file=sys.stderr)
        return 3

    exc = [flyid2i[i] for i in stim_ids]
    ro = flyid2i[readout_id]

    env = _check()
    t_run_s = float(model.default_params["t_run"] / brian2.second)
    total_t0 = time.perf_counter()
    conditions: list[dict[str, Any]] = []
    trials_all: list[dict[str, Any]] = []
    for k, f in enumerate(job["frequencies_hz"]):
        params = dict(model.default_params)
        params["r_poi"] = float(f) * brian2.Hz
        seeds = [seed_base + 1000 * k + t for t in range(n_trials)]
        t0 = time.perf_counter()
        out = cast(
            list[dict[str, Any]],
            joblib.Parallel(n_jobs=n_proc, backend="loky")(
                joblib.delayed(_trial)(s, exc, ro, comp, conn, params) for s in seeds
            ),
        )
        wall = time.perf_counter() - t0
        print(f"[{label}] {f:g} Hz: {n_trials} trials in {wall:.1f} s", file=sys.stderr)
        conditions.append(
            {
                "frequency_hz": float(f),
                "seeds": [r["seed"] for r in out],
                "readout_spikes": [r["readout_spikes"] for r in out],
                "trial_wall_s": [r["wall_s"] for r in out],
                "wall_s": wall,
            }
        )
        trials_all.extend(out)
    total_wall = time.perf_counter() - total_t0

    per_pid: dict[int, int] = {}
    for r in trials_all:
        pid = int(r["pid"])
        per_pid[pid] = max(per_pid.get(pid, 0), int(r["maxrss_bytes"]))

    result = {
        "schema": 1,
        "label": label,
        "job": job,
        "env": env,
        "host": _host(),
        "t_run_s": t_run_s,
        "conditions": conditions,
        "total_wall_s": total_wall,
        "peak_rss": {
            "parent_bytes": _maxrss(),
            "max_worker_bytes": max(per_pid.values()) if per_pid else 0,
            "n_workers": len(per_pid),
            "sum_worker_peak_bytes": sum(per_pid.values()),
        },
    }
    out_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runner.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sweep_p = sub.add_parser("sweep")
    sweep_p.add_argument("--job", required=True)
    sweep_p.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if args.cmd == "check":
        print(json.dumps(_check(), sort_keys=True))
        return 0
    return _sweep(Path(args.job), Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
