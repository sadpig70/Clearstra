#!/usr/bin/env python3
"""QuadraticCarbonMarket — allocate a matching pool by quadratic funding weight.

source_project: github.com/sadpig70/QuadraticCarbonFund
stages: clear
Quadratic funding favors many small contributions: weight = (Σ√contribution)^2.
"""

import math

from ._base import require_non_negative


def priority(bid):
    """Quadratic funding weight = (sum of sqrt(contributions)) ** 2."""
    contributions = bid.get("contributions", [])
    for c in contributions:
        require_non_negative("contribution", c)
    return math.fsum(math.sqrt(c) for c in contributions) ** 2


MANIFEST = {
    "name": "quadratic-carbon", "version": "1.0", "stages": ["clear"],
    "order_schema": "schemas/order-carbon.schema.json",
    "source_project": "github.com/sadpig70/QuadraticCarbonFund",
}

SAMPLES = {
    # many small contributions (grassroots) outweigh one large (whale) at equal sum
    "clear": {"pool": [
        {"party_id": "grassroots", "quantity": 500, "contributions": [1, 1, 1, 1, 1, 1, 1, 1, 1]},
        {"party_id": "whale", "quantity": 500, "contributions": [9]},
    ], "supply": 500},
}
