"""M12 Logger: Parquet tables of docs/schema.md split into observed/, hidden/, market/, results/, meta/.

Spec: docs/spec.md §4.12. Milestone: P2 (results tables, this file), P5 (full, task T3.2).

``RESULTS_TABLES`` holds the on-disk column order and Arrow-style dtypes of the
``results/`` tables; ``tests/test_schema_contract.py`` checks them against
docs/schema.md.
"""

from __future__ import annotations

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
    "throughput_curve": {
        "run_id": "string", "demand_scale": "float64", "fleet_size": "int32", "seed": "int32",
        "completed_per_h": "float64", "requests_per_h": "float64", "mean_pickup_eta_min": "float64",
        "mean_slack": "float64", "abandon_rate": "float64", "cancel_rate": "float64",
    },
}


def cast_table(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """Columns in schema order with schema dtypes; missing or extra columns are an error."""
    missing, extra = set(columns) - set(df.columns), set(df.columns) - set(columns)
    if missing or extra:
        raise ValueError(f"table columns: missing {sorted(missing)}, unexpected {sorted(extra)}")
    return pd.DataFrame({name: df[name].astype(dtype) for name, dtype in columns.items()})


def write_results(out_dir: Path, name: str, df: pd.DataFrame) -> Path:
    """Write ``results/<name>.parquet`` under ``out_dir`` and return its path."""
    path = Path(out_dir) / "results" / f"{name}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    cast_table(df, RESULTS_TABLES[name]).to_parquet(path, index=False)
    return path
