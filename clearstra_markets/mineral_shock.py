#!/usr/bin/env python3
"""MineralShockMarket — strategic-mineral reserve pricing + supply-shock rehearsal.

source_project: github.com/sadpig70/MineralShock
stages: price, rehearse

ROUTING (HELIX BUILD_ON_PLATFORM, machine-aware): MineralShock answers "what is the right
to draw on a strategic-mineral reserve worth, what does the option to refuse a shipment
cost, and how many days does the system survive a supply shock?" — pure pricing + shock
survival. That is Clearstra's machine exactly; in fact the Clearstra kernel's pricing
primitives (coverage_days / scarcity_premium / option_premium) were derived FROM
MineralShock, so this pack simply composes them, and its rehearse maps 1:1 onto the
kernel's shock aggregation (min coverage = survival, summed shortfall).

Reproduces MineralShock.core.price_reserve_right / price_refusal_option / simulate_shock.
See tests/test_mineral_shock_parity.py.
"""

from ._base import require_non_negative, require_unit_interval, coverage_days, scarcity_premium, option_premium


def price(order, P=None):
    """Reserve-right (default) or refusal-option pricing. Mirrors MineralShock.core."""
    if order.get("kind") == "refusal_option":
        cap = order["refusal_capacity_tonnes"]
        threat = order["threat_level"]
        value = order["mineral_value"]
        premium = option_premium(cap, value, threat)   # cap * value * threat * 0.1
        return {"kind": "refusal_option", "refusal_capacity_tonnes": cap, "threat_level": threat,
                "mineral_value": value, "option_premium": premium}
    stockpile = order["stockpile_tonnes"]
    criticality = order["criticality"]
    daily_demand = order["daily_demand"]
    coverage = coverage_days(stockpile, daily_demand)
    scarcity = scarcity_premium(criticality, coverage)
    right_price = stockpile * criticality * (1 + scarcity)
    return {"kind": "reserve_right", "mineral": order.get("mineral", ""),
            "stockpile_tonnes": stockpile, "criticality": criticality, "daily_demand": daily_demand,
            "coverage_days": coverage, "scarcity_premium": scarcity, "right_price": right_price}


def shock_model(scenario, item):
    """Per-reserve supply-shock impact -> {coverage_days, shortfall}.

    The kernel rehearse() aggregates survival (min coverage) + total shortfall over the
    pool, matching MineralShock.simulate_shock's per-mineral loop and aggregation.
    """
    supply_disruption = scenario.get("supply_disruption_pct", 0)
    demand_spike = scenario.get("demand_spike_pct", scenario.get("demand_spiup_pct", 0))
    mission_days = scenario.get("mission_days")
    require_non_negative("demand_spike_pct", demand_spike)
    require_unit_interval("supply_disruption_pct", supply_disruption)
    stockpile = item.get("stockpile_tonnes", 0)
    daily_demand = item.get("daily_demand", 0)
    require_non_negative("stockpile_tonnes", stockpile)
    require_non_negative("daily_demand", daily_demand)
    effective = stockpile * (1 - supply_disruption)
    shocked_demand = daily_demand * (1 + demand_spike)
    coverage = effective / shocked_demand if shocked_demand > 0 else float("inf")
    if mission_days is None:
        shortfall = stockpile * supply_disruption
    else:
        require_non_negative("mission_days", mission_days)
        shortfall = max(0.0, shocked_demand * mission_days - effective)
    return {"id": item.get("mineral", ""), "coverage_days": coverage, "shortfall": shortfall}


MANIFEST = {
    "name": "mineral-shock", "version": "1.0", "stages": ["price", "rehearse"],
    "order_schema": "schemas/order-mineral.schema.json",
    "source_project": "github.com/sadpig70/MineralShock",
}

SAMPLES = {
    "price": {"order": {"kind": "reserve_right", "mineral": "cobalt",
                        "stockpile_tonnes": 1000.0, "criticality": 0.8, "daily_demand": 10.0}},
    "rehearse": {"scenario": {"name": "disruption", "demand_spike_pct": 0.5,
                              "supply_disruption_pct": 0.3, "mission_days": 30},
                 "pool": [{"mineral": "cobalt", "stockpile_tonnes": 1000.0, "daily_demand": 10.0},
                          {"mineral": "lithium", "stockpile_tonnes": 500.0, "daily_demand": 20.0}]},
}
