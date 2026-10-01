"""M8 SupplyModel: periodic shifts; drivers leave only when idle.

Spec: docs/spec.md §4.8; decisions T-02, T-08. Milestone: P1 (task H1.4).

Contract: ``init_drivers`` sets the t = 0 state (drivers whose periodic shift
covers t = 0 start IDLE at their origin cell; ``shift_mode = always_on`` puts
every driver online for the whole run). ``update`` handles shift starts and
ends each tick and keeps ``ctx.cells.idle`` consistent.

Supply never looks at demand, policy or snapshots (hard rule 5). A driver who is
busy when the shift ends is left alone: ``trips.advance`` (step 1) makes them
IDLE at dropoff, and ``update`` (step 2 of the same tick) then takes them offline.
"""

from __future__ import annotations

import numpy as np

from sim.population import on_shift
from sim.state import DriverStatus, SimContext

_DAY_S = 86400.0
_OFFLINE, _IDLE = int(DriverStatus.OFFLINE), int(DriverStatus.IDLE)


def init_drivers(ctx: SimContext) -> None:
    """Called once before the first tick: put the drivers whose shift covers t = 0 online."""
    cfg, drivers, schedule = ctx.cfg, ctx.drivers, ctx.world.drivers
    if cfg.supply.early_exit_enabled:
        raise NotImplementedError("supply.early_exit_enabled: sensitivity analysis only, see decisions Q18")

    if cfg.supply.shift_mode == "always_on":
        drivers.shift_start_s[:] = 0.0
        drivers.shift_end_s[:] = np.inf
        online = np.ones(drivers.n, dtype=bool)
    else:
        start_s = schedule.shift_start_h * 3600.0
        len_s = schedule.shift_len_h * 3600.0
        online = on_shift(schedule, 0.0)
        # A shift that covers t = 0 began yesterday (or right now, if it starts at 00:00).
        began = np.where(online & (start_s > 0), start_s - _DAY_S, start_s)
        drivers.shift_start_s[:] = began
        drivers.shift_end_s[:] = began + len_s

    _go_online(ctx, np.flatnonzero(online), 0.0)


def update(ctx: SimContext, t: float) -> None:
    """Engine step 2: shift ends (idle drivers only), then shift starts."""
    drivers = ctx.drivers
    status = drivers.status

    leaving = np.flatnonzero((status == _IDLE) & (drivers.shift_end_s <= t))
    if len(leaving):
        np.subtract.at(ctx.cells.idle, drivers.cell[leaving], 1)
        status[leaving] = _OFFLINE
        drivers.cell[leaving] = -1
        drivers.idle_since[leaving] = np.nan
        # Next shift: same hours on the first day whose shift has not ended yet (late leavers skip nothing).
        days = np.floor((t - drivers.shift_end_s[leaving]) / _DAY_S) + 1.0
        drivers.shift_start_s[leaving] += days * _DAY_S
        drivers.shift_end_s[leaving] += days * _DAY_S

    starting = np.flatnonzero((status == _OFFLINE) & (drivers.shift_start_s <= t))
    if len(starting):
        _go_online(ctx, starting, t)


def _go_online(ctx: SimContext, idx: np.ndarray, t: float) -> None:
    """OFFLINE -> IDLE at the driver's origin cell."""
    drivers = ctx.drivers
    cell = ctx.world.drivers.origin_cell[idx]
    drivers.status[idx] = _IDLE
    drivers.cell[idx] = cell
    drivers.idle_since[idx] = t
    np.add.at(ctx.cells.idle, cell, 1)
