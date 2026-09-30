"""M4 RiderChoice: logit booking decision and hidden ground-truth probabilities.

Spec: docs/spec.md §4.4. Milestone: P1 (task H1.3).

Contract: ``decide`` reads the rows ``ctx.tick_sessions`` of ``ctx.sessions``,
writes ``requested`` and the hidden ``p_request_*`` columns, creates one order
per booking (``ctx.orders``, columns of step "decide"), sets ``order_idx`` on
the session, and calls ``ctx.ledger.commit`` / ``release_reserved`` for sessions
with ``voucher_cents > 0``.
"""

from __future__ import annotations

from sim.state import SimContext


def decide(ctx: SimContext, t: float) -> None:
    """Engine step 6. Sprint-0 stub."""
    return None
