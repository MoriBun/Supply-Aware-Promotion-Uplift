"""P0: ``python -m sim run`` validates the config and prints its hash."""

import subprocess
import sys
from pathlib import Path

from sim.cli import main
from sim.config import config_hash, load_config


def test_run_prints_config_hash(capsys, default_yaml):
    assert main(["run", "--mode", "evaluate", "--config", str(default_yaml),
                 "--set", "policy.threshold.theta=0.4"]) == 0
    expected = config_hash(load_config(default_yaml, ["policy.threshold.theta=0.4"]))
    assert f"config_hash={expected}" in capsys.readouterr().out


def test_run_accepts_layered_configs(capsys, tiny_layers):
    args = ["run", "--mode", "gte"]
    for path in tiny_layers:
        args += ["--config", str(path)]
    assert main(args) == 0
    assert f"config_hash={config_hash(load_config(tiny_layers))}" in capsys.readouterr().out


def test_run_rejects_bad_config(capsys, default_yaml):
    assert main(["run", "--mode", "evaluate", "--config", str(default_yaml),
                 "--set", "space.grid_radus=2"]) == 2
    assert "config error" in capsys.readouterr().err


def test_python_dash_m_entry_point(default_yaml):
    result = subprocess.run(
        [sys.executable, "-m", "sim", "run", "--mode", "evaluate", "--config", str(default_yaml)],
        capture_output=True, text=True, check=False, cwd=Path(__file__).resolve().parents[1],
    )
    assert result.returncode == 0, result.stderr
    assert "config_hash=" in result.stdout
