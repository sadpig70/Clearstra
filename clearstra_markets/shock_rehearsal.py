#!/usr/bin/env python3
"""ShockRehearsalMarket — rehearse supply-shock scenarios over allocation rights.

source_project: github.com/sadpig70/ShockRehearsal
stages: rehearse
"""


def shock_model(scenario, item):
    """Apply demand spike + supply disruption to one item. Mirrors MineralShock.simulate_shock."""
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
    return {"id": item.get("id", item.get("mineral", "")),
            "coverage_days": coverage, "shortfall": shortfall}


MANIFEST = {
    "name": "shock-rehearsal", "version": "1.0", "stages": ["rehearse"],
    "order_schema": "schemas/order-shock.schema.json",
    "source_project": "github.com/sadpig70/ShockRehearsal",
}

SAMPLES = {
    "rehearse": {"scenario": {"name": "dual-shock", "supply_disruption_pct": 0.5,
                              "demand_spike_pct": 0.3, "mission_days": 30},
                 "pool": [{"id": "Li", "stockpile_tonnes": 1000, "daily_demand": 20},
                          {"id": "Co", "stockpile_tonnes": 200, "daily_demand": 20}]},
}
