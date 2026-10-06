"""Dashboard (dashboard/): the traced loop equals the engine, frames are consistent, the API serves a run.

Fast tests on the tiny configuration. The API tests need ``fastapi`` (extras ``[dashboard]``)
and are skipped without it; the simulator itself is never imported from ``dashboard`` in ``sim/``.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np
import pytest

from sim import engine
from sim.config import Config
from sim.policies import make_policy
from sim.population import build_world
from sim.rng import Rng
from sim.state import DriverStatus, OrderStatus

from dashboard.geometry import torus_display_vectors, world_geometry
from dashboard.trace import EVENT_CODE, Trace, run_traced

ROOT = Path(__file__).resolve().parents[1]
COMPARED = ("N_completed", "V_profit_usd", "voucher_spent_usd", "n_sessions", "n_requests", "n_abandoned", "n_cancelled",
            "mean_pickup_eta_min", "share_cells_off", "n_switches_per_cell_day", "mean_slack", "sim_end_s",
            "n_truncated_orders")


def _setup(cfg: Config, theta: float = 0.5):
    rng = Rng.from_config(cfg)
    world = build_world(cfg, rng)
    policy = make_policy(cfg, world, rng=rng, theta=theta, kappa=-math.inf)
    return world, policy, rng


def test_traced_run_matches_engine(tiny_cfg: Config) -> None:
    """Recording frames must not change a single number of the run (same steps, same order)."""
    world, policy, rng = _setup(tiny_cfg)
    expected = engine.run(tiny_cfg, world, policy, rng, log_level="full", budget_usd=50.0, enforce_budget=True)
    world, policy, rng = _setup(tiny_cfg)
    result, trace = run_traced(tiny_cfg, world, policy, rng, budget_usd=50.0, enforce_budget=True)
    for name in COMPARED:
        a, b = getattr(expected, name), getattr(result, name)
        assert a == b or (isinstance(a, float) and math.isnan(a) and math.isnan(b)), name
    for col in expected.sessions.names():
        x, y = expected.sessions.col(col), result.sessions.col(col)
        assert np.array_equal(x, y, equal_nan=x.dtype.kind == "f"), col
    for col in expected.orders.names():
        x, y = expected.orders.col(col), result.orders.col(col)
        assert np.array_equal(x, y, equal_nan=x.dtype.kind == "f"), col
    assert len(expected.snapshots) == len(result.snapshots) == len(trace.slots)
    assert trace.n_frames == int(result.sim_end_s // tiny_cfg.time.tick_s)


def test_frames_consistent_with_counters(tiny_cfg: Config) -> None:
    """Per-cell idle / en-route counts of a frame equal the driver statuses of that frame; counters are monotone."""
    world, policy, rng = _setup(tiny_cfg)
    _, trace = run_traced(tiny_cfg, world, policy, rng, budget_usd=50.0, enforce_budget=True)
    a = trace.frame_arrays()
    idle, enroute = int(DriverStatus.IDLE), int(DriverStatus.EN_ROUTE)
    for k in range(trace.n_frames):
        assert (a["status"][k] == idle).sum() == a["idle"][k].sum()
        assert (a["status"][k] == enroute).sum() == a["enroute"][k].sum()
        assert (a["cell"][k][a["status"][k] != int(DriverStatus.OFFLINE)] >= 0).all()
    assert (np.diff(a["session_counts"], axis=0) >= 0).all()
    assert (np.diff(a["order_counts"][:, int(OrderStatus.COMPLETED)]) >= 0).all()
    # ledger: used <= limit whenever a limit exists (hard rule 8, seen tick by tick)
    led = a["ledger"]
    has_limit = led[:, 4] >= 0
    assert (led[has_limit, 1:4].sum(axis=1) <= led[has_limit, 4]).all()
    # events: completions in the frames equal the completed orders
    ev = a["events"]
    assert (ev[:, 0] == EVENT_CODE["complete"]).sum() == a["order_counts"][-1][int(OrderStatus.COMPLETED)]
    assert (ev[:, 0] == EVENT_CODE["request"]).sum() == a["order_counts"][-1].sum()
    # a moving driver always has a leg that ends after it starts
    moving = a["status"] >= enroute
    assert (a["busy_until"][moving] >= a["move_start"][moving]).all()
    # round trip through the stacked arrays
    rebuilt = Trace.from_arrays(tiny_cfg, trace_clock(tiny_cfg), a, trace.slots)
    assert rebuilt.n_frames == trace.n_frames and len(rebuilt.events) == trace.n_frames
    assert all(np.array_equal(x, y) for x, y in zip(rebuilt.events, trace.events))


def trace_clock(cfg: Config):
    from sim.state import Clock
    return Clock.from_config(cfg)


def test_torus_display_vectors_are_shortest_images(tiny_cfg: Config) -> None:
    world, _, _ = _setup(tiny_cfg)
    space = world.space
    disp = torus_display_vectors(space.cell_q, space.cell_r, space.radius, space.torus)
    assert disp.shape == (space.n_cells, space.n_cells, 2)
    assert np.allclose(disp[np.arange(space.n_cells), np.arange(space.n_cells)], 0.0)
    # neighbours are exactly one centre-to-centre distance (sqrt(3) in hex units) away on screen
    for c in range(space.n_cells):
        for nb in space.neighbors[c]:
            if nb >= 0:
                assert math.isclose(math.hypot(*disp[c, nb]), math.sqrt(3.0), rel_tol=1e-6)
    geo = world_geometry(tiny_cfg, world)
    assert len(geo["cells"]) == space.n_cells and geo["n_drivers"] == tiny_cfg.supply.fleet_size


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_api_runs_a_tiny_run(tmp_path: Path) -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from dashboard.server import create_app

    app = create_app(ROOT, runs_dir=tmp_path)
    client = TestClient(app)
    assert client.get("/api/config/defaults").status_code == 200
    bad = client.post("/api/config/validate", json={"overrides": ["policy.threshold.nope=1"]}).json()
    assert bad["ok"] is False
    body = {"name": "tiny", "layers": ["tests/fixtures/tiny.yaml"], "overrides": ["policy.threshold.theta=0.5"], "kappa": -1.0}
    run = client.post("/api/runs", json=body).json()
    rid = run["id"]
    for _ in range(600):
        info = client.get(f"/api/runs/{rid}").json()
        if info["status"] in ("done", "error"):
            break
        time.sleep(0.2)
    assert info["status"] == "done", info.get("error")
    assert info["kappa"] == -1.0 and info["kappa_pilots"] == 0
    assert info["budget_usd"] > 0 and info["n_frames"] > 0 and len(info["geometry"]["cells"]) == 7
    frames = client.get(f"/api/runs/{rid}/frames", params={"start": 0, "count": 1000}).json()
    assert frames["frames"] == info["n_frames"] and frames["done"] is True
    assert len(frames["status"][0]) == 10 and len(frames["events"]) == frames["frames"]
    slots = client.get(f"/api/runs/{rid}/slots").json()
    assert slots["n_slots"] == info["n_slots"] and len(slots["promo_on"][0]) == 7
    summary = client.get(f"/api/runs/{rid}/summary").json()
    assert summary["kpis"]["N_completed"] >= 0 and summary["distribution"]["budget_periods"]
    assert (tmp_path / rid / "results" / "policy_results.parquet").exists()
    assert (tmp_path / rid / "observed" / "sessions.parquet").exists()
    assert (tmp_path / rid / "dashboard" / "trace.npz").exists()
    # a fresh app reloads the saved run with its frames and summary
    client2 = TestClient(create_app(ROOT, runs_dir=tmp_path))
    listed = client2.get("/api/runs").json()["runs"]
    assert [r["id"] for r in listed] == [rid] and listed[0]["n_frames"] == info["n_frames"]
    again = client2.get(f"/api/runs/{rid}/frames", params={"start": 0, "count": 5}).json()
    assert again["t"] == frames["t"][:5] and again["events"][0] == frames["events"][0]
    assert client2.get(f"/api/runs/{rid}/summary").json()["kpis"]["N_completed"] == summary["kpis"]["N_completed"]
    assert client2.get("/api/results/sweeps").status_code == 200
