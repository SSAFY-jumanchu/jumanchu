"""
VirtualBroker - 나만의 가상 트레이딩 환경
==========================================

KIS Open API의 시세 데이터를 받아 와서, 매매·체결·자산 관리는
본인 코드 안에서 직접 시뮬레이션하는 가상 브로커입니다.

KIS 모의투자와의 차이
---------------------
- KIS 모의투자: 주문도 KIS 서버가 처리. 규칙 변경 불가.
- VirtualBroker: KIS는 시세만 제공. 체결 로직·수수료·세금·매매 규칙을
  모두 본인이 정의 가능. 백테스트, 강화학습, 자동매매 전략 검증에 적합.

지원 기능
---------
1) 시장가 주문 (즉시 체결, 현재가 기준)
2) 지정가 주문 (호가 1차와 비교하여 체결 가능 여부 판정)
3) 보유 종목·평균단가·실현손익 자동 계산
4) 매매 수수료 + 매도 거래세 반영 (값은 인자로 조정 가능)
5) JSON 파일로 상태 저장/복원
6) 포트폴리오 요약 리포트

의존성
------
- 동일 디렉토리의 kis_domestic_quote.py 사용
- requests
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from kis_domestic_quote import KISDomesticQuote


# ---------------------------------------------------------------------------
# 1. 도메인 모델
# ---------------------------------------------------------------------------

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"  # 시장가
    LIMIT = "LIMIT"    # 지정가


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Position:
    """보유 종목 한 건."""
    code: str
    qty: int = 0
    avg_price: float = 0.0          # 평균 매입 단가
    realized_pnl: float = 0.0       # 누적 실현손익

    def market_value(self, current_price: float) -> float:
        return self.qty * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        return self.qty * (current_price - self.avg_price)


@dataclass
class Order:
    order_id: str
    code: str
    side: Side
    order_type: OrderType
    qty: int
    price: Optional[float]          # 시장가면 None
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_at: Optional[str] = None
    reason: str = ""                # 거절 사유 등 메모
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# 2. VirtualBroker
# ---------------------------------------------------------------------------

class VirtualBroker:
    """가상 브로커. 시세는 KIS API에서, 체결은 내부 시뮬레이션."""

    def __init__(
        self,
        quote_client: KISDomesticQuote,
        initial_cash: float = 10_000_000,
        commission_rate: float = 0.00015,   # 매매 수수료 0.015%
        sell_tax_rate: float = 0.0018,      # 매도 거래세 0.18% (시점에 따라 조정)
    ):
        self.quote = quote_client
        self.cash = float(initial_cash)
        self.initial_cash = float(initial_cash)
        self.commission_rate = commission_rate
        self.sell_tax_rate = sell_tax_rate
        self.positions: dict[str, Position] = {}
        self.orders: list[Order] = []
        self._order_seq = 0

    # ------------------------------------------------------------------
    # 2-1. 주문 인터페이스
    # ------------------------------------------------------------------
    def buy_market(self, code: str, qty: int) -> Order:
        return self._place_and_try_fill(code, Side.BUY, OrderType.MARKET, qty, None)

    def sell_market(self, code: str, qty: int) -> Order:
        return self._place_and_try_fill(code, Side.SELL, OrderType.MARKET, qty, None)

    def buy_limit(self, code: str, qty: int, price: float) -> Order:
        return self._place_and_try_fill(code, Side.BUY, OrderType.LIMIT, qty, price)

    def sell_limit(self, code: str, qty: int, price: float) -> Order:
        return self._place_and_try_fill(code, Side.SELL, OrderType.LIMIT, qty, price)

    def cancel(self, order_id: str) -> bool:
        for o in self.orders:
            if o.order_id == order_id and o.status == OrderStatus.PENDING:
                o.status = OrderStatus.CANCELLED
                return True
        return False

    def _new_order_id(self) -> str:
        self._order_seq += 1
        return f"VBO-{datetime.now():%Y%m%d}-{self._order_seq:05d}"

    # ------------------------------------------------------------------
    # 2-2. 체결 엔진
    # ------------------------------------------------------------------
    def _place_and_try_fill(
        self,
        code: str,
        side: Side,
        order_type: OrderType,
        qty: int,
        price: Optional[float],
    ) -> Order:
        if qty <= 0:
            raise ValueError("qty는 1 이상이어야 합니다.")
        order = Order(self._new_order_id(), code, side, order_type, qty, price)
        self.orders.append(order)
        self._try_fill(order)
        return order

    def _try_fill(self, order: Order) -> None:
        """체결 시뮬레이션 규칙
        - MARKET: 현재가(stck_prpr) 기준으로 즉시 체결
        - LIMIT BUY: 매도1호가(askp1) <= 지정가 면 매도1호가에 체결
        - LIMIT SELL: 매수1호가(bidp1) >= 지정가 면 매수1호가에 체결
        - 호가 잔량은 시뮬레이션 단순화를 위해 무한대로 가정
        """
        if order.order_type == OrderType.MARKET:
            current = float(self.quote.get_current_price(order.code)["output"]["stck_prpr"])
            self._fill(order, current)
            return

        # LIMIT
        book = self.quote.get_order_book(order.code)["output1"]
        askp1 = float(book["askp1"])  # 최우선 매도호가
        bidp1 = float(book["bidp1"])  # 최우선 매수호가
        assert order.price is not None

        if order.side == Side.BUY and askp1 > 0 and askp1 <= order.price:
            self._fill(order, askp1)
        elif order.side == Side.SELL and bidp1 > 0 and bidp1 >= order.price:
            self._fill(order, bidp1)
        # 그렇지 않으면 PENDING 상태로 남아 다음 process_pending_orders 호출 때 재시도

    def process_pending_orders(self) -> int:
        """현재 시세 기준으로 대기 중인 지정가 주문을 재평가. 체결된 건수 반환."""
        filled = 0
        for o in list(self.orders):
            if o.status == OrderStatus.PENDING:
                self._try_fill(o)
                if o.status == OrderStatus.FILLED:
                    filled += 1
        return filled

    def _fill(self, order: Order, fill_price: float) -> None:
        """실제 체결 처리: 현금·포지션 갱신 + 수수료/세금 반영."""
        gross = fill_price * order.qty
        commission = gross * self.commission_rate

        if order.side == Side.BUY:
            cost = gross + commission
            if cost > self.cash:
                order.status = OrderStatus.REJECTED
                order.reason = f"현금 부족: 필요 {cost:,.0f} / 보유 {self.cash:,.0f}"
                return
            self.cash -= cost
            pos = self.positions.setdefault(order.code, Position(code=order.code))
            new_qty = pos.qty + order.qty
            pos.avg_price = (pos.avg_price * pos.qty + fill_price * order.qty) / new_qty
            pos.qty = new_qty

        else:  # SELL
            pos = self.positions.get(order.code)
            if not pos or pos.qty < order.qty:
                order.status = OrderStatus.REJECTED
                order.reason = f"보유수량 부족: 매도 {order.qty} / 보유 {pos.qty if pos else 0}"
                return
            tax = gross * self.sell_tax_rate
            proceeds = gross - commission - tax
            self.cash += proceeds
            pos.realized_pnl += (fill_price - pos.avg_price) * order.qty - commission - tax
            pos.qty -= order.qty
            if pos.qty == 0:
                pos.avg_price = 0.0  # 전량 매도 시 평단 리셋(실현손익은 유지)

        order.status = OrderStatus.FILLED
        order.filled_price = fill_price
        order.filled_at = datetime.now().isoformat()

    # ------------------------------------------------------------------
    # 2-3. 포트폴리오 리포트
    # ------------------------------------------------------------------
    def portfolio_summary(self) -> dict:
        """현재 시세 기준 포트폴리오 요약."""
        rows = []
        total_market_value = 0.0
        total_unrealized = 0.0
        total_realized = 0.0
        for code, pos in self.positions.items():
            if pos.qty == 0 and pos.realized_pnl == 0:
                continue
            current = 0.0
            if pos.qty > 0:
                current = float(self.quote.get_current_price(code)["output"]["stck_prpr"])
            mv = pos.market_value(current)
            upl = pos.unrealized_pnl(current)
            total_market_value += mv
            total_unrealized += upl
            total_realized += pos.realized_pnl
            rows.append({
                "code": code,
                "qty": pos.qty,
                "avg_price": round(pos.avg_price, 2),
                "current_price": current,
                "market_value": round(mv, 0),
                "unrealized_pnl": round(upl, 0),
                "realized_pnl": round(pos.realized_pnl, 0),
            })

        equity = self.cash + total_market_value
        return {
            "cash": round(self.cash, 0),
            "market_value": round(total_market_value, 0),
            "equity": round(equity, 0),
            "total_unrealized_pnl": round(total_unrealized, 0),
            "total_realized_pnl": round(total_realized, 0),
            "total_return_pct": round((equity - self.initial_cash) / self.initial_cash * 100, 2),
            "positions": rows,
        }

    # ------------------------------------------------------------------
    # 2-4. 상태 저장/복원
    # ------------------------------------------------------------------
    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(
                {
                    "cash": self.cash,
                    "initial_cash": self.initial_cash,
                    "commission_rate": self.commission_rate,
                    "sell_tax_rate": self.sell_tax_rate,
                    "positions": {k: asdict(v) for k, v in self.positions.items()},
                    "orders": [asdict(o) for o in self.orders],
                    "order_seq": self._order_seq,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    def load(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.cash = data["cash"]
        self.initial_cash = data["initial_cash"]
        self.commission_rate = data["commission_rate"]
        self.sell_tax_rate = data["sell_tax_rate"]
        self.positions = {k: Position(**v) for k, v in data["positions"].items()}
        self.orders = [
            Order(
                **{**o, "side": Side(o["side"]),
                   "order_type": OrderType(o["order_type"]),
                   "status": OrderStatus(o["status"])}
            )
            for o in data["orders"]
        ]
        self._order_seq = data["order_seq"]


# ---------------------------------------------------------------------------
# 3. 데모: 가상 매매 한 사이클
# ---------------------------------------------------------------------------

def _demo() -> None:
    import os
    from kis_domestic_quote import KISConfig

    cfg = KISConfig(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        env=os.environ.get("KIS_ENV", "vts"),
    )
    quote = KISDomesticQuote(cfg)
    broker = VirtualBroker(quote, initial_cash=10_000_000)

    # 시장가 매수
    o1 = broker.buy_market("005930", qty=10)   # 삼성전자 10주
    print(f"[주문] {o1.order_id} 상태={o1.status} 체결가={o1.filled_price}")

    # 지정가 매수 (당장 안 체결될 수 있음)
    current = float(quote.get_current_price("005930")["output"]["stck_prpr"])
    o2 = broker.buy_limit("005930", qty=5, price=current * 0.99)
    print(f"[주문] {o2.order_id} 상태={o2.status} 사유={o2.reason or '-'}")

    # 잠시 후 다시 시도
    filled = broker.process_pending_orders()
    print(f"[재평가] 추가 체결 {filled}건")

    # 포트폴리오 요약
    summary = broker.portfolio_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 저장
    broker.save("./vb_state.json")
    print("[상태 저장] vb_state.json")


if __name__ == "__main__":
    _demo()