"""P4 on the real engine (docs/phan_cong.md T3.1) and acceptance A2 (docs/tests.md §3).

Budget: the invariant holds in every tick of a day under all_on with B, vouchers are released or
settled according to the order's fate, every budget period starts afresh, and B comes from the
all_on pilot. Policies: a smoke day for legacy, threshold and experiment on top of the all_on /
all_off days of tests/test_integration.py. CRN: same seed, same run; policies face the same sessions.
"""

from unittest import mock

import numpy as np
import pytest

from sim import reposition
from sim.budget import LedgerState, usd_to_cents
from sim.config import load_config
from sim.engine import run
from sim.policies.fixed import FixedPolicy
from sim.population import build_world
from sim.rng import Rng
from sim.runner import DEFAULT_ENGINE, Job, calibrate_budget, execute_job, with_policy
from sim.state import Clock, Mechanism, OrderStatus
from tests.conftest import ROOT

DEFAULT = ROOT / "config" / "default.yaml"
TINY = [DEFAULT, ROOT / "tests" / "fixtures" / "tiny.yaml"]
COMPLETED, ABANDONED, CANCELLED, TRUNCATED = (int(OrderStatus[n]) for n in ("COMPLETED", "ABANDONED", "CANCELLED", "TRUNCATED"))
POLICIES = ("legacy", "threshold", "experiment")


# --- T3.1: budget on the real engine ----------------------------------------------------------


@pytest.fixture(scope="module")
def budget_day():
    """all_on under B for one default day; the ledger invariant is checked after step 9 of every tick."""
    cfg = load_config(DEFAULT)
    budget, pilot = calibrate_budget(cfg)
    world = build_world(cfg, Rng.from_config(cfg))
    seen = {"ticks": 0, "ctx": None}
    original = reposition.step

    def checked_step(ctx, t):
        original(ctx, t)
        ctx.ledger.check_invariant()
        seen["ticks"] += 1
        seen["ctx"] = ctx

    with mock.patch.object(reposition, "step", checked_step):
        res = run(cfg, world, FixedPolicy(True, world.n_cells), Rng.from_config(cfg), budget_usd=budget,
                  enforce_budget=True, log_level="full")
    return cfg, budget, pilot, res, seen["ctx"], seen["ticks"]


def test_calibrate_budget_on_the_real_engine(budget_day):
    cfg, budget, pilot, _, _, _ = budget_day
    assert pilot.policy == "all_on" and np.isnan(pilot.budget_B_usd) and pilot.voucher_spent_usd > 0
    n_periods = Clock.from_config(cfg).n_periods
    assert n_periods == 1
    assert budget == pytest.approx(cfg.budget.fraction * float(pilot.spent_by_period_usd.mean()))
    assert budget == pytest.approx(cfg.budget.fraction * pilot.voucher_spent_usd, abs=0.05)
    assert 0 < budget < pilot.voucher_spent_usd


def test_budget_invariant_holds_in_every_tick_of_a_day(budget_day):
    cfg, budget, _, res, ctx, ticks = budget_day
    assert ticks == res.sim_end_s / cfg.time.tick_s >= 1440
    ctx.ledger.check_invariant()
    assert ctx.ledger.limit_cents(0) == usd_to_cents(budget)
    assert ctx.ledger.used_cents(0) <= ctx.ledger.limit_cents(0)
    assert res.voucher_spent_usd <= budget + 1e-6
    assert res.spent_by_period_usd[0] == pytest.approx(res.voucher_spent_usd, abs=0.05)
    s = res.sessions
    blocked, granted = s.col("budget_blocked"), s.col("arm") == 1
    assert blocked.any() and granted.any() and not (blocked & granted).any()
    assert blocked.sum() > granted.sum()                      # B = 30% of unconstrained spend binds hard
    assert res.N_completed > 0 and res.n_truncated_orders == 0


def test_vouchers_are_settled_or_released_by_the_order_fate(budget_day):
    _, _, _, res, ctx, _ = budget_day
    s, o, ledger = res.sessions, res.orders, ctx.ledger
    voucher = s.col("voucher_cents")
    requested, order_idx = s.col("requested"), s.col("order_idx")
    status = o.col("status")
    expected_state = {COMPLETED: LedgerState.SPENT, ABANDONED: LedgerState.RELEASED, CANCELLED: LedgerState.RELEASED,
                      TRUNCATED: LedgerState.RELEASED}
    checked = {LedgerState.SPENT: 0, LedgerState.RELEASED: 0}
    for i in range(0, s.n, 13):
        sid = int(s.col("session_id")[i])
        entry = ledger.entry(sid)
        if voucher[i] == 0:
            assert entry is None
            continue
        assert entry[1] == voucher[i]
        want = LedgerState.RELEASED if not requested[i] else expected_state[int(status[order_idx[i]])]
        assert entry[2] == want, (sid, want, entry)
        checked[want] += 1
    assert checked[LedgerState.SPENT] > 0 and checked[LedgerState.RELEASED] > 0
    for period in (-1, 0):                                        # every order is closed: nothing left in flight
        spent, committed, reserved = ledger.totals(period)
        assert committed == 0 and reserved == 0
    done = status == COMPLETED
    in_window = o.col("in_window")
    assert ledger.totals(0)[0] == int(o.col("voucher_cents")[done & in_window].sum())
    assert ledger.totals(-1)[0] == int(o.col("voucher_cents")[done & ~in_window].sum())


def test_budget_blocked_sessions_decide_without_a_voucher(budget_day):
    _, _, _, res, _, _ = budget_day
    s = res.sessions
    blocked = s.col("budget_blocked")
    assert (s.col("arm")[blocked] == 0).all() and (s.col("voucher_cents")[blocked] == 0).all()
    assert s.col("promo_on_cell")[blocked].all()
    np.testing.assert_array_equal(s.col("requested")[blocked],
                                  (s.col("u_book") < s.col("p_request_control").astype(np.float64))[blocked])
    granted = s.col("arm") == 1
    np.testing.assert_array_equal(s.col("requested")[granted],
                                  (s.col("u_book") < s.col("p_request_treat").astype(np.float64))[granted])


def test_every_budget_period_starts_with_a_fresh_budget():
    # Two days on the tiny world with a small B: both periods spend, both stay within B, both block.
    cfg = load_config(TINY, ["time.window_min=null", "time.days_per_run=2", "policy.name=all_on"])
    world = build_world(cfg, Rng.from_config(cfg))
    budget = 10.0
    res = run(cfg, world, FixedPolicy(True, world.n_cells), Rng.from_config(cfg), budget_usd=budget,
              enforce_budget=True, log_level="full")
    clock = Clock.from_config(cfg)
    assert clock.n_periods == 2 and len(res.spent_by_period_usd) == 2
    assert (res.spent_by_period_usd > 0).all() and (res.spent_by_period_usd <= budget + 1e-6).all()
    s = res.sessions
    period, blocked = s.col("budget_period"), s.col("budget_blocked")
    assert set(np.unique(period)) == {-1, 0, 1}
    assert blocked[period == 0].any() and blocked[period == 1].any()
    assert (s.col("arm")[period == 1] == 1).any()                 # period 1 granted vouchers again
    assert res.voucher_spent_usd == pytest.approx(res.spent_by_period_usd.sum(), abs=0.05)


# --- T3.1: smoke day with every policy -------------------------------------------------------


@pytest.fixture(scope="module")
def policy_days():
    cfg = load_config(DEFAULT, ["budget.mode=fixed", "budget.fixed_usd=2500"])
    runs = {}
    for name in POLICIES:
        c = with_policy(cfg, name)
        enforce = c.experiment.budget_enforce if name == "experiment" else c.budget.enforce
        runs[name] = execute_job(DEFAULT_ENGINE, Job(cfg=c, seed=0, budget_usd=2500.0 if enforce else None,
                                                     enforce_budget=enforce, log_level="full"))
    return cfg, runs


@pytest.mark.parametrize("policy", POLICIES)
def test_smoke_day_every_policy(policy_days, policy):
    cfg, runs = policy_days
    res = runs[policy]
    assert res.policy == policy
    assert res.N_completed > 0 and res.n_requests > res.N_completed and res.n_sessions > 20_000
    assert res.n_truncated_orders == 0 and res.orders.count_open() == 0
    assert 0 < res.mean_pickup_eta_min <= cfg.matching.max_pickup_eta_min
    assert res.runtime_s < cfg.performance.max_seconds_per_sim_day
    s = res.sessions
    np.testing.assert_allclose(s.col("voucher_value_usd"), s.col("voucher_cents") / 100.0, atol=1e-6)
    assert (s.col("arm")[s.col("voucher_cents") > 0] == 1).all()
    if policy == "experiment":
        assert np.isnan(res.budget_B_usd) and res.voucher_spent_usd > 0
    else:
        assert res.budget_B_usd == 2500.0 and 0 < res.voucher_spent_usd <= 2500.0


def test_legacy_mechanisms_and_propensities(policy_days):
    cfg, runs = policy_days
    s = runs["legacy"].sessions
    mech, on = s.col("assign_mechanism"), s.col("promo_on_cell")
    assert set(np.unique(mech)) <= {int(Mechanism.LEGACY_RULE), int(Mechanism.LEGACY_EPS), int(Mechanism.EXPLORE)}
    explore = mech == int(Mechanism.EXPLORE)
    assert abs(explore.mean() - cfg.policy.legacy.explore_frac) < 0.01
    assert on.any() and not on.all()
    prop = s.col("propensity")
    np.testing.assert_array_equal(np.isnan(prop), on & ~explore)                 # targeting is hidden
    assert (prop[explore] == np.float32(cfg.policy.legacy.explore_p)).all()
    assert (prop[~on & ~explore] == 0.0).all() and (s.col("arm")[~on & ~explore] == 0).all()
    truth = s.col("propensity_true")
    assert np.isfinite(truth).all() and (truth >= 0).all() and (truth <= 1).all()
    assert (truth[on & ~explore] > 0).all() and (truth[on & ~explore] < 1).all()
    assert (s.col("cluster_id") == -1).all() and (s.col("block") == -1).all()


def test_threshold_cuts_cells_and_scores_every_session(policy_days):
    cfg, runs = policy_days
    res = runs["threshold"]
    s = res.sessions
    assert (s.col("assign_mechanism") == int(Mechanism.THRESHOLD)).all()
    assert np.isfinite(s.col("score")).all()                                    # heuristic_low_freq
    assert 0 < res.share_cells_off < 1 and res.n_switches_per_cell_day > 0
    theta = cfg.policy.threshold.theta
    s_hat, on = s.col("slack_hat"), s.col("promo_on_cell")
    clear = np.abs(s_hat - theta) > 1e-4
    np.testing.assert_array_equal(on[clear], ~(s_hat[clear] < theta))          # promo_on = not (s_hat < theta)
    assert (s.col("arm")[~on] == 0).all()
    assert np.isinf(s_hat).any() or np.isnan(s_hat).any() or (s_hat >= 0).all()


def test_experiment_switchback_fields(policy_days):
    cfg, runs = policy_days
    res = runs["experiment"]
    s = res.sessions
    assert (s.col("assign_mechanism") == int(Mechanism.EXPERIMENT)).all()
    assert (s.col("cluster_id") >= 0).all() and s.col("cluster_id").max() == 6
    assert (s.col("block") >= 0).all() and s.col("block")[s.col("in_window")].min() == 1   # warm-up = block 0
    assert abs(s.col("in_burnin").mean() - cfg.experiment.burnin_min / cfg.experiment.block_min) < 0.05
    on = s.col("promo_on_cell")
    assert abs(on.mean() - cfg.experiment.p_on) < 0.15
    np.testing.assert_array_equal(s.col("arm") == 1, on)                          # every session of an on cell
    assert (s.col("propensity") == np.float32(cfg.experiment.p_on)).all()
    assert (s.col("cell_propensity") == np.float32(cfg.experiment.p_on)).all()


# --- A2 (docs/tests.md §3): common random numbers ------------------------------------------------


@pytest.mark.parametrize("policy", POLICIES)
def test_a2a_same_seed_same_run(policy):
    cfg = load_config(TINY, [f"policy.name={policy}", "budget.mode=fixed", "budget.fixed_usd=20"])
    enforce = cfg.experiment.budget_enforce if policy == "experiment" else True
    job = Job(cfg=cfg, seed=3, budget_usd=20.0 if enforce else None, enforce_budget=enforce, log_level="full")
    a, b = execute_job(DEFAULT_ENGINE, job), execute_job(DEFAULT_ENGINE, job)
    assert (a.N_completed, a.V_profit_usd, a.voucher_spent_usd) == (b.N_completed, b.V_profit_usd, b.voucher_spent_usd)
    for name in ("status", "driver_id", "pickup_time_s", "dropoff_time_s", "voucher_cents"):
        np.testing.assert_array_equal(a.orders.col(name), b.orders.col(name), err_msg=name)
    np.testing.assert_array_equal(a.sessions.col("arm"), b.sessions.col("arm"))


def test_a2c_policies_face_the_same_sessions(policy_days):
    _, runs = policy_days
    base = runs["legacy"].sessions
    for name in POLICIES[1:]:
        other = runs[name].sessions
        assert other.n == base.n
        for col in ("session_id", "rider_id", "pu_cell", "do_cell", "u_book", "u_target", "u_score", "e_cancel",
                    "trip_noise", "quoted_fare_usd"):
            np.testing.assert_array_equal(other.col(col), base.col(col), err_msg=f"{name}.{col}")
