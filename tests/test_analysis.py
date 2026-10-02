"""analysis/ (docs/phan_cong.md T3.3): policy value with CI, paired differences, Qini / AUUC, run loading."""

import math

import numpy as np
import pandas as pd
import pytest

from analysis import check_budget
from analysis.check_dataset import check_run_dir, markdown_row
from analysis.io import HIDDEN_TABLES, completed_outcome, load_hidden, load_run
from analysis.metrics import bootstrap_mean_ci, paired_difference, qini_auuc, uplift_curve, value_table
from sim.config import load_config
from sim.runner import evaluate, generate, gte
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


# --- data set validation before a handoff (B7) ------------------------------------------------


def test_check_dataset_accepts_generated_data_and_catches_a_leak(tmp_path):
    cfg = load_config(TINY, ["policy.name=legacy", "generate.days=1", "runner.n_procs=1"])
    generate(cfg, tmp_path / "gen")
    problems, summary = check_run_dir(tmp_path / "gen")
    assert problems == []
    assert summary["mode"] == "generate" and summary["policy"] == "legacy" and summary["days"] == 1.0
    assert summary["sessions"] > 0 and summary["N_completed"] > 0 and summary["budget_B_usd"] > 0
    assert 0 < summary["share_arm"] < 1 and summary["truncated"] == 0
    assert markdown_row(summary).startswith("| `gen` | generate | legacy | 1 |")
    # A hidden column smuggled into observed/ must be reported.
    path = tmp_path / "gen" / "observed" / "sessions.parquet"
    leaked = pd.read_parquet(path)
    leaked["u_latent"] = 0.0
    leaked.to_parquet(path, index=False)
    problems, _ = check_run_dir(tmp_path / "gen")
    assert any("observed/sessions" in p for p in problems)


def test_check_budget_audits_legacy_and_all_on_runs(tmp_path, capsys):
    # Legacy with a small fixed B: sessions are blocked, including explore sessions of cells that are off.
    legacy = load_config(TINY, ["policy.name=legacy", "generate.days=1", "runner.n_procs=1",
                                "budget.mode=fixed", "budget.fixed_usd=4", "policy.legacy.explore_frac=0.3"])
    generate(legacy, tmp_path / "legacy")
    assert check_budget.main(["check_budget", str(tmp_path / "legacy")]) == 0
    out = capsys.readouterr().out
    assert "mọi kỳ trong ngân sách" in out and "bị chặn" in out and "VI PHẠM" not in out
    sessions = pd.read_parquet(tmp_path / "legacy" / "observed" / "sessions.parquet")
    blocked_off = sessions[sessions["budget_blocked"] & ~sessions["promo_on_cell"]]
    assert len(blocked_off) > 0 and (blocked_off["assign_mechanism"] == "explore").all()
    # Several seeds with a full log: one folder per run, each audited.
    on = load_config(TINY, ["policy.name=all_on", "sweep.n_seeds=2", "runner.n_procs=1",
                            "budget.mode=fixed", "budget.fixed_usd=4"])
    evaluate(on, tmp_path / "on", log_level="full")
    assert check_budget.main(["check_budget", str(tmp_path / "on")]) == 0
    assert capsys.readouterr().out.count("policy=all_on") == 2
    assert check_budget.main(["check_budget"]) == 2


def test_gate_plots_write_png_files(tmp_path):
    pytest.importorskip("matplotlib")
    from analysis.plots import plot_theta_sweep, plot_throughput

    sweep = pd.DataFrame({"theta": [0.0, 0.2, 0.5, 1.0], "N_mean": [100.0, 110.0, 108.0, 95.0],
                          "N_se": [2.0, 2.5, 2.0, 3.0], "V_mean": [1.0, 2.0, 3.0, 4.0], "V_se": [0.1] * 4,
                          "spent_mean": [50.0, 50.0, 48.0, 30.0], "n_seeds": [10] * 4,
                          "is_argmax": [False, True, False, False]})
    png = plot_theta_sweep(sweep, tmp_path / "plots" / "sweep.png", budget_usd=50.0,
                           baselines={"all_off": 90.0, "all_on không ngân sách": 105.0})
    assert png.exists() and png.stat().st_size > 10_000 and png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    curve = pd.DataFrame({"demand_scale": np.repeat([0.5, 1.0, 2.0, 4.0], 2), "seed": [0, 1] * 4,
                          "completed_per_h": [100, 104, 190, 196, 240, 236, 200, 204],
                          "mean_slack": [5.0, 5.2, 1.0, 1.1, 0.2, 0.25, 0.05, 0.06],
                          "mean_pickup_eta_min": [2.0, 2.1, 3.0, 3.1, 6.0, 6.2, 9.0, 9.1]})
    png = plot_throughput(curve, tmp_path / "plots" / "throughput.png")
    assert png.exists() and png.stat().st_size > 10_000


def test_check_dataset_on_results_only_and_experiment_dirs(tmp_path):
    cfg = load_config(TINY, ["gte.n_seeds=2", "runner.n_procs=1"])
    gte(cfg, tmp_path / "gte")
    problems, summary = check_run_dir(tmp_path / "gte")
    assert problems == [] and summary["mode"] == "gte" and summary["n_runs"] == 4 and summary["seeds"] == "0–1"
    assert "sessions" not in summary and summary["policy"] == "all_off/all_on" and summary["N_mean"] > 0
    exp = load_config(TINY, ["policy.name=experiment", "experiment.cluster_level=all", "generate.days=1",
                             "runner.n_procs=1"])
    generate(exp, tmp_path / "exp")
    problems, summary = check_run_dir(tmp_path / "exp")
    assert problems == [] and "cluster_switchback, cụm all" in summary["design"]
    assert math.isnan(summary["budget_B_usd"]) and summary["share_blocked"] == 0.0
    problems, _ = check_run_dir(tmp_path / "missing")
    assert problems and "missing" in problems[0]
