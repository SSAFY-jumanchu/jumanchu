# 트랙 A 검증 체크리스트 (BE · Django)

> 근거 `docs/디버깅_통합리스트.md` §7 트랙 A · 검증일 2026-06-24 (브랜치 `feature/semifinal-ab`)
> **A 최신 사용 확인 ✅** — `origin/feature/semifinal-a` 최신 커밋 `0b7cc42`("fix(be): 디버깅 연동 수정 + 자산 마일스톤 + KIS 실서버 전환", 오늘 오전 푸시분)이 현재 브랜치에 전부 포함됨.
> 상태: ☑=실코드 앵커로 검증 완료 / ☐=미완

## ✅ 라이브 검증 (2026-06-24, 서버 :8000 실응답)
- `/api/v1/stocks/` → **200** · `/api/v1/markets/summary/` → **200** · `/api/v1/portfolio/milestones/` → **401**(라우트존재·인증필요) · `/api/v1/watchlist/` → **401**(존재·인증필요) · `/api/v1/stocks/005930/orderbook/` → **501**(미완 확인)
- 결론: A 8건 라우팅·구현 정상, orderbook만 501로 미완 — 코드 검증과 일치.

## A 항목 검증 결과 (9건 중 8건 완료, orderbook만 미완)

| 상태 | 작업 | 실코드 앵커 | 우선 | 비고 |
|---|---|---|---|---|
| ☑ | Account 미생성 500 방어 (get_or_create) | `portfolio/services.py:87·223·295`, `portfolio/views.py:255` | P0 | 잔액/포폴/요약 모두 get_or_create — DoesNotExist 500 해소 |
| ☑ | envelope 키 통일 (total_count) | `portfolio/serializers.py:108·167` | P1 | B의 holdings 매핑과 일치 |
| ☑ | initial_balance 실컬럼 사용 | `portfolio/serializers.py:11` (fields에 포함) | P1 | 1억 하드코딩 제거 |
| ☑ | market_summary 실패지수 4슬롯 보존 | `stocks/services/market_summary.py:74·88·97` (`_index_placeholder`) | P1 | 코스피·코스닥·나스닥·S&P500 4슬롯, 실패 시 null 슬롯 |
| ☑ | 온보딩 재검사 409 완화 | `accounts/views.py:277` ("409 가드 제거") | P1 | **B의 재검사 버튼 의존 → 풀림** |
| ☑ | watchlist 모델+등록/조회 API | `recommend/models.py:77` `UserLikedStock`, `recommend/urls.py:6-7`, `stocks/views.py:212` `is_in_watchlist` | P0 | ⚠ 위치가 `stocks/`가 아닌 **`recommend/`** (이름도 UserLikedStock). **B의 관심버튼 의존 → 풀림** |
| ☑ | 목표/마일스톤 API | `portfolio/urls.py:17` `MilestonesView`, `accounts/migrations/0006·0007` (goal/seed_goals) | P1 | ⚠ `accounts/goal`이 아닌 **`portfolio/milestones/`**. (C 의존) |
| ☑ | 궁합랭킹 응답에 현재가/등락 추가 | `recommend/services.py:55-56·186` (`current_price`/`change_rate`) | P2 | 거래대금(trade_value)은 미포함 — 가격·등락만 |
| ☐ | **orderbook 구현 or 제거 결정** | `stocks/views.py:263` 여전히 `_stub()` = **501** | P1 | **유일한 진짜 미완.** B의 호가 항목이 여기에 의존 → 구현/제거 결정 필요 |

## B 입장에서 풀린 핸드셰이크 (→A 의존 해제 확인)

- ☑ 관심종목 토글 — `UserLikedStock` + `/watchlist/` GET/POST/DELETE + `is_in_watchlist` 정확 채움 → **B 배선 가능(완료됨)**
- ☑ 매수 후 매매일지 — diary `order_id` 지원 → **B 배선 가능(완료됨)**
- ☑ 투자성향 재검사 — 409 가드 제거 → **B 배선 가능(완료됨)**
- ☐ 호가 — orderbook 501 **미완** → B는 구현 대기 or 제거 결정 후 진행
- ⚠ 매매일지·점수 히스토리 — `HoldingDetail`이 `recent_orders`/`related_diaries_count`/`review`만 제공, 종목별 일지 리스트·점수 시계열 직접 소스 없음(부분)
- ⚠ 목표/손절 % — 필드(target/stop_loss_price)는 있으나 %↔절대가 단위 합의 미정
- ☐ 실현수익 actual — diary 직렬화에 `realized_pnl` 미노출

## 결론
- **최신 A 사용 중 ✅** (origin/feature/semifinal-a `0b7cc42` 포함)
- A 작업 9건 중 **8건 완료, orderbook(501) 1건만 미완**
- B가 의존하던 P0/P1 핸드셰이크(관심·매수→일지·재검사)는 **전부 BE 측 준비 완료**
- B 잔여 보류는 호가(BE 미완)·히스토리/% /actual(BE 부분·미노출) — A에 추가 작업 필요
