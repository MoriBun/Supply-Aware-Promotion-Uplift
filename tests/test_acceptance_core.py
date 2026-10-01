"""docs/tests.md §3 and §4, core acceptance: A1 (throughput curve), A5 (run time), CAL (calibration targets).

All tests here are slow: run them with ``pytest -q -m slow tests/test_acceptance_core.py``.
The measuring functions are importable so the calibration (milestone P3) reports the same numbers.
"""

import dataclasses
import statistics

import numpy as np
import pytest

from sim.config import load_config
from sim.runner import DEFAULT_ENGINE, Job, budget_for, execute_job, run_jobs, throughput_curve_table, throughput_jobs, with_policy
from sim.state import OrderStatus
from tests.conftest import ROOT

DEFAULT = ROOT / "config" / "default.yaml"
pytestmark = pytest.mark.slow


# --- A5: run time ----------------------------------------------------------------


def measure_runtime(cfg, policy: str, n_runs: int = 3) -> list[float]:
    """Engine run time (seconds) of one evaluate job, ``n_runs`` times, one process (docs/tests.md A5)."""
    cfg = with_policy(cfg, policy)
    budget = budget_for(cfg)
    job = Job(cfg=cfg, seed=cfg.meta.run_seed, budget_usd=budget, enforce_budget=cfg.budget.enforce)
    return [execute_job(DEFAULT_ENGINE, job).runtime_s for _ in range(n_runs)]


def test_a5_one_simulated_day_within_the_time_limit():
    # S3 measures all_on (docs/phan_cong.md, H3.1); the default policy is measured again in S4 (H4.1).
    cfg = load_config(DEFAULT)
    times = measure_runtime(cfg, "all_on")
    assert statistics.median(times) <= cfg.performance.max_seconds_per_sim_day, times


# --- CAL: calibration targets (docs/tests.md §4) ---------------------------------


def calibration_metrics(cfg, n_seeds: int = 5) -> dict[str, float]:
    """The five CAL quantities of docs/tests.md §4, pooled over ``n_seeds`` seeds of all_off.

    - A session is "in surplus" when the slack its cell had in the **previous** slot is above 1
      (``slack_lag_slot``, what a policy can see). The slack of the session's own slot is an
      outcome of that slot's bookings and must not be conditioned on (decisions H-15).
    - P(request) without voucher: requested / sessions over the surplus sessions.
    - Request uplift: ``mean(p_request_treat) / mean(p_request_control) - 1`` over the same
      sessions. Both probabilities are evaluated in the same context (same fare, same quoted
      ETA), so the figure is free of the congestion a real all_on run adds (decisions H-16).
    - Mean gross fare: completed in-window orders.
    - Shares of (cell, slot) in the window with slack < 0.35 and > 1 (their own slot).
    """
    seeds = [cfg.meta.run_seed + i for i in range(n_seeds)]
    jobs = [Job(cfg=with_policy(cfg, "all_off"), seed=s, enforce_budget=False, log_level="full") for s in seeds]
    requested = sessions = 0
    p_treat = p_control = 0.0
    n_slack = n_tight = n_surplus = 0
    fare_sum, fare_n = 0.0, 0
    for res in run_jobs(jobs, n_procs=cfg.runner.n_procs):
        first_slot = int(res.snapshots[0]["slot"][0])
        slack = np.stack([rec["slack"] for rec in res.snapshots])              # [slot - first_slot, cell]
        lag = np.stack([rec["slack_lag_slot"] for rec in res.snapshots])
        s = res.sessions
        in_w = s.col("in_window")
        surplus = lag[s.col("slot")[in_w] - first_slot, s.col("pu_cell")[in_w]] > 1.0     # NaN counts as not surplus
        requested += int(s.col("requested")[in_w][surplus].sum())
        sessions += int(surplus.sum())
        p_treat += float(s.col("p_request_treat")[in_w][surplus].astype(np.float64).sum())
        p_control += float(s.col("p_request_control")[in_w][surplus].astype(np.float64).sum())
        window_slots = np.unique(s.col("slot")[in_w])
        table = slack[window_slots - first_slot]
        n_slack += table.size
        n_tight += int((table < 0.35).sum())
        n_surplus += int((table > 1.0).sum())
        o = res.orders
        done = o.col("in_window") & (o.col("status") == int(OrderStatus.COMPLETED))
        fare_sum += float(o.col("gross_fare_usd")[done].sum())
        fare_n += int(done.sum())
    return {
        "p_request_no_voucher": requested / sessions,
        "request_uplift_surplus": p_treat / p_control - 1.0,
        "mean_gross_fare_usd": fare_sum / fare_n,
        "share_cellslots_slack_below_0_35": n_tight / n_slack,
        "share_cellslots_slack_above_1": n_surplus / n_slack,
    }


def test_cal_every_target_is_in_range():
    cfg = load_config(DEFAULT)
    metrics = calibration_metrics(cfg)
    targets = dataclasses.asdict(cfg.calibration_targets)
    assert set(metrics) == set(targets)
    out_of_range = {k: (round(v, 4), targets[k]) for k, v in metrics.items() if not targets[k][0] <= v <= targets[k][1]}
    assert not out_of_range, out_of_range


# --- A1: throughput curve (docs/tests.md §3) -------------------------------------


def throughput_summary(cfg) -> dict[str, np.ndarray]:
    """Mean over seeds of the throughput_curve mode (T-08), by ascending demand_scale."""
    jobs = throughput_jobs(cfg)
    table = throughput_curve_table(jobs, run_jobs(jobs, n_procs=cfg.runner.n_procs))
    mean = table.groupby("demand_scale")[["completed_per_h", "mean_slack", "mean_pickup_eta_min"]].mean().sort_index()
    return {"demand_scale": mean.index.to_numpy(), **{c: mean[c].to_numpy() for c in mean.columns}}


def a1_checks(summary: dict[str, np.ndarray]) -> dict[str, bool]:
    done, slack, eta = summary["completed_per_h"], summary["mean_slack"], summary["mean_pickup_eta_min"]
    peak = int(np.argmax(done))
    steps = np.diff(eta)
    return {
        "1_rises_to_a_peak": 0 < peak < len(done) - 1 and bool((np.diff(done[: peak + 1]) > 0).all()),
        "2_falls_to_95pct_of_peak": bool(done[-1] <= 0.95 * done[peak]),
        "3_slack_below_0_45_where_falling": bool((slack[peak + 1:] < 0.45).all()),
        "4_eta_monotone_no_jump_over_3_min": bool((steps > 0).all() and steps.max() <= 3.0),
    }


def test_a1_throughput_curve():
    cfg = load_config(DEFAULT)
    summary = throughput_summary(cfg)
    checks = a1_checks(summary)
    assert all(checks.values()), (checks, {k: np.round(v, 3).tolist() for k, v in summary.items()})
