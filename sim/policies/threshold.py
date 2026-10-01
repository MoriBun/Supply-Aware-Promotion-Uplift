"""ThresholdPolicy pi_theta: cell layer (forecast slack vs theta, hysteresis) and rider layer (score >= kappa).

Spec: docs/spec.md §6 [report M3]; decisions D3, D4, T-21, T-23. Milestone: P4 (task T2.3).

Cell layer: forecast ``s_hat`` of each cell's slack from the published snapshots
(``persistence`` = last slot; ``ar`` = weighted lag slot and lag day with inf
capped at ``monitor.slack_cap``), then ``promo_on = not (s_hat < theta)``, so an
unknown (NaN) or infinite forecast leaves the cell on and ``theta = 0`` cuts
nothing. With ``hysteresis_h > 0`` a cell that is off turns on only when
``s_hat > theta + h``. Rider layer: ``score = score_fn(batch, s_hat)`` and a
session is offered when its cell is on and ``score >= kappa``; the budget is
applied afterwards by the voucher layer (L12). ``kappa = -inf`` is the pilot
setting of kappa-auto (spec §6). Only ``indicator = slack`` is implemented (Q19).
"""

from __future__ import annotations

import math

import numpy as np

from sim.budget import BudgetLedger
from sim.config import Config
from sim.policies.base import CellDecision, OfferDecision, SessionBatch, SnapshotView
from sim.policies.scores import ScoreFn, load_score_fn, score_batch
from sim.state import Mechanism


class ThresholdPolicy:
    name = "threshold"

    def __init__(self, cfg: Config, n_cells: int, *, theta: float | None = None, kappa: float | None = None,
                 score_fn: ScoreFn | None = None) -> None:
        th = cfg.policy.threshold
        if th.indicator != "slack":
            raise NotImplementedError(f"policy.threshold.indicator={th.indicator!r}: only 'slack' is defined (Q19)")
        self.n_cells = int(n_cells)
        self.theta = float(th.theta if theta is None else theta)
        if kappa is not None:
            self.kappa = float(kappa)
        elif th.kappa == "auto":
            self.kappa = -math.inf                     # pilot run of kappa-auto; the runner passes the real kappa
        else:
            self.kappa = float(th.kappa)
        self.forecast = th.forecast
        self.ar_weights = tuple(float(w) for w in th.ar_weights)
        self.hysteresis_h = float(th.hysteresis_h)
        self.slack_cap = float(cfg.monitor.slack_cap)
        self.score_fn = load_score_fn(th.score_fn) if score_fn is None else score_fn
        self._prev_on = np.ones(self.n_cells, dtype=bool)

    def forecast_slack(self, snapshots: SnapshotView) -> np.ndarray:
        """``s_hat`` per cell (float64); NaN where nothing is published yet."""
        lag_slot = snapshots.lag("slack", 1)
        if self.forecast == "persistence":
            return lag_slot
        lag_day = snapshots.lag_day("slack")
        a = np.minimum(lag_slot, self.slack_cap)
        b = np.minimum(lag_day, self.slack_cap)
        w_slot, w_day = self.ar_weights
        ar = w_slot * a + w_day * b
        return np.where(np.isnan(b), a, ar)             # first day: lag day unknown -> persistence (T-23)

    def cell_state(self, slot: int, snapshots: SnapshotView) -> CellDecision:
        s_hat = self.forecast_slack(snapshots)
        on = ~(s_hat < self.theta)
        if self.hysteresis_h > 0:
            on = np.where(self._prev_on, on, s_hat > self.theta + self.hysteresis_h)
        self._prev_on = on
        return CellDecision(
            slot=int(slot), promo_on=on, cell_propensity=on.astype(np.float32),
            mechanism=np.full(self.n_cells, int(Mechanism.THRESHOLD), dtype=np.int8),
            s_hat=s_hat.astype(np.float32), cluster_id=np.full(self.n_cells, -1, dtype=np.int16),
        )

    def offer(self, batch: SessionBatch, cell_dec: CellDecision, ledger: BudgetLedger) -> OfferDecision:
        dec = OfferDecision.blank(len(batch), mechanism=Mechanism.THRESHOLD)
        s_hat = cell_dec.s_hat[batch.pu_cell].astype(np.float64)
        dec.score = score_batch(self.score_fn, batch, s_hat)
        dec.offer = cell_dec.promo_on[batch.pu_cell].astype(bool) & (dec.score >= self.kappa)   # NaN score: no offer
        dec.propensity = dec.offer.astype(np.float32)
        return dec
