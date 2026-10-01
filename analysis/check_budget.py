"""Budget audit of a run directory: ``python -m analysis.check_budget runs/<out>``.

Reads what ``evaluate`` / ``sweep_theta`` / ``generate`` wrote with ``--log-level full``
(observed/ tables at the root for one run, or under ``runs/<run_id>/`` for several)
and prints, per run: B, spend per budget period against its limit (warm-up gets
``B * warmup / period``), how many sessions were offered or blocked, the first hour
the budget ran out, and the ledger fate of every voucher by order outcome
(docs/spec.md §4.3, decisions T-03). Exit code 1 when a limit is exceeded.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml


def run_dirs(out: Path) -> list[tuple[str, Path]]:
    results = pd.read_parquet(out / "results" / "policy_results.parquet")
    if (out / "observed" / "sessions.parquet").exists():
        return [(results["run_id"].iloc[0], out)]
    return [(rid, out / "runs" / rid) for rid in results["run_id"]]


def period_limits(meta_row: pd.Series) -> tuple[float, float]:
    """``(B, warm-up budget)`` of a run from its metadata row."""
    cfg = yaml.safe_load(meta_row["config_yaml"])
    t = cfg["time"]
    window = t["window_min"] if t["window_min"] is not None else t["days_per_run"] * 1440
    period = min(1440, window)
    budget = float(meta_row["budget_B_usd"])
    return budget, budget * t["warmup_min"] / period


def audit_run(run_id: str, folder: Path, meta: pd.DataFrame) -> bool:
    s = pd.read_parquet(folder / "observed" / "sessions.parquet")
    o = pd.read_parquet(folder / "observed" / "orders.parquet")
    row = meta.set_index("run_id").loc[run_id]
    budget, warmup_budget = period_limits(row)
    ok = True
    print(f"\n{run_id}")
    print(f"  policy={row['policy']}  B={budget:.2f} USD/kỳ  kappa={row['kappa']}")

    win = s[s["in_window"]]
    n_on = int(win["promo_on_cell"].sum())
    print(f"  session trong cửa sổ {len(win)}: ô bật {n_on}, được phát {int(win['arm'].sum())}, "
          f"bị chặn {int(win['budget_blocked'].sum())}"
          + (f" ({win['budget_blocked'].sum() / n_on:.1%} của ô bật)" if n_on else ""))
    if win["budget_blocked"].any():
        first = win.loc[win["budget_blocked"], "open_time_s"].min() / 3600
        print(f"  ngân sách bắt đầu chặn lúc {int(first):02d}:{int(first % 1 * 60):02d} (giờ mô phỏng)")
    if budget != budget:                                    # NaN: no budget
        print("  không áp ngân sách")

    spent = (o[o["status"] == "Completed"].merge(s[["session_id", "budget_period"]], on="session_id")
             .groupby("budget_period")["voucher_value_usd"].sum())
    print("  chi tiêu (voucher của order Completed) theo kỳ:")
    for period, value in spent.items():
        limit = warmup_budget if period < 0 else budget
        verdict = "OK" if (limit != limit or value <= limit + 1e-6) else "VI PHẠM"
        ok &= verdict == "OK"
        print(f"    kỳ {period:>3}: {value:10.2f} ≤ {limit:10.2f}  {verdict}")

    blocked = win[win["budget_blocked"]]
    if len(blocked):
        clean = bool((blocked["arm"] == 0).all() and (blocked["voucher_value_usd"] == 0).all()
                     and blocked["promo_on_cell"].all())
        ok &= clean
        print(f"  session bị chặn: arm = 0, voucher = 0, ô vẫn bật: {'OK' if clean else 'SAI'}")

    with_voucher = s[s["voucher_value_usd"] > 0]
    fate = with_voucher.merge(o[["session_id", "status"]], on="session_id", how="left")
    fate["kết cục"] = fate["status"].fillna("không đặt")
    counts = fate.groupby("kết cục")["voucher_value_usd"].agg(["size", "sum"])
    print("  số phận của voucher đã phát (Completed = chi, còn lại = nhả):")
    for name, (n, usd) in counts.iterrows():
        print(f"    {name:<12} {int(n):7d} session  {usd:10.2f} USD")
    return ok


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    out = Path(argv[1])
    meta = pd.read_parquet(out / "meta" / "run_metadata.parquet")
    ok = True
    for run_id, folder in run_dirs(out):
        ok &= audit_run(run_id, folder, meta)
    print("\nKẾT LUẬN:", "mọi kỳ trong ngân sách" if ok else "CÓ VI PHẠM")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
