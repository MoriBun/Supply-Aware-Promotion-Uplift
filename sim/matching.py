"""M5 Matching: FIFO matching, same cell first, then expanding rings up to max_pickup_eta_min.

Spec: docs/spec.md §4.5. Milestone: P2 (task H2.1).

Contract: ``match`` moves Waiting orders to Matched (columns of step "match"),
drivers to EN_ROUTE, and keeps ``ctx.cells`` (idle / enroute / waiting) and
``ctx.slot_counters`` (n_matched, pickup ETA sums) consistent.
"""

from __future__ import annotations

from sim.state import SimContext


def match(ctx: SimContext, t: float) -> None:
    """Engine step 7. Sprint-0 stub."""
    return None
