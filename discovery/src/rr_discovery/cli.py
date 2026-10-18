import argparse
import dataclasses
import sys
from collections.abc import Sequence
from pathlib import Path

from rr_discovery import data
from rr_discovery.config import ConfigError, load_config, require_model_input, with_data_dir
from rr_discovery.data import IntegrityError

DEFAULT_CONFIG = Path("discovery/discovery.toml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rr-discover",
        description="Offline FlyWire v783 discovery toolchain.",
    )
    sub = parser.add_subparsers(dest="stage", required=True)

    fetch_p = sub.add_parser("fetch", help="download v783 data and annotation table; verify sha256")
    fetch_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    fetch_p.add_argument("--data-dir", type=Path)
    fetch_p.add_argument(
        "--record-hashes",
        action="store_true",
        help="pin sha256 of files that have no recorded hash (trust on first use)",
    )

    inspect_p = sub.add_parser("inspect", help="inspect schema and write reports/schema_report.md")
    inspect_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    inspect_p.add_argument("--data-dir", type=Path)
    inspect_p.add_argument("--reports-dir", type=Path)

    shiu_p = sub.add_parser(
        "shiu-fetch",
        help="download pinned Shiu model files and v630/v783 reference inputs; verify sha256",
    )
    shiu_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    shiu_p.add_argument(
        "--record-hashes",
        action="store_true",
        help="pin sha256 of files that have no recorded hash (trust on first use)",
    )

    model_p = sub.add_parser(
        "model-input",
        help="build Shiu-format completeness/connectivity tables and per-target input totals",
    )
    model_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    model_p.add_argument("--data-dir", type=Path)
    model_p.add_argument("--out-dir", type=Path)

    regress_p = sub.add_parser(
        "regress",
        help="run the sugar-GRN→MN9 sweep and check it against the golden (long run)",
    )
    regress_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    mode_group = regress_p.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--capture-golden",
        action="store_true",
        help="run the sweep under --python and write the golden file",
    )
    mode_group.add_argument(
        "--smoke",
        action="store_true",
        help="one trial at 100 Hz to measure wall time and peak RSS",
    )
    regress_p.add_argument("--python", type=Path, help="fallback env python for --capture-golden")
    regress_p.add_argument("--force", action="store_true", help="allow overwriting the golden")

    discover_p = sub.add_parser(
        "discover", help="M5: LC4/LPLC2 whole-brain run (long) and circuit export"
    )
    discover_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    discover_p.add_argument("--step", choices=["all", "run", "post"], default="all")
    discover_p.add_argument("--python", type=Path)
    discover_p.add_argument("--n-proc", type=int)

    robust_p = sub.add_parser(
        "robustness",
        help="M6: robustness grid and negative controls (run step is long)",
    )
    robust_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    robust_p.add_argument(
        "--step", choices=["all", "prepare", "run", "extract", "report"], default="all"
    )
    robust_p.add_argument("--python", type=Path)
    robust_p.add_argument("--n-proc", type=int)
    robust_p.add_argument("--time-cap-s", type=float)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config)
        data_dir = getattr(args, "data_dir", None)
        if data_dir is not None:
            cfg = with_data_dir(cfg, data_dir)

        if args.stage == "fetch":
            data.fetch(cfg, record_hashes=args.record_hashes)
            return 0

        if args.stage == "shiu-fetch":
            from rr_discovery import vendor

            vendor.fetch_shiu(cfg, record_hashes=args.record_hashes)
            return 0

        if args.stage == "model-input":
            from rr_discovery import model_input

            raw = data.paths_from_config(cfg).connections
            if not raw.exists():
                print(
                    f"error: {raw} not found; run 'rr-discover fetch' first",
                    file=sys.stderr,
                )
                return 1
            out_dir = args.out_dir if args.out_dir is not None else require_model_input(cfg).out_dir
            built, stats = model_input.build(raw, out_dir, version=cfg.version)
            for path in (built.completeness, built.connectivity, built.input_totals, built.meta):
                print(path)
            print(stats)
            return 0

        if args.stage == "regress":
            from rr_discovery import regress

            mode: regress.Mode = "regress"
            if args.capture_golden:
                mode = "capture"
            elif args.smoke:
                mode = "smoke"
            return regress.execute(cfg, mode=mode, python=args.python, force=args.force)

        if args.stage == "discover":
            from rr_discovery import connfilter, export, identify, pipeline, run, sanity

            try:
                if args.step in ("all", "run"):
                    run.run_stage(cfg, python=args.python, n_proc=args.n_proc)
                if args.step in ("all", "post"):
                    return pipeline.post_stage(cfg)
                return 0
            except (
                run.RunError,
                connfilter.ConnFilterError,
                identify.IdentifyError,
                export.ExportError,
                sanity.SanityError,
            ) as err:
                print(f"error: {err}", file=sys.stderr)
                return 1

        if args.stage == "robustness":
            from rr_discovery import connfilter, controls, export, identify, robustness, run

            try:
                if args.step in ("all", "prepare"):
                    plan_path = robustness.prepare_stage(cfg)
                    if args.step == "prepare":
                        print(plan_path)
                        return 0
                if args.step in ("all", "run"):
                    summary = robustness.run_stage(
                        cfg,
                        python=args.python,
                        n_proc=args.n_proc,
                        time_cap_s=args.time_cap_s,
                    )
                    print(summary)
                if args.step in ("all", "extract"):
                    print(robustness.extract_stage(cfg))
                if args.step in ("all", "report"):
                    report_path, results_path = robustness.report_stage(cfg)
                    print(report_path)
                    print(results_path)
                return 0
            except (
                robustness.RobustnessError,
                controls.ControlsError,
                run.RunError,
                connfilter.ConnFilterError,
                identify.IdentifyError,
                export.ExportError,
            ) as err:
                print(f"error: {err}", file=sys.stderr)
                return 1

        if args.reports_dir is not None:
            cfg = dataclasses.replace(cfg, reports_dir=args.reports_dir)
        paths = data.paths_from_config(cfg)
        for required in (paths.connections, paths.root_ids, paths.annotations):
            if not required.exists():
                print(
                    f"error: {required} not found; run 'rr-discover fetch' first",
                    file=sys.stderr,
                )
                return 1

        from rr_discovery import schema

        report = schema.inspect(paths, cfg)
        out = schema.write_report(report, cfg.reports_dir, cfg)
        print(out)
        return 0 if report.ok else 1
    except ConfigError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    except IntegrityError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
