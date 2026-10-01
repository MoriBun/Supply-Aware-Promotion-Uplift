"""World generation from world_seed: cell weights, riders, driver shifts.

Spec: docs/spec.md §4.2, §4.8. Milestone: P1 (task H1.2).

The world is a pure function of ``cfg`` and ``world_seed``: it never depends on
``run_seed`` or on the policy. Every random quantity has its own WORLD generator
keyed by ``(WorldPart, variable index)``, so rider ``i`` and driver ``j`` keep
their attributes when ``n_riders`` or ``fleet_size`` changes (only ``zf``, a
z-score over the whole population, moves).
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass

import numpy as np

from sim.config import Config
from sim.rng import Rng, Stream
from sim.space import SpaceTime, build_space


class WorldPart(enum.IntEnum):
    """First key of the WORLD stream (part of the CRN contract: never renumber)."""

    CELL_WEIGHT = 1
    RIDERS = 2
    DRIVERS = 3


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
class DemandTables:
    """Cumulative tables for sampling a session's rider and destination (spec §4.2).

    Each table is an "offset CDF": entry ``i`` of group ``g`` holds ``g + F_g(i)``
    with ``F_g`` the cumulative probability inside the group. One ``searchsorted``
    of ``g + u`` then samples for many sessions of different groups at once.
    """

    home_order: np.ndarray    # int32 [n_riders], rider ids sorted by (home_cell, rider_id)
    home_start: np.ndarray    # int64 [N + 1], home_order[home_start[z]:home_start[z+1]] live in cell z
    home_cdf: np.ndarray      # float64 [n_riders], aligned with home_order: z + cumulative x_freq share in z
    all_cdf: np.ndarray       # float64 [n_riders], cumulative x_freq share over rider ids
    dest_cdf: np.ndarray      # float64 [N * N], row o: o + cumulative P(d | o), P ∝ w_d * exp(-D[o, d] / L)


@dataclass
class World:
    space: SpaceTime
    cell_weight: np.ndarray    # float64 [N], w_z normalized to mean 1
    riders: Riders
    drivers: DriverSchedule
    eval_cell_mask: np.ndarray  # bool [N], cells that count in N(pi) (NYC buffer cells are False)
    tables: DemandTables
    is_stub: bool = False

    @property
    def n_cells(self) -> int:
        return self.space.n_cells


def build_world(cfg: Config, rng: Rng) -> World:
    """Generate the static world from the WORLD stream (seeded by ``world_seed`` only)."""
    space = build_space(cfg)
    cell_weight = _cell_weights(cfg, rng, space.n_cells)
    riders = _riders(cfg, rng, cell_weight)
    drivers = _drivers(cfg, rng, cell_weight)
    return World(
        space=space,
        cell_weight=_frozen(cell_weight),
        riders=riders,
        drivers=drivers,
        eval_cell_mask=_frozen(np.ones(space.n_cells, dtype=bool)),
        tables=_demand_tables(cfg, space, cell_weight, riders),
    )


# ---------------------------------------------------------------------------
# Parts of the world
# ---------------------------------------------------------------------------


def _cell_weights(cfg: Config, rng: Rng, n_cells: int) -> np.ndarray:
    """``w_z ~ LogNormal(0, cell_weight_sigma)``, normalized to mean 1 (spec §4.2)."""
    gen = rng.rng_for(Stream.WORLD, WorldPart.CELL_WEIGHT, 0)
    w = gen.lognormal(0.0, cfg.demand.cell_weight_sigma, size=n_cells)
    return w / w.mean()


def _riders(cfg: Config, rng: Rng, cell_weight: np.ndarray) -> Riders:
    """Rider attributes and behavioural coefficients (spec §4.2, "Sinh rider")."""
    rc = cfg.riders
    n = cfg.demand.n_riders
    gens = _part_generators(rng, WorldPart.RIDERS)

    home_cell = next(gens).choice(len(cell_weight), size=n, p=cell_weight / cell_weight.sum())
    x_freq = next(gens).gamma(rc.x_freq_gamma_shape, 1.0, size=n)
    x_tenure = next(gens).uniform(0.0, rc.x_tenure_max_months, size=n)
    x_segment = next(gens).choice(len(rc.x_segment_probs), size=n, p=np.asarray(rc.x_segment_probs))
    u_latent = next(gens).standard_normal(n)

    sd = x_freq.std()
    zf = (x_freq - x_freq.mean()) / sd if sd > 0 else np.zeros(n)

    alpha = rc.alpha0 + rc.alpha_freq * zf + rc.alpha_u * u_latent + next(gens).normal(0.0, rc.alpha_noise_sd, n)
    seg_mult = np.asarray(rc.beta_price_seg_mult)[x_segment]
    beta_price = -rc.beta_price_per_usd * seg_mult * np.exp(next(gens).normal(0.0, rc.beta_price_noise_sd, n))
    beta_eta = -rc.beta_eta_per_min * np.exp(next(gens).normal(0.0, rc.beta_eta_noise_sd, n))
    delta = (rc.delta0 + rc.delta_u * u_latent + np.asarray(rc.delta_seg)[x_segment]
             + next(gens).normal(0.0, rc.delta_noise_sd, n))
    # LogNormal(mu, sigma) has its mode at exp(mu - sigma^2), so this puts the mode at max_wait_mode_min.
    mu = math.log(rc.max_wait_mode_min) + rc.max_wait_sigma**2
    max_wait = next(gens).lognormal(mu, rc.max_wait_sigma, n)

    f32 = lambda a: _frozen(np.asarray(a, dtype=np.float32))  # noqa: E731
    return Riders(
        rider_id=_frozen(np.arange(n, dtype=np.int32)),
        home_cell=_frozen(home_cell.astype(np.int16)),
        x_freq=f32(x_freq), x_tenure=f32(x_tenure), x_segment=_frozen(x_segment.astype(np.int8)),
        zf=f32(zf),
        u_latent=f32(u_latent), alpha=f32(alpha), beta_price=f32(beta_price), beta_eta=f32(beta_eta),
        delta_promo=f32(delta), max_wait_min=f32(max_wait),
    )


def _drivers(cfg: Config, rng: Rng, cell_weight: np.ndarray) -> DriverSchedule:
    """Shift start, shift length and origin cell of every driver (spec §4.8)."""
    sc = cfg.supply
    n = sc.fleet_size
    gens = _part_generators(rng, WorldPart.DRIVERS)

    mixture = np.asarray(sc.shift_start_mixture, dtype=np.float64)   # rows (from_h, to_h, weight)
    component = next(gens).choice(len(mixture), size=n, p=mixture[:, 2] / mixture[:, 2].sum())
    lo, hi = mixture[component, 0], mixture[component, 1]
    shift_start = (lo + (hi - lo) * next(gens).random(n)) % 24.0
    shift_len = np.clip(next(gens).normal(sc.shift_len_mean_h, sc.shift_len_sd_h, n), *sc.shift_len_clip_h)
    origin = next(gens).choice(len(cell_weight), size=n, p=cell_weight / cell_weight.sum())

    return DriverSchedule(
        driver_id=_frozen(np.arange(n, dtype=np.int32)),
        origin_cell=_frozen(origin.astype(np.int16)),
        shift_start_h=_frozen(shift_start),
        shift_len_h=_frozen(shift_len),
    )


def _demand_tables(cfg: Config, space: SpaceTime, cell_weight: np.ndarray, riders: Riders) -> DemandTables:
    n_cells = space.n_cells
    freq = riders.x_freq.astype(np.float64)

    order = np.lexsort((riders.rider_id, riders.home_cell))
    home_sorted = riders.home_cell[order].astype(np.int64)
    home_start = np.searchsorted(home_sorted, np.arange(n_cells + 1))
    freq_sorted = freq[order]
    cum = np.cumsum(freq_sorted)
    edges = np.concatenate(([0.0], cum))[home_start]                  # cumulative x_freq at each cell boundary
    before, total = edges[:-1], np.diff(edges)                        # mass before / inside each cell's block
    home_cdf = home_sorted + (cum - before[home_sorted]) / total[home_sorted]

    all_cdf = np.cumsum(freq) / freq.sum()

    # P(d | o) ∝ w_d * exp(-D[o, d] / L); d = o is allowed (trip inside the cell).
    p = cell_weight[None, :] * np.exp(-space.D.astype(np.float64) / cfg.demand.dest_decay_rings)
    p /= p.sum(axis=1, keepdims=True)
    dest_cdf = (np.arange(n_cells)[:, None] + np.cumsum(p, axis=1)).ravel()

    return DemandTables(
        home_order=_frozen(order.astype(np.int32)),
        home_start=_frozen(home_start.astype(np.int64)),
        home_cdf=_frozen(home_cdf),
        all_cdf=_frozen(all_cdf),
        dest_cdf=_frozen(dest_cdf),
    )


def _part_generators(rng: Rng, part: WorldPart):
    """One WORLD generator per variable of a part, in a fixed order."""
    k = 0
    while True:
        yield rng.rng_for(Stream.WORLD, part, k)
        k += 1


def _frozen(a: np.ndarray) -> np.ndarray:
    a.setflags(write=False)
    return a
