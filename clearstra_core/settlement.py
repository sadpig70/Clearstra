#!/usr/bin/env python3
"""Settlement — settle a priced contract against a realized outcome (zero-sum).

Generalizes CryoFutures.settle_contract: the market pack supplies the payoff formula;
the kernel enforces the zero-sum invariant (buyer_net + seller_net == 0). Pure stdlib.
"""

_EPS = 1e-9


def settle(contract, outcome, payoff, now=""):
    """Settle `contract` against `outcome` using the pack's `payoff(contract, outcome)`.

    payoff must return at least {buyer_net, seller_net}. Raises if not zero-sum.
    """
    result = payoff(contract, outcome)
    if "buyer_net" not in result or "seller_net" not in result:
        raise ValueError("payoff must return buyer_net and seller_net")
    if abs(result["buyer_net"] + result["seller_net"]) > _EPS:
        raise ValueError("settlement must be zero-sum (buyer_net + seller_net != 0)")
    return {**result, "settled_at": now}


def is_zero_sum(result):
    return abs(result.get("buyer_net", 0) + result.get("seller_net", 0)) <= _EPS
