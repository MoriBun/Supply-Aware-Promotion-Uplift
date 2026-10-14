"""M3 PricingAndPromotion: base fare, voucher value, and the voucher layer of step 5.

Spec: docs/spec.md §4.3, §6. Milestone: P2 (task T2.1).

Decisions L12: step 5 has one voucher layer for every policy. ``start_slot``
asks the policy for its cell decision when the slot changes; ``quote`` prices
the sessions of the tick (fare from ``T[pu, do, h]``, quoted ETA from the M5
search rule without holding a driver), builds the observed ``SessionBatch``,
and ``decide`` asks the policy for offers and then applies the budget in
``session_id`` order, so all policies are budgeted the same way. The outcome is
written back to the session columns of step "quote" (docs/schema.md).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sim import experiment
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
        """Engine step 5: price this tick's sessions, ask the policy, apply the budget, write the columns."""
        start, stop = ctx.tick_sessions
        if stop <= start:
            return
        if self.cell_dec is None:
            raise RuntimeError("start_slot must be called before quote")
        s, space, riders = ctx.sessions, ctx.world.space, ctx.world.riders
        rows = slice(start, stop)
        pu, do, hour = s.pu_cell[rows], s.do_cell[rows], s.hour[rows]

        fare = base_fare_usd(self.cfg, space.T[pu, do, hour])
        eta, no_supply = quote_eta_by_cell(space, pu, int(hour[0]), ctx.cells.idle)
        s.quoted_fare_usd[rows] = fare
        s.quoted_eta_min[rows] = eta
        s.no_supply[rows] = no_supply

        rider = s.rider_id[rows]
        batch = SessionBatch(
            session_id=s.session_id[rows], rider_id=rider, open_time_s=s.open_time_s[rows],
            day=s.day[rows], hour=hour, slot=s.slot[rows], slot_of_day=s.slot_of_day[rows],
            pu_cell=pu, do_cell=do,
            x_freq=riders.x_freq[rider], x_tenure=riders.x_tenure[rider], x_segment=riders.x_segment[rider],
            quoted_fare_usd=fare, quoted_eta_min=eta, no_supply=no_supply,
            u_target=s.u_target[rows], u_explore=s.u_explore[rows], u_explore_arm=s.u_explore_arm[rows],
            u_score=s.u_score[rows],
        )
        out = self.decide(batch)
        cd, dec = self.cell_dec, out.decision

        s.voucher_cents[rows] = out.voucher_cents
        s.voucher_value_usd[rows] = (out.voucher_cents / CENTS_PER_USD).astype(np.float32)
        s.arm[rows] = out.arm
        s.budget_blocked[rows] = out.budget_blocked
        s.budget_period[rows] = out.budget_period
        s.promo_on_cell[rows] = out.promo_on_cell
        s.cell_propensity[rows] = out.cell_propensity
        s.slack_hat[rows] = out.slack_hat
        s.assign_mechanism[rows] = dec.mechanism
        s.propensity[rows] = dec.propensity
        s.score[rows] = dec.score
        s.propensity_true[rows] = dec.propensity_true
        s.cluster_id[rows] = cd.cluster_id[pu]
        s.block[rows] = cd.block
        s.in_burnin[rows] = experiment.in_burnin(self.cfg, s.open_time_s[rows]) if cd.block >= 0 else False
        ctx.monitor.on_offers(ctx.slot_counters, pu[out.arm == 1])


def quote_eta_by_cell(space, pu_cell: np.ndarray, hour: int, idle_count: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Quoted ETA (float32 [n]) and ``no_supply`` (bool [n]) of sessions, one M5 search per distinct cell."""
    n = len(pu_cell)
    eta = np.empty(n, dtype=np.float32)
    no_supply = np.empty(n, dtype=bool)
    for cell in np.unique(pu_cell):
        e, ns = space.quote_eta(int(cell), hour, idle_count)
        mask = pu_cell == cell
        eta[mask] = e
        no_supply[mask] = ns
    return eta, no_supply
