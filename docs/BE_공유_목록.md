# BE 공유 목록 (FE 통합 작업 → 강재민)

> 작성: 2026-06-24 · 브랜치: `feature/semifinal-ab` · 작성자: 정율(통합)
> 이번 세션에서 **FE 통합 중 BE를 일부 직접 수정**했습니다. 충돌 방지 + 마이그레이션 공유용.

---

## 1. 내가 수정한 BE 코드 (3파일 14줄, 전부 additive — 기존 동작 안 깨짐)

| 파일 | 변경 | 이유(FE 연동) |
|---|---|---|
| `community/views.py` | `PostListCreateView.get`에 `?mine=true` 필터(+3줄) | 마이페이지 "내가 쓴 글"만 조회 |
| `portfolio/serializers.py` | `OrderSerializer`에 `market`/`currency` 추가(+3줄, `stock.market`/`stock.currency` 소스) | 마이페이지 거래내역 **국내/해외 구분** |
| `diary/models.py` | `ReasonCategory`에 **매도 사유 6종 추가**(+8줄) | 매매일기 매도 기록용 사유 |

### 1-1. `mine` 필터 (community/views.py)
```python
if p.get('mine') in ('1', 'true', 'True') and request.user.is_authenticated:
    qs = qs.filter(user=request.user)
```
+ `OpenApiParameter('mine', bool, required=False, ...)` 파라미터 1줄.

### 1-2. Order market/currency (portfolio/serializers.py)
```python
market = serializers.CharField(source='stock.market', read_only=True)
currency = serializers.CharField(source='stock.currency', read_only=True)
# fields 리스트에 'market', 'currency' 추가
```

### 1-3. 매도 사유 enum (diary/models.py `ReasonCategory`)
```python
# 매도 사유(결과 기록) — 신규
TARGET_HIT = "TARGET_HIT", "목표 달성"
STOP_LOSS = "STOP_LOSS", "손절"
PROFIT_TAKING = "PROFIT_TAKING", "차익 실현"
DETERIORATED = "DETERIORATED", "펀더멘털 악화"
BETTER_OPP = "BETTER_OPP", "더 좋은 기회"
REBALANCE = "REBALANCE", "리밸런싱"
```

---

## 2. ⚠️ 마이그레이션 (pull 후 **migrate 필수**)

```
diary/migrations/0004_alter_stockdiary_reason_category.py  (신규)
```
- `ReasonCategory` choices 변경(AlterField) — DB 스키마 무변경(no-op)이나 상태 일관성 위해 필요.
- **다른 팀원: `git pull` 후 `python manage.py migrate` 한 번** 돌리면 됨.
- ※ 마이그레이션을 두 사람이 동시에 만들지 않도록, 이 파일은 그대로 두세요.

---

## 3. 환경설정 (.env) — 코드 아님, 각자 로컬

- KIS 매수/시세가 **503(EGW02004)** 나면: `.env`의 KIS 앱키가 **모의투자(VTS)** 키인데 코드가 실전(prod)으로 호출해서임.
- **해결: `.env`에 `KIS_ENV=virtual` 추가** 후 백엔드 재시작.
- 실전 키를 쓸 거면 반대로 키를 실전용으로 교체. (배포 환경도 동일하게 맞춰야 함)

---

## 4. BE에 추가로 요청할 것 (아직 미구현 — FE는 빈 상태/숨김 처리해둠)

| 우선 | 항목 | 현재 BE | 요청 |
|---|---|---|---|
| **발표 필수** | 호가창 | `StockOrderBookView`가 `_stub()` = **501** | 구현 or "FE 호가 패널 제거" 결정 |
| 선택 | 장투 점수 히스토리 | 종목별 점수 **시계열 API 없음** | 있으면 장투 페이지 히스토리 차트 채움 |
| 선택 | 매매일기 실현수익 | diary 직렬화에 `realized_pnl` 없음 | diary 응답에 추가 시 일지에 실현손익 표시 |
| 선택 | 환율 정합 | `total_assets`/`total_current_value`가 KRW+USD **단순합**(환율 미적용) | 해외 평가액 원화 환산(국내+해외 합산 정확도) |

---

## 5. 참고: FE가 의존하는 기존 BE 계약 (이미 구현됨, 변경 금지 요망)

- `GET /portfolio/` → `total_assets`/`total_current_value`/`total_invested`/`total_profit_loss(_rate)`/`account.balance` (마이페이지 내 투자)
- `GET /portfolio/holdings/` → `items[].stock.market`/`currency`/`current_value`/`profit_loss(_rate)` (보유 국내/해외)
- `GET /orders/` → 위 1-2의 `market`/`currency` 포함 (거래내역 국내/해외)
- `GET /posts/?mine=true` → 위 1-1 (활동 내역)
- `GET /watchlist/` (recommend, `UserLikedStock`) + detail `is_in_watchlist` → 관심종목 토글 (종목 상세)
- `POST /orders/` → `order.id` → 매수 후 매매일기 라우팅
- `diary` `order_id` 핸드셰이크 + 위 1-3 매도 사유 enum
- 온보딩 재검사: 409 가드 제거됨(accounts/views) → 재검사 버튼 동작

---

## 6. 한 줄 요약
- **migrate 1개**(diary 0004) + **`.env`에 `KIS_ENV=virtual`** 두 가지만 각자 챙기면 동작.
- BE 신규 작업으로 남은 건 사실상 **호가(orderbook) 하나**.
