"""M3 PricingAndPromotion: base fare, voucher value, and the voucher layer of step 5.

Spec: docs/spec.md §4.3, §6. Milestone: P2 (task T2.1); budget wiring P4.

Sprint-0 contract (decisions L12): step 5 has one voucher layer for every
policy. ``start_slot`` asks the policy for its cell decision when the slot
changes, ``decide`` asks it for offers on a batch and then applies the budget in
``session_id`` order, so all policies are budgeted the same way.
``quote`` (building the batch from the session buffer: fares, quoted ETA) is
task T2.1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sim.budget import BudgetLedger, CENTS_PER_USD
from sim.config import Config
from sim.policies.base import CellDecision, OfferDecision, Policy, SessionBatch, SnapshotView


def base_fare_usd(cfg: Config, trip_min) -> np.ndarray:
    """``p_s = base_fare_usd + per_min_usd * T[pu, do, h]`` (spec §4.3), vectorized, float32."""
    trip_min = np.asarray(trip_min, dtype=np.float64)
    fare = cfg.pricing.base_fare_usd + cfg.pricing.per_min_usd * trip_min
    return fare.astype(np.float32)


def voucher_cents(cfg: Config, fare_usd) -> np.ndarray:
    """``v_s = pct_of_fare * p_s`` capped by ``max_usd``, in integer cents (int64)."""
    fare_usd = np.asarray(fare_usd, dtype=np.float64)
    value = cfg.voucher.pct_of_fare * fare_usd
    if cfg.voucher.max_usd is not None:
        value = np.minimum(value, cfg.voucher.max_usd)
    return np.rint(value * CENTS_PER_USD).astype(np.int64)


@dataclass
class VoucherOutcome:
    """What the voucher layer writes back for one batch (observed columns of docs/schema.md)."""

    decision: OfferDecision        # policy output (propensity, mechanism, score, propensity_true)
    voucher_cents: np.ndarray      # int64 [n], 0 when not granted
    arm: np.ndarray                # int8 [n], 1 = voucher granted
    budget_blocked: np.ndarray     # bool [n], offered but the period budget was exhausted
    budget_period: np.ndarray      # int16 [n]
    promo_on_cell: np.ndarray      # bool [n]
    cell_propensity: np.ndarray    # float32 [n]
    slack_hat: np.ndarray          # float32 [n]

    def __len__(self) -> int:
        return len(self.arm)


class VoucherLayer:
    """The single seam between the engine and the policy (decisions L12)."""

    def __init__(self, cfg: Config, policy: Policy, ledger: BudgetLedger, n_cells: int) -> None:
        self.cfg = cfg
        self.policy = policy
        self.ledger = ledger
        self.n_cells = int(n_cells)
        self.cell_dec: CellDecision | None = None

    def start_slot(self, slot: int, snapshots: SnapshotView) -> CellDecision:
        """Called by the engine when the slot changes (before step 5 of its first tick)."""
        dec = self.policy.cell_state(slot, snapshots)
        if dec.n_cells != self.n_cells or dec.slot != slot:
            raise ValueError("policy returned a CellDecision for the wrong slot or grid")
        self.cell_dec = dec
        return dec

    def decide(self, batch: SessionBatch) -> VoucherOutcome:
        """Policy offers, then budget in ``session_id`` order (spec §4.3)."""
        if self.cell_dec is None:
            raise RuntimeError("start_slot must be called before decide")
        n = len(batch)
        dec = self.policy.offer(batch, self.cell_dec, self.ledger)
        if len(dec) != n:
            raise ValueError("policy returned an OfferDecision of the wrong length")
        cents = voucher_cents(self.cfg, batch.quoted_fare_usd)
        granted = np.zeros(n, dtype=np.int64)
        blocked = np.zeros(n, dtype=bool)
        periods = np.zeros(n, dtype=np.int16)
        for i in np.argsort(batch.session_id, kind="stable"):
            periods[i] = self.ledger.period_of(float(batch.open_time_s[i]))
            if not dec.offer[i]:
                continue
            c = int(cents[i])
            if c > 0 and not self.ledger.reserve(int(batch.session_id[i]), float(batch.open_time_s[i]), c):
                blocked[i] = True
                continue
            granted[i] = c
        arm = (dec.offer & ~blocked).astype(np.int8)
        cd = self.cell_dec
        return VoucherOutcome(
            decision=dec,
            voucher_cents=granted,
            arm=arm,
            budget_blocked=blocked,
            budget_period=periods,
            promo_on_cell=cd.promo_on[batch.pu_cell],
            cell_propensity=cd.cell_propensity[batch.pu_cell],
            slack_hat=cd.s_hat[batch.pu_cell],
        )

    def quote(self, ctx, t: float) -> None:
        """Engine step 5: fares and quoted ETA for the sessions of this tick, then ``decide``.

        Task T2.1. The Sprint-0 stub only handles ticks without new sessions.
        """
        start, stop = ctx.tick_sessions
        if stop > start:
            raise NotImplementedError("pricing.quote: task T2.1")
