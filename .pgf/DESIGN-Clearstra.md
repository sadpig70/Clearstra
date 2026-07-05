# Clearstra Design @v:0.1

> PGF design mode 산출. **Clearstra = 희소·취약·임계 자산의 권리/용량/선물을 결정론적으로 청산하는
> 거래소 플랫폼.** HELIX corpus의 clearing/market 군집(CryoFutures·ColdMkh·FailureFutures·
> ReserveFlow·RefusalOption·ShockRehearsal·ExclusiveGrantWarrant·QuadraticCarbonFund·BuyBloc·RRE)이
> 도메인만 다를 뿐 **동일한 청산 기계**(`price → clear → settle → rehearse` + 청산 원장)를 반복한다는
> 관찰에서 출발한다. Clearstra는 그 기계를 **커널(clearstra-core)** 로 한 번만 정의하고, 각 시장을
> **마켓 팩(market pack)** 으로 얹는다. 계보: HELIX → Clearstra (자식 저장소, 독립 구동).
>
> **★ Attestra 상보성:** Attestra는 청산을 *증언(attest)*하되 *계산(compute)*은 범위 밖으로 명시했다
> (Attestra ADR). Clearstra가 바로 그 계산 절반이다. Clearstra의 `clear()` 산출물은 **Attestra의 clearing
> 검증 packet 형식과 동일**하게 방출되어(`AttestraBridge`), 두 플랫폼이 **"계산 → 증명"으로 조합**된다.

---

## 0. 핵심 명제

> **하나의 결정론 청산 커널 + N개 마켓 팩.** corpus의 각 시장(cryo-futures·reserve-flow·refusal-option…)은
> "희소 자산을 가격화 → 제한 공급에 우선순위로 배분 → 실현결과로 정산 → 쇼크 시나리오로 리허설"이라는
> **같은 substrate**를 도메인 공식만 바꿔 재구현한 것이다. Clearstra는 그 substrate를 단일 출처로 승격하고,
> 마켓 팩은 도메인 공식(가격·우선순위·정산·쇼크)만 기여한다.

설계 원칙 (Attestra/HELIX 계승):
1. **커널 단일 출처** — 청산 엔진·정산·원장·쇼크는 `clearstra-core`에 한 번만 정의. 팩은 도메인 함수만.
2. **팩은 연합(federate)** — 각 시장은 원본 저장소(github.com/sadpig70/*)에 그대로 있고, Clearstra는 그
   가격/배분/정산 공식 계약만 `MarketContract`로 투영. 복사·포크 아님.
3. **결정론 경계** — 커널·팩 함수는 순수 stdlib(시계·네트워크·AI 없음). 시간은 주입(`now`). 청산·정산·쇼크는
   전부 결정론 알고리즘이라 경계와 자연 정합.
4. **정확성-by-construction** — `clear()`는 보존(conservation)·무충돌(no-conflict)·우선순위(priority)를
   불변식으로 보장 → 이는 Attestra clearing 팩의 검증 술어와 정확히 일치 → 두 플랫폼 조합이 증명가능.

---

## 1. HELIX 청산 기계 → Clearstra 매핑 (실코드 근거)

| corpus 반복 요소 (실코드) | Clearstra 커널 요소 | 결정론 클래스 |
|---|---|---|
| `CryoFutures.price_future` (premium = payout·failure_prob·√(days/365)) | **Pricing** — 가격 primitive | 순수 결정론 |
| `MineralShock.price_reserve_right` (scarcity_premium=criticality/coverage) | **Pricing** (팩 공식) | 순수 결정론 |
| ReserveFlow 우선순위 배분 (shock-weighted) | **Clearing** — 충돌 없는 우선순위 배분 엔진 | 순수 결정론 |
| `CryoFutures.settle_contract` (buyer_net/seller_net, zero-sum) | **Settlement** | 순수 결정론 |
| `MineralShock.simulate_shock` (shortfall·survival·affected) | **Shock** — 쇼크 리허설 | 순수 결정론 |
| 각 시장의 청산 원장 | **Ledger** — hash-chain 청산 원장 | 순수 결정론 (now 주입) |
| (신규) 청산 결과 → 검증 | **AttestraBridge** — Attestra clearing packet 방출 | 순수 결정론(transform) |

> 핵심 차이: Attestra는 산출물을 *운영/증언*한다. Clearstra는 시장을 *계산/청산*한다. 두 커널은 대칭이며
> (packet→verdict vs order→allocation), AttestraBridge로 한 파이프라인이 된다.

---

## 2. Gantree — Clearstra 구조

```
Clearstra // 결정론 청산 거래소 플랫폼 (designing) @v:0.1
    ClearstraCore // 커널 — 단일 출처 결정론 청산 substrate (designing) #core
        Order // 주문/입찰 풀 모델 + 검증 (designing) #core
        Pricing // 결정론 가격/프리미엄 primitive (time_factor·scarcity·option) (designing) #core
        Clearing // 충돌 없는 우선순위 배분 엔진 (conservation·no-conflict·priority) (designing) @dep:Order #core
        Settlement // 실현결과 대비 정산 → payoff (zero-sum) (designing) @dep:Clearing #core
        Shock // 쇼크 시나리오 리허설 (shortfall·survival·affected) (designing) @dep:Order #core
        Ledger // hash-chain 청산 원장 (designing) #core
        Fingerprint // 마켓 팩 dedup primitive (designing) #core
        Determinism // stdlib·now/sim 주입 경계 검증기 (designing) #core
        AttestraBridge // 청산 결과 → Attestra clearing packet 방출 (상보) (designing) @dep:Clearing,Settlement #core
    MarketContract // 마켓 팩 확장 규격 (designing) @dep:ClearstraCore #contract
        MarketManifest // {name,version,stages,schema,source_project} (designing) #contract
        MarketAPI // price/priority/settle/rehearse 시그니처 (designing) @dep:ClearstraCore #contract
        MarketLoader // 발견·로드·dedup(fingerprint) (designing) @dep:MarketManifest #contract
        MarketRegistry // 등록된 마켓 레지스트리 + lookup (designing) @dep:MarketLoader #contract
    Markets // 1차 마켓 팩 — see DESIGN-ClearstraMarkets.md (decomposed) @dep:MarketContract #markets
    ClearRun // 파이프라인 price→clear→settle→(rehearse)→ledger→bridge (designing) @dep:Clearing,Settlement,Ledger,AttestraBridge #pipeline
    CLI // sample/price/clear/settle/rehearse/verify/report/market/emit-packet (designing) @dep:ClearstraCore,MarketRegistry #cli
    Schemas // JSON Schema (order/allocation/settlement/ledger/manifest/attestra-packet) (designing) #schema
    Docs // README/ARCHITECTURE/MARKET-CONTRACT/DETERMINISM (designing) #docs
    Tests // 결정론 unittest (커널 + 마켓 + 파이프라인 + Attestra 조합) (designing) @dep:ClearstraCore,Markets #test
```

> `Markets`는 6레벨 진입 회피 + 마켓별 공식 상세를 담기 위해 `DESIGN-ClearstraMarkets.md`로 분리(`(decomposed)`).
> pgxf 인덱스가 파일 경계를 넘어 트리를 재구성한다(>30 노드).

---

## 3. PPR — 커널 핵심 함수 (계약)

### 3.1 Pricing — 결정론 가격 primitive (CryoFutures·MineralShock 일반화)

```python
import math

def time_factor(days_to_expiry: float) -> float:
    """√(days/365) — CryoFutures 계승. 만기까지 시간 위험 계수."""
    require_non_negative("days_to_expiry", days_to_expiry)
    return math.sqrt(days_to_expiry / 365.0)

def scarcity_premium(criticality: float, coverage_days: float) -> float:
    """criticality / max(coverage_days, 1) — MineralShock 계승."""
    require_unit_interval("criticality", criticality)
    return criticality / max(coverage_days, 1.0)

# 팩은 이 primitive들을 조합해 자기 시장의 price(order, P) 공식을 구성한다.
# 예: CryoFutures premium = payout * failure_prob * time_factor(days)
# acceptance_criteria: 순수 결정론(시계 없음), 입력 검증(음수/[0,1] 가드), 동일 입력→동일 출력
```

### 3.2 Clearing — 충돌 없는 우선순위 배분 엔진 (★신규 커널, ReserveFlow 일반화)

```python
def clear(pool: list, supply: float, priority_key, now: str) -> dict:
    """제한 공급을 우선순위대로 충돌 없이 배분. 정확성-by-construction.

    pool: [{party_id, quantity, ...priority-inputs}]  (요청)
    priority_key(bid) -> comparable  (팩 제공 — shock-weighted/criticality/quadratic 등)
    """
    # 결정론 정렬: priority 내림차순, 동순위는 party_id 오름차순(tie-break)
    ranked = sorted(pool, key=lambda b: (-priority_key(b), str(b["party_id"])))
    remaining, allocations = supply, []
    for bid in ranked:
        take = min(bid["quantity"], remaining)          # 그리디 우선순위 충족
        if take > 0:
            allocations.append({"party_id": bid["party_id"], "amount": take,
                                 "priority": priority_key(bid)})
            remaining -= take
    return {
        "supply": supply, "allocated": supply - remaining, "remaining": remaining,
        "allocations": allocations,
        "requests": [{"party_id": b["party_id"], "amount": b["quantity"],
                      "priority": priority_key(b)} for b in pool],
        "cleared_at": now,
    }
    # acceptance_criteria (= Attestra clearing 팩 검증 술어와 일치):
    #   - conservation: Σ amount ≤ supply (그리디상 항상 성립)
    #   - no_conflict: 각 party 1회, amount ≥ 0
    #   - priority: 높은 우선순위가 먼저 충족 (낮은 우선순위가 높은 미충족보다 앞서지 않음)
    #   - 결정론: 정렬 tie-break 고정 → 동일 pool·supply → 동일 allocation
```

### 3.3 Settlement — 실현결과 정산 (CryoFutures.settle_contract 일반화)

```python
def settle(contract: dict, outcome: dict, payoff, now: str) -> dict:
    """가격화된 계약을 실현결과에 대해 정산. zero-sum 불변식."""
    result = payoff(contract, outcome)                  # 팩 제공 payoff 공식
    buyer_net, seller_net = result["buyer_net"], result["seller_net"]
    assert abs(buyer_net + seller_net) < 1e-9, "settlement must be zero-sum"
    return {**result, "settled_at": now}
    # acceptance_criteria:
    #   - buyer_net + seller_net == 0 (zero-sum 청산)
    #   - actual_failure/outcome 대비 결정론 payoff (CryoFutures 규율 계승)
```

### 3.4 Shock — 쇼크 시나리오 리허설 (MineralShock.simulate_shock 일반화)

```python
def rehearse(scenario: dict, pool: list, model, now: str) -> dict:
    """수요 급등·공급 교란 시나리오를 풀에 적용해 shortfall·survival 산정."""
    per_item, total_shortfall, affected, coverages = [], 0.0, [], []
    for item in pool:
        impact = model(scenario, item)                  # 팩 제공 쇼크 모델
        per_item.append(impact); coverages.append(impact["coverage_days"])
        if impact["shortfall"] > 0:
            total_shortfall += impact["shortfall"]; affected.append(item["id"])
    return {"scenario": scenario.get("name",""), "survival_days": min(coverages, default=float("inf")),
            "total_shortfall": total_shortfall, "affected": affected,
            "per_item": per_item, "rehearsed_at": now}
    # acceptance_criteria:
    #   - survival_days = min coverage across pool (MineralShock 계승)
    #   - 결정론: 동일 scenario·pool → 동일 shortfall/survival
```

### 3.5 Ledger — hash-chain 청산 원장 (Attestra 원장 규율 계승)

```python
def append_clearing(ledger_path: str, result: dict, market: str, now: str) -> dict:
    """청산/정산 결과를 결정론 hash-chain 레코드로 append.
       record_hash = sha256(canonical(record − {record_hash, recorded_at})) → 시간독립."""
    # acceptance_criteria: 체인 무결성 verify + 변조 탐지 + now 메타 제외 (Attestra와 동형)
```

### 3.6 AttestraBridge — 상보 결합 (청산 → 검증 packet)

```python
def to_attestra_packet(clear_result: dict, packet_id: str) -> dict:
    """clear() 산출물을 Attestra clearing 검증 packet 형식으로 방출.
       Attestra의 reserve-flow 팩이 conservation/no_conflict/priority를 그대로 검증한다."""
    return {
        "packet_id": packet_id, "subject": packet_id,
        "clearing": {
            "supply": clear_result["supply"],
            "allocations": clear_result["allocations"],
            "requests": clear_result["requests"],
        },
    }
    # acceptance_criteria:
    #   - 방출 packet이 Attestra schemas/packet-clearing.schema.json에 적합
    #   - clear()의 불변식 보장 → Attestra verdict = valid (계산↔증명 조합 증명)
```

### 3.7 MarketContract — 마켓 팩 확장 규격

```python
MarketManifest = dict = {
    "name": str,                 # "cryo-futures"
    "version": str,
    "stages": list[str],         # 구현 단계 subset: ["price","clear","settle","rehearse"]
    "order_schema": str,         # 이 시장의 주문/풀 스키마 (schemas/ 참조)
    "source_project": str,       # github.com/sadpig70/*
    "fingerprint": str,          # 팩 dedup 키
}

# 마켓 팩이 stages에 따라 제공하는 순수 함수 (있는 것만):
def price(order: dict, P: dict) -> dict            # 가격/프리미엄
def priority(bid: dict) -> float                   # clear()용 우선순위 키 (shock-weighted 등)
def payoff(contract: dict, outcome: dict) -> dict  # settle()용 (buyer_net/seller_net)
def shock_model(scenario: dict, item: dict) -> dict# rehearse()용 (coverage_days/shortfall)

def load_markets(pack_dir, seen_fp) -> dict:
    """마켓 팩 발견·검증·dedup(fingerprint). 중복 재조합 마켓 거부."""
    # acceptance_criteria: stages별 필요한 함수 존재 검증, fingerprint 충돌 거부, 결정론
```

---

## 4. 결정론 경계 (지배 제약)

```text
ClearstraCore + MarketContract → 순수 결정론 (stdlib only, 시계/네트워크/AI 없음)
  - 시간은 주입(now), hash 입력에서 now/*_at 제외 → 시간 무관 재현
마켓 팩 함수(price/priority/payoff/shock_model) → 순수 결정론 (부작용 금지)
마켓 내부 예측·시세 피드 등 → 메타층 (Clearstra 경계 밖, 원본 프로젝트 소관 — 주문을 *생산*)
```

---

## 5. 완료 기준 (acceptance)

```text
ClearstraAcceptance
    SingleSourceKernel // clear/settle/shock/ledger를 커널에 1회만 정의 (마켓 중복 0)
    MarketContractStable // price/priority/payoff/shock_model 계약으로 마켓 무한 확장
    ClearCorrectByConstruction // clear() 불변식 = Attestra clearing 검증 술어와 일치
    AttestraComposable // to_attestra_packet 방출 → Attestra verdict=valid (계산↔증명 조합)
    ZeroSumSettlement // 모든 정산 buyer_net+seller_net==0
    DeterministicCore // 커널·팩 전부 stdlib·주입식·시계 없음
    Federated // 마켓은 도메인 공식 계약만 적재 (복사 아님, source_project 태그)
    Tested // 커널 unittest green + 마켓 청산/정산/쇼크 검증 + Attestra 조합 테스트
```
