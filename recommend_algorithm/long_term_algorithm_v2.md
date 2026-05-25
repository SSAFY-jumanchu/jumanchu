# 💘 주만추 — 장기투자 중심 추천 알고리즘 v2
## 📌 Long-Term First 설계 원칙

> **"장기투자가 기본값, 단기투자는 선택지"**
> 사용자의 기본 추천 경험은 장기투자 최적화로 동작하며, 단기는 명시적 설정 시에만 활성화된다.

---

## 🔄 v1 → v2 핵심 변경 요약

| 항목 | v1 (before0525) | v2 (장기 중심) |
|------|-----------------|----------------|
| 기본 모드 | 기간 구분 없음 | 장기투자 Default |
| 단기 처리 | term < 4 분기 처리 | 별도 short_term 모드 (옵션) |
| Stock DNA | 4개 지표 | 7개 지표 (장기 지표 3개 추가) |
| 가중치 구조 | 리스크 35% 중심 | 재무건전성 30% + 성장성 25% 중심 |
| 성장성 지표 | EPS 절대값 | EPS/매출 3년 CAGR |
| 안정성 지표 | Beta 역수 | ROE + 부채비율 + 실적 일관성 |
| 배당 | 미반영 | 배당 궁합 별도 요소 신설 |

---

## 🗺️ 1. 전체 시스템 구조 (v2)

```
[온보딩 설문 (9문항)]
        ↓
[투자 모드 결정: LONG-TERM (기본) / SHORT-TERM (옵션)]
        ↓
        ├─── [장기 모드] → [장기형 유저 프로필 벡터 (6차원)]
        │                          ↓
        │              [Stock DNA v2 (7지표) 정규화]
        │                          ↓
        │              [장기 궁합 점수 (5개 요소)]
        │                          ↓
        │              [최종 장기 궁합 지수 (0~100)]
        │
        └─── [단기 모드] → [단기형 스코어링 (별도 로직)]
                                   ↓
                          [모멘텀/변동성 중심 점수]
                                   ↓
                          [단기 궁합 지수 (0~100)]
        ↓
[추천 (스와이프 UI) — 모드 표시 포함]
```

---

## 👤 2. 온보딩 설문 → 투자 모드 결정

### 🚦 모드 결정 로직

온보딩 9문항 중 **투자 기간 관련 3문항**의 합산으로 모드를 결정한다.

```python
def decide_mode(user_profile):
    """
    investment_term: 1~5 (설문 합산)
    - 4~5점: 장기 모드 (LONG_TERM) — 기본값
    - 1~3점: 단기 모드 (SHORT_TERM) — 옵션
    """
    if user_profile["investment_term"] >= 4:
        return "LONG_TERM"   # Default 경로
    else:
        return "SHORT_TERM"  # 명시적 선택 시 활성화
```

### 📝 추가 온보딩 문항 (v2 신설, 9번)

> **Q9. 배당에 대한 생각은?**
> 1) 배당은 전혀 관심 없다 (성장주 선호)
> 2) 배당이 있으면 좋지만 필수는 아니다
> 3) 배당은 중요한 투자 기준이다 (인컴형)

→ `dividend_preference`: 0 / 0.5 / 1.0 으로 벡터화

---

## 👤 3. 유저 프로필 벡터 (v2, 장기 모드)

```python
user_profile = {
    # --- 기존 유지 ---
    "risk_tolerance":      1~5,   # 리스크 감수 성향
    "investment_term":     1~5,   # 투자 기간 (4~5 = 장기)
    "experience":          1~5,   # 투자 경험
    "loss_aversion":       1~5,   # 손실 회피 성향
    "preferred_sectors":   [],    # 관심 산업

    # --- v2 신설 ---
    "dividend_preference": 0~1,   # 배당 선호도 (Q9)
    "quality_preference":  0~1,   # 재무 건전성 중시 여부 (Q7 파생)
}
```

---

## 📈 4. Stock DNA v2 (7개 지표)

주식 데이터를 0~1 범위로 정규화. **장기투자 핵심 지표 3개 신설.**

```python
stock_profile = {
    # --- 기존 유지 ---
    "volatility":     0~1,   # 변동성 (Beta 정규화)
    "value_score":    0~1,   # 저평가 지표 (1/PBR 정규화)
    "growth_score":   0~1,   # 단기 성장성 (EPS 절대값)

    # --- v2 신설 (장기 지표) ---
    "long_growth":    0~1,   # 장기 성장성: EPS/매출 3년 CAGR
    "quality_score":  0~1,   # 재무 건전성: ROE + 부채비율 + 실적 일관성
    "dividend_score": 0~1,   # 배당 매력도: 배당수익률 + 배당 성장률
    "stability":      0~1,   # 안정성 (Beta 역수 → v2에서 quality_score로 보완)
}
```

### ⚙️ v2 신규 지표 정규화 로직

#### ① long_growth (장기 성장성)
```python
# EPS 3년 CAGR + 매출 3년 CAGR 평균
eps_cagr   = (eps_now / eps_3y_ago) ** (1/3) - 1   # 연복리 성장률
rev_cagr   = (rev_now / rev_3y_ago) ** (1/3) - 1
raw_score  = (eps_cagr + rev_cagr) / 2

# -20% ~ +30% 범위를 0~1로 정규화
long_growth = min(max((raw_score + 0.2) / 0.5, 0), 1)
```

#### ② quality_score (재무 건전성)
```python
# 3개 지표 가중 평균
roe_score        = min(roe / 0.20, 1.0)          # ROE 20% 기준 정규화
debt_score       = 1 - min(debt_ratio / 2.0, 1)  # 부채비율 200% 기준 역수
earnings_consist = std(eps_5y) 기반 역수 정규화   # 실적 일관성 (변동 적을수록 高)

quality_score = (roe_score * 0.4) + (debt_score * 0.35) + (earnings_consist * 0.25)
```

#### ③ dividend_score (배당 매력도)
```python
yield_score   = min(div_yield / 0.05, 1.0)       # 배당수익률 5% 기준
growth_score  = min(div_cagr_3y / 0.10, 1.0)     # 배당 3년 성장률 10% 기준
payout_penalty = 1.0 if payout_ratio < 0.7 else 0.7  # 지급률 70% 초과 시 패널티

dividend_score = (yield_score * 0.5 + growth_score * 0.5) * payout_penalty
```

---

## 💘 5. 장기 궁합 점수 알고리즘 (v2 핵심)

### 📌 장기 모드 최종 공식

```
Long-Term Total Score (0~100) =
    (quality_match   × 0.30)   ← v2 신설, 가장 높은 가중치
  + (growth_match    × 0.25)   ← v2 강화 (장기 성장성)
  + (risk_match      × 0.20)   ← v1 35% → v2 20% 하향
  + (sector_match    × 0.15)   ← v1 20% → v2 15% 소폭 하향
  + (dividend_match  × 0.10)   ← v2 신설
  × 100
```

> **v1 대비 변화**: 리스크 단독 35% → 재무건전성(30%) + 성장성(25%) 주도로 전환

---

## 🔍 6. 장기 궁합 세부 요소

### ① 재무건전성 궁합 (30%) — v2 신설 핵심

```python
def quality_match(user, stock):
    """
    quality_preference 높은 유저 → 높은 quality_score 주식 선호
    quality_preference 낮은 유저 → quality_score에 덜 민감 (중립 0.5 반환)
    """
    if user["quality_preference"] >= 0.7:
        # 재무 중시형: stock quality와 직접 매칭
        return stock["quality_score"]
    elif user["quality_preference"] >= 0.4:
        # 중립형: quality + value 균형
        return (stock["quality_score"] + stock["value_score"]) / 2
    else:
        # 성장 추구형: quality 최소 기준만 체크 (하한선 0.3 보장)
        return max(stock["quality_score"], 0.3)
```

### ② 장기 성장성 궁합 (25%) — v2 강화

```python
def growth_match(user, stock):
    """
    경험 + 리스크 성향 조합으로 성장성 매칭 가중치 결정
    """
    exp   = user["experience"]
    risk  = user["risk_tolerance"]

    if exp >= 4 and risk >= 4:
        # 공격형 고수: 단기 성장 + 장기 성장 균형
        return (stock["growth_score"] * 0.4) + (stock["long_growth"] * 0.6)
    elif exp >= 3:
        # 중급자: 장기 성장 중심
        return (stock["growth_score"] * 0.25) + (stock["long_growth"] * 0.75)
    else:
        # 초보/보수형: 장기 성장성 + 안정성 균형
        return (stock["long_growth"] * 0.5) + (stock["stability"] * 0.5)
```

### ③ 리스크 궁합 (20%) — v1 대비 하향, 로직 개선

```python
def risk_match(user, stock):
    """
    v1: 단순 Beta 차이
    v2: Beta 차이 + 손실회피 성향 반영
    """
    ideal_beta   = user["risk_tolerance"] / 2.5
    beta_diff    = abs(ideal_beta - stock["volatility"])
    beta_score   = 1 - beta_diff

    # 손실 회피 성향이 강할수록 quality_score 보정 추가
    loss_aversion = user["loss_aversion"]
    if loss_aversion >= 4:
        # 손실 회피형: 재무 건전성이 리스크 완충
        quality_buffer = stock["quality_score"] * 0.3
        return min(beta_score * 0.7 + quality_buffer, 1.0)
    else:
        return max(beta_score, 0)
```

### ④ 테마 궁합 (15%) — v1 로직 유지, 가중치 조정

```python
def sector_match(user, stock):
    if stock["sector"] in user["preferred_sectors"]:
        return 1.0
    elif not user["preferred_sectors"]:
        return 0.5   # 무관심 = 중립
    else:
        return 0.0
```

> 📌 향후 개선: 섹터 간 유사도 행렬 도입 (e.g., IT ↔ 반도체 = 0.7)

### ⑤ 배당 궁합 (10%) — v2 신설

```python
def dividend_match(user, stock):
    """
    배당 선호도와 주식의 배당 매력도 매칭
    배당 무관심 유저에게는 패널티 없음 (중립 처리)
    """
    pref = user["dividend_preference"]

    if pref >= 0.7:
        # 인컴형: 배당 점수 직접 반영
        return stock["dividend_score"]
    elif pref >= 0.3:
        # 중립형: 배당 있으면 소폭 보너스
        return 0.5 + (stock["dividend_score"] * 0.3)
    else:
        # 성장주 선호형: 배당 여부 무관, 고정 중립값
        return 0.5
```

---

## ⚡ 7. 단기 모드 (SHORT_TERM) — 옵션

단기 모드는 **별도 스코어링 함수로 분리** 관리한다.

```python
def short_term_score(user, stock):
    """
    단기 모드: 모멘텀 + 변동성 중심
    장기 지표(quality, long_growth, dividend)는 가중치 최소화
    """
    momentum_score = calculate_momentum(stock)  # 52주 모멘텀, RSI 등

    return (
        stock["volatility"]  * 0.40 +   # 변동성 (단기 기회)
        momentum_score       * 0.35 +   # 모멘텀
        sector_match(user, stock) * 0.15 +
        stock["value_score"] * 0.10
    ) * 100
```

> ⚠️ **UI 처리**: 단기 모드 진입 시 "단기투자는 높은 위험을 수반합니다" 경고 표시

---

## 🧮 8. 최종 계산 예시 (v2, 장기 모드)

### 재무중시형 장기투자자 × 삼성전자

| 요소 | 점수 | 가중치 | 기여 |
|------|------|--------|------|
| 재무건전성 | 82.0 | 30% | 24.60 |
| 장기 성장성 | 71.5 | 25% | 17.88 |
| 리스크 | 68.0 | 20% | 13.60 |
| 테마 | 100.0 | 15% | 15.00 |
| 배당 | 55.0 | 10% | 5.50 |

**👉 최종 장기 궁합 점수: 💘 76.6점**

---

## 🏷️ 9. 궁합 등급 라벨 (UI 표시용)

| 점수 | 등급 | 라벨 | 설명 |
|------|------|------|------|
| 90~100 | S | 💘 운명의 주식 | 거의 완벽한 궁합 |
| 75~89  | A | 💖 찰떡 궁합 | 장기 보유 강력 추천 |
| 60~74  | B | 💛 괜찮은 인연 | 고려해볼 만한 종목 |
| 45~59  | C | 💙 어색한 만남 | 조건부 매칭 |
| 0~44   | D | 💔 궁합 불일치 | 추천하지 않음 |

---

## 🚀 10. 단계별 구현 로드맵

### Phase 1 — 핵심 데이터 확보 (즉시)
- [ ] DB에 `roe`, `debt_ratio`, `eps_history(5y)`, `div_yield`, `div_history(3y)` 컬럼 추가
- [ ] 기존 `beta`, `pbr`, `eps` 데이터 정합성 검증

### Phase 2 — Stock DNA v2 계산 (1주차)
- [ ] `long_growth` 계산 함수 구현 (3년 CAGR)
- [ ] `quality_score` 계산 함수 구현 (ROE + 부채비율 + 실적 일관성)
- [ ] `dividend_score` 계산 함수 구현

### Phase 3 — 궁합 엔진 v2 (2주차)
- [ ] `LONG_TERM` / `SHORT_TERM` 모드 분기 구현
- [ ] 장기 궁합 5개 요소 함수 구현
- [ ] v1 스코어와 A/B 비교 테스트

### Phase 4 — 온보딩 업데이트 (3주차)
- [ ] Q9 (배당 선호도) 추가
- [ ] `quality_preference` 파생 로직 구현
- [ ] 모드 선택 UI (기본: 장기 / 선택: 단기)

### Phase 5 — 검증 및 튜닝 (4주차)
- [ ] 실제 주식 데이터로 점수 분포 확인
- [ ] 이상치 종목 수동 검토
- [ ] 가중치 미세 조정

---

## ⚖️ 11. 가중치 결정 근거

| 요소 | 가중치 | 근거 |
|------|--------|------|
| 재무건전성 (30%) | **최고** | 장기 보유 시 재무 위험이 가장 치명적. ROE 일관성이 장기 수익률의 핵심 예측 변수 |
| 장기 성장성 (25%) | 높음 | 장기 복리 효과의 원천. EPS CAGR이 주가 상승과 직접 연결 |
| 리스크 궁합 (20%) | 중간 | v1보다 하향: 장기에서는 단기 변동성보다 펀더멘털이 더 중요 |
| 테마 궁합 (15%) | 중간 | 관심 산업 선호는 유지. 장기엔 섹터 트렌드도 중요 |
| 배당 궁합 (10%) | 보조 | 인컴 선호자 배려. 성장주 선호자에게 패널티 없음 |

---

## 🎯 12. 최종 한줄 정의 (v2)

> **"주만추는 재무건전성과 장기 성장성을 중심으로, 사용자의 투자 성향과 가장 오래 함께할 주식을 연결하는 장기투자 궁합 서비스이다."**
