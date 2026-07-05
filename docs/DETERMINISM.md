# Clearstra Determinism Boundary

> Clearstra's prices, allocations, and settlements must be **reproducible**: the same
> input yields the same output on any machine, at any time. Enforced by a checker.

## The rule

**`clearstra_core/` and `clearstra_markets/` are pure stdlib and fully deterministic.** They must not:

- read the clock (`time.time`, `datetime.now`, `datetime.utcnow`, `date.today`, …)
- use randomness (`random`, `secrets`)
- touch the network (`socket`, `requests`, `urllib`, `http`, …)
- depend on any non-stdlib package

`math` **is** allowed (it is deterministic) — clearing/pricing use `math.sqrt`, `math.fsum`.

Time is **injected** as `now` (a string), appears only as metadata (`cleared_at`,
`settled_at`, `rehearsed_at`, `recorded_at`), and is **excluded from every hash**. So a
clearing computed at two different times is byte-identical.

## Time-independent hashing

Ledger records hash their content minus wall-time metadata:

```
record_hash = sha256(canonical_json(record − {record_hash, recorded_at}))
canonical_json = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
```

Re-running a clearing with a different `now` produces identical `record_hash` values (tested).

## Determinism of the clearing itself

`clear(pool, supply, priority)` is deterministic beyond the boundary rule: bids are ranked by
`(-priority, str(party_id))`, so ties break reproducibly. Same pool + supply → same allocation,
always. This is what lets Attestra independently re-verify a Clearstra clearing.

## The checker

`clearstra_core/determinism.py` walks the AST of every `.py` under `clearstra_core/` and
`clearstra_markets/` and flags forbidden imports/calls.

```bash
python cli.py determinism        # -> {"clean": true, "files_scanned": N, "violations": {}}
```

`clean: true` is a release gate.

## Layer boundaries

| Layer | Files | Rule |
|---|---|---|
| **Kernel** | `clearstra_core/*` | pure stdlib, deterministic, `now` injected — **scanned** |
| **Markets** | `clearstra_markets/*` | pure formulas, deterministic — **scanned** |
| **Meta / IO** | `cli.py`, `clearstra_run.py` | file I/O + injected `now`; still clock-free — not scanned |
| **Domain stage** | the market's source project (price feeds, forecasts) | **outside** the boundary — produces the order |

Non-determinism (market data feeds, demand forecasts, an LLM) legitimately lives in the domain
stage that *builds the order*. It runs before Clearstra. Clearstra's job — order to price to
allocation to settlement — is the deterministic part.
