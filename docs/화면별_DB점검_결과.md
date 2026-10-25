# 화면별 DB 점검 결과 (2026-06-09 ~ 06-10)

> 주만추 전 화면을 돌며 **"이 화면이 어떤 DB로 그려지나"** 를 점검하고, 로직·산식·캐싱 전략까지 정리한 문서.
> 결론: **새로 만들 테이블은 `comment_like` 1개뿐.** 나머지는 전부 기존 테이블 + KIS 라이브 + 계산. 핵심은 **컬럼 정리 + 뉴스/장투/매매일기 설계 결정**.

---

## 1. 화면별 결론

| 화면 | 핵심 DB | 신규 테이블 | 메모 |
|---|---|---|---|
| 온보딩 | `investment_profile`(5벡터) | – | (06-09) |
| 마이페이지 | `user`, `user_goal`/`goal` | – | (06-09) |
| 커뮤니티(피드) | `community_post`·`comment`·`post_like` | **`comment_like`** | 댓글 좋아요 추가, 대댓글 X |
| 홈 | 종합(holding/goal/news/추천) | – | (06-09) |
| 종목 상세 | `stock`·`stock_indicator`·`stock_price` | – | 호가/체결/분봉 = KIS 라이브, 투자자별 제외 |
| 주식 조회 | `stock` + KIS + 뉴스 | – | AI한줄 → 최신뉴스, 관심종목 통합 |
| 보유 종목 | `holding`·`account`·`stock` | – | 평가/손익 = 계산 |
| 장투 케어 | `long_term_score`(+`_history`) | – | 3축 점수 + LLM 보고서(캐시) |
| 매매일기 | `stock_diary`·`diary_review`·`order` | – | 입력 전면 선택형 |
| 스와이프 | `recommendation_cache`·`stock_dna`·`user_liked_stock` | – | 궁합 + Stock DNA |

→ **신규 테이블 = `comment_like` 1개.** 호가·체결·시세·평가손익 등은 전부 **라이브 + 계산**(저장 X).

---

## 2. DBML 변경 (`docs/erd.dbml`)

**신규**
- `comment_like` (댓글 좋아요, `post_like`와 동일 구조)

**변경**
- `stock_diary`: `reason_text` 삭제 → **`reason_category`(선택형)** · `target_price` · `stop_loss_price` 추가
- `diary_review`: **`judgment`(선택형: 성공/실패/보류)** 추가
- `news_related_stock.relevance_score`: 노트 갱신(매칭 신뢰도·정렬용)

**삭제**
- `stock_news.sentiment_score`
- `stock_dna.news_sentiment`

---

## 3. 주요 설계 결정

### 📰 뉴스
- **헤드라인 + 링크만** 저장 (본문·summary 저장 X — 저작권 + RSS summary는 잘린 조각이라 못 보여줌)
- **sentiment 전면 제거** — 화면·궁합·장투 어디서도 실사용 없음. (정율 설계도 컬럼만 있고 점수 산식엔 빠져 있었음)
- 화면 = **"관련 기사"** 로만 (왜 움직였나 인과 주장 X → 가십/할루시네이션/폴백 회피)
- 매칭: **1차 경제 언론사 RSS 피드 + 종목 태깅 / 2차 종목별 구글뉴스(blacklist 필터)**
  - 검증: 경제 피드 = 가십 적음·커버리지 얕음 / 구글 = 커버리지 좋음·가십 많음 → **합치고 출처 blacklist**
  - ⚠️ 일부 경제 피드 URL이 죽어있음(연합뉴스TV·조선비즈) → 헬스체크/갱신 필요

### ⚡ 실시간 / 캐싱
- **호가·체결·분봉·현재가 = KIS 라이브 + Redis 캐시** (저장 X, 일봉만 저장)
- KIS 키 1개라 **호출 한도가 동시접속 병목** → Redis(종목별 캐시)로 "유저 수"가 아니라 "조회 종목 수"로 한계를 옮김
- **AI/LLM 산출물 = Redis 캐시(DB 아님)**: 장투 LLM 보고서(점수 일배치와 키 동기화)

### 🧬 장투 점수 (상세: `docs/장투점수_산정로직.md`)
- 종합 = **재무 30 + 성장 40 + 궁합 30**
- 3축 산식: 재무(4지표 평균) / 성장(매출·순익 YoY) / 궁합(`match_score` 재사용)
- 정성 지표(AI수요·점유율 등)는 **정율 설계에 없음 → 제외** (성장 = 재무 숫자)
- LLM 보고서 = Redis 캐시 / 점수·히스토리 = `long_term_score`(+`_history`) 일배치

### 📓 매매일기
- **모든 입력 선택형** (자유서술·뉴스첨부 제거) → "고르기만" 1초 작성
- 2단계: 작성(확신도·목표·손절 **박제**) → 복기(실제 결과·교훈)
- **대기** = 매매(`order`)는 있는데 일기 없음 → 홈 "투자일기 대기 N건"

---

## 4. 남은 할 일 / 결정

- [ ] **Django 모델 실제 반영** → makemigrations
  - `diary`: `reason_text`·`related_news` 제거, `reason_category` choices화
  - `comment_like` 모델 추가 / `stock_news`·`stock_dna` 컬럼 정리
- [ ] 장투: **절대식 vs 분위수** (데모는 절대식)
- [ ] 매매일기: 이유 **단일/복수**, 목표·손절 **%/가격**
- [ ] 스와이프: 패스 저장 여부 / 소셜증거 COUNT vs 비정규화
- [ ] **추천 엔진(궁합)** + `stock_dna` 적재 배치 (정율 algo)
- [ ] **뉴스 수집 스케줄러**(경제 피드) + 죽은 피드 URL 갱신
- [ ] **장투 데모 포함 여부** (금요일 ERD 회의 결정)

---

## 5. 산출물

- **문서**: `erd.dbml` · `장투점수_산정로직.md` · 이 문서
- **목업**(`docs/wireframe_jam/`): 홈 · 커뮤니티 게시글 · 주식조회 · 보유종목 · 장투케어 · 매매일기 · 스와이프카드 (.html)
- **nav 통일**: 홈 / 피드 / 주식 조회 / 보유 종목 / 매매일기 / 장투 케어
- **검증 스크립트**(`kis_test/`): `news_rss_test.py` · `news_feed_test.py` · `news_combined_test.py` (RSS 뉴스 수집 검증)
