#!/usr/bin/env python3
"""Clearstra CLI — market / run / stage / emit-packet / verify / determinism / report.

stdlib only. `now` is injected via --now (default ""), never read from the clock.
"""

import argparse
import json
import os
import sys

from clearstra_core.ledger import verify_ledger
from clearstra_core.attestra_bridge import to_attestra_packet
from clearstra_core.determinism import check_tree
from clearstra_markets.loader import load_markets, get_market, run_stage
from clearstra_run import clear_run, market_inputs_from_samples

ROOT = os.path.dirname(os.path.abspath(__file__))


def _dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, default=_default))


def _default(o):
    if o == float("inf"):
        return "inf"
    raise TypeError


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_market(args, reg):
    _dump({
        "markets": [
            {"name": m["name"], "version": m["version"], "stages": m["stages"],
             "source_project": m["source_project"], "fingerprint": m["fingerprint"][:16]}
            for m in reg["markets"].values()
        ],
        "dropped": reg["dropped"], "errors": reg["errors"],
    })
    return 0


def cmd_run(args, reg):
    market = get_market(reg, args.market)
    inputs = _load_json(args.input) if args.input else market_inputs_from_samples(market)
    result = clear_run(market, inputs, now=args.now, ledger_path=args.ledger,
                       packet_id=args.packet_id)
    _dump(result)
    if args.ledger and not result.get("chain", {}).get("valid", True):
        return 2
    return 0


def cmd_stage(args, reg):
    market = get_market(reg, args.market)
    inputs = _load_json(args.input) if args.input else market["samples"].get(args.stage, {})
    _dump(run_stage(market, args.stage, inputs, now=args.now))
    return 0


def cmd_emit_packet(args, reg):
    market = get_market(reg, args.market)
    if "clear" not in market["stages"]:
        print(f"market {args.market} has no clear stage", file=sys.stderr)
        return 2
    inputs = _load_json(args.input) if args.input else market["samples"]["clear"]
    result = run_stage(market, "clear", inputs, now=args.now)
    _dump(to_attestra_packet(result, args.packet_id or f"{args.market}-clear"))
    return 0


def cmd_verify(args, _reg):
    report = verify_ledger(args.ledger)
    _dump(report)
    return 0 if report["valid"] else 1


def cmd_determinism(_args, _reg):
    report = check_tree(ROOT)
    _dump(report)
    return 0 if report["clean"] else 1


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--now", default="", help="injected timestamp metadata (default empty)")

    p = argparse.ArgumentParser(prog="clearstra", parents=[common],
                                description="Deterministic clearing exchange platform")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("market", parents=[common], help="list loaded markets").add_argument(
        "list", nargs="?")

    s = sub.add_parser("run", parents=[common], help="run a market's full pipeline")
    s.add_argument("--market", required=True)
    s.add_argument("--input", help="JSON inputs {stage: {...}} (default: market samples)")
    s.add_argument("--ledger", help="clearing ledger path")
    s.add_argument("--packet-id", dest="packet_id")

    s = sub.add_parser("stage", parents=[common], help="run one stage of a market")
    s.add_argument("--market", required=True)
    s.add_argument("--stage", required=True, choices=["price", "clear", "settle", "rehearse"])
    s.add_argument("--input", help="JSON inputs for the stage (default: market sample)")

    s = sub.add_parser("emit-packet", parents=[common], help="clear -> Attestra clearing packet")
    s.add_argument("--market", required=True)
    s.add_argument("--input")
    s.add_argument("--packet-id", dest="packet_id")

    s = sub.add_parser("verify", parents=[common], help="verify a clearing ledger's hash chain")
    s.add_argument("--ledger", required=True)

    sub.add_parser("determinism", parents=[common], help="scan kernel+markets for boundary violations")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    reg = load_markets()
    dispatch = {"market": cmd_market, "run": cmd_run, "stage": cmd_stage,
                "emit-packet": cmd_emit_packet, "verify": cmd_verify,
                "determinism": cmd_determinism}
    return dispatch[args.cmd](args, reg)


if __name__ == "__main__":
    raise SystemExit(main())
