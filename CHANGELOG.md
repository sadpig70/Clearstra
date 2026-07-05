# Changelog

All notable changes to Clearstra are documented here. Dates are ISO-8601.

## [0.1.0] — 2026-07-05

First release of Clearstra — a deterministic clearing exchange platform: one stdlib
kernel + N market packs. Complementary to [Attestra](https://github.com/sadpig70/Attestra)
(Clearstra computes clearings; Attestra attests them).

### Kernel (`clearstra_core/`)
- Order/bid pool model + validation (`order.py`)
- Pricing primitives — `time_factor`, `scarcity_premium`, `option_premium` (CryoFutures /
  MineralShock parity) (`pricing.py`)
- Clearing engine — conflict-free priority allocation, correct-by-construction (`clearing.py`)
- Zero-sum settlement (`settlement.py`), shock rehearsal (`shock.py`)
- Hash-chained, time-independent, tamper-evident clearing ledger (`ledger.py`)
- Market fingerprint / dedup (`fingerprint.py`), determinism checker (`determinism.py`)
- Attestra bridge — emit a clearing as an Attestra clearing packet (`attestra_bridge.py`)

### Markets (`clearstra_markets/`) — 10, all zero-kernel-change
- cryo-futures (reference, CryoFutures parity), reserve-flow (Attestra anchor),
  cold-capacity, failure-futures, refusal-option, exclusive-grant, quadratic-carbon,
  buy-bloc, shock-rehearsal, retrofit-receivable

### Orchestration, interface, docs
- `clearstra_run.py` — ClearRun pipeline (price → clear → settle → rehearse → ledger → bridge)
- `cli.py` — `market / run / stage / emit-packet / verify / determinism`
- 15 schemas (10 order + 5 kernel); loader enforces `order_schema` existence
- `docs/ARCHITECTURE.md`, `docs/MARKET-CONTRACT.md`, `docs/DETERMINISM.md`
- Design under `.pgf/` + `.pgxf/INDEX-Clearstra.json`

### Guarantees
- Determinism boundary enforced (`clearstra determinism` → clean)
- `clear()` correct-by-construction: conservation / no-conflict / priority always hold —
  the exact predicates Attestra verifies. Proven: `clear()` → Attestra verdict=valid.
- Full test suite green (`python -m unittest discover -s tests`) — 52 tests
