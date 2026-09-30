"""M3: base fare, voucher value, BudgetLedger (spec §4.3, decisions T-03) and the voucher layer (L12)."""

import numpy as np
import pytest

from sim.budget import BudgetLedger, LedgerState, cents_to_usd, usd_to_cents
from sim.config import load_config
from sim.policies.base import SnapshotStore, SnapshotView
from sim.policies.fixed import FixedPolicy
from sim.pricing import VoucherLayer, base_fare_usd, voucher_cents
from tests.fakes import make_batch, make_ledger


# --- prices (docs/tests.md M3: p_s = a_f + b_f*T; v_s = 0,2*p_s) ---------------------


def test_base_fare_formula(default_yaml):
    cfg = load_config(default_yaml)  # base 3.0, per_min 1.4
    fare = base_fare_usd(cfg, [0.0, 10.0])
    assert fare.dtype == np.float32
    np.testing.assert_allclose(fare, [3.0, 17.0])


def test_voucher_cents_pct_and_cap(default_yaml):
    cfg = load_config(default_yaml)   # 20%, no cap
    np.testing.assert_array_equal(voucher_cents(cfg, [17.0, 0.0, 19.125]), [340, 0, 382])
    assert voucher_cents(cfg, [17.0]).dtype == np.int64
    capped = load_config(default_yaml, ["voucher.max_usd=2.0"])
    np.testing.assert_array_equal(voucher_cents(capped, [17.0, 5.0]), [200, 100])


def test_money_helpers():
    assert usd_to_cents(19.125) == 1912 or usd_to_cents(19.125) == 1913  # banker's vs half-up; both exact cents
    assert usd_to_cents(3.40) == 340 and cents_to_usd(340) == 3.4


# --- ledger periods (decisions T-03) ---------------------------------------------------


def test_period_anchored_at_window_start():
    led = make_ledger(window_start_s=3600.0, period_s=86400.0, n_periods=2, warmup_s=3600.0)
    assert led.period_of(0.0) == -1 and led.period_of(3599.0) == -1
    assert led.period_of(3600.0) == 0 and led.period_of(3600.0 + 86399.0) == 0
    assert led.period_of(3600.0 + 86400.0) == 1
    with pytest.raises(ValueError):
        led.period_of(3600.0 + 2 * 86400.0)


def test_warmup_budget_is_prorated():
    led = make_ledger(budget_usd=100.0, period_s=86400.0, warmup_s=3600.0)
    assert led.limit_cents(0) == 10000
    assert led.limit_cents(-1) == 10000 // 24     # floor(B * warmup / period)
    led = make_ledger(budget_usd=None, enforce=False)
    assert led.limit_cents(0) is None and led.available_cents(0) is None


def test_enforce_requires_budget():
    with pytest.raises(ValueError):
        make_ledger(enforce=True, budget_usd=None)
    make_ledger(enforce=False, budget_usd=None)  # fine


# --- ledger state machine ----------------------------------------------------------------


def test_reserve_commit_settle_flow():
    led = make_ledger(budget_usd=10.0)
    assert led.reserve(1, 3600.0, 300)
    assert led.totals(0) == (0, 0, 300) and led.entry(1) == (0, 300, LedgerState.RESERVED)
    led.commit(1)
    assert led.totals(0) == (0, 300, 0)
    led.settle(1)
    assert led.totals(0) == (300, 0, 0) and led.entry(1)[2] == LedgerState.SPENT
    np.testing.assert_allclose(led.spent_by_period_usd(), [3.0])
    assert led.warmup_spent_usd() == 0.0
    led.check_invariant()


def test_release_paths():
    led = make_ledger(budget_usd=10.0)
    led.reserve(1, 3600.0, 300)
    led.release_reserved(1)                        # rider did not book
    assert led.totals(0) == (0, 0, 0) and led.entry(1)[2] == LedgerState.RELEASED
    led.reserve(2, 3600.0, 400)
    led.commit(2)
    led.release_committed(2)                       # abandoned / cancelled / truncated
    assert led.totals(0) == (0, 0, 0)
    assert led.entry(99) is None and led.n_entries == 2


def test_invalid_transitions_raise():
    led = make_ledger(budget_usd=10.0)
    led.reserve(1, 3600.0, 100)
    with pytest.raises(ValueError):
        led.reserve(1, 3600.0, 100)                # duplicate
    with pytest.raises(ValueError):
        led.settle(1)                              # not committed yet
    with pytest.raises(KeyError):
        led.commit(2)                              # unknown session
    with pytest.raises(ValueError):
        led.reserve(3, 3600.0, -1)


def test_blocking_when_enforced():
    led = make_ledger(budget_usd=5.0)              # 500 cents
    assert led.reserve(1, 3600.0, 300)
    assert led.can_reserve(3600.0, 200) and not led.can_reserve(3600.0, 201)
    assert not led.reserve(2, 3600.0, 201)         # blocked, nothing recorded
    assert led.entry(2) is None and led.totals(0) == (0, 0, 300)
    assert led.reserve(3, 3600.0, 200)             # exactly fills the budget
    assert led.available_cents(0) == 0
    led.check_invariant()


def test_no_blocking_when_not_enforced_but_totals_tracked():
    led = make_ledger(enforce=False, budget_usd=1.0)
    assert led.reserve(1, 3600.0, 10_000)          # far above B, still granted
    assert led.totals(0) == (0, 0, 10_000)
    led.check_invariant()                          # no-op when not enforced


def test_warmup_period_has_its_own_ledger():
    led = make_ledger(budget_usd=100.0, warmup_s=3600.0)      # warm-up limit 416 cents
    assert led.reserve(1, 0.0, 400)
    assert not led.reserve(2, 10.0, 100)                       # warm-up exhausted
    assert led.reserve(3, 3600.0, 9000)                        # period 0 untouched
    led.commit(1)
    led.settle(1)
    assert led.warmup_spent_usd() == 4.0
    np.testing.assert_allclose(led.spent_by_period_usd(), [0.0])


def test_invariant_detects_corruption():
    led = make_ledger(budget_usd=1.0)
    led.reserve(1, 3600.0, 100)
    led._reserved[1] += 1   # simulate a bug
    with pytest.raises(AssertionError):
        led.check_invariant()


# --- voucher layer (decisions L12) ----------------------------------------------------------


def _layer(cfg, on, ledger, n_cells=7):
    layer = VoucherLayer(cfg, FixedPolicy(on, n_cells), ledger, n_cells)
    layer.start_slot(4, SnapshotView(SnapshotStore(n_cells, 96), 4))
    return layer


def test_layer_requires_start_slot(default_yaml):
    layer = VoucherLayer(load_config(default_yaml), FixedPolicy(True, 7), make_ledger(), 7)
    with pytest.raises(RuntimeError):
        layer.decide(make_batch(2, 7))


def test_layer_all_off_offers_nothing(default_yaml):
    led = make_ledger(budget_usd=100.0)
    out = _layer(load_config(default_yaml), False, led).decide(make_batch(5, 7))
    assert not out.arm.any() and not out.budget_blocked.any() and (out.voucher_cents == 0).all()
    assert not out.promo_on_cell.any() and (out.cell_propensity == 0.0).all()
    assert led.n_entries == 0 and (out.budget_period == 0).all()


def test_layer_all_on_within_budget(default_yaml):
    led = make_ledger(budget_usd=100.0)
    out = _layer(load_config(default_yaml), True, led).decide(make_batch(5, 7, fare_usd=20.0))
    assert out.arm.tolist() == [1] * 5 and (out.voucher_cents == 400).all()
    assert out.decision.offer.all() and out.promo_on_cell.all() and np.isnan(out.slack_hat).all()
    assert led.totals(0) == (0, 0, 2000)


def test_layer_applies_budget_in_session_id_order(default_yaml):
    # Budget for exactly 2 vouchers of 4 USD; ids given in reverse so the smallest ids must win.
    led = make_ledger(budget_usd=8.0)
    batch = make_batch(4, 7, fare_usd=20.0, session_ids=[40, 30, 20, 10])
    out = _layer(load_config(default_yaml), True, led).decide(batch)
    assert out.arm.tolist() == [0, 0, 1, 1]
    assert out.budget_blocked.tolist() == [True, True, False, False]
    assert out.voucher_cents.tolist() == [0, 0, 400, 400]
    assert led.entry(10)[2] == LedgerState.RESERVED and led.entry(40) is None
    led.check_invariant()


def test_layer_rejects_wrong_slot_or_length(default_yaml):
    cfg = load_config(default_yaml)
    layer = VoucherLayer(cfg, FixedPolicy(True, 7), make_ledger(), n_cells=5)
    with pytest.raises(ValueError):
        layer.start_slot(4, SnapshotView(SnapshotStore(7, 96), 4))   # policy built for 7 cells, layer for 5
