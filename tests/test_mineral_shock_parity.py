#!/usr/bin/env python3
"""Parity anchor: clearstra_markets.mineral_shock vs the real MineralShock core.

MineralShock is an independent repo (github.com/sadpig70/MineralShock); it is not vendored
in Clearstra. When its source is importable in a dev checkout, this test asserts the
market's price() reproduces price_reserve_right / price_refusal_option and its rehearse
reproduces simulate_shock's survival_days + total_shortfall. In CI it skips.

Point MINERALSHOCK_SRC at the project's ``src`` dir to run it, e.g.
    MINERALSHOCK_SRC=D:/HELIX/MineralShock/src python -m unittest tests.test_mineral_shock_parity
"""

import os
import sys
import unittest

from clearstra_markets.loader import load_markets, run_stage


def _load_mineralshock():
    candidates = [os.environ.get("MINERALSHOCK_SRC")]
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates += [
        os.path.join(here, "..", "MineralShock", "src"),
        "D:/HELIX/MineralShock/src",
    ]
    for cand in candidates:
        if cand and os.path.isdir(cand) and cand not in sys.path:
            sys.path.insert(0, cand)
    try:
        from MineralShock import core  # noqa: WPS433
        return core
    except Exception:  # noqa: BLE001 — source simply not present here
        return None


_CORE = _load_mineralshock()


@unittest.skipUnless(_CORE is not None, "MineralShock source not importable (independent repo)")
class TestMineralShockParity(unittest.TestCase):
    def setUp(self):
        self.m = load_markets()["markets"]["mineral-shock"]

    def test_reserve_right_price_matches(self):
        order = {"kind": "reserve_right", "mineral": "cobalt",
                 "stockpile_tonnes": 1000.0, "criticality": 0.8, "daily_demand": 10.0}
        pack = run_stage(self.m, "price", {"order": order})
        src = _CORE.price_reserve_right("cobalt", 1000.0, 0.8, 10.0)
        self.assertAlmostEqual(pack["right_price"], src["right_price"], places=9)
        self.assertAlmostEqual(pack["coverage_days"], src["coverage_days"], places=9)
        self.assertAlmostEqual(pack["scarcity_premium"], src["scarcity_premium"], places=9)

    def test_refusal_option_price_matches(self):
        order = {"kind": "refusal_option", "refusal_capacity_tonnes": 200.0,
                 "threat_level": 0.6, "mineral_value": 5000.0}
        pack = run_stage(self.m, "price", {"order": order})
        src = _CORE.price_refusal_option(200.0, 0.6, 5000.0)
        self.assertAlmostEqual(pack["option_premium"], src["option_premium"], places=9)

    def test_shock_rehearse_matches(self):
        scenario = {"name": "disruption", "demand_spike_pct": 0.5,
                    "supply_disruption_pct": 0.3, "mission_days": 30}
        pool = [{"mineral": "cobalt", "stockpile_tonnes": 1000.0, "daily_demand": 10.0},
                {"mineral": "lithium", "stockpile_tonnes": 500.0, "daily_demand": 20.0}]
        pack = run_stage(self.m, "rehearse", {"scenario": scenario, "pool": pool}, now="T")
        src = _CORE.simulate_shock(scenario, pool)
        self.assertAlmostEqual(pack["survival_days"], src["survival_days"], places=9)
        self.assertAlmostEqual(pack["total_shortfall"], src["total_shortfall_tonnes"], places=9)


if __name__ == "__main__":
    unittest.main()
