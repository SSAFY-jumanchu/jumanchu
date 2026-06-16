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

---

## 2. DB 사용법 — 읽기 → 호출 → 쓰기

### 2.1 읽기 (BE가 DB → 입력 dataclass)

| 입력 필드 | 출처 테이블.컬럼 |
|---|---|
| `StockMeta(code,name,market,sector,currency)` | `stocks_stock` |
| `FinancialMetrics.debt_ratio / current_ratio / operating_margin / net_margin / payout_ratio` | `stocks_financialsummary` |
| `FinancialMetrics.roe / roa / dividend_yield` | `stocks_stockindicator` |
| `GrowthMetrics.revenue_yoy / operating_profit_yoy / net_profit_yoy` | `stocks_financialsummary` |
| `LongTermScores.financial / growth` | `recommend_longtermscore` |
| `LongTermScores.total / userfit` | `recommend_recommendationcache.match_score` (rec_type='long_term', 개인궁합) |
| `UserProfile.risk_type / preferred_period_months` | `accounts_investmentprofile.risk_type / preferred_period` |
| `UserProfile.preferred_sectors` | `accounts_userpreferredsector.sector[]` |
| `UserProfile.portfolio_weight_pct` | `portfolio_holding` 계산값 (이 종목 평가액 / 총평가액 × 100) |

> 지표가 없으면 그냥 `None` → 프롬프트가 '데이터 없음' 처리, LLM이 추측 안 함.

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
# recommend_recommendationcache (rec_type='long_term')
cache.reason = report.to_dict()          # JSONField에 4문장 통째 저장
cache.match_score = report.total_score   # 적합도(개인궁합) 점수
cache.expires_at = now + timedelta(days=1)  # TTL — 만료 시 재생성
cache.save()
```

- 화면 'LLM 리포트 재생성' 버튼 = 캐시 무효화 후 재호출.
- 점수 이력은 별도로 `recommend_longtermscorehistory`에 누적(8주 추세 카드용).

### 2.4 권장 View 흐름

```python
class LongTermReportView(APIView):
    def get(self, request, holding_id):
        holding = get_object_or_404(Holding, pk=holding_id, account__user=request.user)
        cache = RecommendationCache.objects.filter(
            user=request.user, stock=holding.stock, rec_type="long_term").first()
        if cache and cache.expires_at > now() and cache.reason:
            return Response(cache.reason)          # 캐시 히트
        meta, fin, grw, scores, profile = load_inputs(request.user, holding)  # §2.1
        report = build_longterm_report(meta, fin, grw, scores, profile,
                                       llm=make_gms_caller(api_key=settings.GMS_API_KEY))
        save_cache(cache, report)                  # §2.3
        return Response(report.to_dict())
```

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

---

## 6. ⚠️ BE와 합의할 점

- [ ] **DB 갭**: 화면은 점수 3섹션(재무·성장·**적합도**)인데 `recommend_longtermscore`는
      `financial/growth/total` **2섹션뿐, userfit_score 없음**. 적합도(개인궁합)는
      `recommend_recommendationcache.match_score`로, 문장 4종은 `reason`(JSON)으로 매핑 가정 → 승인 필요.
- [ ] `total`/`userfit` 점수 산출 주체(점수식은 별도 트랙, 본 모듈은 입력으로 받음).
- [ ] 캐싱 TTL/재생성 트리거 확정.

---

## 부록. 파일 목록 (`616jy/`)

| 파일 | 역할 |
|---|---|
| `longterm_report.py` | **코어** — 입력/출력 dataclass + 프롬프트 build + 파싱 + 진입점 |
| `gms_client.py` | GMS GPT-4o 콜러블 `make_gms_caller` |
| `be_integration_stub.py` | BE 호출 예시(DB→dataclass, GMS→llm 주입) |
| `demo_longterm_report.py` | fake LLM 오프라인 검증 |
| `장투케어_AI리포트_명세.md` | (이 문서) 명세 + DB 사용법 + 실제 결과 |
| `작업요약_BE연동.md` | 상세 연동 가이드 |
