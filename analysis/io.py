"""Read a run directory written by ``sim.logger`` / ``sim.runner`` (docs/schema.md)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OBSERVED_TABLES = ("observed/riders", "observed/sessions", "observed/orders", "market/slot_snapshots")
RESULT_TABLES = ("results/policy_results", "results/theta_sweep", "results/throughput_curve", "meta/run_metadata")
HIDDEN_TABLES = ("hidden/riders_hidden", "hidden/sessions_hidden")


def load_tables(run_dir: Path, names) -> dict[str, pd.DataFrame]:
    """``{table name: frame}`` for the tables of ``names`` that exist under ``run_dir`` (keys without folder)."""
    out = {}
    for name in names:
        path = Path(run_dir) / f"{name}.parquet"
        if path.exists():
            out[name.split("/")[-1]] = pd.read_parquet(path)
    return out


def load_run(run_dir: Path) -> dict[str, pd.DataFrame]:
    """Observed, market, results and meta tables of a run. Never the hidden ones (docs/schema.md)."""
    return load_tables(run_dir, OBSERVED_TABLES + RESULT_TABLES)


def load_hidden(run_dir: Path) -> dict[str, pd.DataFrame]:
    """Ground-truth tables. For evaluation and debugging only; never join them into training data."""
    return load_tables(run_dir, HIDDEN_TABLES)


def completed_outcome(sessions: pd.DataFrame, orders: pd.DataFrame) -> np.ndarray:
    """``y`` per session row: 1 if the session's order was Completed, else 0 (no order counts as 0)."""
    done = orders.loc[orders["status"] == "Completed", "session_id"].to_numpy()
    return np.isin(sessions["session_id"].to_numpy(), done).astype(np.int8)
