"""M13 Runner: run ids, many seeds in parallel, results tables, run modes (spec §7).

Milestone: P2 (``throughput_curve``, task T1.4); ``evaluate``, ``gte``,
``sweep_theta``, ``calibrate_budget`` and ``generate`` are task T2.4.

Seeds run in separate processes started with ``spawn`` (the only start method on
Windows), so a job carries picklable data only: the ``Config`` and scalars. The
worker rebuilds the world from ``world_seed``, builds the policy from
``cfg.policy.name`` and imports the engine from its ``"module:function"`` string
(``tests.fakes:fake_run`` in tests). Results come back in job order.
"""

from __future__ import annotations

import dataclasses
import math
import multiprocessing
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from sim.config import Config, config_hash
from sim.engine import RunResult
from sim.logger import write_results
from sim.policies import make_policy
from sim.policies.scores import import_callable
from sim.population import build_world
from sim.rng import Rng

NAN = float("nan")
DEFAULT_ENGINE = "sim.engine:run"
MODES = ("generate", "evaluate", "sweep_theta", "gte", "calibrate_budget", "throughput_curve")
IMPLEMENTED_MODES = ("throughput_curve",)


@dataclass(frozen=True)
class Job:
    """One engine run. ``cfg.meta.run_seed`` is replaced by ``seed`` in the worker."""

    cfg: Config
    seed: int
    theta: float = NAN
    budget_usd: float | None = None
    enforce_budget: bool | None = None
    log_level: str = "minimal"
    profile: bool = False

    @property
    def policy_name(self) -> str:
        return self.cfg.policy.name


def run_id(mode: str, cfg: Config, policy: str, theta: float, seed: int) -> str:
    """``<mode>-<config_hash>-<policy>-<theta>-<seed>`` (docs/schema.md, meta/run_metadata)."""
    theta_text = "nan" if theta is None or math.isnan(theta) else f"{theta:g}"
    return f"{mode}-{config_hash(cfg)}-{policy}-{theta_text}-{int(seed)}"


def seeds_for(cfg: Config, n_seeds: int) -> list[int]:
    """``run_seed, run_seed + 1, ...`` (config/default.yaml: the runner adds the seed index)."""
    if n_seeds < 1:
        raise ValueError("n_seeds must be >= 1")
    return [cfg.meta.run_seed + i for i in range(int(n_seeds))]


def with_seed(cfg: Config, seed: int) -> Config:
    return dataclasses.replace(cfg, meta=dataclasses.replace(cfg.meta, run_seed=int(seed)))


def execute_job(engine_spec: str, job: Job) -> RunResult:
    """Run one job in the current process (also the worker body of the pool)."""
    engine = import_callable(engine_spec)
    cfg = with_seed(job.cfg, job.seed)
    rng = Rng.from_config(cfg)
    world = build_world(cfg, rng)
    policy = make_policy(cfg, world)
    return engine(cfg, world, policy, rng, log_level=job.log_level, profile=job.profile,
                  budget_usd=job.budget_usd, enforce_budget=job.enforce_budget)


def run_jobs(jobs: list[Job], *, engine: str = DEFAULT_ENGINE, n_procs: int | None = None) -> list[RunResult]:
    """Run jobs, ``n_procs`` at a time (None = ``runner.n_procs`` of the first job's config, then CPU count)."""
    if not jobs:
        return []
    if n_procs is None:
        n_procs = jobs[0].cfg.runner.n_procs
    if n_procs is None:
        n_procs = os.cpu_count() or 1
    n_procs = max(1, min(int(n_procs), len(jobs)))
    import_callable(engine)  # fail fast in the parent on a bad engine spec
    if n_procs == 1:
        return [execute_job(engine, job) for job in jobs]
    with multiprocessing.get_context("spawn").Pool(n_procs) as pool:
        return pool.starmap(execute_job, [(engine, job) for job in jobs])


# ---------------------------------------------------------------------------
# Results tables (docs/schema.md, results/)
# ---------------------------------------------------------------------------


def policy_results_table(mode: str, jobs: list[Job], results: list[RunResult]) -> pd.DataFrame:
    rows = []
    for job, res in zip(jobs, results, strict=True):
        rows.append({
            "run_id": run_id(mode, job.cfg, res.policy, job.theta, job.seed),
            "policy": res.policy, "theta": job.theta, "seed": job.seed,
            "N_completed": res.N_completed, "V_profit_usd": res.V_profit_usd,
            "voucher_spent_usd": res.voucher_spent_usd, "budget_B_usd": res.budget_B_usd,
            "n_sessions": res.n_sessions, "n_requests": res.n_requests,
            "n_abandoned": res.n_abandoned, "n_cancelled": res.n_cancelled,
            "mean_pickup_eta_min": res.mean_pickup_eta_min, "share_cells_off": res.share_cells_off,
            "n_switches_per_cell_day": res.n_switches_per_cell_day, "runtime_s": res.runtime_s,
        })
    return pd.DataFrame(rows)


def throughput_curve_table(jobs: list[Job], results: list[RunResult]) -> pd.DataFrame:
    rows = []
    for job, res in zip(jobs, results, strict=True):
        rows.append({
            "run_id": run_id("throughput_curve", job.cfg, res.policy, job.theta, job.seed),
            "demand_scale": job.cfg.demand.demand_scale, "fleet_size": job.cfg.supply.fleet_size, "seed": job.seed,
            "completed_per_h": res.completed_per_h, "requests_per_h": res.requests_per_h,
            "mean_pickup_eta_min": res.mean_pickup_eta_min, "mean_slack": res.mean_slack,
            "abandon_rate": res.abandon_rate, "cancel_rate": res.cancel_rate,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Mode: throughput_curve (test A1; decisions T-08, T-15)
# ---------------------------------------------------------------------------


def throughput_config(cfg: Config, demand_scale: float) -> Config:
    """all_off, every driver online all run, hour profile and speed frozen at ``throughput.reference_hour``."""
    h = cfg.throughput.reference_hour
    return dataclasses.replace(
        cfg,
        demand=dataclasses.replace(cfg.demand, demand_scale=float(demand_scale),
                                   hour_profile=(cfg.demand.hour_profile[h],) * 24),
        space=dataclasses.replace(cfg.space, speed_factor_by_hour=(cfg.space.speed_factor_by_hour[h],) * 24),
        supply=dataclasses.replace(cfg.supply, shift_mode="always_on"),
        policy=dataclasses.replace(cfg.policy, name="all_off"),
    )


def throughput_jobs(cfg: Config, *, profile: bool = False) -> list[Job]:
    """``throughput.demand_scale_grid`` x ``throughput.n_seeds``, no budget."""
    return [
        Job(cfg=throughput_config(cfg, ds), seed=seed, enforce_budget=False, profile=profile)
        for ds in cfg.throughput.demand_scale_grid
        for seed in seeds_for(cfg, cfg.throughput.n_seeds)
    ]


def run_throughput_curve(cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE,
                         n_procs: int | None = None, profile: bool = False) -> pd.DataFrame:
    """Run the grid and write ``results/throughput_curve.parquet``; returns the table."""
    jobs = throughput_jobs(cfg, profile=profile)
    results = run_jobs(jobs, engine=engine, n_procs=n_procs)
    table = throughput_curve_table(jobs, results)
    write_results(out_dir, "throughput_curve", table)
    return table


def summarize_throughput(table: pd.DataFrame) -> pd.DataFrame:
    """Mean over seeds per demand level, for the console and the P2 gate plot."""
    cols = ["completed_per_h", "requests_per_h", "mean_pickup_eta_min", "mean_slack", "abandon_rate", "cancel_rate"]
    return table.groupby("demand_scale", as_index=False)[cols].mean()


def run_mode(mode: str, cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE, log_level: str = "minimal",
             profile: bool = False) -> pd.DataFrame:
    """Dispatch a mode of spec §7."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    if mode == "throughput_curve":
        return run_throughput_curve(cfg, out_dir, engine=engine, profile=profile)
    raise NotImplementedError(f"mode {mode!r}: task T2.4")
