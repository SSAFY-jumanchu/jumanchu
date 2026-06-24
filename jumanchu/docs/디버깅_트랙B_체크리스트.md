# 트랙 B 검증 체크리스트 (FE 거래·보유 도메인)

> 담당: 정율(B) · 브랜치 `feature/semifinal-ab` · 근거 `docs/디버깅_통합리스트.md` §7 트랙 B + §3 추가발견 + 핸드셰이크
> 전용 파일(충돌 없음): **StockDetailView · HoldingsView · PortfolioView · TradingDiaryView · MyPageView**
> 의존 표기: `—`=순수 FE / `→A`=BE 트랙 선행 필요
> 상태는 작업기록(`디버깅_트랙B_작업기록.md`) 기준 추정 — 직접 코드 대조 후 ☑ 확정하세요.

## ✅ 검증 결과 (2026-06-24, 현재 파일+라이브서버 기준)

**§1 순수 FE 전 항목 코드 대조 통과** — 5개 .vue 실코드 앵커 확인:
- StockDetail: stockInfo 빈ref+BE채움(73·339)·communityPosts=ref([])/author_nickname(228·520)·fetchHoldingDetail/loadHolding(232·330)·setQtyPct SELL분기(285)·fetchStockNews(405)·peers ref([])/targetPrice ref(null)(398-399)·maxVolume/'5분'(172·175·454)·curSym(117)
- Holdings: hv-detail-actions 제거(grep 0)·내계좌 /mypage(188)·hv-news-item `<a>`화(298)·v-if="holdings.length"(293)·*1380 제거+current_value(41·100)·loadError(158)
- Portfolio: hasReport(110)·total ?? null(116)·g-none(42)·holdings ref([])(15)·lt-empty 3곳(240·254·267)·'리포트 준비 중'(206)
- TradingDiary: entries ref([])(25)·fetchOrders(73)·pendingTrades+order_id(47·54)·'090360' 제거(grep 0)·loadError(171)
- MyPage: address 제거·signedFmt/realizedPnl(86·102)·trades ref([])/tradesError(66·67)·retest @click→/onboarding(428)·birth_year 편집(123·216·449)

**§2 핸드셰이크** — 3건 배선 확인 / 4건 보류 확인:
- ✅ 매수→일지(cta+router.push('/trading-diary') 327·1191) · 관심토글(addWatchlist/removeWatchlist/isWatched 13·94·102) · 재검사(MyPage:428)
- ☐ 호가 = **라이브 501 확인**(`/api/v1/stocks/005930/orderbook/` → 501, asks/bids 여전히 하드코딩 183·194) — BE 미완, 정상 보류
- ☐ 히스토리·목표손절%·실현수익 — BE 부분/미노출, 보류

**진행 중(커밋 안 됨)**: MyPage 활동내역/팔로워/받은좋아요 목업→실데이터(fetchPosts `mine=true`·fetchFollowers/Following) — 라이브 `/api/v1/posts/?mine=true`·`/users/1/followers/` 모두 **200 확인**. TradingDiary 잉여 textarea 8줄 제거.
- ⚠ **프로세스 주의**: 이 작업으로 `backend/community/views.py`(mine 파라미터)·`backend/portfolio/serializers.py`(Order에 market/currency 추가)도 수정됨 — **트랙 A(Django) 영역**. 둘 다 additive라 충돌 위험은 낮지만 A 담당과 공유 권장.

## 1. 순수 FE (—) — 이번 PR 범위, 전부 완료해야 함

### StockDetailView
- [ ] 미국상세 삼성 하드코딩 제거 (ceo_name/description/homepage_url/industry 사용) `269-281` **P0**
- [ ] 종토방 목업 제거 + 필드매핑 (author_nickname/title, created_at→상대시간) `176·465-481` **P1**
- [ ] 매매시뮬 보유연동 (holdQty/holdAvg 하드코딩 제거) `186-209` **P1**
- [ ] 매도 '최대'=보유수량 (setQtyPct BUY/SELL 분기) `223-225` **P1**
- [ ] 뉴스 탭 연동 (news 모듈 import + fetchStockNews) `354-385` **P1**
- [ ] 동종업계/목표주가 하드코딩 제거 (없으면 숨김) `337-351` **P1**
- [ ] 3분봉 라벨거짓→5분 정정·거래량 막대 분모100 클리핑 제거 `405·639·630` **P2**
- [ ] 통화 ₩ 하드코딩 → stock.currency (curSym) `33-39·522` **P2**

### HoldingsView
- [ ] 매수/매도 버튼 제거 (死버튼) `283-284` **P1**
- [ ] 바로가기 '내 계좌' 추가 `184-189` **P1**
- [ ] 뉴스 클릭 시 이동 (@click / <a href>) `292-298` **P1**
- [ ] 보유없는데 뉴스/커뮤니티 노출 → 종목별 연동 + communityPost 목업 제거 `138-139·289-306` **P1**
- [ ] USD 통화 표기 분열 + 총액 어긋남 (*1380 제거, current_value 합산) `101·84-107` **P2**
- [ ] loadError 미표시 → 배너 노출 `54-56` **P2**

### PortfolioView (장투)
- [ ] 리포트 없는 종목 0점/C 대량 → null/빈상태 처리 `257` **P0**
- [ ] 로드 실패 시 가짜 보유 노출 제거 + loadError `15-160·272-276` **P1**
- [ ] 빈 배열 섹션 안내 (journal/history/news 0행) `362-397` **P2**

### TradingDiaryView (매매일기)
- [ ] 로보스타 fallback 제거 + 주문내역 기반 (fetchOrders) `53-69·45` **P1**
- [ ] 신규 일기 종목 항상 로보스타('090360') → 종목선택 `99` **P1**
- [ ] '일지를 작성해 주세요' placeholder 처리 `301` **P3**

### MyPageView
- [ ] 주소 항목 삭제 (User에 address 필드 없음) `15·444-450` **P2**
- [ ] phone/name/email 저장 안 됨 → 행 제거/읽기전용, nickname·birth_year만 편집 `13·416·430·178-181` **P2**
- [ ] 주문내역 폴백 오인 (catch 에러삼킴) → tradesError 노출 `127-146` **P2**
- [ ] 투자성향 점수 하드코딩 (62/78/45) → 점수바 제거, 타입배지 유지 `399-403` **P2**
- [ ] 이름=닉네임 모순 해소 `115·413-425` **P2**

### §3 추가발견 (제보 밖, B 담당)
- [ ] MyPage 이달수익/실현손익 `+-318400원` 이중부호 렌더 → signedFmt **P1**

## 2. BE 선행 핸드셰이크 (→A) — 트랙 A 머지 후 연결

> A+B 통합 후 재점검(작업기록 §A+B) 반영. ✅표시는 통합 후 배선 완료된 항목.

- [ ] 매수 후 매매일지 자동연동 (submitOrder 성공 → /trading-diary 유도) **→A(order_id 지원됨)** — *통합 후 배선됨, 동작 확인*
- [ ] 관심종목 추가 버튼 (@click + is_in_watchlist 토글, ★/☆) **→A(watchlist API)** — *통합 후 배선됨, 동작 확인*
- [ ] 투자성향 재검사 버튼 (@click → /onboarding) **→A(409 완화됨)** — *통합 후 배선됨, 동작 확인*
- [ ] 호가 실데이터 (asks/bids) **→A(orderbook 501 — 유일 진짜 미완)** — *구현 or 제거 결정 대기*
- [ ] 매매일지·장투점수 히스토리 데이터 연동 (journal/history) **→A(부분 소스만 존재)** — *보류*
- [ ] 목표/손절 % 저장 (target_price/stop_loss_price) **→A(단위 합의 미정)** — *보류*
- [ ] 실현수익 actual 연동 **→A(diary에 realized_pnl 미노출)** — *보류*

## 3. 최종 확인
- [ ] `cd frontend && npm run build` 0 error
- [ ] 5개 .vue 외 파일 미수정 (router/index.js·api/*.js 충돌 없음)
- [ ] 위 §1 순수 FE 전부 ☑ / §2 핸드셰이크 3건 배선 확인 / 미완(호가·히스토리·%·actual) 보류 사유 명시
