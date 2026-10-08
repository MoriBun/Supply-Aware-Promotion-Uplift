"""Hex-grid geometry for the map: cell centres, torus display vectors, static world facts."""

from __future__ import annotations

import math

import numpy as np

from sim.config import Config
from sim.population import World, online_by_hour
from sim.space import torus_vectors

SQRT3 = math.sqrt(3.0)


def axial_to_xy(q: np.ndarray, r: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Pointy-top hex centres in units of the hex circumradius (size = 1)."""
    q = np.asarray(q, dtype=np.float64)
    r = np.asarray(r, dtype=np.float64)
    return SQRT3 * (q + r / 2.0), 1.5 * r


def torus_display_vectors(q: np.ndarray, r: np.ndarray, radius: int, torus: bool) -> np.ndarray:
    """``disp[a, b] = (dx, dy)``: the shortest on-screen vector from cell ``a`` to an image of cell ``b``.

    On the torus a driver moving to a neighbouring cell across the border leaves one
    edge and enters from the opposite one; the front end draws the leg along this
    vector (first half from ``a``, second half into ``b``). Without the torus the
    vector is simply ``xy[b] - xy[a]``.
    """
    x, y = axial_to_xy(q, r)
    n = len(x)
    if not torus:
        return np.stack([x[None, :] - x[:, None], y[None, :] - y[:, None]], axis=-1)
    (aq, ar), (bq, br) = torus_vectors(radius)
    best = np.full((n, n, 2), np.inf)
    best_d = np.full((n, n), np.inf)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            xi, yi = axial_to_xy(np.asarray(q) + i * aq + j * bq, np.asarray(r) + i * ar + j * br)
            dx = xi[None, :] - x[:, None]
            dy = yi[None, :] - y[:, None]
            d = dx * dx + dy * dy
            take = d < best_d
            best_d = np.where(take, d, best_d)
            best[..., 0] = np.where(take, dx, best[..., 0])
            best[..., 1] = np.where(take, dy, best[..., 1])
    return best


def world_geometry(cfg: Config, world: World) -> dict:
    """Everything static the map needs: cells, display vectors, neighbours, weights, fleet by hour."""
    space = world.space
    x, y = axial_to_xy(space.cell_q, space.cell_r)
    disp = torus_display_vectors(space.cell_q, space.cell_r, space.radius, space.torus)
    home = np.bincount(world.riders.home_cell, minlength=space.n_cells)
    return {
        "n_cells": int(space.n_cells),
        "radius": int(space.radius),
        "torus": bool(space.torus),
        "edge_km": float(cfg.space.edge_km),
        "cells": [{"id": int(i), "q": int(space.cell_q[i]), "r": int(space.cell_r[i]), "x": float(x[i]),
                   "y": float(y[i]), "weight": float(world.cell_weight[i]), "riders_home": int(home[i])}
                  for i in range(space.n_cells)],
        "neighbors": space.neighbors.astype(int).tolist(),
        "disp": np.round(disp, 4).tolist(),
        "n_drivers": int(world.drivers.n),
        "n_riders": int(world.riders.n),
        "online_by_hour": online_by_hour(world.drivers).astype(int).tolist(),
        "driver_origin_cell": world.drivers.origin_cell.astype(int).tolist(),
    }
