#!/usr/bin/env python3
"""ExclusiveGrantMarket — clear bids over a mutually-exclusive rights pool.

source_project: github.com/sadpig70/ExclusiveGrantWarrant
stages: clear
Winner-take-all: each exclusive right (supply=1 unit) goes to the highest bidder.
"""

from ._base import require_non_negative


def priority(bid):
    """Highest valuation wins the exclusive grant."""
    v = float(bid.get("valuation", 0))
    require_non_negative("valuation", v)
    return v


MANIFEST = {
    "name": "exclusive-grant", "version": "1.0", "stages": ["clear"],
    "order_schema": "schemas/order-grant.schema.json",
    "source_project": "github.com/sadpig70/ExclusiveGrantWarrant",
}

SAMPLES = {
    "clear": {"pool": [
        {"party_id": "bidder-1", "quantity": 1, "valuation": 12.0},
        {"party_id": "bidder-2", "quantity": 1, "valuation": 7.0},
        {"party_id": "bidder-3", "quantity": 1, "valuation": 3.0},
    ], "supply": 1},
}
