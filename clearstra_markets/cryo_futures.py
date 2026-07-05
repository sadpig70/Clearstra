#!/usr/bin/env python3
"""CryoFuturesMarket — reference market. Parity with CryoFutures (ColdMkh+FailureFutures).

source_project: github.com/sadpig70/CryoFutures
stages: price, settle
Parity anchor: price/settle must match CryoFutures.price_future / settle_contract.
"""

from ._base import time_factor, require_non_negative, require_unit_interval


def price(order, P=None):
    """premium = payout * failure_prob * time_factor(days). Mirrors CryoFutures.price_future."""
    asset_value = order.get("asset_value", 0)
    failure_prob = order["failure_prob"]
    days = order["days_to_expiry"]
    require_non_negative("asset_value", asset_value)
    require_unit_interval("failure_prob", failure_prob)
    payout = order.get("payout_amount", asset_value)
    require_non_negative("payout_amount", payout)
    tf = time_factor(days)
    premium = payout * failure_prob * tf
    return {"settlement_mode": "failure_protection", "payout_amount": payout,
            "failure_prob": failure_prob, "days_to_expiry": days,
            "time_factor": tf, "premium": premium, "future_price": premium}


def payoff(contract, outcome):
    """Failure-protection settlement (zero-sum). Mirrors CryoFutures.settle_contract."""
    premium = contract.get("premium", contract.get("future_price"))
    payout = contract.get("payout_amount", contract.get("asset_value", 0))
    failure = outcome.get("failure", outcome.get("actual_failure"))
    if failure:
        return {"settlement_amount": payout, "buyer_net": payout - premium,
                "seller_net": premium - payout, "actual_failure": True}
    return {"settlement_amount": 0.0, "buyer_net": -premium,
            "seller_net": premium, "actual_failure": False}


MANIFEST = {
    "name": "cryo-futures", "version": "1.0", "stages": ["price", "settle"],
    "order_schema": "schemas/order-cryo.schema.json",
    "source_project": "github.com/sadpig70/CryoFutures",
}

SAMPLES = {
    "price": {"order": {"asset_value": 100.0, "failure_prob": 0.5, "days_to_expiry": 365}},
    "settle": {"contract": {"payout_amount": 100.0, "premium": 50.0}, "outcome": {"failure": True}},
}
