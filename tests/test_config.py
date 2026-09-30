"""docs/tests.md, section "Cấu hình": unknown keys, --set overrides, config_hash."""

import dataclasses

import pytest
import yaml

from sim.config import (
    ConfigError,
    budget_period_min,
    config_hash,
    eval_window_min,
    load_config,
    load_raw,
    to_dict,
)


def write_yaml(tmp_path, data, name="cfg.yaml"):
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def test_default_yaml_loads(default_yaml):
    cfg = load_config(default_yaml)
    assert cfg.space.grid_radius == 3
    assert cfg.time.tick_s == 60
    assert cfg.policy.threshold.kappa == "auto"
    assert cfg.experiment.cluster_level == 7
    assert cfg.matching.max_ring is None
    assert len(cfg.demand.hour_profile) == 24
    assert cfg.supply.shift_start_mixture[0] == (6.0, 8.5, 0.30)


def test_new_keys_load(default_yaml):
    # Keys added by decisions T-18.
    cfg = load_config(default_yaml)
    assert cfg.time.window_min is None
    assert cfg.supply.shift_mode == "schedule"
    assert len(cfg.throughput.demand_scale_grid) == 16
    assert cfg.throughput.reference_hour == 18
    assert cfg.runner.n_procs is None


def test_tiny_overlay(tiny_cfg, default_yaml):
    default = load_config(default_yaml)
    assert tiny_cfg.space.grid_radius == 1
    assert tiny_cfg.supply.fleet_size == 10
    assert tiny_cfg.time.window_min == 120
    # Keys the overlay does not mention keep their default values.
    assert tiny_cfg.space.edge_km == default.space.edge_km
    assert tiny_cfg.supply.shift_len_mean_h == default.supply.shift_len_mean_h



# --- derived lengths (decisions H-03) -----------------------------------------


@pytest.mark.parametrize(
    "overrides, window, period",
    [
        ([], 1440, 1440),                              # days_per_run = 1
        (["time.days_per_run=2"], 2880, 1440),
        (["time.window_min=120"], 120, 120),          # tiny window: one budget period
        (["time.window_min=2880"], 2880, 1440),       # whole days are allowed
        (["time.window_min=120", "time.days_per_run=3"], 120, 120),  # days_per_run ignored
    ],
)
def test_window_and_budget_period(default_yaml, overrides, window, period):
    cfg = load_config(default_yaml, overrides)
    assert eval_window_min(cfg) == window
    assert budget_period_min(cfg) == period


def test_tiny_window(tiny_cfg):
    assert eval_window_min(tiny_cfg) == 120
    assert budget_period_min(tiny_cfg) == 120

# --- unknown / missing keys -------------------------------------------------


def test_unknown_top_level_key_raises(tmp_path, default_yaml):
    extra = write_yaml(tmp_path, {"surge": {"enabled": True}})
    with pytest.raises(ConfigError, match="unknown key"):
        load_config([default_yaml, extra])


def test_unknown_nested_key_raises(tmp_path, default_yaml):
    extra = write_yaml(tmp_path, {"space": {"grid_radus": 2}})
    with pytest.raises(ConfigError, match=r"space: unknown key\(s\) \['grid_radus'\]"):
        load_config([default_yaml, extra])


def test_missing_key_raises(tmp_path, default_yaml):
    raw = load_raw(default_yaml)
    del raw["cancel"]["eta_free_min"]
    with pytest.raises(ConfigError, match="missing key"):
        load_config(write_yaml(tmp_path, raw))


def test_duplicate_key_raises(tmp_path):
    path = tmp_path / "dup.yaml"
    path.write_text("space:\n  grid_radius: 3\n  grid_radius: 2\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate key"):
        load_config(path)


# --- --set overrides ----------------------------------------------------------


@pytest.mark.parametrize(
    "assignment, getter, expected",
    [
        ("policy.threshold.theta=0.4", lambda c: c.policy.threshold.theta, 0.4),
        ("space.grid_radius=2", lambda c: c.space.grid_radius, 2),
        ("space.edge_km=1", lambda c: c.space.edge_km, 1.0),
        ("space.torus=false", lambda c: c.space.torus, False),
        ("matching.max_ring=2", lambda c: c.matching.max_ring, 2),
        ("voucher.max_usd=5.5", lambda c: c.voucher.max_usd, 5.5),
        ("experiment.cluster_level=all", lambda c: c.experiment.cluster_level, "all"),
        ("policy.threshold.kappa=0.25", lambda c: c.policy.threshold.kappa, 0.25),
        ("policy.name=all_off", lambda c: c.policy.name, "all_off"),
        ("sweep.theta_grid=[0.0, 0.5]", lambda c: c.sweep.theta_grid, (0.0, 0.5)),
        ("time.window_min=120", lambda c: c.time.window_min, 120),
        ("supply.shift_mode=always_on", lambda c: c.supply.shift_mode, "always_on"),
        ("runner.n_procs=4", lambda c: c.runner.n_procs, 4),
    ],
)
def test_set_override_types(default_yaml, assignment, getter, expected):
    value = getter(load_config(default_yaml, [assignment]))
    assert value == expected
    assert type(value) is type(expected)


def test_set_later_override_wins(default_yaml):
    cfg = load_config(default_yaml, ["space.grid_radius=2", "space.grid_radius=4"])
    assert cfg.space.grid_radius == 4


@pytest.mark.parametrize(
    "assignment",
    [
        "space.grid_radus=2",       # unknown key
        "spaces.grid_radius=2",     # unknown section
        "space.grid_radius.x=2",    # not a section
        "space.grid_radius",        # no '='
    ],
)
def test_set_bad_key_raises(default_yaml, assignment):
    with pytest.raises(ConfigError):
        load_config(default_yaml, [assignment])


@pytest.mark.parametrize(
    "assignment",
    [
        "space.grid_radius=2.5",          # float into int
        "space.torus=1",                  # int into bool
        "space.edge_km=abc",              # str into float
        "space.edge_km=.nan",             # NaN
        "policy.name=surge",              # not an allowed choice
        "experiment.cluster_level=3",     # not 1 / 7 / all
        "policy.threshold.kappa=manual",  # neither 'auto' nor a number
        "supply.shift_mode=on",           # not schedule / always_on
        "matching.max_ring=[1]",          # list into Optional[int]
        "supply.shift_len_clip_h=[4.0]",  # wrong tuple length
    ],
)
def test_set_wrong_type_raises(default_yaml, assignment):
    with pytest.raises(ConfigError):
        load_config(default_yaml, [assignment])


@pytest.mark.parametrize(
    "assignment",
    [
        "voucher.pct_of_fare=1.5",
        "space.grid_radius=0",
        "time.tick_s=7",                       # does not divide a day
        "experiment.block_min=20",             # not a multiple of slot_min (15)
        "experiment.burnin_min=60",            # not < block_min
        "riders.x_segment_probs=[0.5, 0.5, 0.5]",
        "space.speed_factor_by_hour=[1.0, 1.0]",
        "budget.mode=fixed",                   # fixed_usd is null
        "calibration_targets.mean_gross_fare_usd=[21.0, 17.2]",
        "time.window_min=100",                 # not a multiple of slot_min (15)
        "time.window_min=0",
        "time.window_min=1500",                # > 1 day but not whole days (H-02)
        "time.warmup_min=45",                  # not a multiple of experiment.block_min (60) (H-01)
        "throughput.reference_hour=24",
        "runner.n_procs=0",
    ],
)
def test_out_of_range_raises(default_yaml, assignment):
    with pytest.raises(ConfigError, match="invalid config"):
        load_config(default_yaml, [assignment])


# --- config_hash --------------------------------------------------------------


def test_hash_same_config_same_hash(default_yaml):
    h = config_hash(load_config(default_yaml))
    assert len(h) == 12
    assert h == config_hash(load_config(default_yaml))


def test_hash_changes_with_config(default_yaml):
    assert config_hash(load_config(default_yaml)) != config_hash(
        load_config(default_yaml, ["policy.threshold.theta=0.4"])
    )


def test_hash_ignores_int_vs_float_spelling(default_yaml):
    a = load_config(default_yaml, ["space.edge_km=1"])
    b = load_config(default_yaml, ["space.edge_km=1.0"])
    assert config_hash(a) == config_hash(b)


def test_hash_same_after_roundtrip_through_yaml(tmp_path, default_yaml):
    cfg = load_config(default_yaml)
    again = load_config(write_yaml(tmp_path, to_dict(cfg)))
    assert again == cfg
    assert config_hash(again) == config_hash(cfg)


def test_config_is_frozen(default_yaml):
    cfg = load_config(default_yaml)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.space.grid_radius = 5
