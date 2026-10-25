# Stock DNA 산정 로직

> 종목별 4축 "성격 점수"(DNA). 궁합 추천(온보딩/장투)의 입력값.
> 일 1회 배치로 `stock_dna` 캐시 테이블에 적재 — 궁합 계산은 이 테이블만 읽는다.
> 결정일: 2026-06-17 · 구현: `backend/recommend/management/commands/calc_stock_dna.py`

---

## 1. 대상 종목

**활성(`is_active=True`) + `FinancialSummary` 행이 있는 종목만.**

- FS 행이 없는 **ETF·ETN·우선주·리츠는 자동 제외** (재무제표가 없으므로). → 종목유형 판별 불필요, "FS 보유 = 사업회사" 게이트.
- 추가 엣지 제외(continue, DNA 미생성):
  - `beta <= 0` (인버스 등)
  - `pbr <= 0` (자본잠식)
  - beta 또는 pbr 값 자체가 없음

> 산출 현황(2026-06-17): 대상 2,956 → 적재 **2,649** (엣지제외 307).

---

## 2. 정규화 방식

- **시장별 분리 정규화**: 한국(`currency=KRW`: KOSPI+KOSDAQ) / 미국(`USD`: NASDAQ+NYSE)을 **각각 따로**. (시장마다 beta·PBR·부채 분포가 달라 섞으면 왜곡)
- **분위수(percentile)**: 같은 시장 풀 안에서 순위 → 0~1. 동점은 평균순위.
- 순위 기반이라 **극단값(outlier)에 면역** — 한 종목의 비정상 수치가 다른 종목 점수를 왜곡하지 않음.

---

## 3. 4축 산식

| 축 | 산식 | 입력 | 방향 |
|---|---|---|---|
| volatility (변동성) | `pct(beta)` | `StockIndicator.beta` | beta 높을수록 ↑ |
| value_score (저평가) | `pct(1/PBR)` | `StockIndicator.pbr` | PBR 낮을수록 ↑ |
| growth_score (성장성) | `pct(net_profit_yoy)` | `FinancialSummary.net_profit_yoy` | 순이익 YoY 높을수록 ↑ |
| stability (안정성) | `avg( pct(↓부채비율), pct(↑유동비율) )` | `FinancialSummary.debt_ratio, current_ratio` | 부채 낮고 유동 높을수록 ↑ |
| sector | `stock.sector` 복사 | — | — |

### 결측(null) 처리 = 중립 0.5
- `growth_score`: net_profit_yoy 없으면 **0.5**. (직전연도 적자/기준연도 1개 등으로 YoY 계산 불가)
- `stability`: 부채비율·유동비율 중 **있는 지표만 평균**, 둘 다 없으면 **0.5**.

> 산출 현황(2026-06-17): 성장 중립 175건, 안정성 중립 19건(US).

---

## 4. 데이터 함정 — beta·pbr는 다른 행에 있다

`StockIndicator`는 종목당 여러 날짜 행이 있고, **소스가 달라 beta와 pbr이 같은 행에 함께 있지 않다** (실측: 같은 행에 둘 다 있는 종목 0개).
- beta/volatility → `calc_market_indicators` 배치가 쓰는 최신 행
- pbr/per/eps → 펀더멘털 소스가 쓰는 다른 날짜 행

→ 배치는 축별로 **"값이 있는 최신 행"을 따로** 수집한다 (`beta__isnull=False` 최신, `pbr__isnull=False` 최신).

---

## 5. 알려진 한계 / 결정 기록

### ① stability 산식 변경 이력
- 초기안: `pct(1/beta)` — 그러나 beta는 "시장 대비 가격 변동성"일 뿐 재무 안정성이 아님. 삼성전자(beta 1.27) 같은 우량주가 안정성 최하위, 스팩·잡주가 최상위로 나오는 문제.
- **확정: 재무 기반** `avg(부채비율↓, 유동비율↑)`. 삼성전자 안정성 0.01 → 0.70으로 직관과 일치.

### ② 금융사(증권·은행·보험·지주)
- 부채비율이 구조적으로 매우 높음(1000%+, 레버리지가 본업) → 안정성 하위로 깔림.
- **결정: 그대로 둠 (A안).** 이유: (1) 분위수 정규화라 cap을 씌워도 순위가 안 바뀌어 무의미, (2) 증권사는 시장리스크 노출이 커 "안정성 낮음"이 부당하지 않음, (3) 금융주 추천 비중이 작음. → 필요 시 금융섹터 중립(0.5) 처리(B안) 재검토.

### ③ volatility ↔ stability 독립성
- 과거 두 축이 모두 beta 기반이라 사실상 거울값이었으나, stability를 재무 기반으로 바꿔 **독립 축**이 됨.

---

## 6. 갱신 / 운영

- **일 1회 배치**: `python manage.py calc_stock_dna` (`--dry-run`, `--limit N` 지원)
- `(stock, calculated_date)` 기준 upsert (당일 재실행 시 update).
- 선행 배치: `calc_market_indicators`(beta) + 재무 적재(`FinancialSummary`) 후 실행.
- (TODO) cron/celery 스케줄 등록 — 현재는 수동.

---

## 7. 역할 분담 / 다운스트림

- 컨벤션상 **정규화 산식 = Algo 도메인(순수 함수), 배치 껍데기·DB upsert = BE.** 현재 Algo 함수 미작성이라 BE가 임시로 함께 구현(`calc_stock_dna.py`). 추후 `recommend_algo`로 분리.
- 다운스트림: 궁합 `match_score`(`장투점수_산정로직.md` §2 / `ALGORITHM_DB_OPTIMIZATION_SPEC.jy.md` §2-5③)에서 4축을 유저 5벡터와 대조. stability는 **기간·경험** 요소에 사용.
- 본 문서는 `ALGORITHM_DB_OPTIMIZATION_SPEC.jy.md §2-2`의 stock_dna 산식(초기안: beta 원값·eps 기반)을 **대체**한다.
