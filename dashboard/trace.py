"""Traced engine loop: the ten steps of ``sim.engine.run`` plus one recorded frame per tick.

The loop below is a copy of :func:`sim.engine.run` (same step order, same
warm-up / window / cool-down rule, same aggregation through the engine's own
helpers). ``sim/engine.py`` belongs to the simulation core and the dashboard must
not change what the simulator does, so instead of adding a hook there this module
re-drives the steps and *reads* the state after each tick. The recording never
writes to the context, so the result is identical to ``engine.run``;
``tests/test_dashboard.py::test_traced_run_matches_engine`` checks that on the
tiny configuration.

What a frame holds (all per tick, after step 10):

- drivers: ``status`` (DriverStatus codes), ``cell`` (current, or target while
  moving), ``origin`` (cell left at match / reposition time), ``move_start`` (when
  the current leg began) and ``busy_until`` (when it ends), so the front end can
  interpolate a moving driver between two cell centres;
- per-cell live counters ``idle / enroute / ontrip / waiting``;
- cumulative counters: orders by status, sessions / offers / budget-blocked / requests;
- the budget ledger of the current period: ``spent, committed, reserved, limit`` (cents);
- the events of the tick (request, match, pickup, complete, abandon, cancel,
  offer, blocked) with their cells, for the pulses of the animation.

Per slot it also keeps the policy's ``CellDecision`` (``promo_on``, ``s_hat``, ...)
and, once published, the market snapshot of the slot (docs/schema.md
``market/slot_snapshots``), which is what the "cells and theta" page shows.
"""

from __future__ import annotations

import time
from collections.abc import Callable

import numpy as np

from sim import cancel, choice, demand, matching, reposition, supply, trips
from sim.budget import CENTS_PER_USD
from sim.config import Config
from sim.engine import RunResult, _aggregate, _truncate_open_orders, build_context
from sim.policies.base import CellDecision, Policy
from sim.population import World
from sim.rng import Rng
from sim.state import Clock, DriverStatus, OrderStatus, SimContext

EVENT_TYPES: tuple[str, ...] = ("request", "match", "pickup", "complete", "abandon", "cancel", "offer", "blocked")
EVENT_CODE: dict[str, int] = {name: i for i, name in enumerate(EVENT_TYPES)}

# Snapshot fields copied into the slot record once the monitor publishes the slot.
SLOT_SNAPSHOT_FIELDS: tuple[str, ...] = (
    "idle_avg", "enroute_avg", "ontrip_avg", "waiting_avg", "slack", "utilization", "mean_pickup_eta_min",
    "n_sessions", "n_offers", "n_requests", "n_matched", "n_completed", "n_abandoned", "n_cancelled",
    "voucher_spent_usd",
)

_ON_TRIP = int(DriverStatus.ON_TRIP)
_N_ORDER_STATUS = len(OrderStatus)


class Trace:
    """Frames of one traced run (lists of per-tick arrays; ``t`` is appended last, so
    ``len(trace.t)`` is the number of complete frames while a run is in progress)."""

    def __init__(self, cfg: Config, clock: Clock, n_drivers: int, n_cells: int) -> None:
        self.tick_s = int(clock.tick_s)
        self.slot_s = int(clock.slot_s)
        self.window_start_s = float(clock.window_start_s)
        self.window_end_s = float(clock.window_end_s)
        self.period_s = float(clock.period_s)
        self.n_periods = int(clock.n_periods)
        self.cooldown_max_s = float(clock.cooldown_max_s)
        self.n_drivers = int(n_drivers)
        self.n_cells = int(n_cells)
        self.budget_cents: int | None = None

        self.t: list[float] = []
        self.status: list[np.ndarray] = []
        self.cell: list[np.ndarray] = []
        self.origin: list[np.ndarray] = []
        self.move_start: list[np.ndarray] = []
        self.busy_until: list[np.ndarray] = []
        self.idle: list[np.ndarray] = []
        self.enroute: list[np.ndarray] = []
        self.ontrip: list[np.ndarray] = []
        self.waiting: list[np.ndarray] = []
        self.order_counts: list[np.ndarray] = []      # int64 [7], cumulative orders by OrderStatus code
        self.session_counts: list[np.ndarray] = []    # int64 [4]: sessions, offers (arm=1), blocked, requests
        self.ledger: list[np.ndarray] = []            # int64 [5]: period, spent, committed, reserved, limit (-1 = none)
        self.events: list[np.ndarray] = []            # int32 [m, 3]: code, cell_a, cell_b (-1 = none)
        self.slots: list[dict] = []                   # index = slot number

        self._prev_status = np.full(n_drivers, -1, dtype=np.int8)
        self._prev_cell = np.full(n_drivers, -2, dtype=np.int16)
        self._prev_busy = np.full(n_drivers, np.nan, dtype=np.float64)
        self._move_start = np.zeros(n_drivers, dtype=np.float64)
        self._prev_order_status = np.zeros(0, dtype=np.int8)
        self._n_offers = 0
        self._n_blocked = 0
        self._n_requests = 0

    # --- recording ---------------------------------------------------------------

    @property
    def n_frames(self) -> int:
        return len(self.t)

    def start_slot(self, dec: CellDecision, t_start: float) -> None:
        if dec.slot != len(self.slots):
            raise ValueError(f"slots must be recorded in order: expected {len(self.slots)}, got {dec.slot}")
        self.slots.append({
            "slot": int(dec.slot), "t_start": float(t_start), "published": False,
            "promo_on": dec.promo_on.astype(bool).copy(), "s_hat": dec.s_hat.astype(np.float32).copy(),
            "mechanism": dec.mechanism.astype(np.int8).copy(), "cluster_id": dec.cluster_id.astype(np.int16).copy(),
            "block": int(dec.block), "in_burnin": bool(dec.in_burnin),
        })

    def publish_slot(self, slot: int, record: dict[str, np.ndarray]) -> None:
        rec = self.slots[slot]
        for name in SLOT_SNAPSHOT_FIELDS:
            rec[name] = np.asarray(record[name]).copy()
        rec["published"] = True

    def record(self, ctx: SimContext, t: float) -> None:
        """Append the frame of tick ``t`` (called after step 10). Reads the context only."""
        drivers, orders, sessions = ctx.drivers, ctx.orders, ctx.sessions
        status, cell, origin, busy = drivers.status, drivers.cell, drivers.origin_cell, drivers.busy_until

        # A driver whose (status, target cell, deadline) changed started a new leg in this tick ...
        changed = (status != self._prev_status) | (cell != self._prev_cell) | (busy != self._prev_busy)
        changed |= np.isnan(self._prev_busy) != np.isnan(busy)
        self._move_start[changed] = t
        # ... except a trip leg, which began at the exact pickup time of its order (trips.advance).
        on_trip = changed & (status == _ON_TRIP)
        if on_trip.any():
            self._move_start[on_trip] = orders.pickup_time_s[drivers.order[on_trip]]
        self._prev_status[:] = status
        self._prev_cell[:] = cell
        self._prev_busy[:] = busy

        self.status.append(status.copy())
        self.cell.append(cell.copy())
        self.origin.append(origin.copy())
        self.move_start.append(self._move_start.astype(np.float32))
        self.busy_until.append(busy.astype(np.float32))
        self.idle.append(ctx.cells.idle.copy())
        self.enroute.append(ctx.cells.enroute.copy())
        self.ontrip.append(ctx.cells.ontrip.copy())
        self.waiting.append(ctx.cells.waiting.copy())

        # Orders: cumulative counts and the events of the tick from status changes.
        o_status = orders.col("status")
        self.order_counts.append(np.bincount(o_status.astype(np.int64), minlength=_N_ORDER_STATUS))
        events = [self._order_events(orders, o_status)]
        self._prev_order_status = o_status.copy()

        # Sessions quoted in this tick: offers and budget blocks (step 5), requests (step 6).
        start, stop = ctx.tick_sessions
        if stop > start:
            arm = sessions.arm[start:stop] == 1
            blocked = sessions.budget_blocked[start:stop]
            pu = sessions.pu_cell[start:stop].astype(np.int32)
            self._n_offers += int(arm.sum())
            self._n_blocked += int(blocked.sum())
            self._n_requests += int(sessions.requested[start:stop].sum())
            events.append(_events(EVENT_CODE["offer"], pu[arm]))
            events.append(_events(EVENT_CODE["blocked"], pu[blocked]))
        self.session_counts.append(np.array([sessions.n, self._n_offers, self._n_blocked, self._n_requests],
                                            dtype=np.int64))
        self.events.append(np.concatenate([e for e in events if len(e)], axis=0) if any(len(e) for e in events)
                           else np.zeros((0, 3), dtype=np.int32))

        # Budget ledger of the period the tick belongs to (warm-up = -1; after the window: last period).
        period = ctx.clock.period_of(t)
        period = max(-1, min(period, ctx.clock.n_periods - 1))
        spent, committed, reserved = ctx.ledger.totals(period)
        limit = ctx.ledger.limit_cents(period)
        self.ledger.append(np.array([period, spent, committed, reserved, -1 if limit is None else limit],
                                    dtype=np.int64))
        self.t.append(float(t))

    def _order_events(self, orders, o_status: np.ndarray) -> np.ndarray:
        n_prev = len(self._prev_order_status)
        pu, do, src = orders.col("pu_cell"), orders.col("do_cell"), orders.col("driver_origin_cell")
        out = []
        if n_prev:
            new = o_status[:n_prev]
            idx = np.flatnonzero(new != self._prev_order_status)
            if len(idx):
                st = new[idx]
                out.append(_events(EVENT_CODE["match"], src[idx][st == int(OrderStatus.MATCHED)],
                                   pu[idx][st == int(OrderStatus.MATCHED)]))
                out.append(_events(EVENT_CODE["pickup"], pu[idx][st == int(OrderStatus.ON_TRIP)]))
                out.append(_events(EVENT_CODE["complete"], do[idx][st == int(OrderStatus.COMPLETED)]))
                out.append(_events(EVENT_CODE["abandon"], pu[idx][st == int(OrderStatus.ABANDONED)]))
                out.append(_events(EVENT_CODE["cancel"], pu[idx][st == int(OrderStatus.CANCELLED)]))
        fresh = np.arange(n_prev, len(o_status))
        if len(fresh):
            out.append(_events(EVENT_CODE["request"], pu[fresh]))
            matched = fresh[o_status[fresh] == int(OrderStatus.MATCHED)]
            out.append(_events(EVENT_CODE["match"], src[matched], pu[matched]))
        out = [e for e in out if len(e)]
        return np.concatenate(out, axis=0) if out else np.zeros((0, 3), dtype=np.int32)

    # --- export ------------------------------------------------------------------

    def frame_arrays(self) -> dict[str, np.ndarray]:
        """Stacked frames (``[n_frames, ...]``) for ``np.savez_compressed`` / the API."""
        n = self.n_frames
        return {
            "t": np.asarray(self.t[:n], dtype=np.float64),
            "status": np.stack(self.status[:n]) if n else np.zeros((0, self.n_drivers), np.int8),
            "cell": np.stack(self.cell[:n]) if n else np.zeros((0, self.n_drivers), np.int16),
            "origin": np.stack(self.origin[:n]) if n else np.zeros((0, self.n_drivers), np.int16),
            "move_start": np.stack(self.move_start[:n]) if n else np.zeros((0, self.n_drivers), np.float32),
            "busy_until": np.stack(self.busy_until[:n]) if n else np.zeros((0, self.n_drivers), np.float32),
            "idle": np.stack(self.idle[:n]) if n else np.zeros((0, self.n_cells), np.int32),
            "enroute": np.stack(self.enroute[:n]) if n else np.zeros((0, self.n_cells), np.int32),
            "ontrip": np.stack(self.ontrip[:n]) if n else np.zeros((0, self.n_cells), np.int32),
            "waiting": np.stack(self.waiting[:n]) if n else np.zeros((0, self.n_cells), np.int32),
            "order_counts": np.stack(self.order_counts[:n]) if n else np.zeros((0, _N_ORDER_STATUS), np.int64),
            "session_counts": np.stack(self.session_counts[:n]) if n else np.zeros((0, 4), np.int64),
            "ledger": np.stack(self.ledger[:n]) if n else np.zeros((0, 5), np.int64),
            "event_offsets": np.cumsum([0] + [len(e) for e in self.events[:n]]).astype(np.int64),
            "events": (np.concatenate(self.events[:n], axis=0) if n else np.zeros((0, 3), np.int32)),
        }

    @classmethod
    def from_arrays(cls, cfg: Config, clock: Clock, arrays: dict[str, np.ndarray], slots: list[dict]) -> Trace:
        """Rebuild a trace from :meth:`frame_arrays` output (loaded from ``trace.npz``)."""
        tr = cls(cfg, clock, arrays["status"].shape[1], arrays["idle"].shape[1])
        n = len(arrays["t"])
        tr.t = [float(x) for x in arrays["t"]]
        for name in ("status", "cell", "origin", "move_start", "busy_until", "idle", "enroute", "ontrip", "waiting",
                     "order_counts", "session_counts", "ledger"):
            setattr(tr, name, list(arrays[name]))
        off = arrays["event_offsets"]
        ev = arrays["events"]
        tr.events = [ev[off[k]:off[k + 1]] for k in range(n)]
        tr.slots = slots
        return tr


def _events(code: int, a: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    a = np.asarray(a, dtype=np.int32)
    if len(a) == 0:
        return np.zeros((0, 3), dtype=np.int32)
    out = np.empty((len(a), 3), dtype=np.int32)
    out[:, 0] = code
    out[:, 1] = a
    out[:, 2] = -1 if b is None else np.asarray(b, dtype=np.int32)
    return out


ProgressFn = Callable[[int, float, int], None]


def run_traced(cfg: Config, world: World, policy: Policy, rng: Rng, *, budget_usd: float | None = None,
               enforce_budget: bool | None = None, on_progress: ProgressFn | None = None,
               on_trace: Callable[[Trace], None] | None = None,
               progress_every: int = 15) -> tuple[RunResult, Trace]:
    """Same contract as ``sim.engine.run(..., log_level="full")``, plus the :class:`Trace`.

    ``on_progress(tick, t, ticks_max)`` is called every ``progress_every`` ticks;
    ``ticks_max`` is the longest possible run (window + cool-down), the actual run
    ends as soon as the window's orders are closed. ``on_trace(trace)`` is called
    once before the first tick, so a caller can read frames while the run is going.
    """
    t_wall = time.perf_counter()
    ctx = build_context(cfg, world, policy, rng, budget_usd=budget_usd, enforce_budget=enforce_budget)
    clock, ledger, layer, monitor = ctx.clock, ctx.ledger, ctx.layer, ctx.monitor
    trace = Trace(cfg, clock, ctx.drivers.n, ctx.n_cells)
    trace.budget_cents = ledger.budget_cents
    if on_trace is not None:
        on_trace(trace)
    supply.init_drivers(ctx)
    ticks_max = int((clock.window_end_s + clock.cooldown_max_s) // clock.tick_s) + 1

    sum_idle_ticks = 0.0
    sum_enroute_ticks = 0.0
    tick = 0
    while True:
        t = tick * clock.tick_s
        if t >= clock.window_end_s and (ctx.orders.count_open() == 0 or t >= clock.window_end_s + clock.cooldown_max_s):
            break
        slot = clock.slot_of(t)
        if slot != ctx.current_slot:
            ctx.current_slot = slot
            dec = layer.start_slot(slot, monitor.view(slot))
            trace.start_slot(dec, t)

        trips.advance(ctx, t)
        supply.update(ctx, t)
        cancel.expire_waiting(ctx, t)
        if t < clock.window_end_s:
            demand.spawn(ctx, t)
        else:
            ctx.tick_sessions = (ctx.sessions.n, ctx.sessions.n)
        layer.quote(ctx, t)
        choice.decide(ctx, t)
        matching.match(ctx, t)
        cancel.en_route(ctx, t)
        reposition.step(ctx, t)
        monitor.accumulate(ctx.cells, ctx.slot_counters)
        if clock.in_window(t):
            sum_idle_ticks += float(ctx.cells.idle.sum())
            sum_enroute_ticks += float(ctx.cells.enroute.sum())
        t_next = t + clock.tick_s
        if t_next % clock.slot_s == 0:
            record = monitor.publish(slot, t_next, ctx.slot_counters, layer.cell_dec)
            trace.publish_slot(slot, record)
        trace.record(ctx, t)
        if on_progress is not None and tick % progress_every == 0:
            on_progress(tick, float(t), ticks_max)
        tick += 1
    sim_end_s = float(tick * clock.tick_s)

    n_truncated = _truncate_open_orders(ctx)
    ledger.check_invariant()
    result = _aggregate(ctx, policy, sim_end_s, n_truncated, budget_usd, sum_idle_ticks, sum_enroute_ticks)
    result.runtime_s = time.perf_counter() - t_wall
    result.sessions = ctx.sessions
    result.orders = ctx.orders
    result.snapshots = monitor.store.records()
    if on_progress is not None:
        on_progress(tick, sim_end_s, ticks_max)
    return result, trace


def budget_period_table(ledger_frames: np.ndarray, n_periods: int) -> list[dict]:
    """Final ``spent / committed / reserved / limit`` (USD) per period from the last frame of each period."""
    out = []
    for p in range(-1, n_periods):
        rows = ledger_frames[ledger_frames[:, 0] == p]
        if len(rows) == 0:
            continue
        last = rows[-1]
        limit = None if last[4] < 0 else last[4] / CENTS_PER_USD
        out.append({"period": int(p), "spent_usd": last[1] / CENTS_PER_USD, "committed_usd": last[2] / CENTS_PER_USD,
                    "reserved_usd": last[3] / CENTS_PER_USD, "limit_usd": limit})
    return out
