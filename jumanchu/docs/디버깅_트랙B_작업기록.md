# 트랙 B 디버깅 작업 기록 (BE 독립 항목)

> 브랜치: `feature/semifinal-b` · 담당: 정율(B) · 작성: 2026-06-23
> 근거: `docs/디버깅_통합리스트.md` §7 트랙 B 체크리스트
> 원칙: **A·C 트랙에 영향 없는 전용 파일만 수정** (StockDetail / Holdings / Portfolio / TradingDiary / MyPage)
> 범위: 의존 `—`(순수 FE) 항목만 우선. `→A`(BE 선행) 항목은 BE 완료 후로 보류.

## 보류 항목 (→A 의존, 이번 작업 제외)

| 항목 | 파일 | 사유 |
|---|---|---|
| 호가 하드코딩 제거 | StockDetail | BE orderbook 구현/결정 필요 |
| 매수 후 매매일지 자동연동 | StockDetail | A 트랙 order_id 핸드셰이크 |
| 관심종목 추가 버튼 | StockDetail | A watchlist 모델 신설 필요 |
| 매매일지·장투점수 히스토리 | Portfolio | A diary/score-history 연동 |
| 목표/손절 % 저장 | TradingDiary | A와 단위 정의 합의 필요 |
| 투자성향 재검사 버튼 | MyPage | A 409 완화 정책 필요 |

---

## 작업 로그

### ✅ TradingDiaryView.vue (P1)

- **로보스타 fallback 제거**: `entries` 초기값 목업 3건(로보스타/삼성/NVIDIA) 삭제 → `ref([])`. `loadDiaries`의 `if(items.length)` 조건부 덮어쓰기 제거 → 항상 `entries.value = items.map(mapDiary)` (DB 0건이면 정직하게 빈 목록).
- **주문내역 기반 작성대기**: `fetchOrders` import. 하드코딩 `pendingTrade('090360')` 제거 → `loadAll()`에서 주문목록 조회 후 **일기 미작성 주문(order_id 미연결)만** `pendingTrades`로 노출. 여러 건이면 칩으로 선택(`selectPending`).
- **신규 일기 종목 하드코딩 제거**: `createDiary`가 선택된 대기 주문의 `stock_code` + `order_id` 전송 → 더이상 '090360' 고정 아님. order_id 연결로 작성 후 자동으로 작성대기에서 빠짐.
- **빈/오류 상태**: 대기 0건이면 "작성할 매매 내역이 없어요" + 저장 버튼 disabled. `loadError` 배너 추가(기존엔 set만 하고 미표시).
- 보류: 목표/손절 % 저장(→A 단위 합의), 실현수익 actual(→A).
</content>
</invoke>
