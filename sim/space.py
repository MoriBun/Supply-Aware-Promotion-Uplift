"""M1 SpaceTime: hex grid, torus, distance matrix D, travel times T[a, b, h], pickup ETA.

Spec: docs/spec.md §4.1. Milestone: P1 (task H1.1).

Sprint-0 contract: the ``SpaceTime`` fields below, the cell enumeration (ids
sorted by ``(q, r)``, spec §2) and the ETA signatures. ``build_space`` is a stub
that returns correctly shaped placeholder arrays (``is_stub = True``); the ETA
methods raise until H1.1 lands.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from sim.config import Config

# Six axial neighbour directions (spec §4.1).
HEX_DIRECTIONS: tuple[tuple[int, int], ...] = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


def n_cells_for_radius(radius: int) -> int:
    return 3 * radius * radius + 3 * radius + 1


def hex_cells(radius: int) -> np.ndarray:
    """Axial coordinates ``(q, r)`` of the radius-``R`` hexagon, sorted by ``(q, r)`` (int16 [N, 2])."""
    cells = [
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(q + r)) <= radius
    ]
    return np.array(sorted(cells), dtype=np.int16)


def hex_area_km2(edge_km: float) -> float:
    """Area of a regular hexagon with side ``edge_km`` (spec §4.1)."""
    return 3.0 * math.sqrt(3.0) / 2.0 * edge_km * edge_km


@dataclass
class SpaceTime:
    """Static geometry and travel times of the world (spec §4.1)."""

    n_cells: int
    cell_q: np.ndarray        # int16 [N]
    cell_r: np.ndarray        # int16 [N]
    D: np.ndarray             # int16 [N, N], hex (torus) ring distance
    T: np.ndarray             # float32 [N, N, 24], travel minutes from a to b in hour h
    neighbors: np.ndarray     # int16 [N, 6], -1 where a direction has no cell (non-torus border)
    area_km2: float
    torus: bool
    is_stub: bool = False

    def eta_in(self, idle_count: int, hour: int) -> float:
        """Expected pickup ETA (minutes) when ``idle_count >= 1`` drivers idle in the rider's cell."""
        raise NotImplementedError("space.eta_in: task H1.1")

    def quote_eta(self, cell: int, hour: int, idle_count: np.ndarray) -> tuple[float, bool]:
        """Quoted ETA (minutes) and ``no_supply`` flag using the M5 search rule, without holding a driver."""
        raise NotImplementedError("space.quote_eta: task H1.1")


def build_space(cfg: Config) -> SpaceTime:
    """Sprint-0 stub: real cell enumeration and area; D, T and neighbours are placeholders."""
    cells = hex_cells(cfg.space.grid_radius)
    n = len(cells)
    return SpaceTime(
        n_cells=n,
        cell_q=cells[:, 0].copy(),
        cell_r=cells[:, 1].copy(),
        D=np.zeros((n, n), dtype=np.int16),
        T=np.zeros((n, n, 24), dtype=np.float32),
        neighbors=np.full((n, 6), -1, dtype=np.int16),
        area_km2=hex_area_km2(cfg.space.edge_km),
        torus=cfg.space.torus,
        is_stub=True,
    )
