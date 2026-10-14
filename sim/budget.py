"""Voucher budget ledger (spec §4.3, decisions L11, T-03).

Money is kept in integer cents so the invariant ``spent + committed + reserved
<= B`` is exact. The ledger is keyed by ``session_id``; every reservation belongs
to the budget period of the session's ``open_time`` and stays there when the
order ends later (cool-down included). Period -1 is the warm-up, with budget
``B * warmup / period``. There is no reset at midnight: each period has its own
counters and the same B, so a new period simply starts with a full budget.

State machine of one session: RESERVED (voucher offered, step 5) -> COMMITTED
(rider booked, step 6) -> SPENT (order Completed, step 1); RESERVED or COMMITTED
-> RELEASED (rider did not book / order Abandoned or Cancelled / Truncated).
"""

from __future__ import annotations

import enum
import math

import numpy as np

from sim.config import Config

CENTS_PER_USD = 100


def resolve_budget_usd(cfg: Config, pilot_spent_by_period_usd=None) -> float:
    """Budget B in USD for this configuration (spec §4.3).

    ``budget.mode = fixed`` returns ``budget.fixed_usd``. ``fraction_of_all_on``
    returns ``fraction`` times the mean voucher spend per budget period of the
    all_on pilot (warm-up excluded), passed as ``RunResult.spent_by_period_usd``.
    """
    b = cfg.budget
    if b.mode == "fixed":
        return float(b.fixed_usd)
    if pilot_spent_by_period_usd is None:
        raise ValueError("budget.mode = fraction_of_all_on needs the pilot's spent_by_period_usd")
    spent = np.asarray(pilot_spent_by_period_usd, dtype=np.float64)
    if spent.size == 0:
        raise ValueError("pilot spent_by_period_usd is empty")
    return float(b.fraction * spent.mean())


def usd_to_cents(usd: float) -> int:
    return int(round(float(usd) * CENTS_PER_USD))


def cents_to_usd(cents: int) -> float:
    return float(cents) / CENTS_PER_USD


class LedgerState(enum.IntEnum):
    RESERVED = 1
    COMMITTED = 2
    SPENT = 3
    RELEASED = 4


class BudgetLedger:
    """Per-period ledger. Always tracks totals; blocks only when ``enforce`` is true."""

    WARMUP_PERIOD = -1

    def __init__(self, *, enforce: bool, budget_cents: int | None, window_start_s: float,
                 period_s: float, n_periods: int, warmup_s: float) -> None:
        if enforce and budget_cents is None:
            raise ValueError("budget.enforce is true but no budget B was given")
        if period_s <= 0 or n_periods < 1:
            raise ValueError("period_s must be > 0 and n_periods >= 1")
        if warmup_s < 0:
            raise ValueError("warmup_s must be >= 0")
        self.enforce = bool(enforce)
        self.budget_cents = None if budget_cents is None else int(budget_cents)
        self.window_start_s = float(window_start_s)
        self.period_s = float(period_s)
        self.n_periods = int(n_periods)
        self.warmup_s = float(warmup_s)
        # Index 0 is the warm-up period (-1); index d+1 is period d.
        size = self.n_periods + 1
        self._spent = np.zeros(size, dtype=np.int64)
        self._committed = np.zeros(size, dtype=np.int64)
        self._reserved = np.zeros(size, dtype=np.int64)
        self._limit = np.full(size, -1, dtype=np.int64)  # -1 = no limit
        if self.budget_cents is not None:
            self._limit[1:] = self.budget_cents
            self._limit[0] = math.floor(self.budget_cents * self.warmup_s / self.period_s)
        self._sessions: dict[int, tuple[int, int, int]] = {}  # sid -> (period, cents, state)

    # --- periods -----------------------------------------------------------

    def period_of(self, open_time_s: float) -> int:
        """Budget period of a session opened at ``open_time_s``; -1 during warm-up."""
        if open_time_s < self.window_start_s:
            return self.WARMUP_PERIOD
        period = int((open_time_s - self.window_start_s) // self.period_s)
        if period >= self.n_periods:
            raise ValueError(f"open_time {open_time_s} is after the last budget period")
        return period

    def _idx(self, period: int) -> int:
        if not self.WARMUP_PERIOD <= period < self.n_periods:
            raise ValueError(f"period {period} out of range")
        return period + 1

    def limit_cents(self, period: int) -> int | None:
        """Budget of a period in cents; None when the ledger has no budget."""
        v = int(self._limit[self._idx(period)])
        return None if v < 0 else v

    def totals(self, period: int) -> tuple[int, int, int]:
        """``(spent, committed, reserved)`` of a period, in cents."""
        i = self._idx(period)
        return int(self._spent[i]), int(self._committed[i]), int(self._reserved[i])

    def used_cents(self, period: int) -> int:
        return sum(self.totals(period))

    def available_cents(self, period: int) -> int | None:
        """Cents still grantable in a period; None when not enforced or no budget."""
        limit = self.limit_cents(period)
        if not self.enforce or limit is None:
            return None
        return limit - self.used_cents(period)

    def can_reserve(self, open_time_s: float, cents: int) -> bool:
        avail = self.available_cents(self.period_of(open_time_s))
        return avail is None or cents <= avail

    # --- session state machine -----------------------------------------------

    def reserve(self, session_id: int, open_time_s: float, cents: int) -> bool:
        """Reserve a voucher at quote time. Returns False (and records nothing) when blocked."""
        sid = int(session_id)
        if sid in self._sessions:
            raise ValueError(f"session {sid} already has a ledger entry")
        if cents < 0:
            raise ValueError("cents must be >= 0")
        period = self.period_of(open_time_s)
        if not self.can_reserve(open_time_s, cents):
            return False
        self._reserved[self._idx(period)] += cents
        self._sessions[sid] = (period, int(cents), int(LedgerState.RESERVED))
        return True

    def release_reserved(self, session_id: int) -> None:
        """Rider did not book (step 6)."""
        period, cents = self._transition(session_id, LedgerState.RESERVED, LedgerState.RELEASED)
        self._reserved[self._idx(period)] -= cents

    def commit(self, session_id: int) -> None:
        """Rider booked (step 6): reserved -> committed."""
        period, cents = self._transition(session_id, LedgerState.RESERVED, LedgerState.COMMITTED)
        i = self._idx(period)
        self._reserved[i] -= cents
        self._committed[i] += cents

    def release_committed(self, session_id: int) -> None:
        """Order Abandoned, Cancelled or Truncated: committed -> released."""
        period, cents = self._transition(session_id, LedgerState.COMMITTED, LedgerState.RELEASED)
        self._committed[self._idx(period)] -= cents

    def settle(self, session_id: int) -> None:
        """Order Completed (step 1): committed -> spent."""
        period, cents = self._transition(session_id, LedgerState.COMMITTED, LedgerState.SPENT)
        i = self._idx(period)
        self._committed[i] -= cents
        self._spent[i] += cents

    def _transition(self, session_id: int, expected: LedgerState, new: LedgerState) -> tuple[int, int]:
        sid = int(session_id)
        try:
            period, cents, state = self._sessions[sid]
        except KeyError:
            raise KeyError(f"session {sid} has no ledger entry") from None
        if state != expected:
            raise ValueError(f"session {sid}: expected {expected.name}, is {LedgerState(state).name}")
        self._sessions[sid] = (period, cents, int(new))
        return period, cents

    def entry(self, session_id: int) -> tuple[int, int, LedgerState] | None:
        """``(period, cents, state)`` of a session, or None if it never held a voucher."""
        e = self._sessions.get(int(session_id))
        return None if e is None else (e[0], e[1], LedgerState(e[2]))

    # --- reporting -----------------------------------------------------------

    def check_invariant(self) -> None:
        """Raise AssertionError if any period exceeds its budget (hard rule 8) or a total went negative."""
        if (self._reserved < 0).any() or (self._committed < 0).any() or (self._spent < 0).any():
            raise AssertionError("negative spent/committed/reserved total")
        if not self.enforce:
            return
        used = self._spent + self._committed + self._reserved
        bad = (self._limit >= 0) & (used > self._limit)
        if bad.any():
            p = int(np.flatnonzero(bad)[0]) - 1
            raise AssertionError(f"budget invariant violated in period {p}: used {used[p + 1]} > {self._limit[p + 1]}")

    def spent_by_period_usd(self) -> np.ndarray:
        """Spent voucher value of periods 0..n_periods-1 in USD (warm-up excluded)."""
        return self._spent[1:] / CENTS_PER_USD

    def warmup_spent_usd(self) -> float:
        return cents_to_usd(int(self._spent[0]))

    @property
    def n_entries(self) -> int:
        return len(self._sessions)
