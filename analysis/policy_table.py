"""N(pi), V(pi) of several voucher policies under the same budget B (task T5.1, docs/phan_cong.md S5).

``python -m analysis.policy_table --config config/default.yaml [--config overlay.yaml] [--set key=value ...]
[--spec "label=tau_x,policy=threshold,theta=0,score_fn=analysis.scores:tau_x_baseline" ...] [--n-seeds 30]
--out runs/s5/policy_table``

Every policy runs on the same seeds (common random numbers, spec §5), and every policy but
``all_off`` under the same B per budget period, from the all_on pilot (spec §4.3). A
threshold policy gets kappa-auto at its theta (decisions H-21), so it spends B too and
policies differ only in who gets the vouchers. Without ``--spec`` the default list of
:data:`DEFAULT_SPECS` runs.

Writes ``results/policy_results.parquet`` and ``meta/run_metadata.parquet`` (docs/schema.md,
mode ``evaluate``), ``results/policy_labels.parquet`` (run_id -> label) and
``results/policy_table.parquet``: one row per label with N, V and spend over seeds, and
the difference with the reference label paired by seed.
"""

from __future__ import annotations

import argparse
import dataclasses
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from sim.config import Config, load_config
from sim.logger import write_metadata, write_results
from sim.runner import (
    DEFAULT_ENGINE, Job, KappaAuto, budget_for, metadata_table, policy_results_table, resolve_kappas, run_jobs,
    run_id, seeds_for, with_policy,
)

NAN = float("nan")
MODE = "evaluate"
POLICIES = ("all_off", "all_on", "threshold", "legacy")


@dataclass(frozen=True)
class PolicySpec:
    """One row of the table: a policy, its theta and rider score (threshold only), and whether B applies."""

    label: str
    policy: str
    theta: float = NAN
    score_fn: str | None = None
    budget: bool = True
    scope: str | None = None           # policy.threshold.scope (cell | ring1); None = config value


# All but all_off spend B. Threshold rows at theta = 0 cut no cell, so they differ only in the rider score:
# the H4.2 table baselines (ties broken at random, decisions T-33 (e)) and the DR-learner scores of H5.2
# (decisions H-24; "_all" = fitted on all legacy sessions, plain = explore slice only). tau_hat(x, s) rows run
# with the cell scope, the slack its model was trained on. pi_theta_hat rows: theta_hat (A) and (B) of H5.3 on
# the ring1 scope (decisions H-25) with tau_hat(x) per dollar, which does not read s.
DR = "analysis.uplift:"
DEFAULT_SPECS = (
    PolicySpec("all_off", "all_off", budget=False),
    PolicySpec("all_on_B", "all_on"),
    PolicySpec("random", "threshold", 0.0, "random"),
    PolicySpec("heuristic", "threshold", 0.0, "heuristic_low_freq"),
    PolicySpec("tau_x", "threshold", 0.0, "analysis.score_ties:tau_x_baseline"),
    PolicySpec("tau_per_usd", "threshold", 0.0, "analysis.score_ties:tau_per_dollar_baseline"),
    PolicySpec("tau_x_dr_all", "threshold", 0.0, DR + "tau_x_dr_all"),
    PolicySpec("tau_xs_dr_all", "threshold", 0.0, DR + "tau_xs_dr_all"),
    PolicySpec("tau_x_dr_all_usd", "threshold", 0.0, DR + "tau_x_dr_all_per_dollar"),
    PolicySpec("tau_xs_dr_all_usd", "threshold", 0.0, DR + "tau_xs_dr_all_per_dollar"),
    PolicySpec("tau_x_dr_usd", "threshold", 0.0, DR + "tau_x_dr_per_dollar"),
    PolicySpec("tau_xs_dr_usd", "threshold", 0.0, DR + "tau_xs_dr_per_dollar"),
    PolicySpec("pi_theta_0.5_heuristic", "threshold", 0.5, "heuristic_low_freq"),
    PolicySpec("pi_thetahatA_ring1_dr_usd", "threshold", 0.25, DR + "tau_x_dr_all_per_dollar", scope="ring1"),
    PolicySpec("pi_thetahatB_ring1_dr_usd", "threshold", 5.0, DR + "tau_x_dr_all_per_dollar", scope="ring1"),
)
REFERENCE = "all_on_B"


def parse_spec(text: str) -> PolicySpec:
    """``label=...,policy=...[,theta=...][,score_fn=...][,scope=cell|ring1][,budget=true|false]`` (score_fn may contain ':')."""
    fields: dict[str, str] = {}
    for part in text.split(","):
        key, sep, value = part.partition("=")
        if not sep or not key.strip():
            raise ValueError(f"bad spec part {part!r} in {text!r}: expected key=value")
        fields[key.strip()] = value.strip()
    unknown = set(fields) - {"label", "policy", "theta", "score_fn", "scope", "budget"}
    if unknown or "label" not in fields or "policy" not in fields:
        raise ValueError(f"spec {text!r}: needs label and policy, allows theta, score_fn, budget; got {sorted(fields)}")
    if fields["policy"] not in POLICIES:
        raise ValueError(f"spec {text!r}: policy must be one of {POLICIES}")
    budget = fields.get("budget", "true").lower()
    if budget not in ("true", "false"):
        raise ValueError(f"spec {text!r}: budget must be true or false")
    return PolicySpec(label=fields["label"], policy=fields["policy"], theta=float(fields.get("theta", "nan")),
                      score_fn=fields.get("score_fn") or None, budget=budget == "true", scope=fields.get("scope") or None)


def configure(cfg: Config, spec: PolicySpec) -> Config:
    """``cfg`` with the spec's policy and, for a threshold spec, its ``score_fn`` and ``scope`` when given."""
    out = with_policy(cfg, spec.policy)
    if spec.policy == "threshold":
        th = out.policy.threshold
        if spec.score_fn:
            th = dataclasses.replace(th, score_fn=spec.score_fn)
        if spec.scope:
            if spec.scope not in ("cell", "ring1"):
                raise ValueError(f"spec {spec.label!r}: scope must be cell or ring1, got {spec.scope!r}")
            th = dataclasses.replace(th, scope=spec.scope)
        out = dataclasses.replace(out, policy=dataclasses.replace(out.policy, threshold=th))
    return out


def run_policy_table(cfg: Config, specs, out_dir: Path, *, n_seeds: int | None = None,
                     engine: str = DEFAULT_ENGINE, reference: str = REFERENCE) -> pd.DataFrame:
    """Run every spec on the same seeds under the same B; write the tables and return the summary."""
    specs = list(specs)
    labels = [s.label for s in specs]
    if len(set(labels)) != len(labels):
        raise ValueError(f"labels must be unique: {labels}")
    if reference not in labels:
        raise ValueError(f"reference {reference!r} is not one of the labels {labels}")
    budget = budget_for(cfg, engine=engine)
    seeds = seeds_for(cfg, cfg.sweep.n_seeds if n_seeds is None else int(n_seeds))
    jobs: list[Job] = []
    job_labels: list[str] = []
    for spec in specs:
        c = configure(cfg, spec)
        theta = float(c.policy.threshold.theta if spec.policy == "threshold" and math.isnan(spec.theta)
                      else spec.theta)
        b = budget if spec.budget else None
        found = resolve_kappas(c, [theta], b, engine=engine)
        ka = KappaAuto(kappa=NAN) if found is None else found[0]
        for s in seeds:
            jobs.append(Job(cfg=c, seed=s, theta=theta, kappa=None if found is None else ka.kappa, budget_usd=b,
                            enforce_budget=b is not None, kappa_pilots=ka.n_pilots))
            job_labels.append(spec.label)
    results = run_jobs(jobs, engine=engine)
    runs = policy_results_table(MODE, jobs, results)
    write_results(out_dir, "policy_results", runs)
    write_metadata(out_dir, metadata_table(MODE, jobs, results))
    labels_table = pd.DataFrame({
        "run_id": [run_id(MODE, j.cfg, r.policy, j.theta, j.seed) for j, r in zip(jobs, results)],
        "label": job_labels,
        "score_fn": [j.cfg.policy.threshold.score_fn if j.policy_name == "threshold" else "" for j in jobs],
        "kappa": [NAN if j.kappa is None else float(j.kappa) for j in jobs],
        "kappa_pilots": [j.kappa_pilots for j in jobs],
    })
    if not labels_table["run_id"].is_unique:
        raise ValueError("two specs give the same run (same config, theta and seed); make them differ")
    _write(out_dir, "policy_labels", labels_table)
    summary = summarize(runs.merge(labels_table, on="run_id"), reference=reference, order=labels)
    _write(out_dir, "policy_table", summary)
    return summary


def _write(out_dir: Path, name: str, table: pd.DataFrame) -> Path:
    path = Path(out_dir) / "results" / f"{name}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(path, index=False)
    return path


def _mean_se(values: pd.Series) -> tuple[float, float]:
    n = int(values.count())
    return float(values.mean()), (float(values.std(ddof=1) / math.sqrt(n)) if n > 1 else NAN)


def summarize(runs: pd.DataFrame, *, reference: str = REFERENCE, order=None) -> pd.DataFrame:
    """Per label: N, V, spend (mean, SE over seeds) and ``label - reference`` paired by seed (CRN)."""
    order = list(dict.fromkeys(runs["label"])) if order is None else list(order)
    by_seed = {m: runs.pivot(index="seed", columns="label", values=m)
               for m in ("N_completed", "V_profit_usd", "voucher_spent_usd")}
    rows = []
    for label in order:
        g = runs[runs["label"] == label]
        row = {"label": label, "policy": g["policy"].iloc[0], "score_fn": g["score_fn"].iloc[0],
               "theta": float(g["theta"].iloc[0]), "kappa": float(g["kappa"].iloc[0]),
               "kappa_pilots": int(g["kappa_pilots"].iloc[0]), "n_seeds": int(len(g)),
               "budget_B_usd": float(g["budget_B_usd"].iloc[0])}
        for metric, prefix in (("N_completed", "N"), ("V_profit_usd", "V"), ("voucher_spent_usd", "spent")):
            row[f"{prefix}_mean"], row[f"{prefix}_se"] = _mean_se(g[metric])
        row["share_cells_off"] = float(g["share_cells_off"].mean())
        for metric, prefix in (("N_completed", "dN"), ("V_profit_usd", "dV")):
            diff = (by_seed[metric][label] - by_seed[metric][reference]).dropna()
            row[f"{prefix}_vs_ref"], row[f"{prefix}_vs_ref_se"] = _mean_se(diff)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.attrs["reference"] = reference
    return out


def _vn(x: float, digits: int = 1) -> str:
    """Vietnamese number format: dot for thousands, comma for decimals, real minus sign."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if math.isinf(x):
        return "−∞" if x < 0 else "+∞"
    text = f"{abs(x):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 else "") + text


def markdown(summary: pd.DataFrame) -> str:
    """The table as Markdown rows for docs/log.md and the report."""
    ref = summary.attrs.get("reference", REFERENCE)
    head = (f"| Chính sách | θ | κ | N (± SE) | V (USD, ± SE) | Chi / B | % (ô, slot) tắt | N − {ref} (± SE) |\n"
            "|---|---|---|---|---|---|---|---|")
    lines = [head]
    for r in summary.itertuples():
        spent = r.spent_mean / r.budget_B_usd if r.budget_B_usd > 0 else NAN
        dn = "0 (mốc)" if r.label == ref else f"{_vn(r.dN_vs_ref)} ± {_vn(r.dN_vs_ref_se)}"
        lines.append(f"| `{r.label}` | {_vn(r.theta, 2) if not math.isnan(r.theta) else '—'} | {_vn(r.kappa, 3)} | "
                     f"{_vn(r.N_mean)} ± {_vn(r.N_se)} | {_vn(r.V_mean)} ± {_vn(r.V_se)} | {_vn(spent, 3)} | "
                     f"{_vn(100 * r.share_cells_off, 0)} | {dn} |")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m analysis.policy_table", description=__doc__.splitlines()[0])
    parser.add_argument("--config", action="append", required=True, metavar="YAML")
    parser.add_argument("--set", dest="overrides", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--spec", action="append", default=[], metavar="SPEC", help="see parse_spec; repeatable")
    parser.add_argument("--reference", default=REFERENCE)
    parser.add_argument("--n-seeds", type=int, default=None, help="default: sweep.n_seeds (decisions T-22)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    cfg = load_config(args.config, args.overrides)
    specs = [parse_spec(s) for s in args.spec] if args.spec else list(DEFAULT_SPECS)
    summary = run_policy_table(cfg, specs, args.out, n_seeds=args.n_seeds, reference=args.reference)
    print(f"B = {summary['budget_B_usd'].dropna().max():.2f} USD per period; {int(summary['n_seeds'].iloc[0])} seeds")
    print(markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
