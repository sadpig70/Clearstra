# Clearstra Architecture

> **One deterministic clearing kernel + N market packs.** Clearstra prices scarce
> assets, clears limited supply by priority, settles against outcomes, and rehearses
> shocks — all deterministically, appending to a hash-chained clearing ledger.

## Layers

```
   cli.py            clearstra_run.py (ClearRun pipeline: price->clear->settle->rehearse->ledger->bridge)
   (subcommands)     ── meta / IO layer (file I/O, injected `now`) ──
                                   │ calls
   ┌───────────────── clearstra_markets/ (federated market packs) ─────────────────┐
   loader.py (discover · validate stages · order_schema · fingerprint dedup · run_stage)
   cryo-futures(ref) · reserve-flow(anchor) · cold-capacity · failure-futures · refusal-option
   exclusive-grant · quadratic-carbon · buy-bloc · shock-rehearsal · retrofit-receivable  (10)
   └────────────────────────────────────────────────────────────────────────────────┘
                                   │ each market contributes formulas only
   ┌───────────────── clearstra_core/ (deterministic kernel) ──────────────────────┐
   order · pricing · clearing · settlement · shock · ledger · fingerprint
   determinism · attestra_bridge          (stdlib only; no clock/network/AI; `now` injected)
   └────────────────────────────────────────────────────────────────────────────────┘
```

- **Kernel (`clearstra_core/`)** — single source of truth. The clearing engine, zero-sum
  settlement, shock aggregation, and ledger are defined **once** here. Markets never redefine them.
- **Markets (`clearstra_markets/`)** — each market is one corpus project projected as domain
  formulas: `price(order,P)`, `priority(bid)`, `payoff(contract,outcome)`, `shock_model(scenario,item)`.
  A market declares which `stages` it implements. Federated (tagged `source_project`).
- **Meta/IO** — CLI + ClearRun pipeline. File I/O + injected `now`, still clock-free.

## The four stages (`clearstra_run.clear_run`)

```
price    -> pricing primitives (time_factor, scarcity_premium, option_premium) compose a premium/price
clear    -> clear(pool, supply, priority) — conflict-free priority allocation
settle   -> settle(contract, outcome, payoff) — enforced zero-sum
rehearse -> rehearse(scenario, pool, shock_model) — survival / shortfall
                              │
                              └─> append_clearing (hash-chain ledger) ; clear -> Attestra packet
```

A market runs only the stages it declares; the price result chains into settle when a
contract is not supplied explicitly.

## Grounded in real corpus code

| Kernel piece | Real code it generalizes |
|---|---|
| `pricing.time_factor` / premium | `CryoFutures.price_future` (`premium = payout·failure_prob·√(days/365)`) |
| `pricing.scarcity_premium` / `option_premium` | `MineralShock.price_reserve_right` / `price_refusal_option` |
| `settlement.settle` | `CryoFutures.settle_contract` (zero-sum payoffs) |
| `shock.rehearse` | `MineralShock.simulate_shock` (survival/shortfall) |
| `clearing.clear` | ReserveFlow priority allocation (new kernel generalization) |

`cryo-futures` is the reference market (price/settle parity with CryoFutures).

## Attestra complementarity (compute ↔ attest)

Attestra ATTESTS clearings but declared their COMPUTATION out of scope. Clearstra is that
computation. `clear()` is **correct-by-construction**: its output always satisfies
conservation, no-conflict, and priority — exactly Attestra's clearing verification predicates.

```
Clearstra.clear() ─► attestra_bridge.to_attestra_packet() ─► Attestra reserve-flow pack ─► verdict=valid
```

Proven on real code (the `reserve-flow` market's clear output attests as `valid`, 4/4 checks).
Clearstra has **no runtime dependency** on Attestra — the bridge only emits the packet shape
Attestra's `schemas/packet-clearing.schema.json` expects.

## Determinism boundary

See [DETERMINISM.md](DETERMINISM.md). Kernel + market formulas are pure stdlib with injected
`now`; `clearstra_core/determinism.py` enforces it (`clearstra determinism` → clean).

## Extending

See [MARKET-CONTRACT.md](MARKET-CONTRACT.md) — a new market is a manifest + stage functions +
order schema, with **no kernel change**.
