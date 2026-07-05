#!/usr/bin/env python3
"""ClearstraCore kernel tests — pricing parity, clearing invariants, settlement,
shock, ledger, fingerprint, Attestra composability, determinism boundary."""

import math
import os
import tempfile
import unittest

from clearstra_core import (
    time_factor, coverage_days, scarcity_premium, option_premium,
    clear, clearing_invariants, settle, is_zero_sum, rehearse,
    append_clearing, verify_ledger, build_record,
    fingerprint_market, to_attestra_packet, validate_pool,
)
from clearstra_core.determinism import check_tree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestPricingParity(unittest.TestCase):
    def test_time_factor(self):
        self.assertEqual(time_factor(365), 1.0)
        self.assertAlmostEqual(time_factor(0), 0.0)
        self.assertAlmostEqual(time_factor(91.25), math.sqrt(0.25))

    def test_cryofutures_premium_composition(self):
        # CryoFutures.price_future(payout=100, failure_prob=0.5, days=365) -> premium 50
        premium = 100 * 0.5 * time_factor(365)
        self.assertEqual(premium, 50.0)

    def test_scarcity_premium(self):
        self.assertEqual(scarcity_premium(0.8, 4), 0.2)     # 0.8 / max(4,1)
        self.assertEqual(scarcity_premium(0.8, 0.5), 0.8)   # 0.8 / max(0.5,1)=1

    def test_coverage_days(self):
        self.assertEqual(coverage_days(100, 10), 10.0)
        self.assertEqual(coverage_days(100, 0), float("inf"))

    def test_option_premium(self):
        # MineralShock refusal: capacity*value*threat*0.1
        self.assertAlmostEqual(option_premium(10, 100, 0.5), 50.0)

    def test_guards(self):
        with self.assertRaises(ValueError):
            time_factor(-1)
        with self.assertRaises(ValueError):
            scarcity_premium(1.5, 4)


class TestClearing(unittest.TestCase):
    POOL = [
        {"party_id": "A", "quantity": 60, "priority": 3},
        {"party_id": "B", "quantity": 50, "priority": 2},
        {"party_id": "C", "quantity": 40, "priority": 1},
    ]

    def test_priority_allocation(self):
        r = clear(self.POOL, 100, now="T")
        served = {a["party_id"]: a["amount"] for a in r["allocations"]}
        self.assertEqual(served, {"A": 60, "B": 40})  # C denied (lowest priority)
        self.assertEqual(r["remaining"], 0)
        self.assertEqual(r["allocated"], 100)

    def test_invariants_hold_by_construction(self):
        for supply in (0, 30, 60, 100, 200):
            inv = clearing_invariants(clear(self.POOL, supply, now="T"))
            self.assertTrue(inv["all_hold"], f"supply={supply}: {inv}")

    def test_deterministic_tiebreak(self):
        tie = [{"party_id": "B", "quantity": 60, "priority": 5},
               {"party_id": "A", "quantity": 60, "priority": 5}]
        r = clear(tie, 60, now="T")
        self.assertEqual(r["allocations"][0]["party_id"], "A")  # tie -> party_id asc

    def test_conservation_never_exceeds_supply(self):
        r = clear(self.POOL, 45, now="T")
        self.assertLessEqual(sum(a["amount"] for a in r["allocations"]), 45)

    def test_invalid_pool_raises(self):
        with self.assertRaises(ValueError):
            clear([{"party_id": "A", "quantity": 1}, {"party_id": "A", "quantity": 2}], 10)
        self.assertFalse(validate_pool("nope")["ok"])


class TestSettlement(unittest.TestCase):
    def test_zero_sum_ok(self):
        def payoff(contract, outcome):
            payout = contract["payout"] if outcome["failure"] else 0
            premium = contract["premium"]
            return {"settlement_amount": payout,
                    "buyer_net": payout - premium, "seller_net": premium - payout}
        r = settle({"payout": 100, "premium": 30}, {"failure": True}, payoff, now="T")
        self.assertTrue(is_zero_sum(r))
        self.assertEqual(r["buyer_net"], 70)
        self.assertEqual(r["seller_net"], -70)

    def test_non_zero_sum_raises(self):
        with self.assertRaises(ValueError):
            settle({}, {}, lambda c, o: {"buyer_net": 5, "seller_net": 5}, now="T")


class TestShock(unittest.TestCase):
    def test_survival_and_shortfall(self):
        def model(scenario, item):
            eff = item["stockpile"] * (1 - scenario["disruption"])
            cov = eff / item["demand"]
            shortfall = max(0.0, item["demand"] * scenario["days"] - eff)
            return {"id": item["id"], "coverage_days": cov, "shortfall": shortfall}
        pool = [{"id": "Li", "stockpile": 100, "demand": 10},
                {"id": "Co", "stockpile": 50, "demand": 10}]
        r = rehearse({"name": "S1", "disruption": 0.5, "days": 8}, pool, model, now="T")
        self.assertEqual(r["survival_days"], 2.5)      # min(5, 2.5)
        self.assertIn("Co", r["affected"])             # 50*0.5=25 < 80 required


class TestLedger(unittest.TestCase):
    def _res(self, s):
        return {"supply": s, "allocations": [], "cleared_at": "X"}

    def test_chain_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "clr.jsonl")
            append_clearing(p, self._res(100), "cryo-futures", "clear", now="T1")
            append_clearing(p, self._res(50), "reserve-flow", "clear", now="T2")
            rep = verify_ledger(p)
            self.assertTrue(rep["valid"])
            self.assertEqual(rep["records"], 2)

    def test_time_independent(self):
        a = build_record("", self._res(100), "m", "clear", now="AAA")
        b = build_record("", self._res(100), "m", "clear", now="ZZZ")
        self.assertEqual(a["record_hash"], b["record_hash"])

    def test_tamper_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "clr.jsonl")
            append_clearing(p, self._res(100), "m", "clear", now="T1")
            append_clearing(p, self._res(50), "m", "clear", now="T2")
            with open(p, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines[0] = lines[0].replace('"clear"', '"settle"')
            with open(p, "w", encoding="utf-8") as f:
                f.writelines(lines)
            self.assertFalse(verify_ledger(p)["valid"])


class TestFingerprintDedup(unittest.TestCase):
    def test_same_source_market_collides(self):
        a = {"name": "cryo-futures", "source_project": "github.com/sadpig70/CryoFutures",
             "stages": ["price", "settle"], "order_schema": "s"}
        b = {"name": "cryo-alias", "source_project": "github.com/sadpig70/CryoFutures",
             "stages": ["settle", "price"], "order_schema": "s"}  # same source, reordered
        self.assertEqual(fingerprint_market(a), fingerprint_market(b))

    def test_distinct_markets_sharing_stages_differ(self):
        a = {"source_project": "github.com/sadpig70/ColdMkh", "stages": ["price", "clear"], "order_schema": "s"}
        b = {"source_project": "github.com/sadpig70/BuyBloc", "stages": ["price", "clear"], "order_schema": "s"}
        self.assertNotEqual(fingerprint_market(a), fingerprint_market(b))


class TestAttestraComposability(unittest.TestCase):
    def test_packet_shape_and_valid_by_construction(self):
        pool = [{"party_id": "A", "quantity": 60, "priority": 3},
                {"party_id": "B", "quantity": 50, "priority": 2}]
        result = clear(pool, 100, now="T")
        packet = to_attestra_packet(result, "CLR-1")
        # shape Attestra's clearing pack expects
        self.assertEqual(set(packet), {"packet_id", "subject", "clearing"})
        self.assertEqual(set(packet["clearing"]), {"supply", "allocations", "requests"})
        # clear() output satisfies exactly Attestra's clearing predicates -> verdict would be valid
        self.assertTrue(clearing_invariants(result)["all_hold"])
        # integer priorities for Attestra's integer-typed schema
        self.assertTrue(all(isinstance(a["priority"], int) for a in packet["clearing"]["allocations"]))


class TestDeterminism(unittest.TestCase):
    def test_kernel_is_deterministic(self):
        rep = check_tree(ROOT)
        self.assertTrue(rep["clean"], f"violations: {rep['violations']}")
        self.assertGreater(rep["files_scanned"], 6)


if __name__ == "__main__":
    unittest.main()
