#!/usr/bin/env python3
"""Parity anchor: clearstra_markets.agent_ops vs the real AgentMesh reference.

AgentMesh is an independent repo (github.com/sadpig70/AgentMesh); it is not vendored in
Clearstra. When its source is importable in a dev checkout, this test asserts the
market's price() reproduces AgentMesh.price_record (cost) and account.assign_role
(accountable role) exactly across every op_type plus an unknown one. In CI (source
absent) it skips.

Point AGENTMESH_SRC at the project's ``src`` dir to run it, e.g.
    AGENTMESH_SRC=D:/IdeaFirst/agentmesh/src python -m unittest tests.test_agent_ops_parity
"""

import os
import sys
import unittest

from clearstra_markets.loader import load_markets, run_stage


def _load_agentmesh():
    candidates = [os.environ.get("AGENTMESH_SRC")]
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates += [
        os.path.join(here, "..", "agentmesh", "src"),
        os.path.join(here, "..", "AgentMesh", "src"),
        "D:/IdeaFirst/agentmesh/src",
    ]
    for cand in candidates:
        if cand and os.path.isdir(cand) and cand not in sys.path:
            sys.path.insert(0, cand)
    try:
        from agentmesh import account as account_mod  # noqa: WPS433
        from agentmesh import price as price_mod  # noqa: WPS433
        from agentmesh import models as models_mod  # noqa: WPS433
        return account_mod, price_mod, models_mod
    except Exception:  # noqa: BLE001 — source simply not present here
        return None, None, None


_ACCOUNT, _PRICE, _MODELS = _load_agentmesh()

_CASES = [
    {"op_type": "memory", "units": 1_000_000},
    {"op_type": "tool", "units": 1000},
    {"op_type": "cost", "units": 42.5},
    {"op_type": "rollback", "units": 3},
    {"op_type": "unknown_op", "units": 10},   # unrecognized -> cost 0, unassigned
]


def _record(spec):
    return _MODELS.CanonicalRecord(
        record_id="r", operator="op", agent_id="a", op_type=spec["op_type"],
        units=float(spec["units"]), unit_kind="", timestamp="", source_framework="generic")


@unittest.skipUnless(_PRICE is not None, "AgentMesh source not importable (independent repo)")
class TestAgentOpsParity(unittest.TestCase):
    def setUp(self):
        self.market = load_markets()["markets"]["agent-ops"]

    def test_cost_and_role_match_source(self):
        for spec in _CASES:
            with self.subTest(op_type=spec["op_type"]):
                record = _record(spec)
                src_cost = _PRICE.price_record(record)
                src_role = _ACCOUNT.assign_role(record)

                r = run_stage(self.market, "price", {"order": spec})
                self.assertAlmostEqual(r["cost"], src_cost, places=12,
                                       msg=f"cost mismatch for {spec['op_type']}")
                self.assertEqual(r["accountable_role"], src_role,
                                 f"role mismatch for {spec['op_type']}")


if __name__ == "__main__":
    unittest.main()
