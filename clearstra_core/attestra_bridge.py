#!/usr/bin/env python3
"""Attestra bridge — emit a clear() result as an Attestra clearing verification packet.

Clearstra COMPUTES; Attestra ATTESTS. This transform turns a clearing result into the
exact packet shape Attestra's `reserve-flow` pack verifies
(schemas/packet-clearing.schema.json), so a Clearstra clearing can be independently
attested. Because clear() is correct-by-construction, the resulting verdict is `valid`.
Pure stdlib; no clock/network/AI.
"""


def to_attestra_packet(clear_result, packet_id, priority_as_int=True):
    """Map a clear() result to an Attestra clearing packet.

    Attestra's clearing schema types `priority` as integer; set priority_as_int=False
    to preserve float priorities (then Attestra's schema would need `number`).
    """
    def _prio(p):
        return int(p) if priority_as_int and float(p).is_integer() else p

    return {
        "packet_id": packet_id,
        "subject": packet_id,
        "clearing": {
            "supply": clear_result["supply"],
            "allocations": [
                {"party_id": a["party_id"], "amount": a["amount"], "priority": _prio(a["priority"])}
                for a in clear_result["allocations"]
            ],
            "requests": [
                {"party_id": r["party_id"], "amount": r["amount"], "priority": _prio(r["priority"])}
                for r in clear_result["requests"]
            ],
        },
    }
