#!/usr/bin/env python3
"""MarketContract — manifest/stage validation, dedup, and stage dispatch through the kernel.

Phase 2 verifies the contract with an in-memory synthetic market (no Phase-3 markets pulled
forward). It exercises all four stages: price / clear / settle / rehearse.
"""

import types
import unittest

from clearstra_markets.loader import (
    validate_module, load_markets, run_stage, get_market, STAGE_FN,
)
from clearstra_markets import _base


def _fake_market():
    """A synthetic four-stage market module (SimpleNamespace stands in for a module)."""
    def price(order, P=None):
        premium = order["payout"] * order["failure_prob"] * _base.time_factor(order["days"])
        return {"premium": premium}

    def priority(bid):
        return bid.get("criticality", 0) * (1.0 / max(bid.get("coverage", 1), 1))

    def payoff(contract, outcome):
        payout = contract["payout"] if outcome["failure"] else 0
        premium = contract["premium"]
        return {"settlement_amount": payout,
                "buyer_net": payout - premium, "seller_net": premium - payout}

    def shock_model(scenario, item):
        eff = item["stockpile"] * (1 - scenario["disruption"])
        return {"id": item["id"], "coverage_days": eff / item["demand"],
                "shortfall": max(0.0, item["demand"] * scenario["days"] - eff)}

    return types.SimpleNamespace(
        MANIFEST={"name": "fake", "version": "1.0",
                  "stages": ["price", "clear", "settle", "rehearse"],
                  "order_schema": "schemas/order-fake.schema.json",
                  "source_project": "github.com/sadpig70/Fake"},
        price=price, priority=priority, payoff=payoff, shock_model=shock_model,
        SAMPLES={},
    )


class TestValidation(unittest.TestCase):
    def test_valid_module(self):
        manifest, fns, err = validate_module(_fake_market(), "fake")
        self.assertEqual(err, "")
        self.assertEqual(set(fns), {"price", "clear", "settle", "rehearse"})

    def test_missing_stage_function(self):
        mod = _fake_market()
        del mod.payoff  # declares 'settle' but has no payoff()
        _, _, err = validate_module(mod, "fake")
        self.assertIn("settle", err)

    def test_bad_stages(self):
        mod = _fake_market()
        mod.MANIFEST = {**mod.MANIFEST, "stages": ["price", "teleport"]}
        _, _, err = validate_module(mod, "fake")
        self.assertIn("stages", err)

    def test_missing_manifest_key(self):
        mod = _fake_market()
        mod.MANIFEST = {k: v for k, v in mod.MANIFEST.items() if k != "source_project"}
        _, _, err = validate_module(mod, "fake")
        self.assertIn("source_project", err)

    def test_stage_fn_map(self):
        self.assertEqual(STAGE_FN,
                         {"price": "price", "clear": "priority",
                          "settle": "payoff", "rehearse": "shock_model"})


class TestRunStage(unittest.TestCase):
    def setUp(self):
        manifest, fns, _ = validate_module(_fake_market(), "fake")
        self.market = {**manifest, "fns": fns}

    def test_price(self):
        r = run_stage(self.market, "price", {"order": {"payout": 100, "failure_prob": 0.5, "days": 365}})
        self.assertEqual(r["premium"], 50.0)

    def test_clear_uses_market_priority(self):
        pool = [{"party_id": "A", "quantity": 60, "criticality": 0.9, "coverage": 2},
                {"party_id": "B", "quantity": 60, "criticality": 0.3, "coverage": 2}]
        r = run_stage(self.market, "clear", {"pool": pool, "supply": 60}, now="T")
        self.assertEqual(r["allocations"][0]["party_id"], "A")  # higher criticality served first

    def test_settle_zero_sum(self):
        r = run_stage(self.market, "settle",
                      {"contract": {"payout": 100, "premium": 30}, "outcome": {"failure": True}}, now="T")
        self.assertEqual(r["buyer_net"] + r["seller_net"], 0)

    def test_rehearse(self):
        pool = [{"id": "Li", "stockpile": 100, "demand": 10}]
        r = run_stage(self.market, "rehearse",
                      {"scenario": {"name": "S", "disruption": 0.5, "days": 8}, "pool": pool}, now="T")
        self.assertEqual(r["survival_days"], 5.0)

    def test_unimplemented_stage_raises(self):
        market = {"name": "x", "fns": {"price": lambda o, P: {}}}
        with self.assertRaises(ValueError):
            run_stage(market, "clear", {})


class TestRegistry(unittest.TestCase):
    def test_package_loads_cleanly(self):
        reg = load_markets()  # real markets exist from Phase 3; contract must load them cleanly
        self.assertEqual(reg["errors"], [])
        self.assertEqual(reg["dropped"], [])
        for m in reg["markets"].values():  # every loaded market satisfies the contract
            self.assertTrue(m["stages"] and "fns" in m)

    def test_get_market_unknown_raises(self):
        with self.assertRaises(KeyError):
            get_market({"markets": {}}, "nope")


if __name__ == "__main__":
    unittest.main()
