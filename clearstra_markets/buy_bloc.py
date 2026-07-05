#!/usr/bin/env python3
"""BuyBlocMarket — demand-side federation aggregates volume into one bloc.

source_project: github.com/sadpig70/BuyBloc
stages: price, clear
Aggregated volume earns a discount; supply is allocated by member commitment.
"""

from ._base import require_non_negative, require_unit_interval


def price(order, P=None):
    """bloc_price = base_price * (1 - discount), discount ∝ aggregated volume."""
    base = order["base_price"]
    volume = order["total_volume"]
    max_discount = order.get("max_discount", 0.3)
    require_non_negative("base_price", base)
    require_non_negative("total_volume", volume)
    require_unit_interval("max_discount", max_discount)
    ref = order.get("discount_reference_volume", 1000)
    discount = min(max_discount, max_discount * (volume / ref)) if ref > 0 else 0.0
    return {"bloc_price": base * (1 - discount), "discount": discount, "total_volume": volume}


def priority(bid):
    """Larger member commitment is allocated first."""
    c = float(bid.get("commitment", bid.get("quantity", 0)))
    require_non_negative("commitment", c)
    return c


MANIFEST = {
    "name": "buy-bloc", "version": "1.0", "stages": ["price", "clear"],
    "order_schema": "schemas/order-bloc.schema.json",
    "source_project": "github.com/sadpig70/BuyBloc",
}

SAMPLES = {
    "price": {"order": {"base_price": 100.0, "total_volume": 800, "discount_reference_volume": 1000}},
    "clear": {"pool": [
        {"party_id": "member-big", "quantity": 600, "commitment": 600},
        {"party_id": "member-small", "quantity": 600, "commitment": 200},
    ], "supply": 800},
}
