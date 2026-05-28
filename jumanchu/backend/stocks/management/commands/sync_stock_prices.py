"""
일봉(StockPrice) 수집.

출처
----
한국(KRW): KIS get_domestic_daily_price (FHKST03010100). 100행/호출 → 날짜 페이징
미국(USD): KIS get_overseas_daily_price (HHDFS76240000). 100행/호출 → 날짜 페이징

적재: bulk_create(ignore_conflicts=True) — unique(stock, price_date)라 재실행 안전.

사용 예
-------
    python manage.py sync_stock_prices --market KR --limit 3 --dry-run
    python manage.py sync_stock_prices --market US --limit 3 --dry-run
    python manage.py sync_stock_prices --market all --only-empty
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from dotenv import load_dotenv

from stocks.models import Stock, StockPrice
from stocks.services.kis_client import KISClient, KISConfig


def _ymd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _dec(x) -> Optional[Decimal]:
    if x is None:
        return None
    try:
        return Decimal(str(float(x)))
    except (TypeError, ValueError, InvalidOperation):
        return None


def _kr_daily_rows(client: KISClient, code: str, start: date, end: date, sleep_sec: float) -> list[dict]:
    """KIS 100행 한계 → 날짜 구간 페이징으로 start~end 전체 일봉 수집."""
    rows: list[dict] = []
    seen: set[str] = set()
    cur = end
    while cur >= start:
        win_start = max(start, cur - timedelta(days=140))  # 거래일 ≈ 100
        resp = client.get_domestic_daily_price(code, _ymd(win_start), _ymd(cur))
        out = resp.get("output2", []) or []
        out = [r for r in out if r.get("stck_bsop_date")]
        if not out:
            break
        new = [r for r in out if r["stck_bsop_date"] not in seen]
        for r in new:
            seen.add(r["stck_bsop_date"])
        rows += new
        oldest = min(r["stck_bsop_date"] for r in out)
        cur = datetime.strptime(oldest, "%Y%m%d").date() - timedelta(days=1)
        time.sleep(sleep_sec)
    return rows


def _kr_to_price(stock: Stock, r: dict) -> Optional[StockPrice]:
    try:
        d = datetime.strptime(r["stck_bsop_date"], "%Y%m%d").date()
    except (ValueError, KeyError):
        return None
    close = _dec(r.get("stck_clpr"))
    if close is None:
        return None
    return StockPrice(
        stock=stock, price_date=d,
        open=_dec(r.get("stck_oprc")) or close,
        high=_dec(r.get("stck_hgpr")) or close,
        low=_dec(r.get("stck_lwpr")) or close,
        close=close,
        volume=int(r.get("acml_vol") or 0),
    )


MARKET_TO_EXCD = {"NASDAQ": "NAS", "NYSE": "NYS"}


def _us_daily_rows(client: KISClient, excd: str, symbol: str,
                   start: date, end: date, sleep_sec: float) -> list[dict]:
    """KIS 해외 일봉 100행 한계 → 날짜 페이징으로 start~end 전체 수집."""
    rows: list[dict] = []
    seen: set[str] = set()
    cur = end
    while cur >= start:
        resp = client.get_overseas_daily_price(excd, symbol, _ymd(cur))
        out = [r for r in (resp.get("output2") or []) if r.get("xymd")]
        time.sleep(sleep_sec)  # KIS 호출마다 sleep (종목 간 rate-limit 보호)
        if not out:
            break
        new = [r for r in out if r["xymd"] not in seen]
        for r in new:
            seen.add(r["xymd"])
        rows += new
        oldest_date = datetime.strptime(min(r["xymd"] for r in out), "%Y%m%d").date()
        if oldest_date <= start:
            break
        cur = oldest_date - timedelta(days=1)
    return [r for r in rows if r["xymd"] >= _ymd(start)]


def _us_to_price(stock: Stock, r: dict) -> Optional[StockPrice]:
    try:
        d = datetime.strptime(r["xymd"], "%Y%m%d").date()
    except (ValueError, KeyError):
        return None
    close = _dec(r.get("clos"))
    if close is None:
        return None
    return StockPrice(
        stock=stock, price_date=d,
        open=_dec(r.get("open")) or close,
        high=_dec(r.get("high")) or close,
        low=_dec(r.get("low")) or close,
        close=close,
        volume=int(r.get("tvol") or 0),
    )


class Command(BaseCommand):
    help = "KIS(KR)/yfinance(US)로 StockPrice 일봉 수집"

    def add_arguments(self, parser):
        parser.add_argument("--market", default="all", choices=["KR", "US", "all"])
        parser.add_argument("--days", type=int, default=365, help="수집 기간(일)")
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--sleep", type=float, default=0.4)
        parser.add_argument("--only-empty", action="store_true",
                            help="StockPrice 없는 종목만 처리")

    def handle(self, *args, **opts):
        load_dotenv(dotenv_path="../.env")
        load_dotenv()

        market = opts["market"]
        days = opts["days"]
        limit = opts["limit"]
        dry_run = opts["dry_run"]
        sleep_sec = opts["sleep"]
        only_empty = opts["only_empty"]

        end = date.today()
        start = end - timedelta(days=days)
        self.stdout.write(
            f"[sync_stock_prices] market={market} days={days} ({_ymd(start)}~{_ymd(end)}) "
            f"limit={limit} dry_run={dry_run} only_empty={only_empty}"
        )

        if market in ("KR", "all"):
            self._run_kr(start, end, limit, dry_run, sleep_sec, only_empty)
        if market in ("US", "all"):
            self._run_us(start, end, limit, dry_run, sleep_sec, only_empty)

    def _base_qs(self, currency, only_empty, limit):
        qs = Stock.objects.filter(currency=currency, is_active=True).order_by("market", "code")
        if only_empty:
            has_price = StockPrice.objects.filter(stock=OuterRef("pk"))
            qs = qs.filter(~Exists(has_price))
        if limit:
            qs = qs[:limit]
        return qs

    def _run_kr(self, start, end, limit, dry_run, sleep_sec, only_empty):
        client = KISClient(KISConfig.from_env())
        qs = self._base_qs("KRW", only_empty, limit)
        total = qs.count()
        self.stdout.write(f"  [KR] 대상 {total}건")
        ok = fail = 0
        for i, stock in enumerate(qs, 1):
            try:
                rows = _kr_daily_rows(client, stock.code, start, end, sleep_sec)
                prices = [p for r in rows if (p := _kr_to_price(stock, r))]
                if dry_run:
                    self.stdout.write(f"  [KR {i:>4}/{total}] {stock.code} {stock.name}: {len(prices)}일봉")
                else:
                    StockPrice.objects.bulk_create(prices, ignore_conflicts=True)
                ok += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(f"  [KR {i:>4}/{total}] {stock.code} FAIL: {e}"))
            if i % 50 == 0:
                self.stdout.write(f"    ... KR {i}/{total} (ok={ok} fail={fail})")
        self.stdout.write(self.style.SUCCESS(f"  [KR] 완료 ok={ok} fail={fail}"))

    def _run_us(self, start, end, limit, dry_run, sleep_sec, only_empty):
        client = KISClient(KISConfig.from_env())
        qs = self._base_qs("USD", only_empty, limit)
        total = qs.count()
        self.stdout.write(f"  [US] 대상 {total}건")
        ok = fail = 0
        for i, stock in enumerate(qs, 1):
            excd = MARKET_TO_EXCD.get(stock.market)
            if not excd:
                fail += 1
                self.stdout.write(self.style.WARNING(
                    f"  [US {i:>4}/{total}] {stock.code} 알 수 없는 시장 {stock.market} skip"))
                continue
            try:
                rows = _us_daily_rows(client, excd, stock.code, start, end, sleep_sec)
                prices = [p for r in rows if (p := _us_to_price(stock, r))]
                if dry_run:
                    self.stdout.write(f"  [US {i:>4}/{total}] {stock.code}: {len(prices)}일봉")
                else:
                    StockPrice.objects.bulk_create(prices, ignore_conflicts=True)
                ok += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(f"  [US {i:>4}/{total}] {stock.code} FAIL: {e}"))
            if i % 50 == 0:
                self.stdout.write(f"    ... US {i}/{total} (ok={ok} fail={fail})")
        self.stdout.write(self.style.SUCCESS(f"  [US] 완료 ok={ok} fail={fail}"))
