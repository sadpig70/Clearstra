#!/usr/bin/env python3
"""FailureFuturesMarket — fragility turned into tradable futures.

source_project: github.com/sadpig70/FailureFutures
stages: price, settle
The most fragile asset issues the most futures: premium grows with fragility.
"""

from ._base import time_factor, require_non_negative, require_unit_interval


def price(order, P=None):
    """premium = asset_value * fragility * time_factor(days) (failure protection)."""
    value = order["asset_value"]
    fragility = order["fragility"]
    days = order["days_to_expiry"]
    require_non_negative("asset_value", value)
    require_unit_interval("fragility", fragility)
    tf = time_factor(days)
    premium = value * fragility * tf
    return {"premium": premium, "payout_amount": value, "fragility": fragility, "time_factor": tf}


def payoff(contract, outcome):
    premium = contract["premium"]
    payout = contract.get("payout_amount", 0)
    if outcome.get("failure"):
        return {"settlement_amount": payout, "buyer_net": payout - premium, "seller_net": premium - payout}
    return {"settlement_amount": 0.0, "buyer_net": -premium, "seller_net": premium}


MANIFEST = {
    "name": "failure-futures", "version": "1.0", "stages": ["price", "settle"],
    "order_schema": "schemas/order-failure.schema.json",
    "source_project": "github.com/sadpig70/FailureFutures",
}

SAMPLES = {
    "price": {"order": {"asset_value": 200.0, "fragility": 0.8, "days_to_expiry": 365}},
    "settle": {"contract": {"payout_amount": 200.0, "premium": 160.0}, "outcome": {"failure": False}},
}
