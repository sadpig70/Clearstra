#!/usr/bin/env python3
"""ClearRun — run a market's declared stages end-to-end.

price -> clear -> settle -> (rehearse) -> clearing ledger -> Attestra packet.
Stages run in canonical order for whichever a market declares; the price result
chains into settle when settle's contract is not given explicitly. Meta/IO layer:
file I/O + injected `now`, clock-free.
"""

from clearstra_core.ledger import append_clearing, verify_ledger
from clearstra_core.attestra_bridge import to_attestra_packet
from clearstra_markets.loader import run_stage

_ORDER = ("price", "clear", "settle", "rehearse")


def clear_run(market, inputs, now="", ledger_path=None, packet_id=None):
    """Run every declared stage the caller supplied inputs for.

    inputs: {"price": {order,P}, "clear": {pool,supply}, "settle": {contract,outcome},
             "rehearse": {scenario,pool}}  (any subset the market declares)
    Returns {market, stages, ledger_records, attestra_packet}.
    """
    pid = packet_id or f"{market['name']}-run"
    out = {"market": market["name"], "stages": {}, "ledger_records": [], "attestra_packet": None}
    for stage in _ORDER:
        if stage not in market["stages"] or stage not in inputs:
            continue
        stage_inputs = dict(inputs[stage])
        # chain price -> settle when the contract is not supplied explicitly
        if stage == "settle" and "contract" not in stage_inputs and "price" in out["stages"]:
            stage_inputs["contract"] = out["stages"]["price"]
        result = run_stage(market, stage, stage_inputs, now=now)
        out["stages"][stage] = result
        if ledger_path:
            rec = append_clearing(ledger_path, result, market["name"], stage, now=now, subject=pid)
            out["ledger_records"].append({"kind": stage, "index": rec["index"]})
        if stage == "clear":
            out["attestra_packet"] = to_attestra_packet(result, pid)
    if ledger_path:
        out["chain"] = verify_ledger(ledger_path)
    return out


def market_inputs_from_samples(market):
    """Build a clear_run inputs dict from a market's SAMPLES (one input per stage)."""
    return {stage: market["samples"][stage] for stage in market["stages"]
            if stage in market.get("samples", {})}
