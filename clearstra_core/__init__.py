"""Clearstra kernel — single-source deterministic clearing substrate.

stdlib only. Time is injected (`now`); hashes exclude wall-time metadata. Market
formulas (price/priority/payoff/shock_model) plug in via the market contract.
Complementary to Attestra: Clearstra computes allocations; Attestra attests them.
"""

from .order import validate_pool, make_bid
from .pricing import (
    require_non_negative, require_unit_interval,
    time_factor, coverage_days, scarcity_premium, option_premium,
)
from .clearing import clear, clearing_invariants
from .settlement import settle, is_zero_sum
from .shock import rehearse
from .ledger import (
    canonical_json, sha256, append_clearing, build_record, verify_ledger,
)
from .fingerprint import normalize, fingerprint, fingerprint_market
from .attestra_bridge import to_attestra_packet

__all__ = [
    "validate_pool", "make_bid",
    "require_non_negative", "require_unit_interval",
    "time_factor", "coverage_days", "scarcity_premium", "option_premium",
    "clear", "clearing_invariants",
    "settle", "is_zero_sum",
    "rehearse",
    "canonical_json", "sha256", "append_clearing", "build_record", "verify_ledger",
    "normalize", "fingerprint", "fingerprint_market",
    "to_attestra_packet",
]
