"""M12 Logger: Parquet tables of docs/schema.md split into observed/, hidden/, market/, results/, meta/.

Spec: docs/spec.md §4.12. Milestone: P2 (results and meta tables, tasks T1.4, T2.4), P5 (observed /
hidden / market tables, task T3.2).

``RESULTS_TABLES`` and ``META_COLUMNS`` hold the on-disk column order and
Arrow-style dtypes; ``tests/test_schema_contract.py`` checks them against
docs/schema.md.
"""

from __future__ import annotations

import functools
import subprocess
from pathlib import Path

import pandas as pd

RESULTS_TABLES: dict[str, dict[str, str]] = {
    "policy_results": {
        "run_id": "string", "policy": "string", "theta": "float64", "seed": "int32",
        "N_completed": "int64", "V_profit_usd": "float64", "voucher_spent_usd": "float64",
        "budget_B_usd": "float64",
        "n_sessions": "int64", "n_requests": "int64", "n_abandoned": "int64", "n_cancelled": "int64",
        "mean_pickup_eta_min": "float64", "share_cells_off": "float64", "n_switches_per_cell_day": "float64",
        "runtime_s": "float64",
    },
    "theta_sweep": {
        "theta": "float64", "N_mean": "float64", "N_se": "float64", "V_mean": "float64", "V_se": "float64",
        "spent_mean": "float64", "n_seeds": "int32", "is_argmax": "bool",
    },
    "throughput_curve": {
        "run_id": "string", "demand_scale": "float64", "fleet_size": "int32", "seed": "int32",
        "completed_per_h": "float64", "requests_per_h": "float64", "mean_pickup_eta_min": "float64",
        "mean_slack": "float64", "abandon_rate": "float64", "cancel_rate": "float64",
    },
}

META_COLUMNS: dict[str, str] = {
    "run_id": "string", "mode": "string", "config_hash": "string", "config_yaml": "string", "git_sha": "string",
    "policy": "string", "theta": "float64", "seed": "int32", "world_seed": "int64", "budget_B_usd": "float64",
    "kappa": "float64", "window_start_s": "float64", "window_end_s": "float64", "sim_end_s": "float64",
    "n_truncated_orders": "int32", "runtime_s": "float64", "created_at": "string",
}


def cast_table(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """Columns in schema order with schema dtypes; missing or extra columns are an error."""
    missing, extra = set(columns) - set(df.columns), set(df.columns) - set(columns)
    if missing or extra:
        raise ValueError(f"table columns: missing {sorted(missing)}, unexpected {sorted(extra)}")
    return pd.DataFrame({name: df[name].astype(dtype) for name, dtype in columns.items()})


def write_table(out_dir: Path, folder: str, name: str, df: pd.DataFrame, columns: dict[str, str]) -> Path:
    path = Path(out_dir) / folder / f"{name}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    cast_table(df, columns).to_parquet(path, index=False)
    return path


def write_results(out_dir: Path, name: str, df: pd.DataFrame) -> Path:
    """Write ``results/<name>.parquet`` under ``out_dir`` and return its path."""
    return write_table(out_dir, "results", name, df, RESULTS_TABLES[name])


def write_metadata(out_dir: Path, df: pd.DataFrame) -> Path:
    """Write ``meta/run_metadata.parquet`` (one row per run)."""
    return write_table(out_dir, "meta", "run_metadata", df, META_COLUMNS)


@functools.lru_cache(maxsize=1)
def git_sha() -> str:
    """Commit of the code, or ``"unknown"`` outside a git checkout."""
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                             cwd=Path(__file__).resolve().parents[1], timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return out.stdout.strip() or "unknown"
