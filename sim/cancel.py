"""M7 Cancellation: abandon after max_wait, en-route cancellation by cumulative hazard.

Spec: docs/spec.md §4.7. Milestone: P2 (task H2.2).

Contract: both steps move orders to a terminal status, release the driver
(en-route case), call ``ctx.ledger.release_committed`` when the order held a
voucher, and update ``ctx.cells`` / ``ctx.slot_counters``.
"""

from __future__ import annotations

from sim.state import SimContext


def expire_waiting(ctx: SimContext, t: float) -> None:
    """Engine step 3: Waiting orders older than max_wait become Abandoned. Sprint-0 stub."""
    return None


def en_route(ctx: SimContext, t: float) -> None:
    """Engine step 8: rider cancels while the driver is en route. Sprint-0 stub."""
    return None
