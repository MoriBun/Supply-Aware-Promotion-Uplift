"""Estimated threshold theta-hat from experiment data, without and with the budget (task H5.3, decisions H-25).

Inputs:

- the voucher effect ``tau(h)`` on the completion rate of a session, and the voucher dollars paid
  per offered session ``cost(h)``, by hour of day, from the **global** switchback
  (``switchback_all_28d``). Only a global design shows the harm in the tight hours: in a cluster
  design an "on" cluster borrows idle drivers from its "off" neighbours (H5.3 log);
- the sessions a day of the policy would see, with the hour and the value of the indicator
  (``analysis.tension`` on ``all_off`` runs), e.g. ``ring1`` or ``cell_persistence``.

The policy cuts every session whose indicator is below theta. Each session is credited with the
effect and cost of its hour (the model's one assumption: within an hour the effect does not depend
on the indicator; the indicator only decides how much of each hour is cut). Per day:

- (A) harm only, no budget: ``gain_A(theta) = sum over kept sessions of tau(h)``.
  ``theta_hat_A`` = argmax; it cuts the hours where tau < 0 as far as the indicator separates them.
- (B) budget B per day spread over the kept sessions (rider tier = random score):
  ``gain_B(theta) = min(B, S(theta)) * r(theta)``, with ``S`` the spend if every kept session were
  offered and ``r = sum tau / sum cost`` over kept sessions (extra trips per dollar there).
  Cutting raises ``r`` while ``S >= B``; past that point money is left unspent.

Both are argmax over a grid; the interval comes from the unit bootstrap of ``tau`` and ``cost``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd



def hour_effects(frame: pd.DataFrame, *, n_boot: int = 500, seed: int = 0, drop_burnin: bool = True) -> dict:
    """``tau`` and ``cost`` by hour (point and ``[n_boot, 24]`` draws) from an ``experiment_frame``.

    ``tau(h)`` = completion rate on minus off; ``cost(h)`` = mean voucher paid per **on** session
    (voucher value x completed). Draws resample the (cluster, block) units with one set of
    weights shared by ``tau`` and ``cost``.
    """
    f = frame[~frame["in_burnin"]] if drop_burnin else frame
    f = f.assign(paid=f["voucher_value_usd"].to_numpy(np.float64) * f["completed"].to_numpy(np.float64))
    u = f.groupby(["hour", "unit"]).agg(arm=("arm", "first"), n=("arm", "size"), y=("completed", "sum"),
                                         paid=("paid", "sum")).reset_index()
    units = u["unit"].unique()
    col = pd.Series(np.arange(len(units)), index=units)[u["unit"]].to_numpy()
    gen = np.random.default_rng(seed)
    weights = np.vstack([np.ones(len(units)),
                         gen.multinomial(len(units), np.full(len(units), 1.0 / len(units)), size=n_boot)])
    w = weights[:, col]                                                     # [1 + n_boot, rows]
    hour, on = u["hour"].to_numpy(), u["arm"].to_numpy() == 1
    n, y, paid = (u[c].to_numpy(np.float64) for c in ("n", "y", "paid"))
    tau = np.full((len(weights), 24), np.nan)
    cost = np.full((len(weights), 24), np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        for h in range(24):
            m1, m0 = (hour == h) & on, (hour == h) & ~on
            n1, n0 = w[:, m1] @ n[m1], w[:, m0] @ n[m0]
            tau[:, h] = (w[:, m1] @ y[m1]) / n1 - (w[:, m0] @ y[m0]) / n0
            cost[:, h] = (w[:, m1] @ paid[m1]) / n1
    return {"tau": tau[0], "cost": cost[0], "tau_draws": tau[1:], "cost_draws": cost[1:]}


def gain_curves(indicator: np.ndarray, hour: np.ndarray, n_days: float, tau: np.ndarray, cost: np.ndarray,
                budget_per_day: float, grid) -> pd.DataFrame:
    """``gain_A`` and ``gain_B`` (trips per day) for every theta of ``grid``."""
    x = np.asarray(indicator, dtype=np.float64)
    h = np.asarray(hour, dtype=np.int64)
    t, c = np.asarray(tau)[h], np.asarray(cost)[h]
    rows = []
    for theta in grid:
        keep = ~(x < theta)                                   # NaN keeps the cell on, as the policy does
        sum_tau, spend = t[keep].sum() / n_days, c[keep].sum() / n_days
        rate = sum_tau / spend if spend > 0 else 0.0
        rows.append({"theta": float(theta), "share_cut": float(1 - keep.mean()), "gain_A": sum_tau,
                     "spend_all_on": spend, "gain_B": min(budget_per_day, spend) * rate})
    return pd.DataFrame(rows)


def theta_hat(indicator, hour, n_days: float, effects: dict, budget_per_day: float, grid,
              alpha: float = 0.05) -> dict:
    """Point estimate and bootstrap interval of ``theta_hat_A`` and ``theta_hat_B``."""
    grid = np.asarray(grid, dtype=np.float64)
    curves = gain_curves(indicator, hour, n_days, effects["tau"], effects["cost"], budget_per_day, grid)
    out = {"curves": curves}
    draws = {"A": [], "B": []}
    for tau_b, cost_b in zip(effects["tau_draws"], effects["cost_draws"]):
        cb = gain_curves(indicator, hour, n_days, tau_b, cost_b, budget_per_day, grid)
        draws["A"].append(grid[int(np.nanargmax(cb["gain_A"]))])
        draws["B"].append(grid[int(np.nanargmax(cb["gain_B"]))])
    for k in ("A", "B"):
        d = np.asarray(draws[k])
        lo, hi = np.quantile(d, [alpha / 2, 1 - alpha / 2])
        out[f"theta_hat_{k}"] = float(grid[int(np.nanargmax(curves[f"gain_{k}"]))])
        out[f"ci_{k}"] = (float(lo), float(hi))
    return out
