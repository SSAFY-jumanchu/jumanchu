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
from django.db import transaction

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
