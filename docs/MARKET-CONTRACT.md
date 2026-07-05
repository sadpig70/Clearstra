# Clearstra Market Contract

> How to author a market pack. A market projects one clearing domain onto the kernel.
> **Adding a market requires no kernel change** — one module + one order schema.

## What a market is

A module under `clearstra_markets/` exposing:

| Name | Type | Meaning |
|---|---|---|
| `MANIFEST` | `dict` | market metadata (below) |
| stage functions | callables | one per declared stage (below) |
| `SAMPLES` | `dict[stage, dict]` | example inputs per stage, for `run_stage` |

The loader (`clearstra_markets/loader.py`) auto-discovers modules, validates the contract,
checks the declared `order_schema` file exists, and dedups by fingerprint. Drop the file in — it loads.

## MANIFEST

```python
MANIFEST = {
    "name": "my-market",                       # unique (kebab-case)
    "version": "1.0",
    "stages": ["price", "clear"],              # subset of price/clear/settle/rehearse
    "order_schema": "schemas/order-my.schema.json",  # must exist (loader errors otherwise)
    "source_project": "github.com/sadpig70/MyMarket",
}
```

## Stages → the function each requires

| Stage | Function you provide | Signature | Kernel uses it via |
|---|---|---|---|
| `price` | `price(order, P)` | `-> dict` (include your price/premium) | called directly |
| `clear` | `priority(bid)` | `-> number` (higher served first) | `clear(pool, supply, priority)` |
| `settle` | `payoff(contract, outcome)` | `-> {buyer_net, seller_net, ...}` | `settle(...)` (zero-sum enforced) |
| `rehearse` | `shock_model(scenario, item)` | `-> {coverage_days, shortfall, ...}` | `rehearse(...)` |

Every function is **pure**: no clock, no network, no randomness, no side effects
(see DETERMINISM.md). Compose price formulas from the primitives in `clearstra_markets._base`
(`time_factor`, `scarcity_premium`, `option_premium`, guards).

Rules the kernel enforces for you:
- `clear` output always satisfies conservation / no-conflict / priority (correct-by-construction).
  If `clear` feeds Attestra, return **integer** priorities (Attestra's clearing schema types them integer).
- `settle` payoff must be zero-sum (`buyer_net + seller_net == 0`), else the kernel raises.

## Complete minimal example

`clearstra_markets/example_market.py`:

```python
from ._base import time_factor, require_unit_interval, require_non_negative

def price(order, P=None):
    require_unit_interval("risk", order["risk"])
    return {"premium": order["notional"] * order["risk"] * time_factor(order["days"])}

def priority(bid):
    return int(bid.get("tier", 0))   # integer -> Attestra-composable

MANIFEST = {
    "name": "example-market", "version": "1.0", "stages": ["price", "clear"],
    "order_schema": "schemas/order-example.schema.json",
    "source_project": "github.com/sadpig70/Example",
}

SAMPLES = {
    "price": {"order": {"notional": 100.0, "risk": 0.5, "days": 365}},
    "clear": {"pool": [{"party_id": "A", "quantity": 60, "tier": 3},
                       {"party_id": "B", "quantity": 60, "tier": 1}], "supply": 60},
}
```

Add `schemas/order-example.schema.json` and it loads with no kernel change:

```bash
python cli.py market                                   # example-market appears, 0 errors
python cli.py stage --market example-market --stage price
python cli.py run --market example-market --now T      # full pipeline
```

## Checklist

- [ ] Module exposes `MANIFEST`, the stage functions for its `stages`, and `SAMPLES`
- [ ] `order_schema` file exists (else the loader reports an error and drops the market)
- [ ] Each stage function is pure (no clock/network/random/side effects)
- [ ] `clear` markets return integer priorities if they feed Attestra
- [ ] `settle` payoff is zero-sum
- [ ] `python cli.py market` shows the market with 0 errors; `determinism` stays clean
