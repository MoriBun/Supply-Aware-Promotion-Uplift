"""Interference and hidden confounding, measured against simulator ground truth (task T5.3).

``python -m analysis.interference designs --gte runs/b7a/gte runs/b7a/rider_ab_28d runs/b7a/switchback_c1_28d ...``
``python -m analysis.interference confounding runs/s5/legacy_gu_0_28d runs/b7a/legacy_28d ...``

**designs**: each randomized data set gives the total effect one would report from it: the
difference in the outcome rate per session, voucher minus none, times the in-window sessions
per day (every session treated against none). Switchback sessions in the burn-in minutes of a
block are left out of the difference (Hu & Wager 2022) but every session counts in the scaling.
Intervals bootstrap the randomized unit: the rider for the rider-level A/B, the (cluster, block)
for a switchback (decisions H-19a). The ground truth is the GTE of the ``gte`` runs, all_on
minus all_off without budget, paired by seed; bias = estimate - GTE (decisions T-34).

**confounding**: legacy runs that differ only in how strongly the old rule targets on the
hidden ``u_latent`` (``policy.legacy.target_g_u``). Three observational estimates of the effect
on completion against their randomized counterpart from the explore slice of the same run:
``naive`` (offered vs not, all non-explore sessions) against the explore slice; ``adjusted``
(offered vs not inside strata of observed rider features, cells with promotion on) against the
explore sessions of cells with promotion on. ``adjusted`` removes what observed columns explain,
so what is left is the bias of ``u_latent`` (decisions T-34).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from analysis.io import completed_outcome, load_run
from analysis.qini_vs_value import UnitBootstrap
from sim.runner import gte_summary

FREQ_BINS = 10


def _num(x: float, digits: int = 1) -> str:
    """Vietnamese number format (dot for thousands, comma for decimals), minus sign only."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    text = f"{abs(x):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 else "") + text


def _signed(x: float, digits: int = 1) -> str:
    text = _num(x, digits)
    return "+" + text if x is not None and not math.isnan(x) and x > 0 else text


def _run_days(run: dict) -> float:
    meta = run["run_metadata"].iloc[0]
    return float(meta["window_end_s"] - meta["window_start_s"]) / 86400.0


def _outcome(sessions: pd.DataFrame, orders: pd.DataFrame, outcome: str) -> np.ndarray:
    if outcome == "completed":
        return completed_outcome(sessions, orders).astype(np.float64)
    if outcome == "requested":
        return sessions["requested"].to_numpy(np.float64)
    raise ValueError(f"outcome must be completed or requested, got {outcome!r}")


def _rate_difference(y: np.ndarray, t: np.ndarray, w: np.ndarray | None = None) -> float:
    w = np.ones(len(y)) if w is None else w
    n1, n0 = (w * t).sum(), (w * ~t).sum()
    if n1 <= 0 or n0 <= 0:
        return math.nan
    return float((w * y * t).sum() / n1 - (w * y * ~t).sum() / n0)


# ---------------------------------------------------------------------------
# Designs against the GTE
# ---------------------------------------------------------------------------


def design_name(cfg: dict) -> str:
    e = cfg["experiment"]
    return "rider_ab" if e["design"] == "rider_ab" else f"{e['design']} cụm {e['cluster_level']}"


def design_effect(run_dir: Path | str, *, outcome: str = "completed", exclude_burnin: bool = True,
                  n_boot: int = 500, seed: int = 0) -> dict:
    """Total effect per day reported by one randomized data set, with a bootstrap over its units."""
    run = load_run(Path(run_dir))
    cfg = yaml.safe_load(run["run_metadata"]["config_yaml"].iloc[0])
    s = run["sessions"]
    s = s[s["in_window"]].reset_index(drop=True)
    if not (s["assign_mechanism"] == "experiment").all():
        raise ValueError(f"{run_dir}: not an experiment run")
    y, t = _outcome(s, run["orders"], outcome), s["arm"].to_numpy() == 1
    switchback = bool((s["cluster_id"] >= 0).all())
    unit = (s["cluster_id"].to_numpy(np.int64) * 1_000_000 + s["block"].to_numpy(np.int64)) if switchback \
        else s["rider_id"].to_numpy(np.int64)
    used = ~s["in_burnin"].to_numpy() if (switchback and exclude_burnin) else np.ones(len(s), dtype=bool)
    per_day = len(s) / _run_days(run)
    y, t, unit = y[used], t[used], unit[used]
    effect = _rate_difference(y, t)
    boot = UnitBootstrap(unit, n_boot, seed)
    draws = np.array([_rate_difference(y, t, boot[b]) for b in range(n_boot)])
    lo, hi = np.nanquantile(draws, [0.025, 0.975])
    return {"design": design_name(cfg), "run": Path(run_dir).name, "outcome": outcome,
            "n_sessions": int(used.sum()), "n_units": boot.n_units, "sessions_per_day": per_day,
            "effect_per_session": effect, "per_day": effect * per_day, "ci_lo": float(lo) * per_day,
            "ci_hi": float(hi) * per_day}


def gte_truth(gte_dir: Path | str, *, outcome: str = "completed") -> dict:
    """GTE from the ``gte`` runs: all_on minus all_off without budget, paired by seed."""
    table = pd.read_parquet(Path(gte_dir) / "results" / "policy_results.parquet")
    metric = {"completed": "N_completed", "requested": "n_requests"}[outcome]
    s = gte_summary(table.assign(N_completed=table[metric]))
    return {"GTE": s["GTE"], "GTE_se": s["GTE_se"], "n_seeds": s["n_seeds"], "N_off": s["N_off"], "N_on": s["N_on"]}


def design_table(run_dirs, gte_dir, *, outcome: str = "completed", n_boot: int = 500) -> pd.DataFrame:
    truth = gte_truth(gte_dir, outcome=outcome)
    rows = []
    for d in run_dirs:
        r = design_effect(d, outcome=outcome, n_boot=n_boot)
        r.update({"GTE": truth["GTE"], "GTE_se": truth["GTE_se"], "bias": r["per_day"] - truth["GTE"],
                  "bias_pct": 100 * (r["per_day"] - truth["GTE"]) / truth["GTE"]})
        rows.append(r)
    return pd.DataFrame(rows)


def designs_markdown(table: pd.DataFrame) -> str:
    g = table.iloc[0]
    lines = [f"GTE ({g['outcome']}/ngày, ghép cặp theo seed): {_signed(g['GTE'])} (SE {_num(g['GTE_se'])})", "",
             "| Thiết kế | Đơn vị | Ước lượng /ngày [95% CI] | Chệch so với GTE | Chệch % |", "|---|---|---|---|---|"]
    for r in table.itertuples():
        lines.append(f"| {r.design} | {_num(r.n_units, 0)} | {_signed(r.per_day)} [{_signed(r.ci_lo)}; "
                     f"{_signed(r.ci_hi)}] | {_signed(r.bias)} | {_signed(r.bias_pct)}% |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hidden confounding: strength of the targeting on u_latent
# ---------------------------------------------------------------------------


def _stratified_difference(y, t, strata, w) -> float:
    """Within-stratum rate differences averaged with the stratum sizes; strata lacking an arm are left out."""
    n_strata = int(strata.max()) + 1 if len(strata) else 0
    n1 = np.bincount(strata, weights=w * t, minlength=n_strata)
    n0 = np.bincount(strata, weights=w * ~t, minlength=n_strata)
    y1 = np.bincount(strata, weights=w * y * t, minlength=n_strata)
    y0 = np.bincount(strata, weights=w * y * ~t, minlength=n_strata)
    ok = (n1 > 0) & (n0 > 0)
    if not ok.any():
        return math.nan
    eff = y1[ok] / n1[ok] - y0[ok] / n0[ok]
    size = (n1 + n0)[ok]
    return float((eff * size).sum() / size.sum())


def confounding_estimates(run_dir: Path | str, *, n_boot: int = 200, seed: int = 0) -> dict:
    """Observational estimates of a legacy run and their randomized counterparts (effect on completion)."""
    run = load_run(Path(run_dir))
    cfg = yaml.safe_load(run["run_metadata"]["config_yaml"].iloc[0])
    if cfg["policy"]["name"] != "legacy":
        raise ValueError(f"{run_dir}: not a legacy run")
    s = run["sessions"]
    s = s[s["in_window"] & ~s["budget_blocked"]].reset_index(drop=True)
    riders = run["riders"].set_index("rider_id")
    y = completed_outcome(s, run["orders"]).astype(np.float64)
    t = s["arm"].to_numpy() == 1
    explore = (s["assign_mechanism"] == "explore").to_numpy()
    on = s["promo_on_cell"].to_numpy(bool)
    freq_edges = np.quantile(riders["x_freq"].to_numpy(np.float64), np.linspace(0, 1, FREQ_BINS + 1)[1:-1])
    r = riders.loc[s["rider_id"].to_numpy()]
    strata = (r["x_segment"].to_numpy(np.int64) * FREQ_BINS
              + np.searchsorted(freq_edges, r["x_freq"].to_numpy(np.float64), side="right"))
    adj = ~explore & on

    def estimates(w):
        return {
            "naive": _rate_difference(y[~explore], t[~explore], w[~explore]),
            "explore_all": _rate_difference(y[explore], t[explore], w[explore]),
            "adjusted": _stratified_difference(y[adj], t[adj], strata[adj], w[adj]),
            "explore_on": _rate_difference(y[explore & on], t[explore & on], w[explore & on]),
        }

    point = estimates(np.ones(len(s)))
    boot = UnitBootstrap(s["rider_id"].to_numpy(np.int64), n_boot, seed)
    draws = [estimates(boot[b]) for b in range(n_boot)]
    out = {"run": Path(run_dir).name, "target_g_u": float(cfg["policy"]["legacy"]["target_g_u"]),
           "share_offered": float(t[~explore].mean()), "n_explore": int(explore.sum()),
           "n_explore_on": int((explore & on).sum())}
    for key, value in point.items():
        out[key] = value
    for name, est, target in (("naive", "naive", "explore_all"), ("adjusted", "adjusted", "explore_on")):
        d = np.array([x[est] - x[target] for x in draws])
        out[f"bias_{name}"] = point[est] - point[target]
        out[f"bias_{name}_lo"], out[f"bias_{name}_hi"] = (float(v) for v in np.nanquantile(d, [0.025, 0.975]))
    return out


def confounding_table(run_dirs, *, n_boot: int = 200) -> pd.DataFrame:
    return pd.DataFrame([confounding_estimates(d, n_boot=n_boot) for d in run_dirs]).sort_values("target_g_u")


def confounding_markdown(table: pd.DataFrame) -> str:
    lines = ["| `target_g_u` | Phát (ngoài explore) | Thô | Explore (mọi ô) | Chệch thô [95% CI] | "
             "Điều chỉnh theo X | Explore (ô bật) | Chệch sau điều chỉnh [95% CI] |",
             "|---|---|---|---|---|---|---|---|"]
    for r in table.itertuples():
        lines.append(
            f"| {_num(r.target_g_u)} | {_num(100 * r.share_offered)}% | "
            f"{_signed(r.naive, 4)} | {_signed(r.explore_all, 4)} | {_signed(r.bias_naive, 4)} "
            f"[{_signed(r.bias_naive_lo, 4)}; {_signed(r.bias_naive_hi, 4)}] | {_signed(r.adjusted, 4)} | "
            f"{_signed(r.explore_on, 4)} | {_signed(r.bias_adjusted, 4)} "
            f"[{_signed(r.bias_adjusted_lo, 4)}; {_signed(r.bias_adjusted_hi, 4)}] |")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m analysis.interference", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("designs")
    d.add_argument("dirs", nargs="+", type=Path)
    d.add_argument("--gte", type=Path, required=True)
    d.add_argument("--outcome", choices=("completed", "requested"), default="completed")
    d.add_argument("--n-boot", type=int, default=500)
    d.add_argument("--out", type=Path, default=None)
    c = sub.add_parser("confounding")
    c.add_argument("dirs", nargs="+", type=Path)
    c.add_argument("--n-boot", type=int, default=200)
    c.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.cmd == "designs":
        table = design_table(args.dirs, args.gte, outcome=args.outcome, n_boot=args.n_boot)
        name, text = f"design_bias_{args.outcome}", designs_markdown(table)
    else:
        table = confounding_table(args.dirs, n_boot=args.n_boot)
        name, text = "confounding_by_u_latent", confounding_markdown(table)
    if args.out is not None:
        path = Path(args.out) / "results" / f"{name}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        table.to_parquet(path, index=False)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
