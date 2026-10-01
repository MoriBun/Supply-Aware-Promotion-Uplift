"""Evaluation metrics (docs/phan_cong.md T3.3): policy value with CI, paired differences, Qini / AUUC.

Policy value comes from ``results/policy_results`` (one row per seed). Standard
errors are over seeds; the normal-approximation CI uses ``z``; a bootstrap CI
is available when the number of seeds is small. Policies run with common random
numbers, so two policies are compared by the paired difference by seed (A2(b)).

The Qini and uplift curves are the plain cumulative definitions (Radcliffe
2007; the "uplift curve" of scikit-uplift), with tied scores grouped into one
point so a constant score gives a straight line. Areas are over the fraction
targeted (x in [0, 1]) so runs of different size are comparable.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

Z95 = 1.959963984540054


def _se(values: pd.Series) -> float:
    n = int(values.count())
    return float(values.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")


def value_table(policy_results: pd.DataFrame, *, z: float = Z95) -> pd.DataFrame:
    """N(pi), V(pi) and spend per policy (and theta when present): mean, SE and normal CI over seeds."""
    keys = ["policy"]
    if "theta" in policy_results.columns and policy_results["theta"].notna().any():
        keys.append("theta")
    rows = []
    for key, g in policy_results.groupby(keys, dropna=False, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(keys, key))
        row["n_seeds"] = int(len(g))
        for metric, prefix in (("N_completed", "N"), ("V_profit_usd", "V")):
            mean, se = float(g[metric].mean()), _se(g[metric])
            row[f"{prefix}_mean"], row[f"{prefix}_se"] = mean, se
            row[f"{prefix}_lo"], row[f"{prefix}_hi"] = mean - z * se, mean + z * se
        row["spent_mean"] = float(g["voucher_spent_usd"].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def paired_difference(policy_results: pd.DataFrame, a: str, b: str, *, metric: str = "N_completed",
                      theta_a: float | None = None, theta_b: float | None = None, z: float = Z95) -> dict:
    """``metric(a) - metric(b)`` paired by seed (common random numbers): mean, SE, CI, share of seeds with a > b."""
    def pick(name, theta):
        sel = policy_results["policy"] == name
        if theta is not None:
            sel &= np.isclose(policy_results["theta"].astype(float), theta)
        return policy_results.loc[sel].set_index("seed")[metric].astype(float)

    diff = (pick(a, theta_a) - pick(b, theta_b)).dropna()
    n = int(len(diff))
    if n == 0:
        raise ValueError(f"no common seeds between {a!r} and {b!r}")
    mean, se = float(diff.mean()), _se(diff)
    return {"a": a, "b": b, "metric": metric, "n_seeds": n, "mean": mean, "se": se,
            "lo": mean - z * se, "hi": mean + z * se, "share_a_better": float((diff > 0).mean())}


def bootstrap_mean_ci(values, *, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    """Percentile bootstrap CI of the mean over seeds (analysis code may use numpy's generator directly)."""
    x = np.asarray(values, dtype=np.float64)
    if len(x) == 0:
        return float("nan"), float("nan")
    gen = np.random.default_rng(seed)
    means = gen.choice(x, size=(n_boot, len(x)), replace=True).mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def uplift_curve(y, t, score) -> pd.DataFrame:
    """Cumulative Qini and uplift curves on sessions ranked by score (descending), ties grouped.

    Columns: ``k`` (sessions targeted), ``frac`` (= k / n), ``n_t``, ``n_c``, ``y_t``, ``y_c``,
    ``qini`` = ``y_t - y_c * n_t / n_c`` and ``uplift`` = ``(y_t/n_t - y_c/n_c) * k``; a term with an
    empty group counts as 0. The first row is the origin.
    """
    y = np.asarray(y, dtype=np.float64)
    t = np.asarray(t).astype(bool)
    s = np.asarray(score, dtype=np.float64)
    if not (len(y) == len(t) == len(s)):
        raise ValueError("y, t and score must have the same length")
    n = len(y)
    order = np.argsort(-s, kind="stable")
    s_sorted = s[order]
    # One point per distinct score: the last index of each tie group.
    ends = np.flatnonzero(np.r_[s_sorted[1:] != s_sorted[:-1], True]) if n else np.zeros(0, dtype=int)
    cum_t = np.cumsum(t[order])
    cum_yt = np.cumsum(y[order] * t[order])
    cum_yc = np.cumsum(y[order] * ~t[order])
    k = ends + 1
    n_t = cum_t[ends].astype(np.float64)
    n_c = k - n_t
    y_t, y_c = cum_yt[ends], cum_yc[ends]
    with np.errstate(divide="ignore", invalid="ignore"):
        qini = y_t - np.where(n_c > 0, y_c * n_t / n_c, 0.0)
        rate_t = np.where(n_t > 0, y_t / n_t, 0.0)
        rate_c = np.where(n_c > 0, y_c / n_c, 0.0)
        uplift = (rate_t - rate_c) * k
    frame = pd.DataFrame({"k": k, "frac": k / n if n else k, "n_t": n_t, "n_c": n_c, "y_t": y_t, "y_c": y_c,
                          "qini": qini, "uplift": uplift})
    origin = pd.DataFrame({c: [0.0] for c in frame.columns})
    return pd.concat([origin, frame], ignore_index=True)


def qini_auuc(y, t, score) -> dict[str, float]:
    """Areas over the fraction targeted: Qini area, its random-ranking baseline, their difference, and AUUC.

    ``qini_coef`` = area under the Qini curve minus the area under the straight line from the origin
    to the curve's end point (random ranking). NaN when there is no treated or no control session.
    """
    curve = uplift_curve(y, t, score)
    t = np.asarray(t).astype(bool)
    if len(curve) < 2 or t.all() or not t.any():
        return {k: float("nan") for k in ("qini_area", "qini_random_area", "qini_coef", "auuc", "qini_end")}
    x = curve["frac"].to_numpy()
    qini_area = float(np.trapezoid(curve["qini"].to_numpy(), x))
    qini_end = float(curve["qini"].iloc[-1])
    random_area = 0.5 * qini_end
    auuc = float(np.trapezoid(curve["uplift"].to_numpy(), x))
    return {"qini_area": qini_area, "qini_random_area": random_area, "qini_coef": qini_area - random_area,
            "auuc": auuc, "qini_end": qini_end}
