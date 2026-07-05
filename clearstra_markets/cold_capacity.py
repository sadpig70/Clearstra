#!/usr/bin/env python3
"""ColdCapacityMarket — two-sided millikelvin cooling-capacity clearing.

source_project: github.com/sadpig70/ColdMkh
stages: price, clear
"""

from ._base import require_non_negative


def price(order, P=None):
    """capacity_price = mk_capacity * demand_ratio (two-sided balance price)."""
    cap = order["mk_capacity"]
    ratio = order["demand_ratio"]
    require_non_negative("mk_capacity", cap)
    require_non_negative("demand_ratio", ratio)
    return {"capacity_price": cap * ratio, "mk_capacity": cap, "demand_ratio": ratio}


def priority(bid):
    """Willingness-to-pay: highest valuation cleared first."""
    return float(bid.get("valuation", 0))


MANIFEST = {
    "name": "cold-capacity", "version": "1.0", "stages": ["price", "clear"],
    "order_schema": "schemas/order-cold.schema.json",
    "source_project": "github.com/sadpig70/ColdMkh",
}

SAMPLES = {
    "price": {"order": {"mk_capacity": 500, "demand_ratio": 1.4}},
    "clear": {"pool": [
        {"party_id": "labA", "quantity": 300, "valuation": 9.0},
        {"party_id": "labB", "quantity": 300, "valuation": 5.0},
    ], "supply": 400},
}
