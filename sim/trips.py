"""M6 TripExecution: pickup and dropoff events, payments.

Spec: docs/spec.md §4.6. Milestone: P2 (task H2.2).

Contract: ``advance`` processes drivers whose ``busy_until <= t``: pickups
(EN_ROUTE -> ON_TRIP, order OnTrip), dropoffs (ON_TRIP -> IDLE at the dropoff
cell, order Completed with payments, ``ctx.ledger.settle`` when the order held a
voucher, slot counters n_completed / voucher_spent) and arrivals of
repositioning drivers.
"""

from __future__ import annotations

from sim.state import SimContext


def advance(ctx: SimContext, t: float) -> None:
    """Engine step 1. Sprint-0 stub."""
    return None
