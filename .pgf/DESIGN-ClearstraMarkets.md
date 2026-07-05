# ClearstraMarkets Design @v:0.1

> `DESIGN-Clearstra.md`의 `Markets` 노드 `(decomposed)` 분리 트리. 1차 마켓 팩 = HELIX corpus의
> **clearing/market 군집**을 `MarketContract`로 투영한 것. 각 팩은 `stages`(price/clear/settle/rehearse
> 중 구현분)와 도메인 공식만 기여하며 커널 로직을 재정의하지 않는다.
> **레퍼런스 마켓**: `cryo-futures`(price+settle 정합성, CryoFutures 실코드 parity),
> `reserve-flow`(clear 정합성 + Attestra 조합 앵커).

---

## 1. Gantree — 1차 마켓 (10종)

```
ClearstraMarkets // 1차 마켓 팩 (clearing/market cluster) (done) @v:0.1
    CryoFuturesMarket // 냉각용량 실패보호 선물 (price+settle) — 레퍼런스 (done) #reference
    ColdCapacityMarket // 밀리켈빈 냉각용량 양면 청산 (price+clear) (done)
    FailureFuturesMarket // 취약도→선물 발행 (price+settle) (done)
    ReserveFlowMarket // 전략비축 flow-rights 청산 (price+clear+rehearse) — Attestra 앵커 (done) #anchor
    RefusalOptionMarket // 거부용량 옵션 프리미엄 (price) (done)
    ExclusiveGrantMarket // 상호배타 권리풀 충돌없는 청산 (clear) (done)
    QuadraticCarbonMarket // 이차 매칭풀 탄소자금 배분 (clear) (done)
    BuyBlocMarket // 수요측 연합 집계 청산 (price+clear) (done)
    ShockRehearsalMarket // 배분권 쇼크 시나리오 리허설 (rehearse) (done)
    RetrofitReceivableMarket // 브라운필드 개보수 채권화 정산 (price+settle) (done)
```

> depth ≤ 2 유지 — 각 마켓의 stages + 공식은 노드 아래 간략 PPR(`#`)로. 커널 계약이
> `price/priority/payoff/shock_model`을 고정하므로 팩은 stages와 공식만 명세하면 된다.

---

## 2. 마켓별 명세 (간략 PPR — 실코드 근거는 [실코드] 표시)

### CryoFuturesMarket — 레퍼런스 (source: CryoFutures = ColdMkh + FailureFutures) [실코드]

```
CryoFuturesMarket // 냉각용량 실패보호 선물 (done) #reference
    # source_project: github.com/sadpig70/CryoFutures
    # stages: price, settle
    # price:  premium = payout_amount * failure_prob * time_factor(days_to_expiry)   [실코드 검증]
    #         (payout_amount = asset_value when omitted; time_factor = √(days/365))
    # payoff: actual_failure → seller pays payout; buyer_net = payout - premium, seller_net = premium - payout
    #         no failure → settlement 0; buyer_net = -premium, seller_net = premium   (zero-sum)
    # criteria: price/settle 결과가 원본 CryoFutures.price_future / settle_contract와 동일 (parity)
```

### ColdCapacityMarket (source: ColdMkh)

```
ColdCapacityMarket // 밀리켈빈 냉각용량 양면 청산 (done)
    # source_project: github.com/sadpig70/ColdMkh
    # stages: price, clear
    # price:    capacity_price = mk_capacity * demand_ratio (양면 수급 균형가)
    # priority: bid valuation 내림차순 (지불의사 높은 수요자 우선)
    # clear:    유휴 냉각용량 pool → 수요 bid에 가치순 배분 (커널 clear)
```

### FailureFuturesMarket (source: FailureFutures)

```
FailureFuturesMarket // 취약도→선물 발행 (done)
    # source_project: github.com/sadpig70/FailureFutures
    # stages: price, settle
    # price:  가장 취약한(실패확률 높은) 자산이 가장 많은 선물 발행 → premium ∝ fragility * time_factor
    # payoff: 실패 실현 시 청산소가 buyer에 payout (CryoFutures와 동형 zero-sum)
```

### ReserveFlowMarket — Attestra 앵커 (source: ReserveFlow / MineralShock reserve) [실코드]

```
ReserveFlowMarket // 전략비축 flow-rights 청산 (done) #anchor
    # source_project: github.com/sadpig70/ReserveFlow
    # stages: price, clear, rehearse
    # price:    scarcity_premium = criticality / max(coverage_days,1)                 [실코드]
    #           right_price = stockpile * criticality * (1 + scarcity_premium)         [실코드]
    # priority: shock-weighted = criticality * (1 / coverage_days)  (희소·임계 우선)
    # clear:    제한 flow 공급 → 요청에 shock-weighted 우선순위 배분 (커널 clear)
    # rehearse: MineralShock.simulate_shock 모델 (effective_stockpile, shortfall, survival)  [실코드]
    # ★ clear() 산출물 → AttestraBridge → Attestra reserve-flow 팩 verdict=valid (조합 앵커)
```

### RefusalOptionMarket (source: RefusalOption / MineralShock refusal) [실코드]

```
RefusalOptionMarket // 거부용량 옵션 프리미엄 (done)
    # source_project: github.com/sadpig70/RefusalOption
    # stages: price
    # price: option_premium = refusal_capacity_tonnes * mineral_value * threat_level * 0.1   [실코드]
```

### ExclusiveGrantMarket (source: ExclusiveGrantWarrant)

```
ExclusiveGrantMarket // 상호배타 권리풀 충돌없는 청산 (done)
    # source_project: github.com/sadpig70/ExclusiveGrantWarrant
    # stages: clear
    # priority: bid valuation; clear는 상호배타 풀 제약(같은 권리 중복 배분 금지)
    # clear:    mutually-exclusive rights pool → 충돌 없이 승자 배정 (커널 clear + exclusivity 제약)
```

### QuadraticCarbonMarket (source: QuadraticCarbonFund)

```
QuadraticCarbonMarket // 이차 매칭풀 탄소자금 배분 (done)
    # source_project: github.com/sadpig70/QuadraticCarbonFund
    # stages: clear
    # priority: quadratic funding weight = (Σ√contribution)^2  (다수 소액 기여 우대)
    # clear:    검증된 감축량에 매칭풀을 이차가중으로 배분 (커널 clear + quadratic priority)
```

### BuyBlocMarket (source: BuyBloc)

```
BuyBlocMarket // 수요측 연합 집계 청산 (done)
    # source_project: github.com/sadpig70/BuyBloc
    # stages: price, clear
    # price:    bloc_price = Σ member_volume 로 협상력 반영 할인가
    # priority: member commitment 크기; clear는 집계 volume을 공급자에 배정
```

### ShockRehearsalMarket (source: ShockRehearsal / MineralShock shock) [실코드]

```
ShockRehearsalMarket // 배분권 쇼크 시나리오 리허설 (done)
    # source_project: github.com/sadpig70/ShockRehearsal
    # stages: rehearse
    # shock_model: demand_spike/supply_disruption 적용 → effective_stockpile, coverage_days, shortfall  [실코드]
    # rehearse: survival_days = min coverage; total_shortfall; affected set (커널 rehearse)
```

### RetrofitReceivableMarket (source: RRE)

```
RetrofitReceivableMarket // 브라운필드 개보수 채권화 정산 (done)
    # source_project: github.com/sadpig70/RRE (Retrofit Receivable Exchange)
    # stages: price, settle
    # price:  receivable_value = upgrade_savings * discount_factor(term)
    # payoff: 실현 절감 대비 정산 (buyer=financier, seller=building owner; zero-sum)
```

---

## 3. 마켓 확장 규칙 & 2차 파도

```text
MarketExpansionRule
    SameContract // price/priority/payoff/shock_model 준수하면 마켓 추가 = 매니페스트 + 공식 파일만
    NoKernelChange // 커널 수정 없이 마켓 등록 (플랫폼성의 증거)
    StagesDeclared // stages로 구현 단계 명시 → 커널이 해당 단계만 실행
    DedupByFingerprint // 중복 재조합 마켓은 MarketLoader가 거부
    AttestraComposable // clear stage 마켓은 to_attestra_packet로 검증 가능 (계산↔증명)
```

2차 파도 후보(동일 계약 적재 가능): `EndowFront`(pay-once 선불), `SettleMesh`(정산 규칙), `WasteStack`(이중 현금흐름),
`SeasonBat`(에너지 저장 차익). clearing 외 자원-라우팅 군집은 별도 platform(C) 소관.
