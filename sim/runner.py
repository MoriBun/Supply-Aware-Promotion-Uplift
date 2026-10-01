"""M13 Runner: run ids, many seeds in parallel, results tables, run modes (spec §7).

Milestone: P2 (``throughput_curve``, task T1.4); P6 (``evaluate``, ``gte``,
``sweep_theta``, ``calibrate_budget``, ``generate``, task T2.4).

Seeds run in separate processes started with ``spawn`` (the only start method on
Windows), so a job carries picklable data only: the ``Config`` and scalars. The
worker rebuilds the world from ``world_seed``, builds the policy from
``cfg.policy.name`` (with the job's theta / kappa) and imports the engine from
its ``"module:function"`` string (``tests.fakes:fake_run`` in tests). Results come
back in job order.

Budget B (USD per budget period) comes from :func:`calibrate_budget`: an all_on
pilot without budget on seed ``run_seed + pilot_seed_offset`` (spec §4.3), unless
``budget.mode = fixed``. kappa-auto runs one threshold pilot per theta with
``kappa = -inf`` and no budget (seed offset + theta index) and keeps the smallest
score whose cumulative expected spend fits ``B x n_periods`` (spec §6, T-23).
"""

from __future__ import annotations

import dataclasses
import math
import multiprocessing
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from sim.budget import resolve_budget_usd
from sim.config import Config, config_hash, to_dict
from sim.engine import RunResult
from sim.logger import git_sha, write_metadata, write_results
from sim.policies import make_policy
from sim.policies.scores import import_callable
from sim.population import build_world
from sim.rng import Rng
from sim.state import Clock

NAN = float("nan")
DEFAULT_ENGINE = "sim.engine:run"
MODES = ("generate", "evaluate", "sweep_theta", "gte", "calibrate_budget", "throughput_curve")


@dataclass(frozen=True)
class Job:
    """One engine run. ``cfg.meta.run_seed`` is replaced by ``seed`` in the worker."""

    cfg: Config
    seed: int
    theta: float = NAN                 # ThresholdPolicy theta; NaN = not applicable / config value
    kappa: float | None = None         # ThresholdPolicy kappa; None = config value (-inf when "auto")
    budget_usd: float | None = None
    enforce_budget: bool | None = None
    log_level: str = "minimal"
    profile: bool = False

    @property
    def policy_name(self) -> str:
        return self.cfg.policy.name


# ---------------------------------------------------------------------------
# Ids, seeds, config helpers
# ---------------------------------------------------------------------------


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


def with_policy(cfg: Config, name: str) -> Config:
    return dataclasses.replace(cfg, policy=dataclasses.replace(cfg.policy, name=name))


def pilot_seed(cfg: Config, index: int = 0) -> int:
    """Seed of a pilot run: ``run_seed + budget.pilot_seed_offset (+ theta index)`` (spec §4.3, §6)."""
    return cfg.meta.run_seed + cfg.budget.pilot_seed_offset + int(index)


# ---------------------------------------------------------------------------
# Running jobs
# ---------------------------------------------------------------------------


def execute_job(engine_spec: str, job: Job) -> RunResult:
    """Run one job in the current process (also the worker body of the pool)."""
    engine = import_callable(engine_spec)
    cfg = with_seed(job.cfg, job.seed)
    rng = Rng.from_config(cfg)
    world = build_world(cfg, rng)
    theta = None if math.isnan(job.theta) else float(job.theta)
    policy = make_policy(cfg, world, rng=rng, theta=theta, kappa=job.kappa)
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
# Tables (docs/schema.md: results/, meta/)
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


def theta_sweep_table(results: pd.DataFrame) -> pd.DataFrame:
    """Aggregate of policy_results over seeds per theta (docs/schema.md results/theta_sweep)."""
    g = results.groupby("theta", sort=True)
    n = g.size()
    root_n = np.sqrt(n.to_numpy(dtype=float))
    out = pd.DataFrame({
        "theta": n.index.to_numpy(dtype=float),
        "N_mean": g["N_completed"].mean().to_numpy(dtype=float),
        "N_se": g["N_completed"].std(ddof=1).to_numpy(dtype=float) / root_n,
        "V_mean": g["V_profit_usd"].mean().to_numpy(dtype=float),
        "V_se": g["V_profit_usd"].std(ddof=1).to_numpy(dtype=float) / root_n,
        "spent_mean": g["voucher_spent_usd"].mean().to_numpy(dtype=float),
        "n_seeds": n.to_numpy(),
    })
    is_argmax = np.zeros(len(out), dtype=bool)
    if len(out):
        is_argmax[int(out["N_mean"].to_numpy().argmax())] = True   # ties: the smallest theta
    out["is_argmax"] = is_argmax
    return out


def metadata_table(mode: str, jobs: list[Job], results: list[RunResult], *,
                   budget_B_usd: float | None = None) -> pd.DataFrame:
    """One meta/run_metadata row per run. ``budget_B_usd`` overrides the engine's value (pilot runs)."""
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sha = git_sha()
    rows = []
    for job, res in zip(jobs, results, strict=True):
        rows.append({
            "run_id": run_id(mode, job.cfg, res.policy, job.theta, job.seed), "mode": mode,
            "config_hash": config_hash(job.cfg),
            "config_yaml": yaml.safe_dump(to_dict(with_seed(job.cfg, job.seed)), sort_keys=True),
            "git_sha": sha, "policy": res.policy, "theta": job.theta, "seed": job.seed,
            "world_seed": job.cfg.meta.world_seed,
            "budget_B_usd": res.budget_B_usd if budget_B_usd is None else budget_B_usd,
            "kappa": NAN if job.kappa is None else float(job.kappa),
            "window_start_s": res.window_start_s, "window_end_s": res.window_end_s, "sim_end_s": res.sim_end_s,
            "n_truncated_orders": res.n_truncated_orders, "runtime_s": res.runtime_s, "created_at": created,
        })
    return pd.DataFrame(rows)


def _finish(mode: str, out_dir: Path, jobs: list[Job], results: list[RunResult]) -> pd.DataFrame:
    table = policy_results_table(mode, jobs, results)
    write_results(out_dir, "policy_results", table)
    write_metadata(out_dir, metadata_table(mode, jobs, results))
    return table


# ---------------------------------------------------------------------------
# Budget B and kappa (spec §4.3, §6; decisions D12, T-03, T-23)
# ---------------------------------------------------------------------------


def calibrate_budget(cfg: Config, *, engine: str = DEFAULT_ENGINE) -> tuple[float, RunResult | None]:
    """B in USD per budget period: ``budget.fixed_usd``, or ``fraction`` x mean spend per period of an all_on pilot."""
    if cfg.budget.mode == "fixed":
        return resolve_budget_usd(cfg), None
    job = Job(cfg=with_policy(cfg, "all_on"), seed=pilot_seed(cfg), enforce_budget=False)
    pilot = run_jobs([job], engine=engine, n_procs=1)[0]
    return resolve_budget_usd(cfg, pilot.spent_by_period_usd), pilot


def budget_for(cfg: Config, *, engine: str = DEFAULT_ENGINE) -> float | None:
    """B when ``budget.enforce`` is on, else None."""
    return calibrate_budget(cfg, engine=engine)[0] if cfg.budget.enforce else None


def kappa_from_pilot(score, voucher_usd, completed, budget_total_usd: float) -> float:
    """Smallest score kept so that the expected spend of the kept sessions fits the budget (spec §6, step 3).

    Expected spend of an offered session is its voucher when the order completed, 0
    otherwise. Sessions are taken from the highest score down; sessions without a
    finite score are never kept. ``+inf`` when not even the first fits, ``-inf``
    when every session fits.
    """
    score = np.asarray(score, dtype=np.float64)
    spend = np.where(np.asarray(completed, dtype=bool), np.asarray(voucher_usd, dtype=np.float64), 0.0)
    keep = np.isfinite(score)
    score, spend = score[keep], spend[keep]
    if len(score) == 0:
        return -math.inf
    order = np.argsort(-score, kind="stable")
    cum = np.cumsum(spend[order])
    k = int(np.searchsorted(cum, float(budget_total_usd), side="right"))   # top-k sessions that fit
    if k == 0:
        return math.inf
    if k >= len(score):
        return -math.inf
    return float(score[order][k - 1])


def kappa_auto(cfg: Config, theta: float, theta_index: int, budget_usd: float, *,
               engine: str = DEFAULT_ENGINE) -> float:
    """One threshold pilot with ``kappa = -inf`` and no budget, then :func:`kappa_from_pilot` on ``B x n_periods``."""
    job = Job(cfg=with_policy(cfg, "threshold"), seed=pilot_seed(cfg, theta_index), theta=float(theta),
              kappa=-math.inf, enforce_budget=False)
    pilot = run_jobs([job], engine=engine, n_procs=1)[0]
    n_periods = Clock.from_config(cfg).n_periods
    return kappa_from_pilot(pilot.offer_score, pilot.offer_voucher_usd, pilot.offer_completed,
                            float(budget_usd) * n_periods)


def resolve_kappa(cfg: Config, theta: float, theta_index: int, budget_usd: float | None, *,
                  engine: str = DEFAULT_ENGINE) -> float | None:
    """kappa for a threshold run: the config value, or kappa-auto; None for other policies."""
    if cfg.policy.name != "threshold":
        return None
    k = cfg.policy.threshold.kappa
    if k != "auto":
        return float(k)
    if budget_usd is None:
        return -math.inf                      # nothing to ration without a budget (T-23)
    return kappa_auto(cfg, theta, theta_index, budget_usd, engine=engine)


# ---------------------------------------------------------------------------
# Modes (spec §7)
# ---------------------------------------------------------------------------


def evaluate(cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE, log_level: str = "minimal",
             profile: bool = False) -> pd.DataFrame:
    """``policy.name`` x ``sweep.n_seeds`` (T-22) under B; writes policy_results and run_metadata."""
    budget = budget_for(cfg, engine=engine)
    theta = float(cfg.policy.threshold.theta) if cfg.policy.name == "threshold" else NAN
    kappa = resolve_kappa(cfg, theta, 0, budget, engine=engine)
    jobs = [Job(cfg=cfg, seed=s, theta=theta, kappa=kappa, budget_usd=budget, enforce_budget=cfg.budget.enforce,
                log_level=log_level, profile=profile) for s in seeds_for(cfg, cfg.sweep.n_seeds)]
    return _finish("evaluate", out_dir, jobs, run_jobs(jobs, engine=engine))


def gte(cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE, log_level: str = "minimal",
        profile: bool = False) -> pd.DataFrame:
    """all_on and all_off x ``gte.n_seeds``, no budget (D10)."""
    jobs = [Job(cfg=with_policy(cfg, name), seed=s, enforce_budget=False, log_level=log_level, profile=profile)
            for name in ("all_on", "all_off") for s in seeds_for(cfg, cfg.gte.n_seeds)]
    return _finish("gte", out_dir, jobs, run_jobs(jobs, engine=engine))


def gte_summary(table: pd.DataFrame) -> dict[str, float]:
    """GTE = mean over seeds of N(all_on) - N(all_off), paired by seed (CRN)."""
    on = table[table["policy"] == "all_on"].set_index("seed")["N_completed"].astype(float)
    off = table[table["policy"] == "all_off"].set_index("seed")["N_completed"].astype(float)
    diff = (on - off).dropna()
    n = int(len(diff))
    return {"N_on": float(on.mean()), "N_off": float(off.mean()), "GTE": float(diff.mean()),
            "GTE_se": float(diff.std(ddof=1) / math.sqrt(n)) if n > 1 else NAN, "n_seeds": n}


def sweep_theta(cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE, log_level: str = "minimal",
                profile: bool = False) -> pd.DataFrame:
    """Threshold policy for every theta of ``sweep.theta_grid`` x ``sweep.n_seeds``, same B; returns theta_sweep."""
    base = with_policy(cfg, "threshold")
    budget = budget_for(base, engine=engine)
    jobs: list[Job] = []
    for i, theta in enumerate(cfg.sweep.theta_grid):
        kappa = resolve_kappa(base, float(theta), i, budget, engine=engine)
        jobs += [Job(cfg=base, seed=s, theta=float(theta), kappa=kappa, budget_usd=budget,
                     enforce_budget=base.budget.enforce, log_level=log_level, profile=profile)
                 for s in seeds_for(base, cfg.sweep.n_seeds)]
    table = _finish("sweep_theta", out_dir, jobs, run_jobs(jobs, engine=engine))
    sweep = theta_sweep_table(table)
    write_results(out_dir, "theta_sweep", sweep)
    return sweep


def generate(cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE, log_level: str = "full",
             profile: bool = False) -> tuple[pd.DataFrame, RunResult]:
    """``generate.days`` continuous days with ``policy.name`` legacy or experiment, one seed, full log.

    The window is ``generate.days`` x 1440 min (``time.window_min`` is ignored). B is
    per budget period, so the all_on pilot runs on the base window. The observed /
    hidden / market tables are written by the logger (task T3.2); this writes
    results/policy_results and meta/run_metadata and returns the engine result.
    """
    if cfg.policy.name not in ("legacy", "experiment"):
        raise ValueError(f"generate needs policy.name legacy or experiment, got {cfg.policy.name!r} (spec §7)")
    enforce = cfg.experiment.budget_enforce if cfg.policy.name == "experiment" else cfg.budget.enforce
    budget = calibrate_budget(cfg, engine=engine)[0] if enforce else None
    gen_cfg = dataclasses.replace(cfg, time=dataclasses.replace(cfg.time, days_per_run=cfg.generate.days,
                                                                window_min=None))
    job = Job(cfg=gen_cfg, seed=cfg.meta.run_seed, budget_usd=budget, enforce_budget=enforce,
              log_level=log_level, profile=profile)
    result = run_jobs([job], engine=engine, n_procs=1)[0]
    return _finish("generate", out_dir, [job], [result]), result


def calibrate_budget_table(cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE) -> pd.DataFrame:
    """Mode ``calibrate_budget``: B and, for a pilot, its run_metadata row carrying B."""
    budget, pilot = calibrate_budget(cfg, engine=engine)
    if pilot is not None:
        job = Job(cfg=with_policy(cfg, "all_on"), seed=pilot_seed(cfg), enforce_budget=False)
        write_metadata(out_dir, metadata_table("calibrate_budget", [job], [pilot], budget_B_usd=budget))
    return pd.DataFrame({"budget_B_usd": [budget], "mode": [cfg.budget.mode], "fraction": [cfg.budget.fraction],
                         "pilot_seed": [-1 if pilot is None else pilot_seed(cfg)],
                         "pilot_spent_usd": [NAN if pilot is None else pilot.voucher_spent_usd]})


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


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def run_mode(mode: str, cfg: Config, out_dir: Path, *, engine: str = DEFAULT_ENGINE, log_level: str = "minimal",
             profile: bool = False) -> pd.DataFrame:
    """Run a mode of spec §7 and return its headline table (also written under ``out_dir``)."""
    out_dir = Path(out_dir)
    if mode == "throughput_curve":
        return run_throughput_curve(cfg, out_dir, engine=engine, profile=profile)
    if mode == "evaluate":
        return evaluate(cfg, out_dir, engine=engine, log_level=log_level, profile=profile)
    if mode == "gte":
        return gte(cfg, out_dir, engine=engine, log_level=log_level, profile=profile)
    if mode == "sweep_theta":
        return sweep_theta(cfg, out_dir, engine=engine, log_level=log_level, profile=profile)
    if mode == "calibrate_budget":
        return calibrate_budget_table(cfg, out_dir, engine=engine)
    if mode == "generate":
        return generate(cfg, out_dir, engine=engine, log_level="full", profile=profile)[0]
    raise ValueError(f"unknown mode {mode!r}")
