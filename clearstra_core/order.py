#!/usr/bin/env python3
"""Order / bid pool model + validation.

A bid is a public order: {party_id, quantity, ...priority-inputs}. A pool is a list
of bids competing for a limited supply. Validation guarantees the preconditions the
clearing engine relies on (unique party per pool, non-negative quantities).
"""


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_pool(pool, supply=None):
    """Return {ok, reason}. Deterministic; no clock/network/AI."""
    if not isinstance(pool, list):
        return {"ok": False, "reason": "pool_not_list"}
    seen = set()
    for bid in pool:
        if not isinstance(bid, dict) or "party_id" not in bid:
            return {"ok": False, "reason": "bid_missing_party_id"}
        pid = bid["party_id"]
        if pid in seen:
            return {"ok": False, "reason": f"duplicate_party:{pid}"}
        seen.add(pid)
        q = bid.get("quantity")
        if not _is_number(q) or q < 0:
            return {"ok": False, "reason": f"bad_quantity:{pid}"}
    if supply is not None and (not _is_number(supply) or supply < 0):
        return {"ok": False, "reason": "bad_supply"}
    return {"ok": True, "reason": ""}


def make_bid(party_id, quantity, **priority_inputs):
    return {"party_id": party_id, "quantity": quantity, **priority_inputs}
