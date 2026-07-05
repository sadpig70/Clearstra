#!/usr/bin/env python3
"""Shock rehearsal — stress a pool against a scenario (shortfall / survival).

Generalizes MineralShock.simulate_shock: the market pack supplies the per-item
shock model; the kernel aggregates survival and shortfall across the pool. Pure stdlib.
"""


def rehearse(scenario, pool, model, now=""):
    """Apply `model(scenario, item)` to each item; aggregate survival and shortfall.

    model must return at least {coverage_days, shortfall}; optional {id}.
    """
    per_item, coverages, affected = [], [], []
    total_shortfall = 0.0
    for item in pool:
        impact = model(scenario, item)
        per_item.append(impact)
        coverages.append(impact.get("coverage_days", float("inf")))
        if impact.get("shortfall", 0) > 0:
            total_shortfall += impact["shortfall"]
            affected.append(impact.get("id", item.get("id", item.get("party_id", ""))))
    return {
        "scenario": scenario.get("name", ""),
        "survival_days": min(coverages) if coverages else float("inf"),
        "total_shortfall": total_shortfall,
        "affected": affected,
        "per_item": per_item,
        "rehearsed_at": now,
    }
