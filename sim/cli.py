"""Command line: ``python -m sim run --mode <mode> --config <yaml> [--set a.b=c ...] [--out DIR]`` (spec §7)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from sim import runner
from sim.config import ConfigError, config_hash, load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m sim", description="Ride-hailing simulator (docs/spec.md).")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run one of the modes of spec §7")
    run.add_argument("--mode", required=True, choices=runner.MODES)
    run.add_argument("--config", action="append", required=True, metavar="YAML",
                     help="config file; repeat to layer files (later files override earlier ones)")
    run.add_argument("--set", dest="overrides", action="append", default=[], metavar="KEY=VALUE",
                     help="override one key, value parsed as YAML (e.g. policy.threshold.theta=0.4)")
    run.add_argument("--out", type=Path, default=None,
                     help="output directory (default runs/<mode>-<config_hash>)")
    run.add_argument("--log-level", choices=("minimal", "full"), default="minimal",
                     help="full also writes session and order tables in evaluate/sweep_theta/gte")
    run.add_argument("--profile", action="store_true", help="print time spent per engine step")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config, args.overrides)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    digest = config_hash(cfg)
    print(f"mode={args.mode} policy={cfg.policy.name} config_hash={digest}")
    out_dir = args.out if args.out is not None else Path("runs") / f"{args.mode}-{digest}"
    try:
        table = runner.run_mode(args.mode, cfg, out_dir, log_level=args.log_level, profile=args.profile)
    except NotImplementedError as exc:
        print(f"mode '{args.mode}' is not implemented yet ({exc})", file=sys.stderr)
        return 1

    print(f"out={out_dir}")
    if args.mode == "throughput_curve":
        with pd.option_context("display.width", 160, "display.max_columns", 20, "display.precision", 3):
            print(runner.summarize_throughput(table).to_string(index=False))
    return 0
