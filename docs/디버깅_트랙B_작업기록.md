# 트랙 B 디버깅 작업 기록 (BE 독립 항목)

> 브랜치: `feature/semifinal-b` · 담당: 정율(B) · 작성: 2026-06-23
> 근거: `docs/디버깅_통합리스트.md` §7 트랙 B 체크리스트
> 원칙: **A·C 트랙에 영향 없는 전용 파일만 수정** (StockDetail / Holdings / Portfolio / TradingDiary / MyPage)
> 범위: 의존 `—`(순수 FE) 항목만 우선. `→A`(BE 선행) 항목은 BE 완료 후로 보류.

## BE(트랙 A) 완료 후 할 일 — FE 핸드셰이크 체크리스트

> 아래는 **BE 선행이 끝나면 FE가 이어서 작업**할 항목. 트랙 A 해당 작업이 머지되면 이 파일로 돌아와 연결한다.
> 현재는 모두 보류(이번 PR 범위 밖). API 함수 다수는 이미 존재(데드 export) — **연결만** 하면 되는 경우가 많음.
> 앵커는 2026-06-24 현재 코드 기준 재검증(아래 §교차검증 참조).

| ☐ | 항목 | 파일:현재앵커 | 현재 상태(死) | BE 선행(트랙 A) | 머지 후 FE가 할 일 |
|---|---|---|---|---|---|
| ☐ | 호가 실데이터 | StockDetail:163·174 (`asks`/`bids` ref 하드코딩), 템플릿 725~772 | 하드코딩 5호가 + BE orderbook **501 스텁** | orderbook 구현 or **제거 결정**(B와 합의) | 구현 시 `fetchStockOrderbook`로 `asks`/`bids` 교체 + 현재가/등락 바인딩. 제거 결정 시 호가 패널(725~772)·`asks`/`bids`/`maxAskQty`/`maxBidQty` 삭제 |
| ☐ | 매수 후 매매일지 자동연동 | StockDetail:286 `submitOrder`, 버튼 1148 | 주문만 생성, 일지 트리거 없음 | order_id 핸드셰이크(**이미 지원됨**) | `submitOrder` 성공 응답 `order_id`로 `/trading-diary` 라우팅 또는 토스트 유도. (TradingDiary는 이미 미작성 주문을 `pendingTrades`로 노출하므로 라우팅만으로 연결됨) |
| ☐ | 관심종목 추가 버튼 | StockDetail:548 `watch-toggle-btn`(`@click` 없음) | 死버튼, `is_in_watchlist` 항상 False | watchlist 모델+등록/조회 API 신설(P0·범위큼) | `watch-toggle-btn`에 `@click` 배선 + `is_in_watchlist` 토글·별표(☆/★) 상태 |
| ☐ | 매매일지·장투점수 히스토리 | Portfolio:124~125 (`journal:[]`/`history:[]` 고정), 템플릿 232~254 | 항상 빈 배열(빈 상태 UI만 처리됨) | diary/score-history 종목별 조회 API | 매핑에서 `journal`/`history` 실데이터 채움 → 빈 상태 자동 해제 |
| ☐ | 목표/손절 % 저장 | TradingDiary:124 (`createDiary` memo만 전송) | %↔절대가 변환불가로 미전송 | %↔절대가 **단위 정의 합의** | 합의된 단위로 `createDiary`에 `target_price`/`stop_loss_price` 추가 전송 |
| ☐ | 실현수익 actual 연동 | TradingDiary:40 (`actual:'—'` 고정) | 복기 실제수익 항상 '—' | Order `realized_pnl`을 diary 응답에 노출 | `mapDiary`에서 `actual`을 실현손익으로 채움(현재 '—' 하드코딩) |
| ☐ | 투자성향 재검사 버튼 | MyPage:401 `retest-btn`(`@click` 없음) | 死버튼 | 재제출 **409 완화 정책** | `retest-btn`에 `@click`으로 `/onboarding` 라우팅(409 정책 확정 후) |

---

## 교차검증 결과 (2026-06-24)

> 작업기록의 '✅ 완료' 항목을 실제 커밋 코드(`ab2d861` 기준, 5개 `.vue`)와 줄 단위 대조.

**§7 트랙 B 체크리스트 항목(의존 `—`) — 전부 코드 반영 확인 ✅**

| 파일 | 검증 포인트(실코드 앵커) |
|---|---|
| TradingDiary | `entries=ref([])`(25)·`fetchOrders` 연동(73)·`pending.code`/`order_id` 전송(119~120)·빈/오류 상태(112·171) |
| StockDetail | `stockInfo=ref({...빈값})`(318)·종토방 `communityPosts=ref([])`+`fetchStockPosts`+`author_nickname`(208·495·499)·`fetchStockNews`(384)·`peers=ref([])`/`targetPrice=ref(null)`(377~378)·`curSym`(97)·`maxVolume`(152)·5분봉 라벨(433)·매도수량 `loadHolding`(212·309) |
| Holdings | `loadError` 배너(16·158)·`current_value` 합산(41·100)·바로가기 3개(내계좌/주문내역/매매일지, 188~196)·뉴스 `<a>` 링크화(298·415)·`hv-detail-actions`/`communityPost`/`*1380` 제거 확인 |
| Portfolio | `hasReport`(110)·`total ?? null`(116)·`g-none`(42·311)·'리포트 준비 중'(206)·`holdings=ref([])`(15)·`loadError`(12·151) |
| MyPage | address 제거(9)·`signedFmt`(88)·`trades=ref([])`/`tradesError`(45~46)·`realizedPnl`(64)·`birth_year` 편집(108·171)·투자성향 점수바 제거·`profileError`(93·390) |

**⚠ 작업기록에 미기재된 잔여 하드코딩(§7 트랙 B 범위 밖 — 후속 정리 후보)**
- **StockDetail 커뮤니티 '피드' 섹션**: `communityFeed` 목업 7건(399~407, 삼전/HBM 등)·`popularPosts` 하드코딩(414~418)·`addPost`는 로컬 `unshift`만(408~412, `createPost` 미연동). ※수정된 '종토방 탭'(`communityPosts`)과 **별개 UI**. §2-2/§7 미포함이라 미수정이나, 같은 목업 fallback 클래스라 기록 보강 차원에서 명시.
- **StockDetail 재무지표 카드**: `valuation`/`earningsMetrics`/`dividendMetrics`/`financials` ref 정적값(322~341, PER 14.2배 등). 트랙 C(Watchlist `summaries` 소비)와 같은 데이터 소스 과제.
- **StockDetail '수익성' 막대차트**: `profitability`/`profitDesc` 삼성 하드코딩(343~351). (작업기록 기존 명시 — BE `summaries[]`로 연동 가능)
- **MyPage**: 계좌요약(balance/판매수익/배당/이자)·보유현황·월별수익률·활동내역·커뮤니티 통계 여전히 정적/목업.

---

## 작업 로그

### ✅ TradingDiaryView.vue (P1)

- **로보스타 fallback 제거**: `entries` 초기값 목업 3건(로보스타/삼성/NVIDIA) 삭제 → `ref([])`. `loadDiaries`의 `if(items.length)` 조건부 덮어쓰기 제거 → 항상 `entries.value = items.map(mapDiary)` (DB 0건이면 정직하게 빈 목록).
- **주문내역 기반 작성대기**: `fetchOrders` import. 하드코딩 `pendingTrade('090360')` 제거 → `loadAll()`에서 주문목록 조회 후 **일기 미작성 주문(order_id 미연결)만** `pendingTrades`로 노출. 여러 건이면 칩으로 선택(`selectPending`).
- **신규 일기 종목 하드코딩 제거**: `createDiary`가 선택된 대기 주문의 `stock_code` + `order_id` 전송 → 더이상 '090360' 고정 아님. order_id 연결로 작성 후 자동으로 작성대기에서 빠짐.
- **빈/오류 상태**: 대기 0건이면 "작성할 매매 내역이 없어요" + 저장 버튼 disabled. `loadError` 배너 추가(기존엔 set만 하고 미표시).
- 보류: 목표/손절 % 저장(→A 단위 합의), 실현수익 actual(→A).
- **검증**: import 4종(`fetchDiaries`/`createDiary`/`updateDiary`, `fetchOrders`, `errMsg`) 실존 확인. BE 직렬화 일치 — Order(`side` BUY/SELL, `items` envelope, `id`/`stock_code`/`stock_name`/`created_at`/`executed_at`), Diary(`order_id` read_only 노출, `reason_category` required=False·allow_blank).

### ✅ StockDetailView.vue (P0·P1·P2)

- **삼성 하드코딩 제거 (P0)**: `stockInfo` 객체 리터럴(삼성 CEO/상장일/발행주식수/실제가치 등) → `ref` + `loadStock`에서 BE detail로 채움(`description`/`ceo_name`/`homepage_url`/`industry`/`listed_at`/`employee_count`). 종목정보 탭은 **BE에 있는 필드만** 조건부 표시, 없는 항목(실제가치/기업명/발행주식수)은 제거. 홈페이지 버튼 `<a :href>`(이전엔 무동작 button). '주요 사업'은 `industry` 사용.
- **종토방 목업 제거+필드매핑 (P1)**: `communityPosts` 목업 6건 → `ref([])`. `loadCommunity`가 `if(items.length)` 조건 제거하고 항상 교체. 필드 정정 — `author_nickname`(기존 `author?.nickname` 오류), 본문은 BE 미제공이라 **`title` 사용**(기존 `content`는 항상 빈값), `created_at`→`relTime()` 상대시간. 0건 빈 상태 추가.
- **매매시뮬 보유연동 (P1)**: `holdQty`/`holdAvg` 하드코딩(20/310500) 제거 → `loadHolding()`이 `fetchHoldingDetail`로 보유 수량·평단 프리필. 미보유/비로그인 catch 시 0.
- **매도 '최대'=보유수량 (P1)**: `setQtyPct`가 SELL이면 보유수량 기준, BUY면 잔고 기준으로 분기(기존엔 둘 다 잔고). 체결 후 `loadHolding` 재호출로 갱신.
- **뉴스 탭 연동 (P1)**: `stockNews` 목업 7건 → `ref([])` + `fetchStockNews` 연동. BE는 category/공시 구분 미제공이라 **필터 버튼 제거**, 각 기사 `<a :href target=_blank>` 원문 링크, 빈 상태 추가. 고아 CSS(`.news-filter`/`.news-cat`) 정리.
- **동종업계/목표주가 숨김 (P1)**: BE 데이터 소스 없음 → `peers=ref([])`, `targetPrice=ref(null)` + 패널 `v-if` 가드로 숨김(하드코딩 6행 제거).
- **5분봉 라벨 정정·거래량 클리핑 (P2)**: 차트 탭 '3분'(실제 5분봉 요청) → **'5분'**으로 라벨 정직화(`CHART_PARAM` 키 동기). 거래량 막대 분모 `100` 고정 → `maxVolume` computed(클리핑 제거). '거래량 (2억)' 고정 라벨 → '거래량'.
- **통화 ₩→currency (P2)**: `curSym` computed(USD=$/그외=₩) 추가. 헤더가·등락·키메트릭·현재가라벨·시뮬·주문총액·커뮤니티 사이드 가격에 적용(미국 종목 원화 오표기 방지).
- 보류(→A): 호가(orderbook 501), 매수 후 일지연동(order_id 핸드셰이크), 관심종목 추가 버튼(watchlist 모델).
- **범위 외 인지**: '수익성' 막대차트(`profitability`/`profitDesc`)는 삼성 하드코딩이나 §7 체크리스트 미포함이라 미수정(BE `summaries[]`로 후속 연동 가능). 시가총액 단위(조/억)는 KRW 가정 — USD 종목 단위는 별도 과제.
- **검증**: `npm run build` 성공(119 modules, 0 error). import(`fetchHoldingDetail`@portfolio, `fetchStockNews`@news) 실존 확인. BE 계약 일치 — StockDetail(`ceo_name`/`description`/`homepage_url`/`industry`/`employee_count`), Post(`author_nickname`/`title`/`created_at`/`like_count`, **본문 필드 없음**), StockNews(`{items:[{title,url,source,published_at}]}`), HoldingDetail(`{holding:{quantity,average_price}}`).

### ✅ HoldingsView.vue (P1·P2)

- **매수/매도 버튼 제거 (P1)**: 선택종목 상세의 `hv-detail-actions`(매수/매도, @click 없는 死버튼) 제거. 주문은 '종목 상세 보기 →'(`/stocks/:code`) 경로로 일원화. 고아 CSS(`.hv-detail-actions`/`.hv-buy`/`.hv-sell`) 정리.
- **바로가기 '내 계좌' 추가 (P1)**: 주문내역·매매일지 2개 → '내 계좌'(`/mypage`) 추가 3개. (전용 account 라우트 부재 → mypage로 연결.)
- **뉴스 클릭 이동 (P1)**: `hv-news-item`을 `<article>`→`<a :href target=_blank>`로 전환(기존 @click 없음). `loadHoldingNews` 매핑에 `url`·`code` 추가(기존엔 버림).
- **보유 없을 때 뉴스/커뮤니티 비노출 + 목업 제거 (P1)**: 뉴스 섹션 `v-if="holdings.length"`. 하드코딩 `communityPost`(TECL미친놈…) const·템플릿·CSS 전부 제거. 섹션명 '뉴스·커뮤니티'→'보유 종목 뉴스', 뉴스 0건 빈 상태 추가.
- **USD 통화 분열·총액 어긋남 (P2)**: 자산구성 `marketGroups`의 클라 환율 추정 `*1380` 제거 → 보유 매핑에 BE `current_value` 추가하고 그대로 합산. 좌측 요약(BE 합계)과 **동일 소스로 일치**. (BE는 `current_value = current_price*quantity`로 **환율 미적용** 확인 — KRW·USD 혼합 합산이라 절대 환산 정합은 track-A 과제로 명시.)
- **loadError 미표시 (P2)**: catch에서 set만 하던 `loadError`를 헤더 하단 배너로 표시. (보유 목록은 이미 `ref([])`+`retry`로 목업 fallback 없음.)
- 보류 없음(이 파일 →A 항목 없음).
- **검증**: `npm run build` 성공(119 modules, 0 error). BE 계약 — Holding(`current_value`/`quantity`/`average_price`/`current_price`), HoldingsNews(`{items:[{stock:{code,name},title,url,source,published_at}]}`). 라우트 `/mypage` 실존 확인.

### ✅ PortfolioView.vue (장투페이지) (P0·P1·P2)

- **리포트 없는 종목 0점/C 오표시 제거 (P0)**: 매핑 `total: r.total?.score ?? 0` → `?? null` + `hasReport` 플래그. `total()`/`grade()`/`gradeColor()`/`gradeClass()`가 null을 받으면 점수 `—`·등급 `—`·중립색(`g-none`) 반환(기존엔 null→0→파랑 C). 리스트·종합원형은 `?? '—'`/'분석중' 표시. 리포트 없으면 재무·성장·궁합 0점 카드 대신 **"리포트 준비 중" 안내 패널**(`v-if="s.hasReport"` else).
- **로드 실패 시 가짜 보유 제거 + loadError (P1)**: 초기 `holdings` 목업(SK하이닉스/삼성/NVIDIA/Apple 4종, ~145줄) → `ref([])`. 실패 시 catch가 빈 배열 유지(가짜 미노출). `loadError` 배너 추가(기존 set만 하고 미표시). `!s` 빈블록 메시지를 로딩/오류/무보유 3분기로 구분.
- **빈 배열 섹션 안내 (P2)**: 매매일지·점수 히스토리·뉴스 0행 시 각 섹션에 빈 상태 문구(`.lt-empty`) 추가(로딩실패/무데이터 구분).
- 보류(→A): 매매일지·장투점수 히스토리 **데이터 연동**(`journal`/`history` 항상 `[]` — diary/score-history API 연동은 A). 단 빈 상태 UI(위)는 FE로 선제 처리.
- **검증**: `npm run build` 성공(0 error, 목업 제거로 JS 337→331kB↓). BE 계약 — Holdings(`items[].stock`), LongtermReport(`total.score/label/opinion`·`financial.score/summary`·`growth`·`userfit.score/summary`, 미존재 시 null), Financials(`summaries[0]`·`indicator`), HoldingsNews(`stock.code`별 그룹핑).

### ✅ MyPageView.vue (P1·P2)

- **주소 항목 제거 (P2)**: BE User에 `address` 필드 자체가 없음 → reactive·기본정보 행 삭제.
- **phone/name/email 저장 안 됨 + 이름=닉네임 모순 (P2)**: BE는 `nickname`/`birth_year`만 수정 가능(`MeUpdateRequestSerializer`), User엔 name·phone 필드 없음. → **이름·휴대폰 행 제거**(name은 nickname 복제였음 — 모순 해소), **이메일 읽기전용**(수정 불가), 닉네임만 편집, 생년월일→**출생연도 편집**(birth_year 연동). "이메일·가입일은 변경 불가" 안내 추가. 헤더 이름도 nickname으로 통일.
- **이중부호 `+-` 렌더 (P1, §3)**: 이달수익·이달수익률·실현손익이 리터럴 `+` + `toLocaleString` 음수 `-` → `+-318400원`. → `signedFmt`/부호 조건부로 교체, 음수 시 `neg` 클래스. 실현손익 합계는 `realizedPnl` computed로 분리.
- **주문내역 폴백 오인 (P2)**: `trades` 목업 10건 → `ref([])`. `loadOrders`의 `if(items.length)` 제거(항상 교체), catch가 에러 삼키던 것 → `tradesError` 노출 + 빈/오류 행 표시(가짜 폴백 제거).
- **투자성향 점수 하드코딩 (P2)**: 안정성62/성장78/리스크45 바·고정 설명 → BE에 0~100 점수 없음(`investment_style` 타입 문자열만) → **점수 바 제거**, 타입 배지(실데이터)·일반 설명 유지. 미검사 시 안내 분기.
- **profileError 표시**: set만 하던 저장 오류를 프로필 섹션에 배너로 노출.
- 보류(→A): 투자성향 재검사 버튼(@click 미배선 유지 — BE 재제출 409 완화 필요, 정책 후 라우팅 연결).
- **범위 외 인지**: 계좌요약(balance/판매수익/배당/이자)·보유현황·월별수익률·활동내역·커뮤니티 통계(294 좋아요 등)는 여전히 목업이나 §7 트랙 B 미포함이라 미수정(account/holdings는 fetch 폴백, 나머지는 정적). 동일 fallback 패턴이라 후속 정리 대상.
- **검증**: `npm run build` 성공(0 error, JS 331→329kB↓). BE 계약 — User(`nickname`/`email`/`birth_year`/`date_joined`/`profile.investment_style`, 전부 read_only), MeUpdate(`nickname`/`birth_year`만), Order(`side`/`price`/`total_amount`/`realized_pnl`/`created_at`).

---

## A+B 통합 후 핸드셰이크 배선 (2026-06-24, `feature/semifinal-ab`)

> 트랙 A(`feature/semifinal-a`) 머지 후 BE 미완목록 재점검 + 풀린 항목 FE 연결.
> `accounts.0006/0007`(goal/seed_goals) 마이그레이션 적용 완료.

**BE 재점검 — '미완'이라 적었던 항목 대부분 실제로는 구현돼 있었음(정정):**
- ✅ **관심종목**: `UserLikedStock` 모델 + `/watchlist/` GET/POST/DELETE + detail `is_in_watchlist`(views.py:212, UserLikedStock 기반 정확 채움). (이전 "모델 없음" 판정은 오판 — 이름만 Watchlist가 아님)
- ✅ **매수→일지**: diary `order_id` 완전 지원.
- ✅ **재검사**: A가 409 가드 제거(accounts/views.py:277).
- ❌ **호가**: `StockOrderBookView.get`이 여전히 `return _stub()` = 501. **유일하게 진짜 미완** → 제거/구현 결정 대기.
- ⚠️ **일지/점수 히스토리**: `HoldingDetail`이 `recent_orders`/`related_diaries_count`/`review`만 제공. 종목별 일지 리스트·점수 시계열 직접 소스 없음(부분).
- ⚠️ **목표/손절 %**: 필드(target/stop_loss_price)는 있으나 %↔절대가 단위 합의 미정.
- ❌ **실현수익 actual**: diary 직렬화에 `realized_pnl` 없음.

**FE 배선 완료(3건):**
- **매수 후 매매일기 유도** — StockDetail `submitOrder` 성공 시 `cta` 플래그 + "📓 이 매매 일기 쓰러가기 →" 버튼으로 `/trading-diary` 라우팅(TradingDiary가 미작성 주문을 자동 노출). order_id 별도 전달 불요.
- **관심종목 토글** — StockDetail `watch-toggle-btn`에 `addWatchlist`/`removeWatchlist` 배선. `isWatched`(loadStock에서 `is_in_watchlist` 프리필) + 낙관적 토글·실패 시 별표 롤백. ★/☆ 상태 표시.
- **투자성향 재검사** — MyPage `retest-btn`에 `@click="router.push('/onboarding')"`(`useRouter` import 추가). 409 가드 제거로 재제출 가능.
- **검증**: `npm run build` 성공(119 modules, 0 error). 라우트 `/trading-diary`·`/onboarding` 실존. API `addWatchlist`/`removeWatchlist`(api/recommend.js) 실존.
- **남은 →A**: 호가(501 결정), 일지/점수 히스토리(부분 소스), 목표/손절 %(단위합의), 실현수익(realized_pnl 미노출).

