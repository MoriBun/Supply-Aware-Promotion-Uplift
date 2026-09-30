"""M9 Repositioning: static-weight moves of long-idle drivers; never reads demand or snapshots.

Spec: docs/spec.md §4.9; hard rule 5. Milestone: P2 (task H2.3).

Contract: ``step`` uses only ``ctx.world.cell_weight``, ``ctx.world.space`` and
the DRIVER stream keyed by ``(driver_id, reposition_count)``. It must not touch
``ctx.monitor``, ``ctx.sessions`` or ``ctx.orders`` (docs/tests.md, M9).
"""

from __future__ import annotations

from sim.state import SimContext


def step(ctx: SimContext, t: float) -> None:
    """Engine step 9. Sprint-0 stub."""
    return None
