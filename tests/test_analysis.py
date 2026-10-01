"""analysis/ (docs/phan_cong.md T3.3): policy value with CI, paired differences, Qini / AUUC, run loading."""

import math

import numpy as np
import pandas as pd
import pytest

from analysis.io import HIDDEN_TABLES, completed_outcome, load_hidden, load_run
from analysis.metrics import bootstrap_mean_ci, paired_difference, qini_auuc, uplift_curve, value_table
from sim.config import load_config
from sim.runner import evaluate
from tests.conftest import ROOT

TINY = [ROOT / "config" / "default.yaml", ROOT / "tests" / "fixtures" / "tiny.yaml"]


# --- policy value ------------------------------------------------------------------------------


def results_frame() -> pd.DataFrame:
    rows = []
    for seed, (n_on, n_off) in enumerate(((100, 90), (110, 95), (105, 100), (120, 101))):
        rows.append({"policy": "all_on", "theta": np.nan, "seed": seed, "N_completed": n_on,
                     "V_profit_usd": 1.0 * n_on, "voucher_spent_usd": 50.0})
        rows.append({"policy": "all_off", "theta": np.nan, "seed": seed, "N_completed": n_off,
                     "V_profit_usd": 2.0 * n_off, "voucher_spent_usd": 0.0})
    return pd.DataFrame(rows)


def test_value_table_means_and_cis():
    t = value_table(results_frame()).set_index("policy")
    assert list(t.index) == ["all_off", "all_on"] and (t["n_seeds"] == 4).all()
    on = t.loc["all_on"]
    assert on["N_mean"] == 108.75 and on["N_se"] == pytest.approx(np.std([100, 110, 105, 120], ddof=1) / 2)
    assert on["N_lo"] == pytest.approx(on["N_mean"] - 1.959964 * on["N_se"], rel=1e-6)
    assert on["N_hi"] > on["N_mean"] > on["N_lo"] and on["spent_mean"] == 50.0 and on["V_mean"] == 108.75
    assert "theta" not in t.columns                                           # all NaN: not a key
    single = value_table(results_frame().iloc[:2])
    assert math.isnan(single["N_se"][0])                                      # one seed: no SE


def test_value_table_groups_by_theta_when_present():
    df = results_frame()
    df["theta"] = [0.0, 0.0, 0.5, 0.5] * 2
    t = value_table(df)
    assert list(t.columns[:2]) == ["policy", "theta"] and len(t) == 4
    assert t[(t.policy == "all_on") & (t.theta == 0.5)]["n_seeds"].iloc[0] == 2


def test_paired_difference_by_seed():
    d = paired_difference(results_frame(), "all_on", "all_off")
    assert d["n_seeds"] == 4 and d["mean"] == pytest.approx(np.mean([10, 15, 5, 19]))
    assert d["se"] == pytest.approx(np.std([10, 15, 5, 19], ddof=1) / 2) and d["share_a_better"] == 1.0
    assert d["lo"] < d["mean"] < d["hi"]
    v = paired_difference(results_frame(), "all_on", "all_off", metric="V_profit_usd")
    assert v["mean"] == pytest.approx(np.mean([100 - 180, 110 - 190, 105 - 200, 120 - 202]))
    with pytest.raises(ValueError):
        paired_difference(results_frame(), "all_on", "legacy")


def test_bootstrap_ci_contains_the_mean_and_is_deterministic():
    x = np.array([100, 110, 105, 120], dtype=float)
    lo, hi = bootstrap_mean_ci(x, n_boot=500, seed=1)
    assert lo <= x.mean() <= hi and (lo, hi) == bootstrap_mean_ci(x, n_boot=500, seed=1)
    assert all(math.isnan(v) for v in bootstrap_mean_ci([]))


# --- Qini / AUUC --------------------------------------------------------------------------------


def test_uplift_curve_perfect_ranking():
    y, t, score = [1, 0, 0, 0], [1, 0, 1, 0], [0.9, 0.8, 0.2, 0.1]
    curve = uplift_curve(y, t, score)
    assert curve["k"].tolist() == [0, 1, 2, 3, 4] and curve["frac"].tolist() == [0, 0.25, 0.5, 0.75, 1.0]
    assert curve["n_t"].tolist() == [0, 1, 1, 2, 2] and curve["n_c"].tolist() == [0, 0, 1, 1, 2]
    assert curve["qini"].tolist() == [0, 1, 1, 1, 1]                             # empty control group counts 0
    assert curve["uplift"].tolist() == [0, 1, 2, 1.5, 2]
    areas = qini_auuc(y, t, score)
    assert areas["qini_end"] == 1.0 and areas["qini_random_area"] == 0.5
    assert areas["qini_area"] == pytest.approx(0.875) and areas["qini_coef"] == pytest.approx(0.375)
    assert areas["auuc"] == pytest.approx(np.trapezoid([0, 1, 2, 1.5, 2], [0, 0.25, 0.5, 0.75, 1.0]))


def test_uplift_curve_groups_tied_scores():
    y, t = [1, 0, 1, 0, 0, 1], [1, 0, 1, 0, 1, 0]
    curve = uplift_curve(y, t, [0.9, 0.9, 0.9, 0.1, 0.1, 0.1])
    assert curve["k"].tolist() == [0, 3, 6]                                      # one point per distinct score
    assert curve["qini"].iloc[1] == pytest.approx(2 - 0 * 2 / 1) and curve["qini"].iloc[2] == pytest.approx(2 - 1 * 3 / 3)
    constant = qini_auuc(y, t, [0.5] * 6)
    assert constant["qini_coef"] == pytest.approx(0.0)                            # a constant score is the random line


def test_qini_is_nan_without_both_arms_and_checks_lengths():
    assert all(math.isnan(v) for v in qini_auuc([1, 0], [1, 1], [0.2, 0.1]).values())
    assert all(math.isnan(v) for v in qini_auuc([1, 0], [0, 0], [0.2, 0.1]).values())
    with pytest.raises(ValueError):
        uplift_curve([1, 0], [1], [0.5, 0.4])


def test_random_score_has_small_qini_and_true_uplift_ranking_a_large_one():
    gen = np.random.default_rng(3)
    n = 20000
    tau = gen.uniform(0.0, 0.4, n)                                              # true uplift per session
    t = gen.random(n) < 0.5
    y = (gen.random(n) < 0.2 + tau * t).astype(int)
    good = qini_auuc(y, t, tau)["qini_coef"]
    noise = qini_auuc(y, t, gen.random(n))["qini_coef"]
    assert good > 5 * abs(noise) and good > 0


# --- loading runs -------------------------------------------------------------------------------


def test_completed_outcome_maps_orders_to_sessions():
    sessions = pd.DataFrame({"session_id": [10, 11, 12, 13]})
    orders = pd.DataFrame({"session_id": [11, 13, 12], "status": ["Completed", "Cancelled", "Completed"]})
    np.testing.assert_array_equal(completed_outcome(sessions, orders), [0, 1, 1, 0])


def test_load_run_never_returns_hidden_tables(tmp_path):
    cfg = load_config(TINY, ["policy.name=all_on", "sweep.n_seeds=1", "runner.n_procs=1", "budget.enforce=false"])
    evaluate(cfg, tmp_path, log_level="full")                                  # one run: tables at the root
    run = load_run(tmp_path)
    assert {"riders", "sessions", "orders", "slot_snapshots", "policy_results", "run_metadata"} <= set(run)
    assert not {"riders_hidden", "sessions_hidden"} & set(run)
    hidden = load_hidden(tmp_path)
    assert set(hidden) == {name.split("/")[-1] for name in HIDDEN_TABLES}
    y = completed_outcome(run["sessions"], run["orders"])
    assert y.sum() == run["policy_results"]["N_completed"][0] + (
        (run["orders"]["status"] == "Completed") & ~run["orders"]["in_window"]).sum()
    assert (run["sessions"]["arm"] == 1).all()
    # Rider features live in observed/riders and are joined on rider_id, never read from hidden/.
    x_freq = run["riders"].set_index("rider_id").loc[run["sessions"]["rider_id"], "x_freq"].to_numpy()
    assert len(x_freq) == len(y)
    assert math.isnan(qini_auuc(y, run["sessions"]["arm"], x_freq)["qini_coef"])   # no control arm under all_on
