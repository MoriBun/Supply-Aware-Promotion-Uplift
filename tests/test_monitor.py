"""M11 monitor mechanics (spec §4.11; decisions T-09, T-10, T-15) and the no-look-ahead view."""

import numpy as np
import pytest

from sim.monitor import MarketMonitor
from sim.policies.base import SNAPSHOT_FIELDS, CellDecision, LookAheadError
from sim.state import CellCounters, Clock, Mechanism, SlotCounters


@pytest.fixture
def monitor(tiny_cfg):
    clock = Clock.from_config(tiny_cfg)
    return MarketMonitor(tiny_cfg, clock, n_cells=7), clock


def test_accumulate_and_publish_means(monitor):
    mon, clock = monitor
    cells, acc = CellCounters(7), SlotCounters(7)
    cells.idle[:] = 2
    cells.enroute[0] = 1          # cell 0: I=2, E=1 -> slack 2
    cells.ontrip[1] = 3           # cell 1: I=2, E=0 -> slack inf; utilization 3/5
    cells.waiting[2] = 4
    for _ in range(3):
        mon.accumulate(cells, acc)
    acc.n_matched[0] = 2
    acc.sum_pickup_eta_min[0] = 9.0
    acc.n_pickup_eta[0] = 2
    acc.voucher_spent_cents[3] = 250
    cd = CellDecision.blank(0, 7, promo_on=True, mechanism=Mechanism.FIXED)
    rec = mon.publish(0, clock.slot_s, acc, cd)
    assert set(rec) == set(SNAPSHOT_FIELDS)
    assert (rec["idle_avg"] == 2).all() and rec["enroute_avg"][0] == 1 and rec["waiting_avg"][2] == 4
    assert rec["slack"][0] == 2.0 and np.isinf(rec["slack"][1])
    assert rec["utilization"][0] == pytest.approx(1 / 3) and rec["utilization"][1] == pytest.approx(3 / 5)
    assert rec["mean_pickup_eta_min"][0] == 4.5 and np.isnan(rec["mean_pickup_eta_min"][1])
    assert rec["voucher_spent_usd"][3] == np.float32(2.5) and rec["n_matched"][0] == 2
    assert rec["promo_on"].all() and (rec["assign_mechanism_cell"] == int(Mechanism.FIXED)).all()
    assert rec["block"][0] == -1 and not rec["in_burnin"].any()
    assert np.isnan(rec["slack_lag_slot"]).all() and np.isnan(rec["slack_lag_day"]).all()
    assert (rec["published_at_s"] == clock.slot_s).all() and (rec["slot"] == 0).all() and (rec["cell"] == np.arange(7)).all()
    assert acc.n_ticks == 0 and (acc.sum_idle == 0).all()      # reset after publish


def test_lags_and_time_fields(monitor):
    mon, clock = monitor
    cells, acc = CellCounters(7), SlotCounters(7)
    cells.idle[:] = 1
    cells.enroute[:] = 1
    mon.accumulate(cells, acc)
    mon.publish(0, clock.slot_s, acc, None)
    cells.idle[:] = 3
    mon.accumulate(cells, acc)
    rec = mon.publish(1, 2 * clock.slot_s, acc, None)
    assert (rec["slack"] == 3.0).all() and (rec["slack_lag_slot"] == 1.0).all()
    assert np.isnan(rec["slack_lag_day"]).all()
    assert not rec["promo_on"].any() and np.isnan(rec["cell_propensity"]).all() and (rec["cluster_id"] == -1).all()
    # slot 5 of day 0 starts at 75 min -> hour 1, slot_of_day 5
    for s in range(2, 6):
        mon.accumulate(cells, acc)
        mon.publish(s, (s + 1) * clock.slot_s, acc, None)
    rec5 = mon.store.get("hour", 5)
    assert rec5[0] == 1 and mon.store.get("slot_of_day", 5)[0] == 5 and mon.store.get("day", 5)[0] == 0


def test_slack_lag_day_after_one_day(monitor):
    mon, clock = monitor
    cells, acc = CellCounters(7), SlotCounters(7)
    cells.enroute[:] = 1
    for s in range(clock.slots_per_day + 1):        # 97 slots
        cells.idle[:] = s
        mon.accumulate(cells, acc)
        mon.publish(s, (s + 1) * clock.slot_s, acc, None)
    last = clock.slots_per_day
    assert (mon.store.get("slack_lag_day", last) == 0.0).all()        # slot 0 had I = 0
    assert (mon.store.get("slack_lag_slot", last) == last - 1).all()
    assert mon.store.get("day", last)[0] == 1 and mon.store.get("slot_of_day", last)[0] == 0


def test_publish_without_ticks_gives_nan(monitor):
    mon, clock = monitor
    rec = mon.publish(0, clock.slot_s, SlotCounters(7), None)
    assert np.isnan(rec["idle_avg"]).all() and np.isnan(rec["slack"]).all() and np.isnan(rec["utilization"]).all()


def test_view_from_monitor_refuses_look_ahead(monitor):
    mon, clock = monitor
    cells, acc = CellCounters(7), SlotCounters(7)
    mon.accumulate(cells, acc)
    mon.publish(0, clock.slot_s, acc, None)
    view = mon.view(1)
    assert view.get("slack", 0).shape == (7,)
    with pytest.raises(LookAheadError):
        view.get("slack", 1)
    with pytest.raises(LookAheadError):
        mon.view(0).get("slack", 0)
