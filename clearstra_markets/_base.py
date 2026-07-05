#!/usr/bin/env python3
"""Shared helpers for market packs. A market module exposes MANIFEST + the stage
functions its `stages` declare + SAMPLES.

Stage → function it must provide:
  price    -> price(order, P) -> dict            (uses pricing primitives below)
  clear    -> priority(bid) -> float             (kernel clear() ranks by this)
  settle   -> payoff(contract, outcome) -> dict  (must be zero-sum)
  rehearse -> shock_model(scenario, item) -> dict ({coverage_days, shortfall})

Markets compose their price formula from these deterministic primitives; they never
redefine clearing/settlement/ledger (that lives once in clearstra_core).
"""

from clearstra_core.pricing import (
    require_non_negative, require_unit_interval,
    time_factor, coverage_days, scarcity_premium, option_premium,
)

__all__ = [
    "require_non_negative", "require_unit_interval",
    "time_factor", "coverage_days", "scarcity_premium", "option_premium",
]
