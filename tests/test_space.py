"""docs/tests.md, M1 SpaceTime; plus the pickup search shared with M5 (spec §4.1, §4.5)."""

import math

import numpy as np
import pytest

from sim.config import load_config
from sim.space import HEX_DIRECTIONS, build_space, hex_area_km2, hex_cells, hex_distance, n_cells_for_radius


@pytest.fixture
def space(default_yaml):
    return build_space(load_config(default_yaml))


def make_space(default_yaml, *overrides):
    return build_space(load_config(default_yaml, list(overrides)))


# --- cells --------------------------------------------------------------------


@pytest.mark.parametrize("R, n", [(1, 7), (2, 19), (3, 37), (4, 61)])
def test_cell_count(default_yaml, R, n):
    sp = make_space(default_yaml, f"space.grid_radius={R}")
    assert sp.n_cells == n == n_cells_for_radius(R) == len(hex_cells(R))
    assert not sp.is_stub


def test_cell_ids_sorted_by_axial_coordinates(space):
    coords = list(zip(space.cell_q.tolist(), space.cell_r.tolist()))
    assert coords == sorted(coords)
    assert len(set(coords)) == space.n_cells


# --- torus --------------------------------------------------------------------


@pytest.mark.parametrize("R", [1, 2, 3, 4])
def test_torus_six_distinct_symmetric_neighbours(default_yaml, R):
    sp = make_space(default_yaml, f"space.grid_radius={R}")
    for z in range(sp.n_cells):
        nb = sp.neighbors[z]
        assert (nb >= 0).all()
        assert len(set(nb.tolist())) == 6
        assert z not in nb
        for y in nb:
            assert z in sp.neighbors[y]


@pytest.mark.parametrize("R", [1, 2, 3, 4])
def test_neighbours_are_exactly_distance_one(default_yaml, R):
    sp = make_space(default_yaml, f"space.grid_radius={R}")
    for z in range(sp.n_cells):
        assert set(sp.neighbors[z].tolist()) == set(np.flatnonzero(sp.D[z] == 1).tolist())


@pytest.mark.parametrize("R", [1, 2, 3, 4])
def test_torus_distance_is_a_metric_with_max_R(default_yaml, R):
    D = make_space(default_yaml, f"space.grid_radius={R}").D.astype(np.int64)
    assert (D == D.T).all()
    assert (np.diag(D) == 0).all()
    assert (D[~np.eye(len(D), dtype=bool)] > 0).all()
    assert D.max() == R
    # Triangle inequality: D[x, z] <= D[x, y] + D[y, z] for all x, y, z.
    assert (D[:, None, :] <= D[:, :, None] + D[None, :, :]).all()


def test_neighbour_directions_follow_axial_offsets(space):
    # A cell whose six axial neighbours are all inside the grid uses them directly.
    index = {(q, r): i for i, (q, r) in enumerate(zip(space.cell_q.tolist(), space.cell_r.tolist()))}
    centre = index[(0, 0)]
    expected = [index[(dq, dr)] for dq, dr in HEX_DIRECTIONS]
    assert space.neighbors[centre].tolist() == expected


def test_clusters_of_seven_have_spec_sizes(space):
    # Handoff B1 check (docs/phan_cong.md): cluster centres (q + 5r) mod 7 == 0, each cell
    # to the nearest centre by torus distance, ties to the smaller cell id (spec §4.10).
    centres = np.flatnonzero((space.cell_q.astype(int) + 5 * space.cell_r.astype(int)) % 7 == 0)
    nearest = centres[np.argmin(space.D[:, centres], axis=1)]
    assert (space.D[np.arange(space.n_cells), nearest] <= 1).all()
    sizes = sorted(np.bincount(nearest, minlength=space.n_cells)[centres].tolist())
    assert sizes == [3, 3, 4, 6, 7, 7, 7]


# --- no torus -----------------------------------------------------------------


def test_without_torus_edge_cells_have_fewer_neighbours(default_yaml):
    sp = make_space(default_yaml, "space.torus=false")
    n_nb = (sp.neighbors >= 0).sum(axis=1)
    ring = hex_distance(sp.cell_q.astype(int), sp.cell_r.astype(int))
    assert (n_nb[ring == sp.radius] < 6).all()
    assert (n_nb[ring < sp.radius] == 6).all()
    assert sp.D.max() == 2 * sp.radius
    # Plain hex distance, no wrapping.
    dq = sp.cell_q.astype(int)[None, :] - sp.cell_q.astype(int)[:, None]
    dr = sp.cell_r.astype(int)[None, :] - sp.cell_r.astype(int)[:, None]
    assert (sp.D == hex_distance(dq, dr)).all()


# --- travel times -------------------------------------------------------------


def test_travel_time_shape_positive_symmetric(space):
    T = space.T
    assert T.shape == (space.n_cells, space.n_cells, 24)
    assert T.dtype == np.float32
    assert (T > 0).all()
    assert (T == T.transpose(1, 0, 2)).all()


def test_intra_cell_trip_shorter_than_any_other(space):
    off = ~np.eye(space.n_cells, dtype=bool)
    for h in range(24):
        diag = np.diag(space.T[:, :, h])
        other = np.where(off, space.T[:, :, h], np.inf)
        assert (diag < other.min(axis=1)).all()


def test_travel_time_matches_formula(default_yaml, space):
    sc = load_config(default_yaml).space
    area = 3 * math.sqrt(3) / 2 * sc.edge_km**2
    s = math.sqrt(3) * sc.edge_km
    a, b = 0, int(np.flatnonzero(space.D[0] == 2)[0])
    for h in (0, 8, 18):
        v = sc.base_speed_kmh * sc.speed_factor_by_hour[h]
        assert space.T[a, b, h] == pytest.approx(sc.detour_factor * 2 * s / v * 60, rel=1e-6)
        intra = sc.detour_factor * sc.intra_cell_dist_factor * math.sqrt(area)
        assert space.T[a, a, h] == pytest.approx(intra / v * 60, rel=1e-6)
    assert space.area_km2 == pytest.approx(area) == pytest.approx(hex_area_km2(sc.edge_km))
    assert space.center_dist_km == pytest.approx(s)


# --- ETA_in (T-04) ------------------------------------------------------------


def test_eta_in_monotone_with_floor(space):
    idle = np.arange(1, 60)
    adjacent = int(space.neighbors[0, 0])
    for h in range(24):
        eta = space.eta_in(idle, h)
        assert (np.diff(eta) <= 0).all()                     # never increases in I
        assert (eta >= space.eta_floor_min).all()            # never below the floor
        above = eta[:-1] > space.eta_floor_min
        assert (np.diff(eta)[above] < 0).all()               # strictly decreasing above the floor
        assert space.eta_in(1, h) < space.T[adjacent, 0, h]  # one idle car here beats the next cell


def test_eta_in_reaches_floor_with_defaults(space):
    # The floor is reachable with default parameters, which is why T-04 relaxed the test.
    assert space.eta_in(60, 18) == space.eta_floor_min


def test_eta_in_rejects_zero_idle(space):
    with pytest.raises(ValueError):
        space.eta_in(0, 12)


# --- pickup search and quoted ETA (spec §4.1, §4.5) ---------------------------


def test_pickup_in_own_cell_uses_eta_in(space):
    idle = np.zeros(space.n_cells, dtype=np.int32)
    idle[5] = 3
    assert space.find_pickup(5, 9, idle) == (5, pytest.approx(space.eta_in(3, 9)))
    assert space.quote_eta(5, 9, idle) == (pytest.approx(space.eta_in(3, 9)), False)


def test_pickup_takes_nearest_ring_then_smallest_id(space):
    z, h = 0, 18
    ring1 = space.rings[z][0]
    ring2 = space.rings[z][1]
    idle = np.zeros(space.n_cells, dtype=np.int32)
    idle[ring2[0]] = 1
    idle[ring1[-1]] = 1
    idle[ring1[-2]] = 1
    # Every cell of a synthetic ring has the same T, so the tie goes to the smallest id.
    assert space.find_pickup(z, h, idle) == (int(ring1[-2]), pytest.approx(float(space.T[ring1[-2], z, h])))


def test_pickup_goes_to_farther_ring_when_nearer_are_empty(space):
    z, h = 3, 12
    far = space.rings[z][-1]
    idle = np.zeros(space.n_cells, dtype=np.int32)
    idle[far[0]] = 2
    src, eta = space.find_pickup(z, h, idle)
    assert src == int(far[0])
    assert eta == pytest.approx(float(space.T[far[0], z, h]))


def test_no_idle_driver_means_no_supply(space):
    idle = np.zeros(space.n_cells, dtype=np.int32)
    assert space.find_pickup(0, 12, idle) == (-1, math.inf)
    assert space.quote_eta(0, 12, idle) == (space.max_pickup_eta_min, True)


def test_max_pickup_eta_limits_the_search(default_yaml):
    # Tight limit: ring 1 is reachable, ring 2 is not (default T is far below 30 min, spec notes).
    base = make_space(default_yaml)
    z, h = 0, 18
    t1 = float(base.T[base.rings[z][0][0], z, h])
    t2 = float(base.T[base.rings[z][1][0], z, h])
    sp = make_space(default_yaml, f"matching.max_pickup_eta_min={(t1 + t2) / 2}")
    idle = np.zeros(sp.n_cells, dtype=np.int32)
    idle[sp.rings[z][1][0]] = 1
    assert sp.find_pickup(z, h, idle) == (-1, math.inf)
    assert sp.quote_eta(z, h, idle) == (sp.max_pickup_eta_min, True)
    idle[sp.rings[z][0][0]] = 1
    assert sp.find_pickup(z, h, idle)[0] == int(sp.rings[z][0][0])


def test_max_ring_limits_the_search(default_yaml):
    sp = make_space(default_yaml, "matching.max_ring=1")
    z = 0
    idle = np.zeros(sp.n_cells, dtype=np.int32)
    idle[sp.rings[z][1][0]] = 1
    assert sp.find_pickup(z, 12, idle) == (-1, math.inf)


def test_pickup_search_does_not_touch_counts(space):
    idle = np.zeros(space.n_cells, dtype=np.int32)
    idle[space.rings[0][0][0]] = 1
    before = idle.copy()
    space.find_pickup(0, 12, idle)
    space.quote_eta(0, 12, idle)
    assert (idle == before).all()


# --- misc ---------------------------------------------------------------------


def test_arrays_are_read_only(space):
    for arr in (space.cell_q, space.cell_r, space.D, space.neighbors, space.T, space.speed_kmh, space.rings[0][0]):
        with pytest.raises(ValueError):
            arr[0] = arr[0]


def test_rings_partition_other_cells(space):
    for z in range(space.n_cells):
        cells = np.concatenate(space.rings[z])
        assert sorted(cells.tolist()) == [c for c in range(space.n_cells) if c != z]
        for k, ring in enumerate(space.rings[z], start=1):
            assert (space.D[z, ring] == k).all()
            assert (np.diff(ring) > 0).all()


def test_nyc_variant_not_implemented(default_yaml):
    with pytest.raises(NotImplementedError):
        make_space(default_yaml, "space.variant=nyc")


def test_tiny_fixture_builds(tiny_cfg):
    sp = build_space(tiny_cfg)
    assert sp.n_cells == 7
    assert sp.D.max() == 1
