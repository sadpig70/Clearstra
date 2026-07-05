#!/usr/bin/env python3
"""RefusalOptionMarket — price the option to refuse shipping a mineral.

source_project: github.com/sadpig70/RefusalOption
stages: price
"""

from ._base import option_premium


def price(order, P=None):
    """option_premium = capacity * value * threat * 0.1. Mirrors MineralShock.price_refusal_option."""
    premium = option_premium(order["refusal_capacity_tonnes"], order["mineral_value"],
                             order["threat_level"])
    return {"option_premium": premium,
            "refusal_capacity_tonnes": order["refusal_capacity_tonnes"],
            "threat_level": order["threat_level"], "mineral_value": order["mineral_value"]}


MANIFEST = {
    "name": "refusal-option", "version": "1.0", "stages": ["price"],
    "order_schema": "schemas/order-refusal.schema.json",
    "source_project": "github.com/sadpig70/RefusalOption",
}

SAMPLES = {
    "price": {"order": {"refusal_capacity_tonnes": 10.0, "mineral_value": 100.0, "threat_level": 0.5}},
}
