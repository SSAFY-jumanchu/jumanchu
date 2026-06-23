"""
매매 서비스 — 매수/매도 실행 + 미리보기(preview).

SCRUM-121. 핵심 학습: DB 트랜잭션(atomic / select_for_update / idempotency).
- preview_order : DB 변경 없이 체결 결과를 시뮬레이션 (읽기 전용)
- execute_buy   : 시장가 매수 — 잔액 차감 + 보유 갱신 + 주문 기록 (all-or-nothing)
- execute_sell  : 시장가 매도 — 실현손익 계산 + 잔액 증가 + 보유 차감

수수료는 정률(FEE_RATE), 세금(거래세)은 데모에서 0.
현재가는 stocks의 KIS 경로(fetch_price)를 재사용한다.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import requests
from django.db import IntegrityError, transaction
from django.utils import timezone

from portfolio.models import Account, Holding, Order
from stocks.models import Stock
from stocks.services.price_dispatch import fetch_price

# 수수료율 0.015% (팀 조정 가능). 세금(거래세)은 데모에서 0.
FEE_RATE = Decimal("0.00015")


def _fee(total: Decimal) -> Decimal:
    """체결금액(total)에 대한 수수료 — 원 단위 반올림."""
    return (total * FEE_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _round_won(value: Decimal) -> Decimal:
    """원 단위(1의 자리)로 반올림. 평균단가 등 가격에 사용."""
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# ───────────────────────── 예외 ─────────────────────────


class TradeError(Exception):
    """매매 실패의 베이스 예외 (view에서 적절한 HTTP status로 변환)."""


class StockNotFound(TradeError):
    """종목 코드에 해당하는 (활성) 종목이 없음."""


class InsufficientBalance(TradeError):
    """매수 시 잔액 부족."""


class InsufficientHolding(TradeError):
    """매도 시 보유 수량 부족."""


class PriceUnavailable(TradeError):
    """KIS 현재가 조회 실패 (외부 API 오류). view에서 503으로 변환."""


# ───────────────────────── 내부 헬퍼 ─────────────────────────


def _resolve_stock(stock_code: str) -> Stock:
    """종목 코드 → 활성 Stock. 없으면 StockNotFound."""
    stock = Stock.objects.filter(code=stock_code, is_active=True).first()
    if stock is None:
        raise StockNotFound(stock_code)
    return stock


def _current_price(stock: Stock) -> Decimal:
    """KIS 현재가(Decimal). 외부 API 오류는 PriceUnavailable로 감싼다.

    StockPriceView와 동일한 예외 집합을 잡아 도메인 예외로 변환 →
    view는 KIS 라이브러리 예외를 몰라도 됨(503만 처리).
    """
    try:
        return fetch_price(stock)["current"]
    except (requests.HTTPError, requests.Timeout, RuntimeError, KeyError,
            ValueError, InvalidOperation) as exc:
        raise PriceUnavailable(stock.code) from exc


def _holding_snapshot(
    stock: Stock,
    quantity: int,
    average_price: Decimal,
    current_price: Decimal,
    first_acquired_at=None,
    updated_at=None,
) -> dict:
    """HoldingSerializer 모양의 보유 스냅샷 dict (preview·execute 응답 공용).

    저장하지 않은 가상 보유 상태를 직렬화하기 위한 dict.
    평가손익/수익률은 현재가(current_price) 기준으로 계산한다.
    """
    total_invested = average_price * quantity
    current_value = current_price * quantity
    profit_loss = current_value - total_invested
    profit_loss_rate = (
        float(profit_loss / total_invested * 100) if total_invested > 0 else 0.0
    )
    return {
        "stock": stock,
        "quantity": quantity,
        "average_price": average_price,
        "total_invested": total_invested,
        "current_price": current_price,
        "current_value": current_value,
        "profit_loss": profit_loss,
        "profit_loss_rate": profit_loss_rate,
        "first_acquired_at": first_acquired_at,
        "updated_at": updated_at,
    }


# ───────────────────────── preview (읽기 전용) ─────────────────────────


def preview_order(user, stock_code: str, side: str, quantity: int) -> dict:
    """매매를 실제로 실행하지 않고 결과만 시뮬레이션한다 (DB 변경 없음).

    반환: OrderPreviewResponseSerializer 모양 dict
        {"is_valid": bool, "errors": [str], "preview": {OrderPreviewBodySerializer ...}}

    - 매수(BUY): 추가매수 후 새 평균단가(avg_price_after) + 미실현 평가수익률(holding_after)
    - 매도(SELL): 실현손익(realized_profit) + 실현 수익률(realized_profit_rate)
    """
    stock = _resolve_stock(stock_code)
    price = _current_price(stock)  # KIS 현재가(Decimal). 실패 시 PriceUnavailable → view 503
    total = price * quantity
    fee = _fee(total)

    account = Account.objects.get(user=user)
    holding = Holding.objects.filter(user=user, stock=stock).first()

    errors: list[str] = []
    body = {
        "stock_code": stock.code,
        "stock_name": stock.name,
        "side": side,
        "quantity": quantity,
        "current_price": price,
        "estimated_total": total,
        "estimated_fee": fee,
        "balance_after": account.balance,
        "holding_after": None,
        "avg_price_after": None,
        "realized_profit": None,
        "realized_profit_rate": None,
    }

    if side == Order.Side.BUY:
        need = total + fee
        body["balance_after"] = account.balance - need
        if account.balance < need:
            errors.append("잔액이 부족합니다.")

        old_qty = holding.quantity if holding else 0
        old_avg = holding.average_price if holding else Decimal("0")
        new_qty = old_qty + quantity
        new_avg = _round_won((old_avg * old_qty + total) / new_qty)  # 가중평균(원 단위)
        body["avg_price_after"] = new_avg
        body["holding_after"] = _holding_snapshot(
            stock, new_qty, new_avg, price,
            first_acquired_at=holding.first_acquired_at if holding else None,
        )
    else:  # SELL
        body["balance_after"] = account.balance + (total - fee)
        if holding is None or holding.quantity < quantity:
            errors.append("보유 수량이 부족합니다.")
        if holding is not None:
            avg = holding.average_price
            body["realized_profit"] = (price - avg) * quantity
            body["realized_profit_rate"] = (
                float((price - avg) / avg * 100) if avg > 0 else 0.0
            )
            remaining = holding.quantity - quantity
            if remaining > 0:
                body["holding_after"] = _holding_snapshot(
                    stock, remaining, avg, price,
                    first_acquired_at=holding.first_acquired_at,
                )

    return {"is_valid": not errors, "errors": errors, "preview": body}


# ───────────────────────── execute (DB 변경) ─────────────────────────


def execute_buy(user, stock_code: str, quantity: int, idempotency_key: str) -> dict:
    """시장가 매수 — 잔액 차감 + 보유 갱신 + 주문 기록을 한 트랜잭션으로 처리.

    반환: OrderCreateResponseSerializer 모양 dict {order, balance_after, holding_after}.
    balance_after/holding_after는 트랜잭션 안(잠금 보유 중)에서 확정하므로,
    같은 유저의 동시 매매가 끼어들어도 "이 주문 직후" 상태를 정확히 반영한다.

    안전장치 3종:
    - transaction.atomic : 잔액/보유/주문 변경이 all-or-nothing (중간 실패 시 전부 롤백)
    - select_for_update  : Account 행을 잠가 동시 매수 race condition 방지
    - idempotency_key    : 같은 주문 중복 요청 시 한 번만 체결 (선검사 + unique 제약)
    """
    # 멱등 선검사: 이미 처리된 주문이면 재처리하지 않고 현재 상태로 반환
    existing = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing is not None:
        return order_result(existing)

    stock = _resolve_stock(stock_code)
    price = _current_price(stock)
    total = price * quantity
    fee = _fee(total)
    need = total + fee

    try:
        with transaction.atomic():
            account = Account.objects.select_for_update().get(user=user)  # 행 잠금
            if account.balance < need:
                raise InsufficientBalance(f"잔액 부족: 보유 {account.balance}, 필요 {need}")
            account.balance -= need
            account.save(update_fields=["balance", "updated_at"])

            holding = (
                Holding.objects.select_for_update().filter(user=user, stock=stock).first()
            )
            if holding is not None:
                new_qty = holding.quantity + quantity
                holding.average_price = _round_won(
                    (holding.average_price * holding.quantity + total) / new_qty
                )  # 가중평균(원 단위)
                holding.quantity = new_qty
                holding.save(update_fields=["quantity", "average_price", "updated_at"])
            else:
                # 최초 매수 — 장투 재검증 기준점(PBR·궁합)을 이 순간으로 박제(고정).
                base_pbr, base_match = _buy_snapshot(user, stock)
                holding = Holding.objects.create(
                    user=user,
                    stock=stock,
                    quantity=quantity,
                    average_price=_round_won(total / quantity),
                    base_pbr=base_pbr,
                    base_match_score=base_match,
                )

            order = Order.objects.create(
                user=user,
                account=account,
                stock=stock,
                side=Order.Side.BUY,
                quantity=quantity,
                price=price,
                total_amount=total,
                fee=fee,
                tax=Decimal("0"),
                realized_pnl=None,  # 매수는 실현손익 없음
                status=Order.Status.FILLED,
                executed_at=timezone.now(),
                idempotency_key=idempotency_key,
            )
            # 잠금 보유 중(트랜잭션 안)에 응답 스냅샷 확정 → 동시 매매와 무관하게 정확
            return _build_result(order, account.balance, holding)
    except IntegrityError:
        # 동시 요청이 같은 idempotency_key로 먼저 커밋 → 이 트랜잭션은 롤백됨
        # (잔액/보유 변경도 함께 롤백되어 이중 체결 없음). 기존 주문을 반환.
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            return order_result(existing)
        raise


def execute_sell(user, stock_code: str, quantity: int, idempotency_key: str) -> dict:
    """시장가 매도 — 실현손익 계산 + 잔액 증가 + 보유 차감을 한 트랜잭션으로 처리.

    반환은 execute_buy와 동일한 OrderCreateResponseSerializer 모양 dict.
    안전장치(atomic / select_for_update / idempotency)와 락 순서(account→holding)도 동일.
    """
    existing = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing is not None:
        return order_result(existing)

    stock = _resolve_stock(stock_code)
    price = _current_price(stock)
    total = price * quantity
    fee = _fee(total)
    proceeds = total - fee  # 매도 대금에서 수수료를 떼고 입금

    try:
        with transaction.atomic():
            account = Account.objects.select_for_update().get(user=user)  # 락 순서: account 먼저
            holding = (
                Holding.objects.select_for_update().filter(user=user, stock=stock).first()
            )
            if holding is None or holding.quantity < quantity:
                have = holding.quantity if holding is not None else 0
                raise InsufficientHolding(f"보유 부족: 보유 {have}, 매도 {quantity}")

            # 실현손익 = (체결가 - 평균매입가) × 수량 (ERD 정의, 수수료/세금 제외 gross)
            realized = (price - holding.average_price) * quantity

            account.balance += proceeds
            account.save(update_fields=["balance", "updated_at"])

            remaining = holding.quantity - quantity
            if remaining == 0:
                holding.delete()  # 다 팔면 보유 행 제거
                holding = None    # 응답 holding_after = None
            else:
                holding.quantity = remaining  # 평균단가는 매도해도 불변
                holding.save(update_fields=["quantity", "updated_at"])

            order = Order.objects.create(
                user=user,
                account=account,
                stock=stock,
                side=Order.Side.SELL,
                quantity=quantity,
                price=price,
                total_amount=total,
                fee=fee,
                tax=Decimal("0"),
                realized_pnl=realized,
                status=Order.Status.FILLED,
                executed_at=timezone.now(),
                idempotency_key=idempotency_key,
            )
            return _build_result(order, account.balance, holding)
    except IntegrityError:
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            return order_result(existing)
        raise


def _build_result(order: Order, balance_after, holding) -> dict:
    """OrderCreateResponseSerializer 모양 dict.

    현재가는 방금 체결가(order.price)를 써서 KIS 재호출을 피한다.
    holding이 None이면(다 팔았거나 보유 없음) holding_after=None.
    """
    holding_after = None
    if holding is not None:
        holding_after = _holding_snapshot(
            order.stock,
            holding.quantity,
            holding.average_price,
            order.price,
            first_acquired_at=holding.first_acquired_at,
            updated_at=holding.updated_at,
        )
    return {"order": order, "balance_after": balance_after, "holding_after": holding_after}


def order_result(order: Order) -> dict:
    """멱등 재요청(이미 처리된 주문) 응답용 — 현재 DB 상태를 echo.

    원래 체결 시점의 잔액은 따로 저장하지 않으므로, 재요청 시엔 현재 잔액/보유를 보여준다.
    신규 체결 응답은 execute_buy/sell이 트랜잭션 안에서 _build_result로 직접 만든다.
    """
    account = Account.objects.get(user=order.user)
    holding = Holding.objects.filter(user=order.user, stock=order.stock).first()
    return _build_result(order, account.balance, holding)


# ───────────────────────── 장투 재검증 (보유 기준) ─────────────────────────


def _buy_snapshot(user, stock) -> tuple[Decimal | None, Decimal | None]:
    """최초 매수 시점 스냅샷 — (base_pbr, base_match_score). 입력이 없으면 None.

    base_pbr        : 최신 StockIndicator.pbr (재검증 ±30% 기준점)
    base_match_score: 온보딩 프로필 + 종목 DNA가 있을 때만 궁합 점수, 없으면 None.
    recommend/accounts는 lazy import (앱 간 순환 방지 — recommend가 portfolio를 참조).
    """
    from accounts.models import UserPreferredSector
    from recommend.matching import compute_match_score
    from recommend.models import StockDna

    ind = stock.indicators.order_by("-calculated_date").first()
    base_pbr = None if (ind is None or ind.pbr is None) else Decimal(str(ind.pbr))

    base_match = None
    profile = getattr(user, "investment_profile", None)
    if profile is not None and profile.profiled_at is not None:
        dna = StockDna.objects.filter(stock=stock).order_by("-calculated_date").first()
        if dna is not None:
            weights = {
                p.sector: float(p.weight)
                for p in UserPreferredSector.objects.filter(user=user)
            }
            base_match = Decimal(str(round(compute_match_score(profile, dna, weights), 2)))
    return base_pbr, base_match


def review_holding(holding) -> dict:
    """보유 종목 장투 재검증 — 4지표 위반수 → 🟢🟡🔴 (docs/추천_장투_DB결정.md §3-4).

    위반: ROE<10% · 부채비율>200% · 순이익증가율<=0% · |현재PBR-매수PBR|/매수PBR>30%
    지표는 fraction 저장(0.10=10%)이라 %로 비교할 땐 ×100. 결과를 holding에 저장하고 dict 반환.
    """
    stock = holding.stock
    ind = stock.indicators.order_by("-calculated_date").first()
    fs = stock.financials.order_by("-fiscal_period").first()

    # 지표·재무가 둘 다 없으면 판정 불가 — 거짓 🟢 방지
    if ind is None and fs is None:
        holding.last_review_status = ""
        holding.last_reviewed_at = timezone.now()
        holding.save(update_fields=["last_review_status", "last_reviewed_at"])
        return {"status": "", "violations": ["판정에 필요한 지표/재무 데이터가 없습니다."],
                "checked_at": holding.last_reviewed_at}

    violations: list[str] = []
    roe = ind.roe if ind else None
    if roe is not None and roe * 100 < 10:
        violations.append("ROE 10% 미만")
    debt = fs.debt_ratio if fs else None
    if debt is not None and debt * 100 > 200:
        violations.append("부채비율 200% 초과")
    npy = fs.net_profit_yoy if fs else None
    if npy is not None and npy <= 0:
        violations.append("순이익 증가율 0 이하")
    cur_pbr = ind.pbr if ind else None
    if holding.base_pbr is not None and cur_pbr is not None and float(holding.base_pbr) > 0:
        drift = abs(cur_pbr - float(holding.base_pbr)) / float(holding.base_pbr)
        if drift > 0.30:
            violations.append("PBR이 매수 시점 대비 ±30% 이탈")

    n = len(violations)
    if n == 0:
        st = Holding.ReviewStatus.GREEN
    elif n <= 2:
        st = Holding.ReviewStatus.YELLOW
    else:
        st = Holding.ReviewStatus.RED

    holding.last_review_status = st
    holding.last_reviewed_at = timezone.now()
    holding.save(update_fields=["last_review_status", "last_reviewed_at"])
    return {"status": st, "violations": violations, "checked_at": holding.last_reviewed_at}


# ───────────────────────── 포트폴리오 조회 (읽기 전용) ─────────────────────────


def _priced_holdings(user) -> list:
    """유저 보유 종목을 현재가로 평가한 스냅샷 리스트(HoldingSerializer 모양)."""
    holdings = Holding.objects.filter(user=user).select_related("stock")
    return [
        _holding_snapshot(
            h.stock,
            h.quantity,
            h.average_price,
            _current_price(h.stock),
            first_acquired_at=h.first_acquired_at,
            updated_at=h.updated_at,
        )
        for h in holdings
    ]


def _sum(items, key) -> Decimal:
    """스냅샷 리스트에서 특정 키의 Decimal 합계."""
    total = Decimal("0")
    for it in items:
        total += it[key]
    return total


def _pct(value, total) -> float:
    """value / total 백분율. total이 0 이하면 0.0."""
    return float(value / total * 100) if total > 0 else 0.0


def portfolio_summary(user) -> dict:
    """홈 위젯용 통합 조회 — 총 평가/손익 + 총자산 + 보유 미리보기(평가액 상위 5)."""
    items = _priced_holdings(user)
    total_invested = _sum(items, "total_invested")
    total_current_value = _sum(items, "current_value")
    total_profit_loss = total_current_value - total_invested
    account = Account.objects.get(user=user)
    preview = sorted(items, key=lambda h: h["current_value"], reverse=True)[:5]
    return {
        "account": account,
        "total_invested": total_invested,
        "total_current_value": total_current_value,
        "total_profit_loss": total_profit_loss,
        "total_profit_loss_rate": _pct(total_profit_loss, total_invested),
        "total_assets": account.balance + total_current_value,
        "holdings_count": len(items),
        "holdings_preview": preview,
        "generated_at": timezone.now(),
    }


_HOLDING_SORT_KEYS = {
    "value": lambda h: h["current_value"],
    "profit_loss": lambda h: h["profit_loss"],
    "profit_loss_rate": lambda h: h["profit_loss_rate"],
    "code": lambda h: h["stock"].code,
}


def holdings_list(user, sort: str = "value", order: str = "desc") -> dict:
    """보유 종목 리스트 — 정렬(sort/order) + 합계."""
    items = _priced_holdings(user)
    keyfn = _HOLDING_SORT_KEYS.get(sort, _HOLDING_SORT_KEYS["value"])
    items.sort(key=keyfn, reverse=(order != "asc"))
    total_invested = _sum(items, "total_invested")
    total_current_value = _sum(items, "current_value")
    return {
        "items": items,
        "total_count": len(items),
        "total_invested": total_invested,
        "total_current_value": total_current_value,
        "total_profit_loss": total_current_value - total_invested,
        "generated_at": timezone.now(),
    }


def holding_detail(user, stock_code: str):
    """특정 종목 보유 상세 — 평가 + 거래 수 + 최근 주문 + 일기 수.

    종목 자체가 없으면 StockNotFound, 보유는 안 했으면 None(view에서 404).
    """
    from diary.models import StockDiary  # 지연 import(앱 간 순환 방지)

    stock = _resolve_stock(stock_code)
    holding = Holding.objects.filter(user=user, stock=stock).first()
    if holding is None:
        return None

    snapshot = _holding_snapshot(
        stock,
        holding.quantity,
        holding.average_price,
        _current_price(stock),
        first_acquired_at=holding.first_acquired_at,
        updated_at=holding.updated_at,
    )
    orders = Order.objects.filter(user=user, stock=stock).order_by("-created_at")
    return {
        "holding": snapshot,
        "transaction_count": orders.count(),
        "recent_orders": list(orders[:10]),
        "related_diaries_count": StockDiary.objects.filter(user=user, stock=stock).count(),
        "review": review_holding(holding),  # 보유 기준 장투 재검증 🟢🟡🔴
    }


def allocation(user) -> dict:
    """자산 배분 — 섹터/종목별 비중 + 현금 비중 (모두 총자산 기준, 합 ≈ 100%)."""
    items = _priced_holdings(user)
    account = Account.objects.get(user=user)
    total_value = _sum(items, "current_value")        # 주식 평가액 합
    total_assets = total_value + account.balance       # 현금 포함

    by_stock = [
        {
            "stock_code": h["stock"].code,
            "stock_name": h["stock"].name,
            "value": h["current_value"],
            "rate": _pct(h["current_value"], total_assets),
        }
        for h in items
    ]

    sector_value: dict = {}
    for h in items:
        sec = h["stock"].sector or "기타"
        sector_value[sec] = sector_value.get(sec, Decimal("0")) + h["current_value"]
    by_sector = [
        {"sector": sec, "value": val, "rate": _pct(val, total_assets)}
        for sec, val in sector_value.items()
    ]

    return {
        "total_value": total_value,
        "by_sector": by_sector,
        "by_stock": by_stock,
        "cash_rate": _pct(account.balance, total_assets),
    }
