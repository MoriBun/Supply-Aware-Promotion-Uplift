"""M2 DemandGenerator: Poisson sessions per (cell, tick), rider and destination choice, pre-drawn numbers.

Spec: docs/spec.md §4.2. Milestone: P1 (task H1.2).

Contract: ``spawn`` appends this tick's sessions to ``ctx.sessions`` (columns of
step "spawn" in ``state.SESSION_COLUMNS``) and sets ``ctx.tick_sessions`` to
their row range. Session ids come from ``rng.session_ids_for_tick``; the SESSION
generator of each session is consumed in ``rng.SESSION_DRAW_ORDER``.
"""

from __future__ import annotations

from sim.state import SimContext


def spawn(ctx: SimContext, t: float) -> None:
    """Engine step 4. Sprint-0 stub: spawns nothing."""
    ctx.tick_sessions = (ctx.sessions.n, ctx.sessions.n)
