"""Command line: ``python -m sim run --mode <mode> --config <yaml> [--set a.b=c ...]`` (spec §7)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from sim.config import ConfigError, config_hash, load_config

MODES = ("generate", "evaluate", "sweep_theta", "gte", "calibrate_budget", "throughput_curve")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m sim", description="Ride-hailing simulator (docs/spec.md).")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run one of the modes of spec §7")
    run.add_argument("--mode", required=True, choices=MODES)
    run.add_argument("--config", action="append", required=True, metavar="YAML",
                     help="config file; repeat to layer files (later files override earlier ones)")
    run.add_argument("--set", dest="overrides", action="append", default=[], metavar="KEY=VALUE",
                     help="override one key, value parsed as YAML (e.g. policy.threshold.theta=0.4)")
    run.add_argument("--out", type=Path, default=None, help="output directory, e.g. runs/<name>")
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

    print(f"mode={args.mode} policy={cfg.policy.name} config_hash={config_hash(cfg)}")
    # P0: the command only validates the config; modes are implemented from P2 on (docs/plan.md).
    print(f"mode '{args.mode}' is not implemented yet (milestone P0)", file=sys.stderr)
    return 0
