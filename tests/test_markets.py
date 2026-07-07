#!/usr/bin/env python3
"""Phase 3 markets — registry load, per-stage execution, reference parity, Attestra anchor."""

import os
import unittest

from clearstra_core.clearing import clearing_invariants
from clearstra_core.attestra_bridge import to_attestra_packet
from clearstra_core.determinism import check_tree
from clearstra_markets.loader import load_markets, run_stage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED = {
    "cryo-futures", "reserve-flow", "cold-capacity", "failure-futures", "refusal-option",
    "exclusive-grant", "quadratic-carbon", "buy-bloc", "shock-rehearsal", "retrofit-receivable",
    "agent-ops",   # BUILD_ON_PLATFORM: compat-mesh cluster (AgentMesh) -> Clearstra price market
    "mineral-shock",  # BUILD_ON_PLATFORM: MineralShock reserve pricing + supply-shock rehearsal
}


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = load_markets()

    def test_all_markets_loaded(self):
        self.assertEqual(set(self.reg["markets"]), EXPECTED)

    def test_no_errors_or_drops(self):
        self.assertEqual(self.reg["errors"], [])
        self.assertEqual(self.reg["dropped"], [])

    def test_source_projects_tagged(self):
        for m in self.reg["markets"].values():
            self.assertTrue(m["source_project"].startswith("github.com/sadpig70/"))


class TestEveryStageRuns(unittest.TestCase):
    def test_declared_stages_execute(self):
        reg = load_markets()
        for name, market in reg["markets"].items():
            for stage in market["stages"]:
                self.assertIn(stage, market["samples"], f"{name} missing sample for {stage}")
                result = run_stage(market, stage, market["samples"][stage], now="T")
                self.assertIsInstance(result, dict, f"{name}.{stage} returned non-dict")


class TestCryoFuturesParity(unittest.TestCase):
    def setUp(self):
        self.m = load_markets()["markets"]["cryo-futures"]

    def test_price(self):
        r = run_stage(self.m, "price", self.m["samples"]["price"])
        self.assertEqual(r["premium"], 50.0)        # 100 * 0.5 * time_factor(365)=1
        self.assertEqual(r["future_price"], r["premium"])

    def test_settle_zero_sum(self):
        r = run_stage(self.m, "settle", self.m["samples"]["settle"], now="T")
        self.assertEqual(r["buyer_net"], 50.0)      # payout 100 - premium 50
        self.assertEqual(r["buyer_net"] + r["seller_net"], 0)


class TestReserveFlowAttestraAnchor(unittest.TestCase):
    def setUp(self):
        self.m = load_markets()["markets"]["reserve-flow"]

    def test_clear_invariants_and_packet(self):
        result = run_stage(self.m, "clear", self.m["samples"]["clear"], now="T")
        self.assertTrue(clearing_invariants(result)["all_hold"])
        packet = to_attestra_packet(result, "RF-CLR-1")
        self.assertEqual(set(packet["clearing"]), {"supply", "allocations", "requests"})
        # integer priorities so the packet fits Attestra's clearing schema
        self.assertTrue(all(isinstance(a["priority"], int) for a in packet["clearing"]["allocations"]))
        served = {a["party_id"]: a["amount"] for a in result["allocations"]}
        self.assertEqual(served, {"defense": 400, "energy": 400})  # highest shock-weight first

    def test_price_and_rehearse(self):
        p = run_stage(self.m, "price", self.m["samples"]["price"])
        self.assertGreater(p["right_price"], 0)
        r = run_stage(self.m, "rehearse", self.m["samples"]["rehearse"], now="T")
        self.assertIn("survival_days", r)


class TestMarketSemantics(unittest.TestCase):
    def setUp(self):
        self.reg = load_markets()

    def test_quadratic_favors_many_small(self):
        m = self.reg["markets"]["quadratic-carbon"]
        r = run_stage(m, "clear", m["samples"]["clear"], now="T")
        self.assertEqual(r["allocations"][0]["party_id"], "grassroots")  # (Σ√1)^2=81 > (√9)^2=9

    def test_exclusive_grant_highest_bidder(self):
        m = self.reg["markets"]["exclusive-grant"]
        r = run_stage(m, "clear", m["samples"]["clear"], now="T")
        self.assertEqual(len(r["allocations"]), 1)
        self.assertEqual(r["allocations"][0]["party_id"], "bidder-1")

    def test_cold_capacity_highest_valuation(self):
        m = self.reg["markets"]["cold-capacity"]
        r = run_stage(m, "clear", m["samples"]["clear"], now="T")
        self.assertEqual(r["allocations"][0]["party_id"], "labA")


class TestDeterminism(unittest.TestCase):
    def test_markets_deterministic(self):
        rep = check_tree(ROOT)
        self.assertTrue(rep["clean"], f"violations: {rep['violations']}")


if __name__ == "__main__":
    unittest.main()
