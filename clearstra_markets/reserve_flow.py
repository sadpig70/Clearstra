#!/usr/bin/env python3
"""ReserveFlowMarket — Attestra anchor. Strategic-reserve flow-rights clearing.

source_project: github.com/sadpig70/ReserveFlow
stages: price, clear, rehearse
Anchor: clear() output -> to_attestra_packet() -> Attestra reserve-flow verdict=valid.
priority is an integer shock-weight so the emitted packet fits Attestra's clearing schema.
"""

from ._base import (
    coverage_days, scarcity_premium, require_non_negative, require_unit_interval,
)


def price(order, P=None):
    """right_price = stockpile * criticality * (1 + scarcity_premium). Mirrors MineralShock."""
    stockpile = order["stockpile_tonnes"]
    criticality = order["criticality"]
    daily_demand = order.get("daily_demand", 0)
    require_non_negative("stockpile_tonnes", stockpile)
    require_unit_interval("criticality", criticality)
    cov = coverage_days(stockpile, daily_demand)
    sp = scarcity_premium(criticality, cov)
    return {"right_price": stockpile * criticality * (1 + sp),
            "coverage_days": cov, "scarcity_premium": sp}


def priority(bid):
    """Integer shock-weight: higher criticality and lower coverage rank first."""
    crit = bid.get("criticality", 0)
    cov = bid.get("coverage_days", 1)
    return int(round(crit * 100 - min(cov, 100)))


def shock_model(scenario, item):
    """Per-reserve shock impact. Mirrors MineralShock.simulate_shock."""
    disruption = scenario.get("supply_disruption_pct", scenario.get("disruption", 0))
    spike = scenario.get("demand_spike_pct", scenario.get("spike", 0))
    mission_days = scenario.get("mission_days")
    stockpile = item["stockpile_tonnes"]
    demand = item["daily_demand"]
    effective = stockpile * (1 - disruption)
    shocked_demand = demand * (1 + spike)
    coverage = effective / shocked_demand if shocked_demand > 0 else float("inf")
    if mission_days is None:
        shortfall = stockpile * disruption
    else:
        shortfall = max(0.0, shocked_demand * mission_days - effective)
    return {"id": item.get("mineral", item.get("id", "")),
            "coverage_days": coverage, "shortfall": shortfall,
            "effective_stockpile_tonnes": effective}


MANIFEST = {
    "name": "reserve-flow", "version": "1.0", "stages": ["price", "clear", "rehearse"],
    "order_schema": "schemas/order-reserve.schema.json",
    "source_project": "github.com/sadpig70/ReserveFlow",
}

SAMPLES = {
    "price": {"order": {"stockpile_tonnes": 1000, "criticality": 0.8, "daily_demand": 20}},
    "clear": {"pool": [
        {"party_id": "defense", "quantity": 400, "criticality": 0.9, "coverage_days": 10},
        {"party_id": "energy", "quantity": 400, "criticality": 0.6, "coverage_days": 30},
        {"party_id": "consumer", "quantity": 400, "criticality": 0.3, "coverage_days": 90},
    ], "supply": 800},
    "rehearse": {"scenario": {"name": "embargo", "supply_disruption_pct": 0.4,
                              "demand_spike_pct": 0.2, "mission_days": 60},
                 "pool": [{"mineral": "Li", "stockpile_tonnes": 1000, "daily_demand": 20},
                          {"mineral": "Co", "stockpile_tonnes": 300, "daily_demand": 20}]},
}
