#!/usr/bin/env python3
"""RetrofitReceivableMarket — turn brownfield upgrades into financeable receivables.

source_project: github.com/sadpig70/RRE (Retrofit Receivable Exchange)
stages: price, settle
A financier (buyer) buys the receivable; the building owner (seller) gets financing.
"""

from ._base import require_non_negative, require_unit_interval


def price(order, P=None):
    """receivable_value = upgrade_savings * discount_factor(term, rate)."""
    savings = order["upgrade_savings"]
    term = order["term_years"]
    rate = order.get("discount_rate", 0.08)
    require_non_negative("upgrade_savings", savings)
    require_non_negative("term_years", term)
    require_unit_interval("discount_rate", rate)
    discount_factor = 1.0 / ((1.0 + rate) ** term)
    return {"receivable_value": savings * discount_factor,
            "discount_factor": discount_factor, "upgrade_savings": savings}


def payoff(contract, outcome):
    """Settle realized savings vs the financed receivable value (zero-sum)."""
    financed = contract["receivable_value"]
    realized = outcome["realized_savings"]
    # financier (buyer) gains realized - financed; owner (seller) mirrors
    buyer_net = realized - financed
    return {"settlement_amount": realized, "buyer_net": buyer_net, "seller_net": -buyer_net}


MANIFEST = {
    "name": "retrofit-receivable", "version": "1.0", "stages": ["price", "settle"],
    "order_schema": "schemas/order-retrofit.schema.json",
    "source_project": "github.com/sadpig70/RRE",
}

SAMPLES = {
    "price": {"order": {"upgrade_savings": 10000.0, "term_years": 5, "discount_rate": 0.08}},
    "settle": {"contract": {"receivable_value": 6805.83}, "outcome": {"realized_savings": 7000.0}},
}
