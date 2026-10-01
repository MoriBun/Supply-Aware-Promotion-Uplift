"""Sprint-0 contract: policies/base.py, FixedPolicy, policy factory (docs/phan_cong.md, S0 item 4)."""

import dataclasses

import numpy as np
import pytest

from sim.policies import make_policy
from sim.policies.base import (
    FORBIDDEN_IN_BATCH, SNAPSHOT_FIELDS, CellDecision, LegacyHiddenView, LookAheadError, OfferDecision, Policy,
    SessionBatch, SnapshotStore, SnapshotView,
)
from sim.policies.fixed import FixedPolicy
from sim.policies.scores import BUILTIN_SCORES, import_callable, load_score_fn, score_batch
from sim.state import HIDDEN_COLUMNS, POLICY_UNIFORMS, Mechanism
from tests.fakes import blank_record, fake_score, make_batch, make_ledger, published_store, stub_world


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


def test_make_policy(tiny_cfg, default_yaml):
    from sim.config import load_config
    world = stub_world(tiny_cfg)
    assert make_policy(load_config(default_yaml, ["policy.name=all_on"]), world).name == "all_on"
    assert make_policy(load_config(default_yaml, ["policy.name=all_off"]), world).name == "all_off"
    with pytest.raises(NotImplementedError):
        make_policy(tiny_cfg, world)   # default policy is threshold (task T2.3)


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
