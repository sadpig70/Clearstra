# WORKPLAN-Clearstra — 실행 계획 (PGF plan)

> DESIGN-Clearstra.md + DESIGN-ClearstraMarkets.md → 실행 가능한 작업 계획.
> POLICY + 노드 위상정렬 + 검증 게이트. 이 저장소만으로 자립 구동(독립 repo). Attestra와 상보 조합.

## POLICY

```yaml
POLICY:
  max_verify_cycles: 2
  stdlib_only: true               # HELIX/Attestra CI 철학 계승 — 외부 의존 금지
  determinism: strict             # 커널·팩 시계/네트워크/AI 금지 (now 주입)
  federate_not_fuse: true         # 원본 시장 복사·포크 금지 — 공식 계약만 적재
  single_source_of_truth: true    # clear/settle/shock/ledger 커널에 1회만 정의
  reference_market_parity: true   # CryoFuturesMarket == CryoFutures.price_future/settle_contract
  clear_correct_by_construction: true  # clear() 불변식 = Attestra clearing 검증 술어
  attestra_composable: true       # clear 마켓은 to_attestra_packet → Attestra verdict=valid
  on_blocked: skip_and_continue
  completion: all_done_or_blocked
```

## 노드 순서 (의존 위상정렬)

```text
# ── Phase 1: 커널 (ClearstraCore) ──
1.  Order          — 주문/입찰 풀 모델 + 검증
2.  Pricing        — time_factor·scarcity_premium primitive (CryoFutures/MineralShock 계승)
3.  Clearing       @dep:1 — 충돌 없는 우선순위 배분 엔진 (★신규 커널)
4.  Settlement     @dep:3 — zero-sum 정산 (CryoFutures.settle 계승)
5.  Shock          @dep:1 — 쇼크 리허설 (MineralShock.simulate_shock 계승)
6.  Ledger         — hash-chain 청산 원장 (Attestra 원장 규율)
7.  Fingerprint    — 마켓 dedup primitive
8.  Determinism    @dep:3,4 — stdlib·주입 경계 검증기
9.  AttestraBridge @dep:3,4 — to_attestra_packet (상보 결합)

# ── Phase 2: 마켓 계약 (MarketContract) ──
10. MarketManifest @dep:1 — {name,version,stages,order_schema,source_project}
11. MarketAPI      @dep:3,4,5 — price/priority/payoff/shock_model 계약
12. MarketLoader   @dep:10,7 — 발견·로드·stages검증·dedup
13. MarketRegistry @dep:12 — 레지스트리 + lookup

# ── Phase 3: 마켓 (Markets) — 레퍼런스/앵커 우선 ──
14. CryoFuturesMarket   @dep:11 — 레퍼런스 (price/settle parity)
15. ReserveFlowMarket   @dep:11 — 앵커 (clear + Attestra 조합)
16. Markets[나머지 8종]  @dep:14,15 — ColdCapacity/FailureFutures/RefusalOption/
                                     ExclusiveGrant/QuadraticCarbon/BuyBloc/ShockRehearsal/RRE
                                     [parallel] — 계약 동일, 독립 포팅

# ── Phase 4: 합성 · 인터페이스 ──
17. ClearRun       @dep:3,4,6,9 — price→clear→settle→(rehearse)→ledger→bridge 파이프라인
18. Schemas        @dep:1,3,4,6,10 — JSON Schema (order/allocation/settlement/ledger/manifest/attestra-packet)
19. CLI            @dep:13,17 — sample/price/clear/settle/rehearse/verify/report/market/emit-packet
20. Docs           @dep:8 — README/ARCHITECTURE/MARKET-CONTRACT/DETERMINISM

# ── Phase 5: 검증 ──
21. Tests          @dep:14,15,17 — 커널 + 마켓 parity + 파이프라인 + Attestra 조합 unittest
22. VERIFY         @dep:21 — 3관점 (acceptance/quality/architecture)
```

## 검증 게이트

```text
- 커널·팩 전부 stdlib import만 (외부 패키지 0)
- 커널·팩 전부 now 주입식 (Date.now·random·socket 호출 0); hash에서 now/*_at 제외
- ★ reference_market_parity: CryoFuturesMarket price/settle == 원본 CryoFutures (샘플 다수)
- ★ clear_correct_by_construction: clear() 산출물이 conservation/no_conflict/priority 항상 만족
- ★ attestra_composable: to_attestra_packet 방출 packet을 Attestra reserve-flow 팩이 verdict=valid로 검증
    (Attestra 저장소를 읽기전용 참조하거나, packet-clearing.schema 형식 준수로 검증)
- ZeroSumSettlement: 모든 settle 결과 buyer_net+seller_net==0
- MarketLoader dedup: 동일 fingerprint 마켓 거부
- unittest green + Determinism 검증기 PASS
- 3관점: acceptance · quality(커널/팩 중복 0) · architecture(federate 유지)
```

## 페이즈 전이

```text
Phase1(커널) → Phase2(계약): 커널 9노드 done + Determinism PASS + clear 불변식 테스트 green
Phase2 → Phase3(마켓): MarketAPI 계약 확정 + MarketRegistry 동작
Phase3 → Phase4: CryoFuturesMarket parity + ReserveFlowMarket Attestra 조합 통과 (레퍼런스/앵커 선행)
Phase4 → Phase5(검증): 모든 노드 terminal
Phase5 → 완료: VERIFY passed (rework ≤ max_verify_cycles)
```
