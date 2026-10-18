"""M5 whole-brain condition runner (MIT, this project's code).

Drives Shiu's vendored model.run_trial once per trial with an explicit brian2.seed(seed).
default_params are unchanged except r_poi, which is set from the job.
Must run on Python 3.10 and 3.14.
"""

import argparse
import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, cast

import brian2
import joblib
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
_base: Any = importlib.import_module("runner")


def _counts_trial(
    seed: int,
    exc: list[int],
    comp: str,
    conn: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    model = _base._load_model()
    brian2.seed(seed)
    t = time.perf_counter()
    spk = model.run_trial(exc, [], [], Path(comp), Path(conn), params)
    wall = time.perf_counter() - t
    return {
        "seed": seed,
        "counts": sorted((int(k), len(v)) for k, v in spk.items() if len(v)),
        "wall_s": wall,
        "pid": os.getpid(),
        "maxrss_bytes": _base._maxrss(),
    }


def _condition(job_path: Path, spikes_path: Path, out_path: Path) -> int:
    job = json.loads(job_path.read_text())
    model = _base._load_model()
    comp = job["completeness"]
    conn = job["connectivity"]
    stim_ids = [int(i) for i in job["stim_ids"]]
    r_poi_hz = float(job["r_poi_hz"])
    n_trials = int(job["n_trials"])
    seed_base = int(job["seed_base"])
    n_proc = int(job["n_proc"])
    label = job["label"]

    flyid2i = {int(fid): i for i, fid in enumerate(pd.read_csv(comp, index_col=0).index)}
    i2flyid = {i: fid for fid, i in flyid2i.items()}
    missing = sorted({i for i in stim_ids if i not in flyid2i})
    if missing:
        print(f"error: ids not in completeness: {missing}", file=sys.stderr)
        return 3

    exc = [flyid2i[i] for i in stim_ids]

    env = _base._check()
    params = dict(model.default_params)
    params["r_poi"] = r_poi_hz * brian2.Hz
    t_run_s = float(model.default_params["t_run"] / brian2.second)
    seeds = [seed_base + t for t in range(n_trials)]

    total_t0 = time.perf_counter()
    out = cast(
        list[dict[str, Any]],
        joblib.Parallel(n_jobs=n_proc, backend="loky")(
            joblib.delayed(_counts_trial)(s, exc, comp, conn, params) for s in seeds
        ),
    )
    total_wall = time.perf_counter() - total_t0

    rows: list[tuple[int, int, int]] = []
    for t, r in enumerate(out):
        for idx, n in r["counts"]:
            rows.append((t, i2flyid[idx], n))
    rows.sort(key=lambda row: (row[0], row[1]))

    data = b"trial\troot_id\tn_spikes\n" + "".join(
        f"{t}\t{rid}\t{n}\n" for t, rid, n in rows
    ).encode("ascii")
    spikes_path.write_bytes(data)

    per_pid: dict[int, int] = {}
    for r in out:
        pid = int(r["pid"])
        per_pid[pid] = max(per_pid.get(pid, 0), int(r["maxrss_bytes"]))

    result = {
        "schema": 1,
        "label": label,
        "job": job,
        "env": env,
        "host": _base._host(),
        "t_run_s": t_run_s,
        "seeds": seeds,
        "params": {k: str(v) for k, v in sorted(params.items())},
        "spikes": {
            "file": spikes_path.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "n_rows": len(rows),
        },
        "trial_wall_s": [r["wall_s"] for r in out],
        "total_wall_s": total_wall,
        "peak_rss": {
            "parent_bytes": _base._maxrss(),
            "max_worker_bytes": max(per_pid.values()) if per_pid else 0,
            "n_workers": len(per_pid),
            "sum_worker_peak_bytes": sum(per_pid.values()),
        },
    }
    out_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="condition_runner.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    cond_p = sub.add_parser("condition")
    cond_p.add_argument("--job", required=True)
    cond_p.add_argument("--spikes", required=True)
    cond_p.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if args.cmd == "check":
        print(json.dumps(_base._check(), sort_keys=True))
        return 0
    return _condition(Path(args.job), Path(args.spikes), Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
