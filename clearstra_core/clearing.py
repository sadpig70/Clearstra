#!/usr/bin/env python3
"""The clearing engine — conflict-free priority allocation of a limited supply.

`clear` is correct-by-construction: its output always satisfies conservation,
no-conflict, and priority — the exact predicates Attestra's clearing pack verifies.
That is what makes Clearstra (compute) and Attestra (attest) provably composable.
Pure stdlib; `now` injected.
"""

from .order import validate_pool
from .pricing import require_non_negative


def clear(pool, supply, priority_key=None, now=""):
    """Allocate `supply` across `pool` in strict priority order (deterministic).

    priority_key(bid) -> number (higher = served first); defaults to bid["priority"].
    Ties break by str(party_id) so the result is fully deterministic.
    """
    pv = validate_pool(pool, supply)
    if not pv["ok"]:
        raise ValueError(f"invalid pool: {pv['reason']}")
    require_non_negative("supply", supply)
    key = priority_key or (lambda b: b.get("priority", 0))

    ranked = sorted(pool, key=lambda b: (-float(key(b)), str(b["party_id"])))
    remaining = supply
    allocations = []
    for bid in ranked:
        take = min(bid["quantity"], remaining)
        if take > 0:
            allocations.append({"party_id": bid["party_id"], "amount": take,
                                "priority": float(key(bid))})
            remaining -= take
    return {
        "supply": supply,
        "allocated": supply - remaining,
        "remaining": remaining,
        "allocations": allocations,
        "requests": [{"party_id": b["party_id"], "amount": b["quantity"],
                      "priority": float(key(b))} for b in pool],
        "cleared_at": now,
    }


def clearing_invariants(clear_result):
    """Independently check the three invariants (mirrors Attestra's clearing predicates).

    Returns {conservation, no_conflict, priority, all_hold}. Used to prove that clear()
    output attests as valid without importing Attestra.
    """
    allocs = clear_result["allocations"]
    supply = clear_result["supply"]
    requests = clear_result["requests"]
    total = sum(a["amount"] for a in allocs)
    parties = [a["party_id"] for a in allocs]

    conservation = total <= supply + 1e-9
    no_conflict = len(parties) == len(set(parties)) and all(a["amount"] >= 0 for a in allocs)

    served = {a["party_id"]: a["amount"] for a in allocs}
    served_priorities = [r["priority"] for r in requests if served.get(r["party_id"], 0) > 0]
    priority = True
    for r in requests:
        got = served.get(r["party_id"], 0)
        # a fully denied party must not outrank any served party
        if got == 0 and any(r["priority"] > sp for sp in served_priorities):
            priority = False
        # an underserved party must not outrank a served party
        if 0 < got < r["amount"] and any(r["priority"] > sp for sp in served_priorities):
            priority = False

    return {"conservation": conservation, "no_conflict": no_conflict,
            "priority": priority, "all_hold": conservation and no_conflict and priority}
