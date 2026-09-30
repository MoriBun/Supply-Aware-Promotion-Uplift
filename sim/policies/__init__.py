"""Voucher policies (docs/spec.md §6)."""

from __future__ import annotations

from sim.config import Config
from sim.policies.base import Policy
from sim.policies.fixed import FixedPolicy


def make_policy(cfg: Config, world) -> Policy:
    """Build the policy named by ``cfg.policy.name`` (factory completed in task T2.3)."""
    name = cfg.policy.name
    if name == "all_on":
        return FixedPolicy(True, world.n_cells)
    if name == "all_off":
        return FixedPolicy(False, world.n_cells)
    raise NotImplementedError(f"policy {name!r}: task T2.3")
