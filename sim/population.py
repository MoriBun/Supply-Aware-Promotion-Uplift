"""World generation from world_seed: cell weights, riders, driver shifts.

Spec: docs/spec.md §4.2, §4.8. Milestone: P1 (task H1.2).

Sprint-0 contract: the ``World``, ``Riders`` and ``DriverSchedule`` fields.
``build_world`` is a stub returning correctly shaped placeholder arrays
(``is_stub = True``); H1.2 fills them from the WORLD stream.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sim.config import Config
from sim.rng import Rng
from sim.space import SpaceTime, build_space


@dataclass
class Riders:
    """Rider population. Observed columns are logged to observed/riders, the rest to hidden/riders_hidden."""

    rider_id: np.ndarray      # int32
    home_cell: np.ndarray     # int16
    x_freq: np.ndarray        # float32
    x_tenure: np.ndarray      # float32, months
    x_segment: np.ndarray     # int8
    zf: np.ndarray            # float32, z-scored x_freq (used by M4 and LegacyPolicy)
    # hidden
    u_latent: np.ndarray      # float32
    alpha: np.ndarray         # float32
    beta_price: np.ndarray    # float32 (negative)
    beta_eta: np.ndarray      # float32 (negative)
    delta_promo: np.ndarray   # float32
    max_wait_min: np.ndarray  # float32

    OBSERVED = ("rider_id", "home_cell", "x_freq", "x_tenure", "x_segment")
    HIDDEN = ("u_latent", "alpha", "beta_price", "beta_eta", "delta_promo", "max_wait_min")

    @property
    def n(self) -> int:
        return len(self.rider_id)


@dataclass
class DriverSchedule:
    """Per-driver shift, periodic by day (spec §4.8, decisions T-02)."""

    driver_id: np.ndarray     # int32
    origin_cell: np.ndarray   # int16
    shift_start_h: np.ndarray  # float64, hour of day in [0, 24)
    shift_len_h: np.ndarray    # float64

    @property
    def n(self) -> int:
        return len(self.driver_id)


@dataclass
class World:
    space: SpaceTime
    cell_weight: np.ndarray    # float64 [N], w_z normalized to mean 1
    riders: Riders
    drivers: DriverSchedule
    eval_cell_mask: np.ndarray  # bool [N], cells that count in N(pi) (NYC buffer cells are False)
    is_stub: bool = False

    @property
    def n_cells(self) -> int:
        return self.space.n_cells


def build_world(cfg: Config, rng: Rng) -> World:
    """Sprint-0 stub: shapes and dtypes are final, values are placeholders (task H1.2)."""
    space = build_space(cfg)
    n_riders = cfg.demand.n_riders
    n_drivers = cfg.supply.fleet_size
    f32 = lambda n: np.zeros(n, dtype=np.float32)  # noqa: E731
    riders = Riders(
        rider_id=np.arange(n_riders, dtype=np.int32),
        home_cell=np.zeros(n_riders, dtype=np.int16),
        x_freq=f32(n_riders), x_tenure=f32(n_riders), x_segment=np.zeros(n_riders, dtype=np.int8),
        zf=f32(n_riders),
        u_latent=f32(n_riders), alpha=f32(n_riders), beta_price=f32(n_riders), beta_eta=f32(n_riders),
        delta_promo=f32(n_riders), max_wait_min=f32(n_riders),
    )
    drivers = DriverSchedule(
        driver_id=np.arange(n_drivers, dtype=np.int32),
        origin_cell=np.zeros(n_drivers, dtype=np.int16),
        shift_start_h=np.zeros(n_drivers, dtype=np.float64),
        shift_len_h=np.zeros(n_drivers, dtype=np.float64),
    )
    return World(
        space=space,
        cell_weight=np.ones(space.n_cells, dtype=np.float64),
        riders=riders,
        drivers=drivers,
        eval_cell_mask=np.ones(space.n_cells, dtype=bool),
        is_stub=True,
    )
