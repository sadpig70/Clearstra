#!/usr/bin/env python3
"""Deterministic pricing primitives (stdlib only).

Lifted from the corpus clearing markets so every market pack composes its price
formula from a single source. Grounded in real code:
  - CryoFutures.price_future:      premium = payout * failure_prob * time_factor(days)
  - MineralShock.price_reserve_right: scarcity_premium = criticality / max(coverage,1)
  - MineralShock.price_refusal_option: option_premium = capacity * value * threat * rate
No clock/network/AI; same input -> same output.
"""

import math


def require_non_negative(name, value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a number")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def require_unit_interval(name, value):
    require_non_negative(name, value)
    if value > 1:
        raise ValueError(f"{name} must be within [0, 1]")


def time_factor(days_to_expiry):
    """sqrt(days / 365) — CryoFutures time-to-expiry risk factor."""
    require_non_negative("days_to_expiry", days_to_expiry)
    return math.sqrt(days_to_expiry / 365.0)


def coverage_days(stockpile, daily_demand):
    """stockpile / daily_demand (inf when demand is zero) — MineralShock coverage."""
    require_non_negative("stockpile", stockpile)
    require_non_negative("daily_demand", daily_demand)
    return stockpile / daily_demand if daily_demand > 0 else float("inf")


def scarcity_premium(criticality, coverage):
    """criticality / max(coverage, 1) — MineralShock scarcity premium."""
    require_unit_interval("criticality", criticality)
    require_non_negative("coverage", coverage)
    return criticality / max(coverage, 1.0)


def option_premium(capacity, value, threat, rate=0.1):
    """capacity * value * threat * rate — MineralShock refusal-option premium."""
    require_non_negative("capacity", capacity)
    require_non_negative("value", value)
    require_unit_interval("threat", threat)
    return capacity * value * threat * rate
