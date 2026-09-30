"""M11 MarketMonitor: per-(cell, slot) I, E, O, W, slack, utilization; publishes snapshots after each slot.

Spec: docs/spec.md §4.11; decisions T-09, T-10, T-15. Milestone: P1 (task T1.2).

Sprint-0 contract: ``accumulate`` every tick from the live counters,
``publish`` at the end of a slot (record fields = docs/schema.md), ``view``
for the policy of a slot. Values are computed from the per-slot accumulators
that the other modules fill; T1.2 adds tests and the remaining counters.
"""

from __future__ import annotations

import numpy as np

from sim.config import Config
from sim.policies.base import CellDecision, SnapshotStore, SnapshotView
from sim.state import CellCounters, Clock, SlotCounters

NAN = float("nan")


class MarketMonitor:
    def __init__(self, cfg: Config, clock: Clock, n_cells: int) -> None:
        self.cfg = cfg
        self.clock = clock
        self.n_cells = int(n_cells)
        self.store = SnapshotStore(n_cells, clock.slots_per_day)

    def accumulate(self, cells: CellCounters, acc: SlotCounters) -> None:
        """Step 10 of every tick: add the live per-cell counts to the slot sums."""
        acc.sum_idle += cells.idle
        acc.sum_enroute += cells.enroute
        acc.sum_ontrip += cells.ontrip
        acc.sum_waiting += cells.waiting
        acc.n_ticks += 1

    def publish(self, slot: int, published_at_s: float, acc: SlotCounters,
                cell_dec: CellDecision | None) -> dict[str, np.ndarray]:
        """Close slot ``slot``: compute the snapshot, store it, reset the accumulators."""
        n = self.n_cells
        t_start = slot * self.clock.slot_s
        full = lambda v, dt: np.full(n, v, dtype=dt)  # noqa: E731
        with np.errstate(divide="ignore", invalid="ignore"):
            ticks = acc.n_ticks if acc.n_ticks > 0 else NAN
            I = (acc.sum_idle / ticks).astype(np.float32)
            E = (acc.sum_enroute / ticks).astype(np.float32)
            O = (acc.sum_ontrip / ticks).astype(np.float32)
            W = (acc.sum_waiting / ticks).astype(np.float32)
            # slack = I/E, +inf when E = 0 (spec §4.11, decisions T-10)
            slack = np.where(E > 0, I.astype(np.float64) / E, np.inf)
            slack = np.where(np.isnan(I), NAN, slack).astype(np.float64)
            busy = E.astype(np.float64) + O
            denom = I.astype(np.float64) + busy
            utilization = np.where(denom > 0, busy / denom, NAN).astype(np.float32)  # T-09: repositioning excluded
            eta = np.where(acc.n_pickup_eta > 0, acc.sum_pickup_eta_min / acc.n_pickup_eta, NAN).astype(np.float32)
        lag_slot = self._lag("slack", slot, 1)
        lag_day = self._lag("slack", slot, self.clock.slots_per_day)
        if cell_dec is None:
            promo_on = full(False, bool)
            cell_prop = full(NAN, np.float32)
            mech = full(-1, np.int8)
            cluster = full(-1, np.int16)
            block, burnin = -1, False
        else:
            promo_on = cell_dec.promo_on.astype(bool)
            cell_prop = cell_dec.cell_propensity.astype(np.float32)
            mech = cell_dec.mechanism.astype(np.int8)
            cluster = cell_dec.cluster_id.astype(np.int16)
            block, burnin = cell_dec.block, cell_dec.in_burnin
        record = {
            "cell": np.arange(n, dtype=np.int16),
            "slot": full(slot, np.int32),
            "day": full(self.clock.day_of(t_start), np.int16),
            "slot_of_day": full(self.clock.slot_of_day(t_start), np.int16),
            "hour": full(self.clock.hour_of(t_start), np.int16),
            "idle_avg": I, "enroute_avg": E, "ontrip_avg": O, "waiting_avg": W,
            "slack": slack, "utilization": utilization, "mean_pickup_eta_min": eta,
            "n_sessions": acc.n_sessions.copy(), "n_offers": acc.n_offers.copy(),
            "n_requests": acc.n_requests.copy(), "n_matched": acc.n_matched.copy(),
            "n_completed": acc.n_completed.copy(), "n_abandoned": acc.n_abandoned.copy(),
            "n_cancelled": acc.n_cancelled.copy(),
            "voucher_spent_usd": (acc.voucher_spent_cents / 100.0).astype(np.float32),
            "promo_on": promo_on, "cell_propensity": cell_prop, "assign_mechanism_cell": mech,
            "cluster_id": cluster, "block": full(block, np.int32), "in_burnin": full(burnin, bool),
            "slack_lag_slot": lag_slot, "slack_lag_day": lag_day,
            "published_at_s": full(float(published_at_s), np.float64),
        }
        self.store.publish(slot, record)
        acc.reset()
        return record

    def _lag(self, field: str, slot: int, k: int) -> np.ndarray:
        prev = slot - k
        if self.store.has(prev):
            return self.store.get(field, prev).astype(np.float64)
        return np.full(self.n_cells, NAN, dtype=np.float64)

    def view(self, current_slot: int) -> SnapshotView:
        """View for decisions taken in ``current_slot``: only earlier slots are readable."""
        return SnapshotView(self.store, current_slot)
