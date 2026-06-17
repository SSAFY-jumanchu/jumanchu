# 장투케어 AI 리포트 생성기 (Long-Term Care AI Report) — 명세 & BE DB 사용법

> 정식 명칭: **장투케어 AI 리포트 생성기 (Long-Term Care AI Report)**
> 코드명: `longterm_report` · 진입함수: `build_longterm_report()` · LLM: **GMS GPT-4o**
> 작성: 정율(Algo) → 강재민(BE), 2026-06-16 · 위치: `616jy/`
> 한 줄: **보유 종목 1개 → 장투 케어 화면용 AI 문장 4종(재무·성장·적합도 요약 + 종합의견)을
> JSON으로 생성.** BE는 DB에서 숫자 뽑아 넣고, 결과 JSON을 캐시 테이블에 저장만 하면 됨.

---

## 1. 무엇을 만드나 (출력 4종)

| 화면 위치 | 출력 키 | 타입 |
|---|---|---|
| 기반·Financial Score 요약 | `financial.summary` | LLM 문장 |
| 성장성·Growth Score 요약 | `growth.summary` | LLM 문장 |
| 적합도·Userfit Score 요약 | `userfit.summary` | LLM 문장 |
| 최종 종합의견 | `total.opinion` | LLM 문장 |

- 점수·등급·라벨(`grade`, `total.label`)은 **결정적 코드 산출** — LLM이 점수를 지어내지 않음.
- LLM은 받은 숫자로 **설명 문장만** 생성(환각 방지 가드레일 포함).
- **재무·성장·적합도는 각 2문장 이내 요약, 종합의견(`total.opinion`)은 셋을 종합한 총평(3~4문장).**

---

## 2. DB 사용법 — 읽기 → 호출 → 쓰기

### 2.1 읽기 (BE가 DB → 입력 dataclass)

| 입력 필드 | 출처 테이블.컬럼 |
|---|---|
| `StockMeta(code,name,market,sector,currency)` | `stocks_stock` |
| `FinancialMetrics.debt_ratio / current_ratio / operating_margin / net_margin / payout_ratio` | `stocks_financialsummary` |
| `FinancialMetrics.roe / roa / dividend_yield` | `stocks_stockindicator` |
| `GrowthMetrics.revenue_yoy / operating_profit_yoy / net_profit_yoy` | `stocks_financialsummary` |
| `LongTermScores.financial / growth` | `recommend_longtermscore` *또는* 지표로 `longterm_score`가 산출 |
| `LongTermScores.userfit` (궁합/적합도) | **`recommend_recommendationcache.match_score` (rec_type=`onboarding`)** — 온보딩에서 산출/입력된 궁합 |
| `LongTermScores.total` (종합) | **`longterm_score`가 산출**: 종목소계(재무·성장)×0.7 + 궁합×0.3 |
| `UserProfile.risk_type / preferred_period_months` | `accounts_investmentprofile.risk_type / preferred_period` |
| `UserProfile.preferred_sectors` | `accounts_userpreferredsector.sector[]` |
| `UserProfile.portfolio_weight_pct` | `portfolio_holding` 계산값 (이 종목 평가액 / 총평가액 × 100) |

> 지표가 없으면 그냥 `None` → 프롬프트가 '데이터 없음' 처리, LLM이 추측 안 함.
> ⚠️ **단위**: `stocks_financialsummary`/`stocks_stockindicator`의 비율 컬럼은 **fraction으로 저장**
> (예: `operating_margin=0.1088`). 입력 dataclass는 **%**를 받으므로 매핑 시 **×100** 환산.
>
> **궁합(userfit)은 온보딩 산출값**: 온보딩 때 `StockDna` × 유저 투자성향 매칭 결과를
> `RecommendationCache(rec_type='onboarding').match_score`로 저장 → 장투 리포트는 그 값을 그대로 읽는다.
> (사용자가 온보딩을 안 했으면 행이 없음 → `userfit=None`으로 두면 적합도 빠지고 재무·성장만.)

#### 점수 산출 모듈 `longterm_score` (정율 Algo)

```python
from longterm_score import compute_scores   # 지표+궁합 → LongTermScores(financial/growth/total/userfit)

userfit = float(onboarding.match_score)            # 온보딩 궁합 (rec_type='onboarding')
scores  = compute_scores(fin, grw, userfit_score=userfit)
#  financial/growth = 지표→0~100 점수,  종목소계 = 재무·성장 1:1,
#  total = 종목소계 × (1-0.30) + 궁합 × 0.30   ← 궁합 30%는 recommend.LongTermScore docstring으로 확정
```

가중치 상수(`longterm_score` 상단): `W_MATCH=0.30`(확정) · `W_FINANCIAL=W_GROWTH=0.50`(잠정, 팀 합의로 조정).
지표→점수 환산 기준선도 잠정(상수/함수로 분리).

### 2.2 호출

```python
from gms_client import make_gms_caller
from longterm_report import build_longterm_report

llm = make_gms_caller(api_key=settings.GMS_API_KEY, model="gpt-4o")  # 또는 .env GMS_API_KEY
report = build_longterm_report(meta, fin, grw, scores, profile, llm=llm)
payload = report.to_dict()   # 아래 §4 구조
```

- **종목 1개당 GMS 1콜.** 보유종목 N개면 N콜 → **캐싱 필수**.
- `profile=None` 주면 적합도 빼고 재무+성장+종합의견만(개인화 전 단계).

### 2.3 쓰기 (결과 JSON → 캐시 테이블)

```python
# recommend_recommendationcache (rec_type='long_term')  ← 'onboarding'(궁합)과 다른 행
cache.reason = report.to_dict()          # JSONField에 4문장 통째 저장
cache.match_score = report.total_score   # 장투 종합 total (= 소계×0.7 + 궁합×0.3)
cache.expires_at = now + timedelta(days=1)  # TTL — 만료 시 재생성
cache.save()
```

> 읽기(궁합)는 `rec_type='onboarding'` 행, 쓰기(장투 결과)는 `rec_type='long_term'` 행 — **서로 다른 행**.

- 화면 'LLM 리포트 재생성' 버튼 = 캐시 무효화 후 재호출.
- 점수 이력은 별도로 `recommend_longtermscorehistory`에 누적(8주 추세 카드용).

### 2.4 BE 연동 — 전체 흐름 (권장, 검증된 매핑)

장투 케어 화면이 보유종목 1개 리포트를 요청 → BE는 **① 캐시확인 → ② 입력로드 → ③ 점수산출
→ ④ 리포트생성 → ⑤ 캐시저장** 순으로 처리한다. (아래 코드는 `_db_demo.py`에서 실 DB로 검증한 매핑과 동일)

```python
from longterm_report import StockMeta, FinancialMetrics, GrowthMetrics, UserProfile, build_longterm_report
from longterm_score import compute_scores          # 재무·성장→점수, 궁합 결합→total
from gms_client import make_gms_caller

class LongTermReportView(APIView):
    def get(self, request, holding_id):
        holding = get_object_or_404(Holding, pk=holding_id, account__user=request.user)
        stock, user = holding.stock, request.user

        # ① 캐시 히트(rec_type='long_term', 미만료) → reason(JSON) 그대로
        cache = RecommendationCache.objects.filter(
            user=user, stock=stock, rec_type="long_term").first()
        if cache and cache.reason and cache.expires_at > now():
            return Response(cache.reason)

        # ② 입력 로드 — ⚠️ DB는 비율(fraction) 저장 → %로 ×100 환산
        fs   = stock.financial_summaries.latest("fetched_at")
        ind  = stock.indicators.latest("calculated_date")
        prof = user.investmentprofile
        P = lambda x: None if x is None else float(x) * 100
        meta = StockMeta(stock.code, stock.name, stock.market, stock.sector, stock.currency)
        fin  = FinancialMetrics(P(fs.debt_ratio), P(fs.current_ratio), P(fs.operating_margin),
                                P(fs.net_margin), P(ind.roe), P(ind.roa), P(ind.dividend_yield),
                                P(fs.payout_ratio), fs.fiscal_period)
        grw  = GrowthMetrics(P(fs.revenue_yoy), P(fs.operating_profit_yoy), P(fs.net_profit_yoy))

        # 궁합 = 온보딩 산출값(rec_type='onboarding'). 없으면 None → 적합도 빠지고 재무·성장만
        ob = RecommendationCache.objects.filter(
            user=user, stock=stock, rec_type="onboarding").first()
        userfit = float(ob.match_score) if ob else None
        profile = (UserProfile(prof.risk_type, prof.preferred_period,
                               [s.sector for s in user.preferred_sectors.all()],
                               weight_pct(holding))
                   if userfit is not None else None)

        # ③ 점수 산출 (total = 종목소계×0.7 + 궁합×0.3)   ④ 리포트 생성 (GMS 1콜)
        scores = compute_scores(fin, grw, userfit_score=userfit)
        report = build_longterm_report(meta, fin, grw, scores, profile,
                                       llm=make_gms_caller(api_key=settings.GMS_API_KEY))

        # ⑤ 캐시 저장 (match_score=종합 total, reason=문장 JSON, TTL 1일)
        RecommendationCache.objects.update_or_create(
            user=user, stock=stock, rec_type="long_term",
            defaults=dict(match_score=report.total_score, reason=report.to_dict(),
                          expires_at=now() + timedelta(days=1)))
        return Response(report.to_dict())
```

- 보유종목 N개 화면이면 N콜 → 위 캐시(TTL 1일)가 비용 차단. '리포트 재생성' 버튼 = 캐시 삭제 후 재호출.
- (선택) 종목 점수(재무·성장 소계)를 일배치로 `recommend_longtermscore`에 미리 적재한다면, View에선
  `compute_scores` 대신 그 값 + `longterm_score.longterm_total(소계, userfit)`로 결합해도 됨.

---

## 3. LLM = GMS GPT-4o (의존성)

- OpenAI SDK 그대로 + `base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1/"` + 키 `GMS_API_KEY`.
- 의존성: **`openai>=1.55`** (httpx 0.28과 호환. 1.39는 `proxies` 오류), `python-dotenv`.
- 모델: 기본 `gpt-4o`. GMS 노출 id 다르면 `make_gms_caller(model=...)`만 교체.
- 더 안전한 파싱: `make_gms_caller(force_json=True)` → `response_format=json_object`.

---

## 4. 출력 JSON 구조 (`report.to_dict()`)

```json
{
  "stock_code": "000660",
  "financial": {"section":"financial","score":78,"grade":"B","summary":"..."},
  "growth":    {"section":"growth","score":92,"grade":"A","summary":"..."},
  "userfit":   {"section":"userfit","score":87,"grade":"B+","summary":"..."},
  "total":     {"score":86,"grade":"B+","label":"장기 보유 추천","opinion":"..."}
}
```

`userfit`은 `profile=None`이면 `null`.

---

## 5. 실제 생성 결과 (GMS GPT-4o, 2026-06-16 검증)

> 화면 보유 5종목 실데이터로 실호출한 결과. **입력 수치만 사용**(지어낸 숫자·목표가 없음),
> 데이터 없는 항목은 '데이터 부족'으로 처리(환각 방지 확인).

### SK하이닉스 (000660) · 총점 86 B+ — 장기 보유 추천
- **재무 78 B**: SK하이닉스는 안정적인 재무 상태를 유지하고 있습니다. 부채비율이 22.4%로 낮아 재무 건전성이 뛰어나며, 유동비율도 198.3%로 높아 단기 채무를 충분히 감당할 수 있는 여력이 있습니다.
- **성장 92 A**: 성장성이 매우 뛰어난 기업입니다. 특히, 매출 성장률이 48.2%에 달하며, 영업이익 성장률은 120.5%로 급격한 성장을 보여주고 있습니다.
- **적합 87 B+**: SK하이닉스는 공격적인 투자 성향을 가진 분께 적합한 종목입니다. 반도체 섹터에 대한 선호와 일치하며, 포트폴리오 내 비중이 38.4%로 높은 만큼 분산 투자에 유의하셔야 합니다.
- **★ 종합의견**: SK하이닉스는 총점 86/100으로 B+ 등급을 받았으며, 장기 보유에 적합한 종목으로 평가됩니다. 재무 건전성과 높은 성장성을 바탕으로 장기적인 투자 가치가 있습니다. 다만, 포트폴리오 비중이 높다면 분산 투자 전략을 고려해 보시는 것도 좋겠습니다.

### 삼성전자 (005930) · 총점 80 B+ — 장기 보유 추천
- **재무 82 B+**: 삼성전자는 재무적으로 안정적인 모습을 보이고 있습니다. 부채비율이 26.8%로 낮아 재무 건전성이 뛰어나며, 영업이익률도 14.2%로 양호한 편입니다.
- **성장 68 C+**: 매출 성장률이 12.3%로 나타나며, 이는 회사의 지속적인 성장 가능성을 보여줍니다. 다만, 영업이익과 순이익 성장률에 대한 데이터는 아직 부족합니다.
- **적합 91 A**: 사용자의 투자 성향이 균형형이라면, 삼성전자는 적합한 선택일 수 있습니다. 다만, 선호 섹터와는 일치하지 않지만 포트폴리오 내 적정 비중을 유지하고 있습니다.
- **★ 종합의견**: 삼성전자는 총점 80/100으로 B+ 등급을 받았으며, 장기 보유에 적합한 종목으로 평가됩니다. 재무적으로 안정적이고 성장 가능성도 보이는 만큼, 장기적인 관점에서 긍정적인 선택일 수 있습니다. 사용자의 투자 성향과 포트폴리오 비중을 고려할 때, 현재 보유를 유지하는 것이 좋겠습니다.

### NVIDIA (NVDA) · 총점 91 A — 장기 핵심 보유 추천
- **재무 95 A**: NVIDIA는 재무 건전성이 매우 우수한 편입니다. 부채비율이 41.2%로 안정적이며, 영업이익률이 54.7%로 높은 수익성을 보여줍니다.
- **성장 97 A**: NVIDIA의 매출 성장률은 무려 427.0%로, 최근 급격한 성장을 이루고 있습니다. 이는 회사의 성장 가능성을 강력하게 뒷받침합니다.
- **적합 82 B+**: 이 종목은 공격형 투자 성향을 가진 분들께 적합하며, 반도체 섹터에 대한 선호가 있는 경우 더욱 매력적입니다. 포트폴리오 비중도 적정 수준인 22.0%로 유지되고 있습니다.
- **★ 종합의견**: NVIDIA는 총점 91/100으로 A등급을 받은 만큼, 장기 보유에 적합한 핵심 종목으로 평가됩니다. 재무 건전성과 성장성이 모두 뛰어나며, 반도체 섹터에 대한 투자 매력을 제공합니다. 따라서 장기적인 관점에서 지속적인 관심을 가질 만한 가치가 있다고 판단됩니다.

### Apple (AAPL) · 총점 78 B — 보유 유지·모니터링
- **재무 88 B+**: Apple의 재무 건전성은 매우 우수합니다. 특히, 영업이익률이 31.5%로 높은 수익성을 보여주고 있으며, ROE가 141.5%로 매우 강력한 자본 효율성을 나타냅니다.
- **성장 62 C+**: 성장성 측면에서는 아직 데이터가 부족하지만, 현재 점수로는 평균 수준입니다. 추가적인 성장 데이터가 필요할 것으로 보입니다.
- **적합 85 B+**: 사용자님의 투자 성향과는 일부 불일치하지만, 포트폴리오 비중은 적정 범위 내에 있습니다. 12개월 보유를 선호하신다면, 현재로서는 적합한 선택일 수 있습니다.
- **★ 종합의견**: Apple은 재무적으로 매우 건전하며, 이는 장기 투자에 있어 긍정적인 요소입니다. 성장성 데이터가 부족하지만, 현재 점수로는 안정적인 수준입니다. 총점 78점으로, 보유를 유지하며 모니터링하시는 것이 좋겠습니다.

### NAVER (035420) · 총점 71 B — 보유 유지·모니터링
- **재무 71 B**: NAVER의 재무 건전성은 비교적 안정적입니다. 특히 부채비율이 58.1%로 적정 수준을 유지하고 있으며, 영업이익률도 11.8%로 양호합니다.
- **성장 65 C+**: NAVER는 매출 성장률이 18.4%로 긍정적인 성장을 보이고 있습니다. 그러나 영업이익 성장률은 5.1%로 다소 낮은 편입니다.
- **적합 76 B**: 이 종목은 IT·소프트웨어 섹터에 속해 있으며, 사용자의 투자 성향과 잘 맞습니다. 포트폴리오 비중도 14.0%로 적정 범위에 있습니다.
- **★ 종합의견**: NAVER는 총점 71/100으로 B등급을 받았습니다. 이는 보유를 유지하며 모니터링하기에 적합한 수준입니다. 장기적인 관점에서 안정적인 재무 상태와 성장 가능성을 고려할 때, 지속적인 관심이 필요합니다.

### 5.1 실 DB + 온보딩 궁합 검증 (2026-06-17, `longterm_score` 산출)

> 덤프(`0615jy/jumanchu_db_20260615.sql`) 실 지표(×100 환산) + 온보딩 궁합 가정값 + 실 GMS GPT-4o.
> total = 종목소계(재무·성장 1:1)×0.7 + 궁합×0.3.

| 종목 | 재무 | 성장 | 궁합 | **총평(종합)** |
|---|---|---|---|---|
| SK하이닉스 (000660) | 91 A | 100 A | 81 B+ | **91 A — 장기 핵심 보유 추천** |
| NVIDIA (NVDA) | 99 A | 100 A | 88 B+ | **96 A — 장기 핵심 보유 추천** |
| 삼성전자 (005930) | 62 C+ | 92 A | 78 B | **77 B — 보유 유지·모니터링** |
| Apple (AAPL) | 83 B+ | 82 B+ | 64 C+ | **77 B — 보유 유지·모니터링** |
| NAVER (035420) | 65 C+ | 89 B+ | 70 B | **75 B — 보유 유지·모니터링** |
| 현대차 (005380) | 36 D | 52 C | 66 C+ | **51 C — 보유 재검토** |

예) **삼성전자** — 재무: "부채비율 27.9%로 안정적이나 ROE 8.6%는 다소 아쉽습니다." / 성장: "매출 16.2%·영업이익 398.3% 성장으로 성장성이 뛰어납니다." / 궁합: "전기·전자 선호와 일치, 균형형 성향에 적합." / **총평**: "안정적 재무·높은 성장성으로 장기 보유·모니터링에 적합. 다만 ROE는 유의."

---

## 6. ⚠️ BE와 합의할 점

- [x] **점수 산출 확정** (2026-06-17): 궁합(userfit)=온보딩 `RecommendationCache(rec_type='onboarding').match_score`,
      종합 total=종목소계(재무·성장)×0.7 + 궁합×0.3 → `longterm_score.compute_scores`가 산출. 궁합 30%는
      `recommend.LongTermScore` docstring으로 확정. 재무:성장 1:1·환산 기준선은 잠정(상수로 조정).
- [x] **실 DB 검증** (2026-06-17): 삼성전자(005930)·Apple(AAPL) 덤프 지표로 산출 + 실 GMS GPT-4o 총평 정상.
      `recommend_*`(궁합/DNA/장투점수) 테이블은 **현재 비어 있음** → 궁합은 온보딩 구현 후 채워짐.
- [ ] 재무:성장 비중·지표→점수 환산 기준선 최종 합의(현재 잠정값).
- [ ] 캐싱 TTL/재생성 트리거 확정.

---

## 부록. 파일 목록 (`616jy/`)

| 파일 | 역할 |
|---|---|
| `longterm_report.py` | **코어** — 입력/출력 dataclass + 프롬프트 build + 파싱 + 진입점 |
| `longterm_score.py` | **점수 산출** — 지표→재무·성장 점수, 궁합 결합 → 종합 total (`compute_scores`) |
| `gms_client.py` | GMS GPT-4o 콜러블 `make_gms_caller` |
| `be_integration_stub.py` | BE 호출 예시(DB→dataclass, 온보딩 궁합 조회, GMS→llm 주입) |
| `demo_longterm_report.py` | fake LLM 오프라인 검증 |
| `demo_longterm_score.py` | 점수 산출 오프라인 검증 (예시 종목) |
| `장투케어_AI리포트_명세.md` | (이 문서) 명세 + DB 사용법 + 실제 결과 |
| `작업요약_BE연동.md` | 상세 연동 가이드 |
