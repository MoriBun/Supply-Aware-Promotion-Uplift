"""Hand-over check of package B12 (task H9.7): everything S9 produced loads in a child process, deterministically.

B12 = for W0 and W1: the refitted DR score functions per 1.000đ (``analysis.uplift``), the hour-off rule
(``analysis.hour_rule`` + ``analysis/models/hour_rule_<world>.json``), the chosen tension indicator and the
thresholds (``runs/s9/<world>/summary.json``), the waterfall and burn-in tables (``runs/s9/<world>/results``).

``python -m analysis.b12_check [--runs runs/s9] [--out runs/s9/b12_manifest.json]`` runs the receiver's
checks of docs/phan_cong_v3.md (B12): every score function of the list below is loaded by its spec string in a
spawned worker twice and must give the same scores; the harmful-hour files exist; the waterfall steps add up
to raw − GTE_big; the thresholds JSON has every moderator. Exit code 1 on any failure.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path

import numpy as np

SCORE_SPECS = [
    "analysis.uplift:tau_x_dr_all_per_kvnd", "analysis.uplift:tau_xs_dr_all_per_kvnd",
    "analysis.uplift:tau_x_dr_per_kvnd", "analysis.uplift:tau_xs_dr_per_kvnd",
    "analysis.uplift:tau_x_dr_all_w1_per_kvnd", "analysis.uplift:tau_xs_dr_all_w1_per_kvnd",
    "analysis.uplift:tau_x_dr_w1_per_kvnd", "analysis.uplift:tau_xs_dr_w1_per_kvnd",
    "analysis.hour_rule:off_hours_random_w0", "analysis.hour_rule:off_hours_dr_w0",
    "analysis.hour_rule:off_hours_random_w1", "analysis.hour_rule:off_hours_dr_w1",
]
WORLDS = ("w0", "w1")


def _score_in_worker(spec: str) -> np.ndarray:
    """A fixed batch scored by ``spec`` (runs in a spawned process: fresh imports, no shared cache)."""
    import dataclasses

    from sim.policies.scores import load_score_fn, score_batch
    from tests.fakes import make_batch

    g = np.random.default_rng(0)
    n = 48
    b = make_batch(n, 61)
    b = dataclasses.replace(b, x_freq=g.gamma(2.0, 1.0, n).astype(np.float32), x_tenure=g.uniform(0, 36, n).astype(np.float32),
                            x_segment=np.tile([0, 1, 2], n // 3).astype(np.int8), hour=np.tile(np.arange(24), 2).astype(np.int16))
    s_hat = np.tile([0.1, 0.5, 2.0, np.inf, np.nan, 1.0], n // 6)
    return score_batch(load_score_fn(spec), b, s_hat)


def check_scores(specs=SCORE_SPECS) -> list[dict]:
    rows = []
    with multiprocessing.get_context("spawn").Pool(1) as pool:
        for spec in specs:
            try:
                a = pool.apply(_score_in_worker, (spec,))
                b = pool.apply(_score_in_worker, (spec,))
                same = bool(np.array_equal(a, b, equal_nan=True))
                finite = float(np.mean(np.isfinite(a)))
                rows.append({"spec": spec, "ok": same and finite > 0, "deterministic": same, "share_finite": finite,
                             "error": ""})
            except Exception as exc:                                    # noqa: BLE001 - report, do not stop
                rows.append({"spec": spec, "ok": False, "deterministic": False, "share_finite": 0.0, "error": repr(exc)})
    return rows


def check_files(runs: Path) -> list[dict]:
    from analysis.hour_rule import rule_path

    rows = []
    for w in WORLDS:
        p = rule_path(w)
        rows.append({"item": f"hour_rule_{w}.json", "ok": p.exists(), "detail": str(p)})
        summary = runs / w / "summary.json"
        ok = summary.exists()
        detail = ""
        if ok:
            data = json.loads(summary.read_text(encoding="utf-8"))
            ok = set(data.get("theta_hat_tension", {})) >= {"system_pre", "ring_pre", "cell_pre"} and "harmful_hours" in data
            detail = f"harmful_hours={data.get('harmful_hours')}"
        rows.append({"item": f"{w}/summary.json (tension thresholds)", "ok": ok, "detail": detail})
        for name in ("waterfall_completed", "burnin_completed"):
            path = runs / w / "results" / f"{name}.parquet"
            ok = path.exists()
            detail = ""
            if ok and name.startswith("waterfall"):
                attrs = json.loads((runs / w / "results" / f"{name}_attrs.json").read_text(encoding="utf-8"))
                sc = attrs["sum_check"]
                ok = abs(sc["steps_sum"] - sc["raw_minus_big"]) < 1e-6
                detail = f"steps_sum={sc['steps_sum']:.3f} raw_minus_big={sc['raw_minus_big']:.3f}"
            rows.append({"item": f"{w}/results/{name}.parquet", "ok": ok, "detail": detail})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="B12 hand-over check (task H9.7)")
    ap.add_argument("--runs", type=Path, default=Path("runs/s9"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    scores = check_scores()
    files = check_files(args.runs)
    ok = all(r["ok"] for r in scores) and all(r["ok"] for r in files)
    for r in scores:
        print(f"[{'OK' if r['ok'] else 'FAIL'}] {r['spec']}: deterministic={r['deterministic']} finite={r['share_finite']:.2f} {r['error']}")
    for r in files:
        print(f"[{'OK' if r['ok'] else 'FAIL'}] {r['item']} {r['detail']}")
    print("B12:", "OK" if ok else "FAILED")
    out = args.out or (args.runs / "b12_manifest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"ok": ok, "scores": scores, "files": files}, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
