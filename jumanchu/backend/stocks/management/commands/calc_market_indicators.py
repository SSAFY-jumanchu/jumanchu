"""
시장 기반 지표 계산 - StockIndicator.beta/volatility/high_52w/low_52w.

전제: StockPrice 일봉이 선적재되어 있어야 함 (sync_stock_prices 먼저).
외부 API는 시장지수 2개만 호출 (KOSPI=^KS11, S&P500=^GSPC). 나머지는 DB read + 계산.

계산식
------
volatility = 일간수익률.std() * sqrt(252) * 100   (연환산 %)
high_52w/low_52w = 최근 252거래일 high/low (정수)
beta = cov(종목수익률, 시장수익률) / var(시장수익률)   (날짜 교집합 정렬)

사용 예
-------
    python manage.py calc_market_indicators --limit 10
    python manage.py calc_market_indicators
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef

from stocks.models import Stock, StockPrice, StockIndicator


def _market_returns(ticker: str) -> Optional[pd.Series]:
    """시장지수 1년 일간수익률. index를 naive date로 정규화."""
    try:
        import yfinance as yf
        close = yf.Ticker(ticker).history(period="1y")["Close"]
        if close is None or close.empty:
            return None
        ret = close.pct_change().dropna()
        ret.index = [
            (d.tz_localize(None).date() if getattr(d, "tzinfo", None) else d.date())
            if hasattr(d, "date") else d
            for d in ret.index
        ]
        return ret
    except Exception:
        return None


def _beta(stock_ret: pd.Series, mkt_ret: Optional[pd.Series]) -> Optional[float]:
    if mkt_ret is None:
        return None
    df = pd.concat([stock_ret, mkt_ret], axis=1, join="inner").dropna()
    if len(df) < 30:
        return None
    cov = np.cov(df.iloc[:, 0], df.iloc[:, 1])
    var_mkt = cov[1, 1]
    if not var_mkt:
        return None
    return round(float(cov[0, 1] / var_mkt), 4)


class Command(BaseCommand):
    help = "StockPrice + 시장지수로 beta/volatility/high_52w/low_52w 계산"

    def add_arguments(self, parser):
        parser.add_argument("--market", default="all", choices=["KR", "US", "all"])
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        market = opts["market"]
        limit = opts["limit"]
        dry_run = opts["dry_run"]
        today = date.today()

        self.stdout.write(f"[calc_market_indicators] market={market} limit={limit} dry_run={dry_run}")

        kospi_ret = _market_returns("^KS11")
        snp_ret = _market_returns("^GSPC")
        self.stdout.write(
            f"  시장지수: KOSPI={'OK' if kospi_ret is not None else 'FAIL'} "
            f"S&P500={'OK' if snp_ret is not None else 'FAIL'}"
        )

        # StockPrice가 있는 종목만
        qs = Stock.objects.filter(is_active=True).filter(
            Exists(StockPrice.objects.filter(stock=OuterRef("pk")))
        ).order_by("market", "code")
        if market == "KR":
            qs = qs.filter(currency="KRW")
        elif market == "US":
            qs = qs.filter(currency="USD")
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"  대상 {total}건 (StockPrice 있는 종목)")
        ok = skip = fail = 0

        for i, stock in enumerate(qs, 1):
            try:
                prices = list(stock.prices.order_by("price_date").values("price_date", "high", "low", "close"))
                if len(prices) < 30:
                    skip += 1
                    continue

                closes = pd.Series(
                    [float(p["close"]) for p in prices],
                    index=[p["price_date"] for p in prices],
                )
                ret = closes.pct_change().dropna()
                volatility = round(float(ret.std() * np.sqrt(252) * 100), 4)

                recent = prices[-252:]
                high_52w = round(max(float(p["high"]) for p in recent))
                low_52w = round(min(float(p["low"]) for p in recent))

                mkt = kospi_ret if stock.currency == "KRW" else snp_ret
                beta = _beta(ret, mkt)

                if dry_run:
                    self.stdout.write(
                        f"  [{i:>4}/{total}] {stock.code}: vol={volatility} beta={beta} "
                        f"52w=[{low_52w},{high_52w}] (n={len(prices)})"
                    )
                else:
                    StockIndicator.objects.update_or_create(
                        stock=stock, calculated_date=today,
                        defaults={
                            "beta": beta,
                            "volatility": volatility,
                            "high_52w": high_52w,
                            "low_52w": low_52w,
                        },
                    )
                ok += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(f"  [{i:>4}/{total}] {stock.code} FAIL: {e}"))
            if i % 100 == 0:
                self.stdout.write(f"    ... {i}/{total} (ok={ok} skip={skip} fail={fail})")

        self.stdout.write(self.style.SUCCESS(
            f"[calc_market_indicators] 완료 ok={ok} skip(<30일)={skip} fail={fail}"))
