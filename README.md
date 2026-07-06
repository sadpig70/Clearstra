![Clearstra](assets/Clearstra_hero.png)

[![CI](https://github.com/sadpig70/Clearstra/actions/workflows/ci.yml/badge.svg)](https://github.com/sadpig70/Clearstra/actions/workflows/ci.yml)

# Clearstra

> **희소·취약·임계 자산의 권리/용량/선물을 결정론적으로 청산하는 거래소 플랫폼.**
> `price → clear → settle → rehearse` + hash-chain 청산 원장 — 하나의 커널, N개 마켓 팩.

Clearstra는 **하나의 결정론 청산 커널 + N개 마켓 팩** 구조다. HELIX corpus의 clearing/market
프로젝트들(CryoFutures·ColdMkh·FailureFutures·ReserveFlow·RefusalOption·ShockRehearsal·
ExclusiveGrantWarrant·QuadraticCarbonFund·BuyBloc·RRE)이 도메인 공식만 바꿔 같은 청산 기계를 반복
구현해 왔는데, Clearstra는 그 기계를 커널로 한 번만 정의하고 각 시장을 **마켓 팩**으로 얹는다.

## 계보 & Attestra 상보성
> 🔗 **생태계 데모**: [stra-demo](https://github.com/sadpig70/stra-demo) — route → clear → certify → attest가 한 결정을 함께 처리하는 end-to-end 데모.


Clearstra는 [HELIX](../README.md)의 자식 프로젝트이며 **독립 저장소**로 자립 구동한다.

- **HELIX** = 프로젝트를 *생성*하는 자율 창조 루프.
- **[Attestra](../Attestra/README.md)** = 산출물을 *증언(attest)*하는 verdict 플랫폼. Attestra는
  청산의 *계산*을 명시적으로 범위 밖에 뒀다.
- **Clearstra** = 그 *계산* 절반. 시장을 *청산(compute)*한다.

두 플랫폼은 **"계산 → 증명"으로 조합**된다:

```
Clearstra.clear()  ──►  to_attestra_packet()  ──►  Attestra reserve-flow 팩  ──►  verdict=valid
   (배분 계산)              (검증 packet 방출)            (배분 증언)
```

`clear()`는 보존(conservation)·무충돌(no-conflict)·우선순위(priority)를 **불변식으로 보장**하는데,
이는 정확히 Attestra clearing 팩의 검증 술어다 → 두 플랫폼 조합이 **증명가능**하다.

## 청산 기계 (실코드 근거)

corpus의 각 시장은 아래 4단계 중 자기 것을 구현한다. 커널이 오케스트레이션하고, 팩은 공식만 준다.

| 단계 | 커널 함수 | 실코드 근거 |
|---|---|---|
| **price** | `Pricing` primitive 조합 | `CryoFutures.price_future`, `MineralShock.price_reserve_right` |
| **clear** | `clear(pool, supply, priority)` — 충돌 없는 우선순위 배분 | ReserveFlow 배분 (신규 커널 일반화) |
| **settle** | `settle(contract, outcome, payoff)` — zero-sum 정산 | `CryoFutures.settle_contract` |
| **rehearse** | `rehearse(scenario, pool, model)` — 쇼크 shortfall/survival | `MineralShock.simulate_shock` |

## 구조

```
Clearstra/
├── README.md
├── .pgf/                          # PGF 설계·계획·상태 (pgf full-cycle로 지어짐)
│   ├── DESIGN-Clearstra.md        #   메인 설계 (Gantree + PPR)
│   ├── DESIGN-ClearstraMarkets.md #   (decomposed) 1차 마켓 10종 명세
│   ├── WORKPLAN-Clearstra.md      #   실행 계획 (POLICY + 위상정렬 + 검증 게이트)
│   └── status-Clearstra.json      #   노드별 상태
├── .pgxf/INDEX-Clearstra.json     # PGXF 인덱스 (32 노드 · decomposed 크로스ref)
├── clearstra_core/                # ★ 커널 — 결정론 청산 substrate (stdlib only) [예정]
│   ├── order.py · pricing.py · clearing.py · settlement.py · shock.py
│   ├── ledger.py · fingerprint.py · determinism.py · attestra_bridge.py
├── clearstra_markets/             # ★ 마켓 팩 — 각 HELIX 시장의 공식 계약 [예정]
│   └── cryo_futures/ (레퍼런스) · reserve_flow/ (Attestra 앵커) · ...
├── schemas/ · cli.py · tests/     # [예정]
```

> 현재 상태: **설계 완료(design phase)**. 코드 노드는 WORKPLAN Phase 1부터 구현 예정.

## 1차 마켓 팩 (10종)

`cryo-futures`(레퍼런스) · `reserve-flow`(Attestra 앵커) · `cold-capacity` · `failure-futures` ·
`refusal-option` · `exclusive-grant` · `quadratic-carbon` · `buy-bloc` · `shock-rehearsal` ·
`retrofit-receivable`.

**추가 흡수 마켓 (총 11종):** `agent-ops` — AgentMesh(에이전트 운영 비용). **machine-aware routing**이
AgentMesh는 verdict 게이트가 아니라 cost pricing(`units × unit_cost`) + rollup, 즉 Clearstra의 `price`
machine임을 실코드로 판정해 여기로 라우팅했다(원본과 parity 테스트 동봉).

각 팩은 `source_project`로 원본 저장소(github.com/sadpig70/*)를 추적한다.

## 결정론 경계

- **커널 + 마켓 함수 = 순수 결정론**: stdlib only, 시계·네트워크·AI 없음. 시간은 주입(`now`),
  hash 입력에서 `now`/`*_at` 제외 → 시간 무관 재현. 청산·정산·쇼크는 전부 결정론 알고리즘.
- **시장 예측·시세 피드 = 메타층** — Clearstra 경계 밖(주문을 *생산*).

## 라이선스

MIT License © 2026 sadpig70 (Jung Wook Yang)
