#!/usr/bin/env python3
"""Phase 4 — ClearRun pipeline, order_schema enforcement, and docs consistency."""

import os
import tempfile
import unittest

from clearstra_markets.loader import load_markets
from clearstra_run import clear_run, market_inputs_from_samples

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.reg = load_markets()

    def test_reserve_flow_full_run_with_ledger(self):
        m = self.reg["markets"]["reserve-flow"]
        with tempfile.TemporaryDirectory() as d:
            ledger = os.path.join(d, "clr.jsonl")
            out = clear_run(m, market_inputs_from_samples(m), now="T",
                            ledger_path=ledger, packet_id="RF-1")
            self.assertEqual(set(out["stages"]), {"price", "clear", "rehearse"})
            self.assertEqual(len(out["ledger_records"]), 3)
            self.assertTrue(out["chain"]["valid"])
            # clear stage emitted an Attestra packet
            self.assertIsNotNone(out["attestra_packet"])
            self.assertEqual(set(out["attestra_packet"]["clearing"]),
                             {"supply", "allocations", "requests"})

    def test_price_chains_into_settle(self):
        m = self.reg["markets"]["cryo-futures"]
        inputs = {"price": {"order": {"asset_value": 100.0, "failure_prob": 0.5, "days_to_expiry": 365}},
                  "settle": {"outcome": {"failure": True}}}  # no explicit contract -> chain from price
        out = clear_run(m, inputs, now="T")
        self.assertEqual(out["stages"]["price"]["premium"], 50.0)
        self.assertEqual(out["stages"]["settle"]["buyer_net"], 50.0)  # payout 100 - premium 50

    def test_idempotent_ledger(self):
        m = self.reg["markets"]["cold-capacity"]
        with tempfile.TemporaryDirectory() as d:
            l1, l2 = os.path.join(d, "a.jsonl"), os.path.join(d, "b.jsonl")
            clear_run(m, market_inputs_from_samples(m), now="AAA", ledger_path=l1)
            clear_run(m, market_inputs_from_samples(m), now="ZZZ", ledger_path=l2)
            import json
            with open(l1, encoding="utf-8") as f:
                h1 = [json.loads(x)["record_hash"] for x in f]
            with open(l2, encoding="utf-8") as f:
                h2 = [json.loads(x)["record_hash"] for x in f]
            self.assertEqual(h1, h2)  # now excluded from record_hash


class TestOrderSchemaEnforcement(unittest.TestCase):
    def test_all_markets_have_existing_schema(self):
        reg = load_markets()
        self.assertEqual(reg["errors"], [])  # every declared order_schema exists
        for m in reg["markets"].values():
            self.assertTrue(os.path.exists(os.path.join(ROOT, m["order_schema"])))


class TestDocs(unittest.TestCase):
    def _read(self, name):
        with open(os.path.join(DOCS, name), "r", encoding="utf-8") as f:
            return f.read()

    def test_three_docs_substantial(self):
        for name in ("ARCHITECTURE.md", "MARKET-CONTRACT.md", "DETERMINISM.md"):
            self.assertTrue(os.path.exists(os.path.join(DOCS, name)))
            self.assertGreater(len(self._read(name)), 800)

    def test_market_contract_matches_code(self):
        txt = self._read("MARKET-CONTRACT.md")
        for key in ("name", "version", "stages", "order_schema", "source_project"):
            self.assertIn(key, txt)
        for fn in ("price", "priority", "payoff", "shock_model"):
            self.assertIn(fn, txt)

    def test_determinism_doc_terms(self):
        txt = self._read("DETERMINISM.md")
        for term in ("random", "socket", "datetime.now", "record_hash", "math"):
            self.assertIn(term, txt)


if __name__ == "__main__":
    unittest.main()
