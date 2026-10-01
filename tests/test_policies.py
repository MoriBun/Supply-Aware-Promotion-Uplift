"""Sprint-0 contract: policies/base.py, FixedPolicy, policy factory (docs/phan_cong.md, S0 item 4)."""

import dataclasses
import math

import numpy as np
import pytest

from sim import experiment
from sim.config import load_config
from sim.policies import make_policy
from sim.policies.base import (
    FORBIDDEN_IN_BATCH, SNAPSHOT_FIELDS, CellDecision, LegacyHiddenView, LookAheadError, OfferDecision, Policy,
    SessionBatch, SnapshotStore, SnapshotView,
)
from sim.policies.experiment import ExperimentPolicy
from sim.policies.fixed import FixedPolicy
from sim.policies.legacy import LegacyPolicy, sigmoid
from sim.policies.scores import BUILTIN_SCORES, import_callable, load_score_fn, score_batch
from sim.policies.threshold import ThresholdPolicy
from sim.rng import CellSlotKind, Rng, Stream
from sim.state import HIDDEN_COLUMNS, POLICY_UNIFORMS, Mechanism
from tests.fakes import blank_record, fake_score, make_batch, make_ledger, published_store, stub_world

NAN = float("nan")


def store_with_slack(n_cells: int, slack_rows: list[list[float]], slots_per_day: int = 96) -> SnapshotStore:
    """A store whose slot k has ``slack = slack_rows[k]`` (other fields from blank_record)."""
    store = SnapshotStore(n_cells, slots_per_day)
    for k, row in enumerate(slack_rows):
        store.publish(k, blank_record(n_cells, k, slack=np.asarray(row, dtype=np.float64)))
    return store


# --- SessionBatch (docs/tests.md: "SessionBatch truyền cho π_θ không chứa cột ẩn") ---


def test_session_batch_has_no_hidden_columns():
    names = {f.name for f in dataclasses.fields(SessionBatch)}
    assert not names & FORBIDDEN_IN_BATCH
    assert FORBIDDEN_IN_BATCH == HIDDEN_COLUMNS - POLICY_UNIFORMS
    assert POLICY_UNIFORMS <= names            # the policy uniforms are the only hidden-list fields present
    assert "u_book" not in names and "u_latent" not in names and "e_cancel" not in names


def test_session_batch_validates_lengths():
    b = make_batch(3, 7)
    assert len(b) == 3 and b.n == 3
    bad = dataclasses.asdict(b)
    bad["x_freq"] = np.ones(2, dtype=np.float32)
    with pytest.raises(ValueError):
        SessionBatch(**bad)


# --- decisions ------------------------------------------------------------------


def test_cell_decision_blank():
    d = CellDecision.blank(3, 7, promo_on=True)
    assert d.slot == 3 and d.n_cells == 7
    assert d.promo_on.dtype == bool and d.promo_on.all()
    assert d.cell_propensity.dtype == np.float32 and (d.cell_propensity == 1.0).all()
    assert (d.mechanism == int(Mechanism.FIXED)).all() and d.mechanism.dtype == np.int8
    assert np.isnan(d.s_hat).all() and (d.cluster_id == -1).all() and d.block == -1 and d.in_burnin is False
    off = CellDecision.blank(0, 7)
    assert not off.promo_on.any() and (off.cell_propensity == 0.0).all()


def test_offer_decision_blank():
    d = OfferDecision.blank(4)
    assert len(d) == 4 and not d.offer.any()
    assert np.isnan(d.propensity).all() and np.isnan(d.score).all() and np.isnan(d.propensity_true).all()
    assert (d.mechanism == int(Mechanism.FIXED)).all()


# --- SnapshotStore / SnapshotView (hard rule 2) --------------------------------------


def test_store_requires_order_and_full_records():
    store = SnapshotStore(7, 96)
    assert store.last_published_slot == -1 and not store.has(0)
    with pytest.raises(ValueError):
        store.publish(1, blank_record(7, 1))          # slot 0 first
    rec = blank_record(7, 0)
    del rec["slack"]
    with pytest.raises(ValueError):
        store.publish(0, rec)                          # missing field
    rec = blank_record(7, 0)
    rec["extra"] = np.zeros(7)
    with pytest.raises(ValueError):
        store.publish(0, rec)                          # unknown field
    rec = blank_record(7, 0)
    rec["slack"] = np.zeros(3)
    with pytest.raises(ValueError):
        store.publish(0, rec)                          # wrong shape
    store.publish(0, blank_record(7, 0))
    assert store.has(0) and len(store) == 1 and set(store.records()[0]) == set(SNAPSHOT_FIELDS)


def test_view_refuses_current_and_future_slots():
    store = published_store(7, n_slots=5)
    view = SnapshotView(store, current_slot=3)
    np.testing.assert_allclose(view.get("slack", 2), 2 + 0.1 * np.arange(7))
    np.testing.assert_allclose(view.lag("slack", 1), 2 + 0.1 * np.arange(7))
    np.testing.assert_allclose(view.lag("slack", 3), 0 + 0.1 * np.arange(7))
    for slot in (3, 4, 100):                           # 4 is published but still forbidden
        with pytest.raises(LookAheadError):
            view.get("slack", slot)
    with pytest.raises(LookAheadError):
        view.lag("slack", 0)
    assert view.available(2) and not view.available(3)


def test_view_is_nan_before_first_publish():
    view = SnapshotView(SnapshotStore(7, 96), current_slot=0)
    assert np.isnan(view.get("slack", -1)).all()
    assert np.isnan(view.lag("slack", 1)).all()
    view = SnapshotView(published_store(7, n_slots=2), current_slot=5)
    assert np.isnan(view.get("slack", 3)).all()       # slot 3 not published yet (gap)
    assert np.isnan(view.lag_day("slack")).all()       # slot 5 - 96 < 0


def test_view_casts_to_float64_and_rejects_unknown_field():
    view = SnapshotView(published_store(7, n_slots=2), current_slot=2)
    assert view.get("promo_on", 1).dtype == np.float64
    assert view.get("n_sessions", 1).dtype == np.float64
    with pytest.raises(KeyError):
        view.get("slac", 1)
    assert view.n_cells == 7 and view.slots_per_day == 96


# --- LegacyHiddenView ---------------------------------------------------------------


def test_legacy_hidden_view(tiny_cfg):
    hv = LegacyHiddenView(np.array([0.5, -1.0, 2.0]), np.array([1.0, 2.0, 3.0]))
    np.testing.assert_array_equal(hv.u_latent_of(np.array([2, 0])), np.array([2.0, 0.5], dtype=np.float32))
    np.testing.assert_array_equal(hv.zf_of(np.array([1])), np.array([2.0], dtype=np.float32))
    with pytest.raises(ValueError):
        LegacyHiddenView(np.zeros(2), np.zeros(3))
    world = stub_world(tiny_cfg)
    assert LegacyHiddenView.from_world(world).u_latent_of(np.array([0])).shape == (1,)


# --- FixedPolicy and factory ---------------------------------------------------------


@pytest.mark.parametrize("on", [True, False])
def test_fixed_policy(on):
    n_cells = 7
    policy = FixedPolicy(on, n_cells)
    assert isinstance(policy, Policy) and policy.name == ("all_on" if on else "all_off")
    cd = policy.cell_state(3, SnapshotView(SnapshotStore(n_cells, 96), 3))
    assert cd.slot == 3 and cd.promo_on.all() == on and (cd.mechanism == int(Mechanism.FIXED)).all()
    batch = make_batch(10, n_cells)
    dec = policy.offer(batch, cd, make_ledger())
    assert len(dec) == 10 and dec.offer.all() == on and (dec.propensity == float(on)).all()
    assert np.isnan(dec.score).all() and np.isnan(dec.propensity_true).all()


def test_make_policy_builds_every_policy(tiny_cfg, tiny_layers):
    world = stub_world(tiny_cfg)
    for name, cls in (("all_on", FixedPolicy), ("all_off", FixedPolicy), ("legacy", LegacyPolicy),
                      ("threshold", ThresholdPolicy), ("experiment", ExperimentPolicy)):
        policy = make_policy(load_config(tiny_layers, [f"policy.name={name}"]), world)
        assert isinstance(policy, cls) and isinstance(policy, Policy) and policy.name == name
    th = make_policy(tiny_cfg, world, theta=0.7, kappa=0.2)             # tiny default policy is threshold
    assert th.theta == 0.7 and th.kappa == 0.2
    assert make_policy(tiny_cfg, world).theta == tiny_cfg.policy.threshold.theta
    with pytest.raises(NotImplementedError):
        make_policy(load_config(tiny_layers, ["policy.threshold.indicator=utilization"]), world)   # Q19


# --- score functions (spec §6; decisions T-07, T-21; task T1.3) ---------------------------


def test_builtin_scores_random_and_low_freq():
    batch = make_batch(5, 7, x_freq=[1.0, 4.0, 2.0, 8.0, 3.0])
    s_hat = np.full(5, np.nan)
    rnd = score_batch(load_score_fn("random"), batch, s_hat)
    assert rnd.dtype == np.float32
    np.testing.assert_array_equal(rnd, batch.u_score.astype(np.float32))      # T-07: pre-drawn, never redrawn
    low = score_batch(load_score_fn("heuristic_low_freq"), batch, s_hat)
    np.testing.assert_array_equal(low, -batch.x_freq)
    assert int(low.argmax()) == 0                                              # lowest frequency scores highest
    assert load_score_fn(" random ") is BUILTIN_SCORES["random"]
    assert set(BUILTIN_SCORES) == {"random", "heuristic_low_freq"}


def test_score_fn_loader_module_function():
    fn = load_score_fn("tests.fakes:fake_score")
    assert fn is fake_score and import_callable("tests.fakes:fake_score") is fake_score
    batch = make_batch(3, 7)                                                   # x_tenure = 12
    out = score_batch(fn, batch, np.array([0.5, np.nan, 2.0]))
    np.testing.assert_allclose(out, [12.5, 12.0, 14.0])
    for bad in ("nope", "tests.fakes", "tests.fakes:missing", "tests.no_such_module:f", "tests.fakes:NAN", ":f", "m:"):
        with pytest.raises(ValueError):
            load_score_fn(bad)


def test_score_batch_validates_output_and_s_hat():
    batch, s_hat = make_batch(4, 7), np.zeros(4)
    for fn in (lambda b, s: np.zeros(3), lambda b, s: np.zeros((4, 1)), lambda b, s: np.ones(4, dtype=bool),
               lambda b, s: np.array(["a"] * 4)):
        with pytest.raises(ValueError):
            score_batch(fn, batch, s_hat)
    with pytest.raises(ValueError):
        score_batch(fake_score, batch, np.zeros(3))                            # s_hat must be [n]
    out = score_batch(lambda b, s: list(range(4)), batch, s_hat)
    assert out.dtype == np.float32 and out.tolist() == [0.0, 1.0, 2.0, 3.0]


# --- ThresholdPolicy pi_theta (spec §6; docs/tests.md "Chính sách"; T-23; task T2.3) ------------


def threshold(default_yaml, *overrides, **kw) -> ThresholdPolicy:
    return ThresholdPolicy(load_config(default_yaml, list(overrides)), 7, **kw)


def test_threshold_theta_zero_cuts_nothing_and_huge_theta_cuts_every_finite_cell(default_yaml):
    store = store_with_slack(7, [[0.1, 0.5, math.inf, 2.0, 0.34, 0.36, 10.0]])
    view = SnapshotView(store, 1)
    zero = threshold(default_yaml, theta=0.0).cell_state(1, view)
    assert zero.promo_on.all() and (zero.cell_propensity == 1.0).all()
    assert (zero.mechanism == int(Mechanism.THRESHOLD)).all() and (zero.cluster_id == -1).all() and zero.block == -1
    np.testing.assert_array_equal(zero.s_hat, np.array([0.1, 0.5, math.inf, 2.0, 0.34, 0.36, 10.0], dtype=np.float32))
    huge = threshold(default_yaml, theta=1e9).cell_state(1, view)
    assert huge.promo_on.tolist() == [False, False, True, False, False, False, False]   # inf never counts as tight
    mid = threshold(default_yaml, theta=0.35).cell_state(1, view)
    assert mid.promo_on.tolist() == [False, True, True, True, False, True, True]
    first = threshold(default_yaml, theta=0.35).cell_state(0, SnapshotView(SnapshotStore(7, 96), 0))
    assert first.promo_on.all() and np.isnan(first.s_hat).all()                      # nothing published: on


def test_threshold_offer_scores_and_kappa(default_yaml):
    pol = threshold(default_yaml, "policy.threshold.score_fn=heuristic_low_freq", kappa=-2.5)
    cd = CellDecision.blank(1, 7, promo_on=True)
    cd.promo_on[3] = False
    cd.s_hat[:] = 0.8
    batch = make_batch(5, 7, x_freq=[1.0, 2.0, 3.0, 4.0, 1.0])            # pu cells 0..4, scores -x_freq
    dec = pol.offer(batch, cd, make_ledger())
    np.testing.assert_array_equal(dec.score, np.array([-1, -2, -3, -4, -1], dtype=np.float32))
    assert dec.offer.tolist() == [True, True, False, False, True]           # score >= -2.5 ... but cell 3 is off anyway
    cd.promo_on[0] = False
    dec = pol.offer(batch, cd, make_ledger())
    assert dec.offer.tolist() == [False, True, False, False, True]          # cell off -> no offer
    assert (dec.propensity == dec.offer.astype(np.float32)).all() and (dec.mechanism == int(Mechanism.THRESHOLD)).all()
    assert np.isnan(dec.propensity_true).all()
    everyone = threshold(default_yaml, "policy.threshold.score_fn=heuristic_low_freq", kappa=-math.inf)
    assert everyone.offer(batch, CellDecision.blank(1, 7, promo_on=True), make_ledger()).offer.all()
    nobody = threshold(default_yaml, kappa=math.inf)
    assert not nobody.offer(batch, CellDecision.blank(1, 7, promo_on=True), make_ledger()).offer.any()
    nan_scores = threshold(default_yaml, kappa=-math.inf, score_fn=lambda b, s: np.full(len(b), NAN))
    assert not nan_scores.offer(batch, CellDecision.blank(1, 7, promo_on=True), make_ledger()).offer.any()


def test_threshold_score_fn_sees_the_forecast_of_each_session_cell(default_yaml):
    seen = {}

    def spy(batch, s_hat):
        seen["s_hat"] = s_hat.copy()
        return np.zeros(len(batch))

    pol = threshold(default_yaml, kappa=-math.inf, score_fn=spy)
    cd = CellDecision.blank(1, 7, promo_on=True)
    cd.s_hat[:] = np.arange(7, dtype=np.float32) / 10
    pol.offer(make_batch(4, 7, pu_cell=[6, 0, 6, 2]), cd, make_ledger())
    np.testing.assert_allclose(seen["s_hat"], [0.6, 0.0, 0.6, 0.2], atol=1e-7)


def test_threshold_hysteresis_reduces_switches(default_yaml):
    # One cell whose forecast alternates 0.33 / 0.37 around theta = 0.35 (docs/tests.md).
    rows = [[0.33 if k % 2 == 0 else 0.37] * 7 for k in range(20)]
    store = store_with_slack(7, rows)

    def switches(h: float) -> int:
        pol = threshold(default_yaml, f"policy.threshold.hysteresis_h={h}", theta=0.35)
        states = [pol.cell_state(k, SnapshotView(store, k)).promo_on[0] for k in range(1, 21)]
        return int(np.sum(np.array(states[1:]) != np.array(states[:-1])))

    # h = 0: flips every slot. h = 0.1: off at the first observed 0.33 and 0.37 never clears theta + h = 0.45.
    assert switches(0.0) == 19 and switches(0.1) == 0


def test_threshold_ar_forecast_caps_inf_and_falls_back_to_persistence_on_day_one(default_yaml):
    pol = threshold(default_yaml, "policy.threshold.forecast=ar", theta=0.0)
    cap, (w_slot, w_day) = pol.slack_cap, pol.ar_weights
    assert cap == 10.0 and (w_slot, w_day) == (0.7, 0.3)
    rows = [[k + 0.1 * c for c in range(7)] for k in range(97)]             # slack of slot k = k + 0.1c
    rows[96][2] = math.inf
    store = store_with_slack(7, rows)
    day_one = pol.forecast_slack(SnapshotView(store, 5))                   # lag day unknown -> lag slot, capped
    np.testing.assert_allclose(day_one, np.minimum([4 + 0.1 * c for c in range(7)], cap))
    day_two = pol.forecast_slack(SnapshotView(store, 97))                  # lag slot 96 (capped at 10), lag day = slot 1
    expected = w_slot * np.minimum(np.array([96 + 0.1 * c for c in range(7)]), cap) + w_day * np.array([1 + 0.1 * c for c in range(7)])
    np.testing.assert_allclose(day_two, expected)
    assert day_two[2] == pytest.approx(w_slot * cap + w_day * 1.2)         # inf capped before weighting


def test_threshold_kappa_and_indicator_defaults(default_yaml):
    assert threshold(default_yaml).kappa == -math.inf                       # config "auto": pilot setting
    assert threshold(default_yaml, "policy.threshold.kappa=0.3").kappa == 0.3
    assert threshold(default_yaml, "policy.threshold.kappa=0.3", kappa=0.9).kappa == 0.9
    assert threshold(default_yaml).theta == load_config(default_yaml).policy.threshold.theta
    with pytest.raises(NotImplementedError):
        threshold(default_yaml, "policy.threshold.indicator=eta")


# --- LegacyPolicy (spec §6; docs/tests.md "Chính sách"; T-24; task T2.3) -----------------------


def legacy(tiny_layers, *overrides, u_latent=None, zf=None) -> tuple[LegacyPolicy, object]:
    cfg = load_config(tiny_layers, ["policy.name=legacy", *overrides])
    n = 4 if u_latent is None else len(u_latent)
    hidden = LegacyHiddenView(np.zeros(n) if u_latent is None else np.asarray(u_latent, dtype=np.float32),
                              np.zeros(n) if zf is None else np.asarray(zf, dtype=np.float32))
    return LegacyPolicy(cfg, hidden, Rng.from_config(cfg), 7), cfg


def test_legacy_cell_rule_on_lagged_slack_with_epsilon_coin(tiny_layers):
    pol, cfg = legacy(tiny_layers)
    p = cfg.policy.legacy
    assert p.slack_on == 0.6 and p.epsilon_cell == 0.1 and p.epsilon_p_on == 0.5
    slack = [0.2, 0.7, math.inf, 0.6, 0.59, 0.61, 5.0]
    view = SnapshotView(store_with_slack(7, [slack]), 1)
    cd = pol.cell_state(1, view)
    rule_on = np.array([False, True, True, True, False, True, True])
    u = np.array([Rng.from_config(cfg).rng_for(Stream.CELLSLOT, CellSlotKind.LEGACY_EPS, 0, c, 1).random(2) for c in range(7)])
    is_eps, coin = u[:, 0] < p.epsilon_cell, u[:, 1] < p.epsilon_p_on
    np.testing.assert_array_equal(cd.promo_on, np.where(is_eps, coin, rule_on))
    np.testing.assert_array_equal(cd.mechanism, np.where(is_eps, int(Mechanism.LEGACY_EPS), int(Mechanism.LEGACY_RULE)))
    np.testing.assert_allclose(cd.cell_propensity, 0.9 * rule_on + 0.05, atol=1e-6)
    assert np.isnan(cd.s_hat).all() and (cd.cluster_id == -1).all() and cd.block == -1 and not cd.in_burnin
    first = pol.cell_state(0, SnapshotView(SnapshotStore(7, 96), 0))       # no snapshot yet: rule is off
    np.testing.assert_allclose(first.cell_propensity, 0.05)
    assert not first.promo_on[~(np.array([Rng.from_config(cfg).rng_for(Stream.CELLSLOT, CellSlotKind.LEGACY_EPS, 0, c, 0).random(2)[0] < p.epsilon_cell for c in range(7)]))].any()
    exact, _ = legacy(tiny_layers, "policy.legacy.epsilon_cell=0.0")
    cd0 = exact.cell_state(1, view)
    np.testing.assert_array_equal(cd0.promo_on, rule_on)
    assert (cd0.mechanism == int(Mechanism.LEGACY_RULE)).all() and (cd0.cell_propensity == rule_on.astype(np.float32)).all()


def test_legacy_targets_riders_by_hidden_u_latent(tiny_layers):
    pol, cfg = legacy(tiny_layers, u_latent=[3.0, -3.0, 0.0, 0.0])
    p = cfg.policy.legacy
    batch = make_batch(4, 7)                                                # u_target = u_explore = [.125 .375 .625 .875]
    assert (batch.u_explore >= p.explore_frac).all()                        # explore_frac 0.05: nobody explores here
    cd = CellDecision.blank(2, 7, promo_on=True, mechanism=Mechanism.LEGACY_RULE)
    dec = pol.offer(batch, cd, make_ledger())
    p_target = sigmoid(p.target_g0 + p.target_g_u * np.array([3.0, -3.0, 0.0, 0.0]))
    np.testing.assert_allclose(dec.propensity_true, p_target, atol=1e-6)    # hidden truth (T-24)
    np.testing.assert_array_equal(dec.offer, batch.u_target < p_target)
    assert dec.offer.tolist() == [True, False, False, False]
    assert np.isnan(dec.propensity).all()                                   # analyst does not know the targeting
    assert (dec.mechanism == int(Mechanism.LEGACY_RULE)).all() and np.isnan(dec.score).all()
    off = pol.offer(batch, CellDecision.blank(2, 7, promo_on=False, mechanism=Mechanism.LEGACY_RULE), make_ledger())
    assert not off.offer.any() and (off.propensity == 0.0).all() and (off.propensity_true == 0.0).all()


def test_legacy_explore_slice_is_randomized_whatever_the_cell_state(tiny_layers):
    pol, cfg = legacy(tiny_layers, "policy.legacy.explore_frac=0.5", "policy.legacy.explore_p=0.5")
    batch = make_batch(4, 7)                                                # u_explore < 0.5 for sessions 0, 1
    for on in (True, False):
        dec = pol.offer(batch, CellDecision.blank(2, 7, promo_on=on, mechanism=Mechanism.LEGACY_EPS), make_ledger())
        assert dec.offer[:2].tolist() == [True, True]                        # u_explore_arm .125, .375 < explore_p
        assert (dec.mechanism[:2] == int(Mechanism.EXPLORE)).all() and (dec.propensity[:2] == 0.5).all()
        assert (dec.propensity_true[:2] == 0.5).all()
        assert (dec.mechanism[2:] == int(Mechanism.LEGACY_EPS)).all()
        if on:
            assert np.isnan(dec.propensity[2:]).all()
        else:
            assert not dec.offer[2:].any() and (dec.propensity[2:] == 0.0).all()


def test_legacy_draws_only_from_the_cellslot_stream(tiny_layers):
    class Recording(Rng):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.streams = set()

        def rng_for(self, stream, *key):
            self.streams.add(Stream(stream))
            return super().rng_for(stream, *key)

    cfg = load_config(tiny_layers, ["policy.name=legacy"])
    rng = Recording(run_seed=0, world_seed=cfg.meta.world_seed)
    pol = LegacyPolicy(cfg, LegacyHiddenView(np.zeros(4), np.zeros(4)), rng, 7)
    cd = pol.cell_state(3, SnapshotView(published_store(7, 3), 3))
    pol.offer(make_batch(4, 7), cd, make_ledger())
    assert rng.streams == {Stream.CELLSLOT}


# --- ExperimentPolicy (spec §4.10, §6; T-25; task T2.3) ---------------------------------------


def test_experiment_policy_cluster_switchback(default_yaml):
    cfg = load_config(default_yaml, ["policy.name=experiment"])
    world = stub_world(cfg)
    rng = Rng.from_config(cfg)
    pol = ExperimentPolicy(cfg, world, rng)
    assert pol.name == "experiment" and pol.level == 7
    np.testing.assert_array_equal(pol.clusters, experiment.cluster_ids(world.space, 7))
    cd = pol.cell_state(4, SnapshotView(SnapshotStore(37, 96), 4))             # slot 4 starts at 3600 s = block 1
    assert cd.block == 1 and cd.in_burnin is True
    np.testing.assert_array_equal(cd.promo_on, experiment.cluster_on(Rng.from_config(cfg), cfg, pol.clusters, 7, 1))
    assert (cd.cell_propensity == np.float32(cfg.experiment.p_on)).all()
    assert (cd.mechanism == int(Mechanism.EXPERIMENT)).all() and np.isnan(cd.s_hat).all()
    np.testing.assert_array_equal(cd.cluster_id, pol.clusters)
    assert pol.cell_state(5, SnapshotView(SnapshotStore(37, 96), 5)).in_burnin is False   # 4500 s: 15 min into block 1
    batch = make_batch(10, 37)
    dec = pol.offer(batch, cd, make_ledger())
    np.testing.assert_array_equal(dec.offer, cd.promo_on[batch.pu_cell])
    assert (dec.propensity == np.float32(0.5)).all() and (dec.propensity_true == np.float32(0.5)).all()
    assert (dec.mechanism == int(Mechanism.EXPERIMENT)).all() and np.isnan(dec.score).all()


def test_experiment_policy_global_switchback_and_rider_ab(default_yaml):
    glob = load_config(default_yaml, ["policy.name=experiment", "experiment.design=global_switchback"])
    world = stub_world(glob)
    pol = ExperimentPolicy(glob, world, Rng.from_config(glob))
    assert pol.level == "all" and (pol.clusters == 0).all()
    states = [pol.cell_state(k, SnapshotView(SnapshotStore(37, 96), k)).promo_on for k in range(0, 40, 4)]
    assert all(len(set(s.tolist())) == 1 for s in states) and len({bool(s[0]) for s in states}) == 2

    ab = load_config(default_yaml, ["policy.name=experiment", "experiment.design=rider_ab"])
    pol = ExperimentPolicy(ab, world, Rng.from_config(ab))
    cd = pol.cell_state(8, SnapshotView(SnapshotStore(37, 96), 8))
    assert cd.promo_on.all() and (cd.cell_propensity == 1.0).all() and (cd.cluster_id == -1).all() and cd.block == 2
    batch = make_batch(12, 37)
    dec = pol.offer(batch, cd, make_ledger())
    np.testing.assert_array_equal(dec.offer, experiment.rider_arm(Rng.from_config(ab), ab, batch.rider_id))
    np.testing.assert_array_equal(pol.offer(batch, cd, make_ledger()).offer, dec.offer)   # fixed for the run
    assert (dec.propensity == np.float32(0.5)).all()
