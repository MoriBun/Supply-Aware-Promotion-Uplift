"""M13 runner skeleton on the fake engine (docs/phan_cong.md T1.4, B4; spec §7; decisions T-08)."""

import math

import numpy as np
import pandas as pd
import pytest

from sim.config import config_hash, load_config
from sim.logger import RESULTS_TABLES, cast_table, write_results
from sim.runner import (
    Job, policy_results_table, run_id, run_jobs, run_mode, run_throughput_curve, seeds_for, summarize_throughput,
    throughput_config, throughput_jobs, with_seed,
)
from tests.fakes import make_run_result

FAKE = "tests.fakes:fake_run"


@pytest.fixture
def off_cfg(tiny_layers):
    return load_config(tiny_layers, ["policy.name=all_off"])


# --- ids, seeds -------------------------------------------------------------------------


def test_run_id_format(tiny_cfg):
    assert run_id("evaluate", tiny_cfg, "threshold", 0.35, 3) == f"evaluate-{config_hash(tiny_cfg)}-threshold-0.35-3"
    assert run_id("gte", tiny_cfg, "all_on", float("nan"), 0).endswith("-all_on-nan-0")


def test_seeds_and_with_seed(tiny_cfg):
    assert seeds_for(tiny_cfg, 3) == [0, 1, 2]
    with_7 = with_seed(tiny_cfg, 7)
    assert with_7.meta.run_seed == 7 and with_7.meta.world_seed == tiny_cfg.meta.world_seed
    assert tiny_cfg.meta.run_seed == 0                                        # original untouched
    assert config_hash(with_7) != config_hash(tiny_cfg)
    with pytest.raises(ValueError):
        seeds_for(tiny_cfg, 0)


# --- running jobs ------------------------------------------------------------------------


def test_run_jobs_inline_keeps_order_and_is_deterministic(off_cfg):
    jobs = [Job(cfg=off_cfg, seed=s) for s in (2, 0, 1)]
    res = run_jobs(jobs, engine=FAKE, n_procs=1)
    assert [r.profile["run_seed"] for r in res] == [2.0, 0.0, 1.0]
    assert all(r.policy == "all_off" for r in res)
    again = run_jobs(jobs, engine=FAKE, n_procs=1)
    assert [r.N_completed for r in res] == [r.N_completed for r in again]
    assert len({r.N_completed for r in res}) > 1                              # different seeds, different jitter


def test_run_jobs_spawn_pool_matches_inline(off_cfg):
    # Windows starts workers with spawn; the engine spec is a string so the worker can import it.
    jobs = [Job(cfg=off_cfg, seed=s) for s in range(3)]
    inline = run_jobs(jobs, engine=FAKE, n_procs=1)
    pooled = run_jobs(jobs, engine=FAKE, n_procs=2)
    for a, b in zip(inline, pooled, strict=True):
        assert (a.policy, a.N_completed, a.n_requests, a.profile) == (b.policy, b.N_completed, b.n_requests, b.profile)


def test_run_jobs_edge_cases(off_cfg, tiny_cfg):
    assert run_jobs([], engine=FAKE) == []
    with pytest.raises(ValueError):
        run_jobs([Job(cfg=off_cfg, seed=0)], engine="sim.engine:no_such_function")
    with pytest.raises(NotImplementedError):
        run_jobs([Job(cfg=tiny_cfg, seed=0)], engine=FAKE, n_procs=1)         # policy threshold is task T2.3


def test_run_jobs_passes_budget_arguments(tiny_layers):
    cfg_on = load_config(tiny_layers, ["policy.name=all_on"])
    res = run_jobs([Job(cfg=cfg_on, seed=0, budget_usd=12.5, enforce_budget=True)], engine=FAKE, n_procs=1)[0]
    assert res.policy == "all_on" and res.budget_B_usd == 12.5 and res.profile["enforce"] == 1.0
    assert res.voucher_spent_usd <= 12.5 * 1 + 1e-9                           # tiny window: one budget period
    free = run_jobs([Job(cfg=cfg_on, seed=0, enforce_budget=False)], engine=FAKE, n_procs=1)[0]
    assert np.isnan(free.budget_B_usd) and free.voucher_spent_usd >= res.voucher_spent_usd


# --- throughput_curve (decisions T-08) ----------------------------------------------------


def test_throughput_config_transforms(default_yaml):
    cfg = load_config(default_yaml)
    h = cfg.throughput.reference_hour
    t = throughput_config(cfg, 2.5)
    assert t.demand.demand_scale == 2.5 and t.policy.name == "all_off" and t.supply.shift_mode == "always_on"
    assert t.demand.hour_profile == (cfg.demand.hour_profile[h],) * 24
    assert t.space.speed_factor_by_hour == (cfg.space.speed_factor_by_hour[h],) * 24
    assert t.demand.hour_profile[0] == 1.85 and t.space.speed_factor_by_hour[0] == 0.75     # hour 18 in default.yaml
    assert cfg.demand.demand_scale == 1.0 and cfg.policy.name == "threshold"                  # original untouched


def test_throughput_jobs_grid_times_seeds(default_yaml):
    cfg = load_config(default_yaml, ["throughput.n_seeds=2", "throughput.demand_scale_grid=[0.5, 1.0, 2.0]"])
    jobs = throughput_jobs(cfg)
    assert [j.cfg.demand.demand_scale for j in jobs] == [0.5, 0.5, 1.0, 1.0, 2.0, 2.0]
    assert [j.seed for j in jobs] == [0, 1, 0, 1, 0, 1]
    assert all(j.enforce_budget is False and j.budget_usd is None and math.isnan(j.theta) for j in jobs)


def test_fake_engine_receives_the_throughput_config(default_yaml):
    cfg = load_config(default_yaml, ["throughput.n_seeds=1", "throughput.demand_scale_grid=[1.0]"])
    res = run_jobs(throughput_jobs(cfg), engine=FAKE, n_procs=1)[0]
    assert res.profile == {"demand_scale": 1.0, "always_on": 1.0, "hour_profile_const": 1.0, "speed_const": 1.0,
                           "enforce": 0.0, "run_seed": 0.0}
    assert res.policy == "all_off" and np.isnan(res.budget_B_usd)


def test_throughput_curve_end_to_end(default_yaml, tmp_path):
    cfg = load_config(default_yaml, ["throughput.n_seeds=2"])
    table = run_throughput_curve(cfg, tmp_path, engine=FAKE, n_procs=1)
    path = tmp_path / "results" / "throughput_curve.parquet"
    assert path.exists()
    disk = pd.read_parquet(path)
    assert list(disk.columns) == list(RESULTS_TABLES["throughput_curve"])
    assert len(disk) == len(cfg.throughput.demand_scale_grid) * 2 and set(disk["seed"]) == {0, 1}
    assert str(disk["seed"].dtype) == "int32" and str(disk["fleet_size"].dtype) == "int32"
    assert str(disk["run_id"].dtype) == "string" and disk["run_id"].is_unique
    assert disk["run_id"].str.startswith("throughput_curve-").all() and disk["run_id"].str.endswith("-all_off-nan-0").sum() == 16
    assert (disk["fleet_size"] == cfg.supply.fleet_size).all()

    s = summarize_throughput(table)
    assert s["demand_scale"].tolist() == list(cfg.throughput.demand_scale_grid)
    c = s["completed_per_h"].to_numpy()
    peak = int(c.argmax())
    assert 0 < peak < len(c) - 1 and c[-1] <= 0.95 * c[peak]                  # the fake has the A1 hump
    assert (np.diff(s["mean_slack"]) < 0).all() and (np.diff(s["mean_pickup_eta_min"]) > 0).all()
    assert (np.diff(s["requests_per_h"]) > 0).all()


# --- results tables (docs/schema.md) ------------------------------------------------------


def test_policy_results_table(off_cfg):
    jobs = [Job(cfg=off_cfg, seed=s, theta=0.3) for s in range(2)]
    res = run_jobs(jobs, engine=FAKE, n_procs=1)
    df = policy_results_table("evaluate", jobs, res)
    assert list(df.columns) == list(RESULTS_TABLES["policy_results"])
    cast = cast_table(df, RESULTS_TABLES["policy_results"])
    assert cast["run_id"].tolist() == [run_id("evaluate", off_cfg, "all_off", 0.3, s) for s in range(2)]
    assert cast["N_completed"].tolist() == [r.N_completed for r in res] and cast["seed"].tolist() == [0, 1]
    assert str(cast["theta"].dtype) == "float64" and (cast["theta"] == 0.3).all()
    assert str(cast["N_completed"].dtype) == "int64" and str(cast["policy"].dtype) == "string"


def test_cast_table_rejects_wrong_columns():
    with pytest.raises(ValueError):
        cast_table(pd.DataFrame({"run_id": ["a"]}), RESULTS_TABLES["policy_results"])
    full = {c: [0] for c in RESULTS_TABLES["throughput_curve"]}
    full["extra"] = [1]
    with pytest.raises(ValueError):
        cast_table(pd.DataFrame(full), RESULTS_TABLES["throughput_curve"])


def test_write_results_roundtrip(off_cfg, tmp_path):
    jobs = [Job(cfg=off_cfg, seed=4)]
    df = policy_results_table("gte", jobs, [make_run_result(policy="all_on", N_completed=5, V_profit_usd=1.5)])
    path = write_results(tmp_path, "policy_results", df)
    assert path == tmp_path / "results" / "policy_results.parquet"
    back = pd.read_parquet(path)
    assert back["N_completed"].tolist() == [5] and back["policy"].tolist() == ["all_on"] and back["seed"].tolist() == [4]
    assert np.isnan(back["budget_B_usd"][0]) and back["V_profit_usd"][0] == 1.5


# --- mode dispatch -----------------------------------------------------------------------


def test_run_mode_dispatch(off_cfg, default_yaml, tmp_path):
    for mode in ("evaluate", "gte", "sweep_theta", "calibrate_budget", "generate"):
        with pytest.raises(NotImplementedError, match="T2.4"):
            run_mode(mode, off_cfg, tmp_path, engine=FAKE)
    with pytest.raises(ValueError):
        run_mode("bogus", off_cfg, tmp_path, engine=FAKE)
    cfg = load_config(default_yaml, ["throughput.n_seeds=1", "throughput.demand_scale_grid=[1.0]", "runner.n_procs=1"])
    table = run_mode("throughput_curve", cfg, tmp_path, engine=FAKE)
    assert isinstance(table, pd.DataFrame) and len(table) == 1
    assert (tmp_path / "results" / "throughput_curve.parquet").exists()
