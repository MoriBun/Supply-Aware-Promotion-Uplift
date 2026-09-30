"""Fakes and builders shared by the tests (docs/phan_cong.md, task T1.3).

Everything here is deterministic and free of randomness, so a test that uses a
fake never depends on the other person's module.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from sim.budget import BudgetLedger, usd_to_cents
from sim.policies.base import SNAPSHOT_FIELDS, SessionBatch, SnapshotStore
from sim.policies.fixed import FixedPolicy
from sim.population import World, build_world
from sim.rng import Rng
from sim.state import SimContext

NAN = float("nan")


class ForbiddenAccess:
    """Stand-in for a ``SimContext`` field a step must not touch (docs/tests.md, M9; hard rule 5).

    Any attribute access raises, so ``reposition.step`` reading ``ctx.monitor``
    fails loudly in a test.
    """

    def __init__(self, name: str) -> None:
        self._name = name

    def __getattr__(self, item: str) -> None:
        raise AssertionError(f"ctx.{self._name} must not be used here (accessed .{item})")


def make_context(cfg, *, on: bool = False, budget_usd: float | None = None,
                 enforce_budget: bool | None = False) -> SimContext:
    """A fresh ``SimContext`` on the stub world with a FixedPolicy; use it to call one step in a test."""
    from sim.engine import build_context  # local import: engine imports every module

    world = stub_world(cfg)
    return build_context(cfg, world, FixedPolicy(on, world.n_cells), Rng.from_config(cfg),
                         budget_usd=budget_usd, enforce_budget=enforce_budget)


def with_forbidden(ctx: SimContext, *fields: str) -> SimContext:
    """Copy of ``ctx`` where the named fields raise on any use."""
    return dataclasses.replace(ctx, **{f: ForbiddenAccess(f) for f in fields})


def make_batch(n: int, n_cells: int, *, fare_usd: float = 20.0, open_time_s: float = 3600.0,
               slot: int = 4, session_ids=None, pu_cell=None) -> SessionBatch:
    """A batch of ``n`` quoted sessions with simple deterministic values."""
    ids = np.arange(n, dtype=np.int64) if session_ids is None else np.asarray(session_ids, dtype=np.int64)
    pu = (np.arange(n) % n_cells).astype(np.int16) if pu_cell is None else np.asarray(pu_cell, dtype=np.int16)
    u = (np.arange(n, dtype=np.float64) + 0.5) / max(n, 1)
    return SessionBatch(
        session_id=ids,
        rider_id=np.arange(n, dtype=np.int32),
        open_time_s=np.full(n, float(open_time_s)),
        day=np.zeros(n, dtype=np.int16),
        hour=np.full(n, int(open_time_s // 3600) % 24, dtype=np.int16),
        slot=np.full(n, slot, dtype=np.int16),
        slot_of_day=np.full(n, slot, dtype=np.int16),
        pu_cell=pu,
        do_cell=((np.arange(n) + 1) % n_cells).astype(np.int16),
        x_freq=np.ones(n, dtype=np.float32),
        x_tenure=np.full(n, 12.0, dtype=np.float32),
        x_segment=np.zeros(n, dtype=np.int8),
        quoted_fare_usd=np.full(n, fare_usd, dtype=np.float32),
        quoted_eta_min=np.full(n, 3.0, dtype=np.float32),
        no_supply=np.zeros(n, dtype=bool),
        u_target=u.copy(), u_explore=u.copy(), u_explore_arm=u.copy(), u_score=u.copy(),
    )


def stub_world(cfg) -> World:
    return build_world(cfg, Rng.from_config(cfg))


def make_ledger(*, enforce: bool = True, budget_usd: float | None = 100.0, window_start_s: float = 3600.0,
                period_s: float = 86400.0, n_periods: int = 1, warmup_s: float = 3600.0) -> BudgetLedger:
    return BudgetLedger(
        enforce=enforce,
        budget_cents=None if budget_usd is None else usd_to_cents(budget_usd),
        window_start_s=window_start_s, period_s=period_s, n_periods=n_periods, warmup_s=warmup_s,
    )


def blank_record(n_cells: int, slot: int, **overrides) -> dict[str, np.ndarray]:
    """A snapshot record with every field of docs/schema.md; numbers default to slot + 0.1*cell."""
    base = slot + 0.1 * np.arange(n_cells)
    rec: dict[str, np.ndarray] = {}
    for f in SNAPSHOT_FIELDS:
        if f == "cell":
            rec[f] = np.arange(n_cells, dtype=np.int16)
        elif f in ("promo_on", "in_burnin"):
            rec[f] = np.zeros(n_cells, dtype=bool)
        elif f in ("slot", "block"):
            rec[f] = np.full(n_cells, slot, dtype=np.int32)
        elif f in ("day", "slot_of_day", "hour", "cluster_id", "assign_mechanism_cell"):
            rec[f] = np.zeros(n_cells, dtype=np.int16)
        elif f.startswith("n_"):
            rec[f] = np.zeros(n_cells, dtype=np.int32)
        else:
            rec[f] = base.astype(np.float64)
    for k, v in overrides.items():
        rec[k] = np.asarray(v)
    return rec


def published_store(n_cells: int, n_slots: int, slots_per_day: int = 96) -> SnapshotStore:
    """A store with slots 0..n_slots-1 published (values from :func:`blank_record`)."""
    store = SnapshotStore(n_cells, slots_per_day)
    for s in range(n_slots):
        store.publish(s, blank_record(n_cells, s))
    return store
