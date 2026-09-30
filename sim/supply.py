"""M8 SupplyModel: periodic shifts; drivers leave only when idle.

Spec: docs/spec.md §4.8; decisions T-02, T-08. Milestone: P1 (task H1.4).

Contract: ``init_drivers`` sets the t = 0 state (drivers whose periodic shift
covers t = 0 start IDLE at their origin cell; ``shift_mode = always_on`` puts
every driver online for the whole run). ``update`` handles shift starts and
ends each tick and keeps ``ctx.cells.idle`` consistent.
"""

from __future__ import annotations

from sim.state import SimContext


def init_drivers(ctx: SimContext) -> None:
    """Called once before the first tick. Sprint-0 stub: everyone stays OFFLINE."""
    return None


def update(ctx: SimContext, t: float) -> None:
    """Engine step 2. Sprint-0 stub."""
    return None
