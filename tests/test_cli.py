"""``python -m sim run``: config validation, mode dispatch, throughput_curve end to end (spec §7; task T1.4)."""

import subprocess
import sys
from pathlib import Path

import pandas as pd

from sim.cli import main
from sim.config import config_hash, load_config

ROOT = Path(__file__).resolve().parents[1]

# The real engine runs with stubs for the other steps until B3, so demand must be zero
# (pricing.quote accepts no sessions before T2.1; decisions H-05 f). Small grid, one process.
ZERO_DEMAND = ["--set", "demand.base_sessions_per_cell_h=0", "--set", "throughput.n_seeds=1",
               "--set", "throughput.demand_scale_grid=[0.5, 1.0]", "--set", "runner.n_procs=1"]


def _configs(paths) -> list[str]:
    args = []
    for p in paths:
        args += ["--config", str(p)]
    return args


def test_unimplemented_mode_prints_hash_and_exits_1(capsys, default_yaml):
    assert main(["run", "--mode", "evaluate", "--config", str(default_yaml),
                 "--set", "policy.threshold.theta=0.4"]) == 1
    out, err = capsys.readouterr()
    expected = config_hash(load_config(default_yaml, ["policy.threshold.theta=0.4"]))
    assert f"config_hash={expected}" in out and "T2.4" in err


def test_run_accepts_layered_configs(capsys, tiny_layers):
    assert main(["run", "--mode", "gte"] + _configs(tiny_layers)) == 1
    assert f"config_hash={config_hash(load_config(tiny_layers))}" in capsys.readouterr().out


def test_run_rejects_bad_config(capsys, default_yaml):
    assert main(["run", "--mode", "evaluate", "--config", str(default_yaml),
                 "--set", "space.grid_radus=2"]) == 2
    assert "config error" in capsys.readouterr().err


def test_throughput_curve_writes_results(capsys, tiny_layers, tmp_path):
    code = main(["run", "--mode", "throughput_curve"] + _configs(tiny_layers) + ZERO_DEMAND + ["--out", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert f"out={tmp_path}" in out and "demand_scale" in out and "completed_per_h" in out
    table = pd.read_parquet(tmp_path / "results" / "throughput_curve.parquet")
    assert table["demand_scale"].tolist() == [0.5, 1.0] and table["seed"].tolist() == [0, 0]
    assert (table["completed_per_h"] == 0.0).all()          # stubs: no trips yet


def test_python_dash_m_entry_point(tiny_layers, tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "sim", "run", "--mode", "throughput_curve"] + _configs(tiny_layers) + ZERO_DEMAND
        + ["--out", str(tmp_path)],
        capture_output=True, text=True, check=False, cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert "config_hash=" in result.stdout and (tmp_path / "results" / "throughput_curve.parquet").exists()
