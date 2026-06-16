# 장투케어 AI 리포트 생성기 (Long-Term Care AI Report) — 작업요약 & BE 연동 (정율→재민, 2026-06-16)

> 정식 명칭 **장투케어 AI 리포트 생성기** · 코드명 `longterm_report` · 진입함수 `build_longterm_report`.
> DB 사용법·실제 결과 샘플은 → **`장투케어_AI리포트_명세.md`** (캐노니컬 명세).

> 위치: `616jy/` (정율 개인 폴더, 기존 팀 폴더 안 건드림).
> 한 줄: **장투 케어 화면의 종목별 LLM 문장 4종(재무·성장·적합도 요약 + 종합의견)을
> 만드는 순수 Algo 로직 완성.** BE는 ① 점수·지표 dataclass 채우고 ② OpenAI 콜러블
> 주입해서 `build_longterm_report(...)` 호출만 하면 됨.

---

## 0. 무엇을 만들었나

장투 케어(포트폴리오) 화면에서 **사용자 보유 종목**마다 뜨는 LLM 생성 문장:

| 화면 위치 | 출력 키 | 근거 |
|---|---|---|
| 기반·Financial Score 요약 | `financial.summary` | 재무 지표 + financial_score |
| 성장성·Growth Score 요약 | `growth.summary` | YoY 지표 + growth_score |
| 적합도·Userfit Score 요약 | `userfit.summary` | 유저 프로필 + 개인궁합 점수 |
| 최종 종합의견 | `total.opinion` | 총점 + 세 점수 결합 |

- 점수·등급·라벨은 **결정적(코드)** 으로 산출 — LLM이 점수를 지어내지 않음.
- LLM은 **숫자를 받아 설명 문장만** 생성. 환각 방지 가드레일 포함(아래 §4).

## 0.1 ⚠️ 먼저 합의할 것 — DB 스키마 갭

화면은 점수 **3섹션**(재무·성장·**적합도**)인데 현재 DB는:

- `recommend_longtermscore` = `financial_score` + `growth_score` + `total_score` **2섹션뿐**.
  `userfit_score` 컬럼 없음.
- 적합도(=개인 궁합)는 per-user라 종목 테이블에 못 넣음 →
  **`recommend_recommendationcache.match_score`(rec_type='long_term')** 를 적합도 점수로 쓰는 걸로 가정함.
- LLM 문장 4종은 비싸므로 **`recommend_recommendationcache.reason`(JSONField)에 캐싱** 권장
  (`report.to_dict()` 통째로 저장 → TTL은 기존 `expires_at` 활용).

> 위 매핑(적합도=match_score, 문장=reason JSON)이 OK인지만 확인해 주세요. 아니면 컬럼/필드 합의.

---

## 1. BE가 호출할 함수 (시그니처)

```python
from longterm_report import (
    StockMeta, FinancialMetrics, GrowthMetrics, LongTermScores, UserProfile,
    build_longterm_report,
)

report = build_longterm_report(meta, fin, grw, scores, profile, *, llm=콜러블)
#   반환: LongTermReport  → report.to_dict() 로 REST 직렬화 / reason 저장
```

- **종목 1개당 LLM 호출 1번** (4문장을 JSON 한 방에 받음). 보유종목 N개면 N콜 → 캐싱 필수.
- `profile=None` 으로 주면 적합도 빼고 재무+성장+종합의견만 생성(개인화 전 단계용).

### 순수 함수도 따로 노출 (LLM 없이 테스트/디버깅)
```python
build_report_prompt(meta, fin, grw, scores, profile) -> str      # 프롬프트만
parse_report_response(raw, meta, scores, *, has_userfit) -> LongTermReport  # 파싱만
grade_of(score) -> str        # 90→A, 80→B+, 70→B, 60→C+, 50→C, else D (화면 JS와 동일)
label_of(total) -> str        # 총점→한줄 라벨
```

---

## 2. 입력 dataclass ↔ DB 컬럼 매핑 (BE가 채움)

| dataclass.필드 | 출처 테이블.컬럼 |
|---|---|
| `StockMeta(code,name,market,sector,currency)` | `stocks_stock` |
| `FinancialMetrics.debt_ratio / current_ratio / operating_margin / net_margin / payout_ratio` | `stocks_financialsummary` |
| `FinancialMetrics.roe / roa / dividend_yield` | `stocks_stockindicator` |
| `GrowthMetrics.revenue_yoy / operating_profit_yoy / net_profit_yoy` | `stocks_financialsummary` |
| `LongTermScores.financial / growth` | `recommend_longtermscore` |
| `LongTermScores.total / userfit` | `recommend_recommendationcache.match_score` (개인궁합) |
| `UserProfile.risk_type / preferred_period_months` | `accounts_investmentprofile.risk_type / preferred_period` |
| `UserProfile.preferred_sectors` | `accounts_userpreferredsector.sector[]` |
| `UserProfile.portfolio_weight_pct` | `portfolio_holding` 계산값(이 종목 평가액 / 총평가액 × 100) |

- 지표가 없으면 **그냥 `None`** 으로 두면 됨 → 프롬프트에서 '데이터 없음' 처리, LLM이 추측 안 함.
- 구체 매핑 코드는 `be_integration_stub.py::_load_inputs` 주석 참고.

---

## 3. LLM 콜러블 주입 — GMS GPT-4o (OpenAI 아님, 0615jy 패턴 동일)

LLM은 **GMS(SSAFY) 프록시로 GPT-4o** 사용. OpenAI SDK를 그대로 쓰되 `base_url`·키만 다름.
이미 `gms_client.py`로 래핑해 뒀으니 BE는 한 줄:

```python
from gms_client import make_gms_caller
llm = make_gms_caller(api_key=settings.GMS_API_KEY, model="gpt-4o")  # 또는 .env GMS_API_KEY
report = build_longterm_report(meta, fin, grw, scores, profile, llm=llm)
```

`gms_client.make_gms_caller` 내부(0615jy `test_gms.py`와 동일):
```python
from openai import OpenAI
client = OpenAI(api_key=GMS_API_KEY,
                base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1/")
client.chat.completions.create(model="gpt-4o", messages=[...], temperature=0.4, max_tokens=900)
```

- 의존성: `openai`, `python-dotenv`. 키: **`GMS_API_KEY`** (0615jy/.env와 동일 이름).
- 모델 id: 0615jy는 `gpt-4o-mini` 사용 → 본건은 **`gpt-4o`(4o pro)** 기본. GMS 노출 id 다르면 `model=`만 교체.
- 파서가 ```json 펜스/잡텍스트 방어(첫 `{`~마지막 `}`)하므로 그냥 써도 됨.
  더 안전하게 하려면 `make_gms_caller(force_json=True)`로 `response_format=json_object` 강제.
- 단독 확인: `python gms_client.py` (GMS_API_KEY 있으면 실제 1콜 응답 출력).

---

## 4. 환각 방지 (프롬프트 가드레일)

`build_report_prompt`가 자동으로 박는 규칙:
- 제공된 근거 수치만 사용, 목표가·미래 전망·없는 지표 **생성 금지**
- '데이터 없음' 항목은 언급 안 함
- **보유 종목 분석이며 매수·매도 권유 아님** (금융 컴플라이언스)
- 숫자 1~2개만 자연스럽게 인용

> 금융 서비스라 이 가드레일은 유지 권장. 톤/문장 수 조정은 `_GUARDRAIL` 상수에서.

---

## 5. 검증 결과

- ✅ `python demo_longterm_report.py` — fake LLM 주입으로 프롬프트 build→parse→to_dict 전 경로 통과(키 불필요).
- ✅ `profile=None` 경로(적합도 생략) 정상.
- ✅ None 지표 → '데이터 없음' 라벨 확인(배당성향 등).
- ⏳ 실제 OpenAI 연동 문장 품질은 BE 키 연결 후 함께 점검 필요.

---

## 6. 합의 필요 / 다음 단계

- [ ] **적합도=`recommendationcache.match_score`, 문장=`reason` JSON** 매핑 확정 (§0.1).
- [ ] 캐싱 정책: 보유종목 N개 × LLM 1콜 → `reason`에 저장 + TTL. 재생성 트리거(화면 'LLM 리포트 재생성' 버튼) 정의.
- [ ] `total`/`userfit` 점수의 정확한 산출 주체 — 본 모듈은 **입력으로 받음**(점수식은 별도 트랙).
- [ ] (옵션) 화면의 섹션별 4개 '항목+코멘트'(부채비율 → "업종 평균 대비 낮음")는 이번 범위 밖.
      필요하면 결정적 룰 기반 헬퍼로 추가 가능(LLM 아님).

---

## 부록. 파일 목록 (`616jy/`)

| 파일 | 역할 |
|---|---|
| `longterm_report.py` | 코어: 입력/출력 dataclass + 프롬프트 build + 파싱 + 진입점 |
| `gms_client.py` | GMS GPT-4o 콜러블(`make_gms_caller`) — 0615jy 패턴 |
| `be_integration_stub.py` | BE 호출 예시(ORM→dataclass 매핑, GMS→llm 주입) |
| `demo_longterm_report.py` | fake LLM 독립 실행 검증 |
| `작업요약_BE연동.md` | (이 문서) |
