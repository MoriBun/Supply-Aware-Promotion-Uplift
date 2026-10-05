"""Qini against policy value: a score can rank uplift better and still give fewer trips under B (task T5.2).

``python -m analysis.qini_vs_value --data runs/b7a/rider_ab_28d --table runs/s5/policy_table
[--outcome completed] [--n-boot 200] [--out runs/s5/qini_vs_value]``

Qini is computed the way an uplift team would: on randomized data (default the rider-level A/B
of B7a, which none of the H4.2 baselines was fitted on), with the session's own outcome. Each
score is the policy's own ``score_fn`` applied to the logged sessions: a ``SessionBatch`` built
from observed columns only, and ``s_hat`` = the cell's slack in the previous slot, as the
policy would have seen it. Confidence intervals resample riders, the unit randomized in that
data. N(pi) comes from the policy table of task T5.1 (threshold policy at theta = 0 with that
score, kappa-auto, budget B), and differences are paired by seed.

A pair (a, b) is an example for the acceptance criterion "Qini higher but N lower" when the
Qini of a is higher than the Qini of b and N(a) is lower than N(b), both with 95% intervals that
exclude 0 (decisions T-33).
"""

from __future__ import annotations

import argparse
import math
import sys
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.io import completed_outcome, load_run
from sim.policies.base import SessionBatch
from sim.policies.scores import load_score_fn, score_batch

Z95 = 1.959963984540054


# ---------------------------------------------------------------------------
# Scoring logged sessions with a policy's score function
# ---------------------------------------------------------------------------


def session_batch(sessions: pd.DataFrame, riders: pd.DataFrame, *, seed: int = 0) -> SessionBatch:
    """Observed columns of logged sessions as a ``SessionBatch``.

    The pre-drawn policy uniforms are hidden columns (docs/schema.md), so they are not read:
    ``u_score`` is a fresh uniform (what ``score_fn = random`` returns), the others are NaN.
    """
    r = riders.set_index("rider_id").loc[sessions["rider_id"].to_numpy(), ["x_freq", "x_tenure", "x_segment"]]
    n = len(sessions)
    nan = np.full(n, np.nan)
    col = lambda name, dtype: sessions[name].to_numpy(dtype)   # noqa: E731
    return SessionBatch(
        session_id=col("session_id", np.int64), rider_id=col("rider_id", np.int32),
        open_time_s=col("open_time_s", np.float64), day=col("day", np.int16), hour=col("hour", np.int16),
        slot=col("slot", np.int16), slot_of_day=col("slot_of_day", np.int16), pu_cell=col("pu_cell", np.int16),
        do_cell=col("do_cell", np.int16), x_freq=r["x_freq"].to_numpy(np.float32),
        x_tenure=r["x_tenure"].to_numpy(np.float32), x_segment=r["x_segment"].to_numpy(np.int8),
        quoted_fare_usd=col("quoted_fare_usd", np.float32), quoted_eta_min=col("quoted_eta_min", np.float32),
        no_supply=col("no_supply", bool), u_target=nan, u_explore=nan, u_explore_arm=nan,
        u_score=np.random.default_rng(seed).random(n),
    )


def slack_hat(sessions: pd.DataFrame, snapshots: pd.DataFrame) -> np.ndarray:
    """Persistence forecast of each session's cell: ``slack_lag_slot`` of (slot, pu_cell); NaN if unknown."""
    lag = snapshots[["slot", "cell", "slack_lag_slot"]].rename(columns={"cell": "pu_cell"})
    merged = sessions[["slot", "pu_cell"]].merge(lag, on=["slot", "pu_cell"], how="left")
    return merged["slack_lag_slot"].to_numpy(np.float64)


def score_sessions(sessions: pd.DataFrame, riders: pd.DataFrame, snapshots: pd.DataFrame, score_fn: str, *,
                   seed: int = 0) -> np.ndarray:
    """The scores a threshold policy with ``score_fn`` would give the logged sessions (float32)."""
    batch = session_batch(sessions, riders, seed=seed)
    return score_batch(load_score_fn(score_fn), batch, slack_hat(sessions, snapshots))


# ---------------------------------------------------------------------------
# Qini with sample weights (bootstrap)
# ---------------------------------------------------------------------------


class RankedSessions:
    """Sessions sorted once by a score (descending) with the end of each tie group, for fast reweighting."""

    def __init__(self, y, t, score) -> None:
        score = np.asarray(score, dtype=np.float64)
        self.order = np.argsort(-score, kind="stable")
        s = score[self.order]
        self.ends = np.flatnonzero(np.r_[s[1:] != s[:-1], True]) if len(s) else np.zeros(0, dtype=int)
        self.y = np.asarray(y, dtype=np.float64)[self.order]
        self.t = np.asarray(t).astype(bool)[self.order]

    def qini_coef(self, weights=None) -> float:
        """Qini coefficient as in ``analysis.metrics.qini_auuc``, with a weight (multiplicity) per session.

        With unit weights it equals ``qini_auuc(y, t, score)["qini_coef"]``: area under
        ``Q(k) = Y_T(k) - Y_C(k) N_T(k) / N_C(k)`` over the share targeted, minus the area of the
        straight line to the end point (T-27).
        """
        w = np.ones(len(self.y)) if weights is None else np.asarray(weights, dtype=np.float64)[self.order]
        if len(self.ends) == 0:
            return math.nan
        k = np.cumsum(w)[self.ends]
        n_t = np.cumsum(w * self.t)[self.ends]
        n_c = k - n_t
        y_t = np.cumsum(w * self.y * self.t)[self.ends]
        y_c = np.cumsum(w * self.y * ~self.t)[self.ends]
        if n_t[-1] <= 0 or n_c[-1] <= 0:
            return math.nan
        with np.errstate(divide="ignore", invalid="ignore"):
            q = y_t - np.where(n_c > 0, y_c * n_t / n_c, 0.0)
        x = np.r_[0.0, k / k[-1]]
        q = np.r_[0.0, q]
        return float(np.trapezoid(q, x) - 0.5 * q[-1])


class UnitBootstrap:
    """Bootstrap over units: draw ``b`` gives each session the number of times its unit was drawn.

    Only the ``[n_boot, n_units]`` counts are stored; a draw's session weights are built on demand.
    """

    def __init__(self, units, n_boot: int, seed: int) -> None:
        codes, self.inverse = np.unique(np.asarray(units), return_inverse=True)
        gen = np.random.default_rng(seed)
        self.counts = gen.multinomial(len(codes), np.full(len(codes), 1.0 / len(codes)), size=n_boot)
        self.n_units = len(codes)

    def __len__(self) -> int:
        return len(self.counts)

    def __getitem__(self, b: int) -> np.ndarray:
        return self.counts[b][self.inverse].astype(np.float64)


# ---------------------------------------------------------------------------
# Qini table, policy value, and the pairs
# ---------------------------------------------------------------------------


def randomized_sessions(run_dir: Path, *, outcome: str = "completed", explore_only: bool = False) -> dict:
    """In-window sessions of a randomized run with ``y`` (completed or requested), ``t`` (arm) and ``unit``.

    ``explore_only`` keeps the explore slice of a legacy run (propensity 0.5). The unit is the rider
    for rider-level randomization and the (cluster, block) for a switchback.
    """
    run = load_run(Path(run_dir))
    s = run["sessions"]
    s = s[s["in_window"] & ~s["budget_blocked"]]
    if explore_only:
        s = s[s["assign_mechanism"] == "explore"]
    elif not (s["assign_mechanism"] == "experiment").all():
        raise ValueError(f"{run_dir}: not a randomized run; use explore_only for a legacy run")
    s = s.reset_index(drop=True)
    if outcome == "completed":
        y = completed_outcome(s, run["orders"]).astype(np.float64)
    elif outcome == "requested":
        y = s["requested"].to_numpy(np.float64)
    else:
        raise ValueError(f"outcome must be completed or requested, got {outcome!r}")
    switchback = (s["cluster_id"] >= 0).all() and not explore_only
    unit = (s["cluster_id"].to_numpy(np.int64) * 1_000_000 + s["block"].to_numpy(np.int64)) if switchback \
        else s["rider_id"].to_numpy(np.int64)
    return {"sessions": s, "riders": run["riders"], "snapshots": run["slot_snapshots"], "y": y,
            "t": s["arm"].to_numpy() == 1, "unit": unit}


def qini_table(data: dict, scores: dict[str, str], *, n_boot: int = 200, seed: int = 0) -> tuple[pd.DataFrame, dict]:
    """Qini coefficient per label with a bootstrap over units; also returns the bootstrap draws per label."""
    w = UnitBootstrap(data["unit"], n_boot, seed)
    rows, draws = [], {}
    for label, score_fn in scores.items():
        ranked = RankedSessions(data["y"], data["t"], score_sessions(data["sessions"], data["riders"],
                                                                    data["snapshots"], score_fn, seed=seed))
        point = ranked.qini_coef()
        boot = np.array([ranked.qini_coef(w[b]) for b in range(n_boot)])
        draws[label] = boot
        lo, hi = np.nanquantile(boot, [0.025, 0.975])
        rows.append({"label": label, "score_fn": score_fn, "qini_coef": point, "qini_lo": float(lo),
                     "qini_hi": float(hi), "n_sessions": len(data["y"]), "n_distinct_scores": len(ranked.ends)})
    return pd.DataFrame(rows), draws


def policy_runs(table_dir: Path) -> pd.DataFrame:
    """Per-seed results of the T5.1 policy table, with their labels."""
    runs = pd.read_parquet(Path(table_dir) / "results" / "policy_results.parquet")
    labels = pd.read_parquet(Path(table_dir) / "results" / "policy_labels.parquet")
    return runs.merge(labels, on="run_id")


def compare_pairs(qini: pd.DataFrame, draws: dict, runs: pd.DataFrame) -> pd.DataFrame:
    """Every ordered pair (a, b): Qini(a) - Qini(b) with a bootstrap interval, N(a) - N(b) paired by seed."""
    n = runs.pivot(index="seed", columns="label", values="N_completed")
    rows = []
    for a, b in permutations(qini["label"], 2):
        if a not in n.columns or b not in n.columns:
            continue
        q = qini.set_index("label")
        dq = float(q.loc[a, "qini_coef"] - q.loc[b, "qini_coef"])
        dq_lo, dq_hi = np.nanquantile(draws[a] - draws[b], [0.025, 0.975])
        diff = (n[a] - n[b]).dropna()
        se = float(diff.std(ddof=1) / math.sqrt(len(diff))) if len(diff) > 1 else math.nan
        dn = float(diff.mean())
        rows.append({"a": a, "b": b, "dqini": dq, "dqini_lo": float(dq_lo), "dqini_hi": float(dq_hi),
                     "dN": dn, "dN_se": se, "dN_lo": dn - Z95 * se, "dN_hi": dn + Z95 * se, "n_seeds": len(diff),
                     "qini_higher_n_lower": bool(dq_lo > 0 and dn + Z95 * se < 0)})
    return pd.DataFrame(rows)


def _vn(x: float, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    text = f"{abs(x):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 else "") + text


def markdown(qini: pd.DataFrame, pairs: pd.DataFrame, runs: pd.DataFrame) -> str:
    n = runs.groupby("label")["N_completed"].agg(["mean", "std", "count"])
    lines = ["| Hàm điểm | Qini (95% CI, bootstrap theo đơn vị) | N dưới B (± SE) |", "|---|---|---|"]
    for r in qini.sort_values("qini_coef", ascending=False).itertuples():
        nm = n.loc[r.label] if r.label in n.index else None
        n_txt = "—" if nm is None else f"{_vn(nm['mean'])} ± {_vn(nm['std'] / math.sqrt(nm['count']))}"
        lines.append(f"| `{r.label}` | {_vn(r.qini_coef)} [{_vn(r.qini_lo)}; {_vn(r.qini_hi)}] | {n_txt} |")
    hits = pairs[pairs["qini_higher_n_lower"]]
    lines += ["", "| a | b | Qini(a) − Qini(b) [95% CI] | N(a) − N(b) (± SE, ghép cặp) |", "|---|---|---|---|"]
    for r in hits.sort_values("dN").itertuples():
        lines.append(f"| `{r.a}` | `{r.b}` | {_vn(r.dqini)} [{_vn(r.dqini_lo)}; {_vn(r.dqini_hi)}] | "
                     f"{_vn(r.dN)} ± {_vn(r.dN_se)} |")
    if hits.empty:
        lines.append("| — | — | không có cặp nào thỏa cả hai điều kiện | |")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m analysis.qini_vs_value", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, required=True, help="randomized run (rider_ab, switchback) or legacy")
    parser.add_argument("--explore-only", action="store_true", help="use the explore slice of a legacy run")
    parser.add_argument("--table", type=Path, required=True, help="output directory of analysis.policy_table")
    parser.add_argument("--outcome", choices=("completed", "requested"), default="completed")
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    runs = policy_runs(args.table)
    scored = runs[(runs["policy"] == "threshold") & (runs["theta"] == 0.0)]
    scores = dict(scored.groupby("label")["score_fn"].first())
    data = randomized_sessions(args.data, outcome=args.outcome, explore_only=args.explore_only)
    qini, draws = qini_table(data, scores, n_boot=args.n_boot)
    pairs = compare_pairs(qini, draws, runs)
    if args.out is not None:
        out = Path(args.out) / "results"
        out.mkdir(parents=True, exist_ok=True)
        qini.to_parquet(out / f"qini_{args.outcome}.parquet", index=False)
        pairs.to_parquet(out / f"qini_pairs_{args.outcome}.parquet", index=False)
    print(f"data {args.data} ({'explore slice' if args.explore_only else 'all sessions'}), outcome {args.outcome}, "
          f"{len(data['y'])} sessions, {len(np.unique(data['unit']))} units, {args.n_boot} bootstrap draws")
    print(markdown(qini, pairs, runs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
