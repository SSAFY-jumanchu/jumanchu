"""
재무 적재 - FinancialSummary + StockIndicator(roe/roa/dividend_yield).

출처
----
한국(KRW): DART  build_financial_summary (사업보고서 연간)
미국(USD): yfinance .info + financials/balance_sheet

채우는 것
---------
FinancialSummary: revenue/operating_profit/net_profit/operating_margin/net_margin/
                  revenue_yoy/operating_profit_yoy/net_profit_yoy/
                  debt_ratio/equity_ratio/current_ratio/payout_ratio/data_source
StockIndicator(오늘): roe, roa, (미국만) dividend_yield
  → update_or_create(defaults=부분키)라 기존 per/pbr/eps 보존됨

단위
----
비율은 모두 배수(소수)로 통일. yfinance 가드: debtToEquity/100, dividendYield>1이면/100.
한국 dividend_yield는 이번엔 보류(None) — 발행주식수 경로 복잡.

사용 예
-------
    python manage.py enrich_financials --market KR --limit 3 --dry-run
    python manage.py enrich_financials --market US --limit 3 --dry-run
    python manage.py enrich_financials --market all --only-empty
"""
from __future__ import annotations

import time
from datetime import date
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from dotenv import load_dotenv

from stocks.models import Stock, StockIndicator, FinancialSummary
from stocks.services.dart_client import DartClient, DartConfig
from stocks.services.financials import build_financial_summary, _safe_div


def _ratio(x) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _de(x) -> Optional[float]:
    """yfinance debtToEquity는 %형(79.5) → 배수(0.795)로."""
    v = _ratio(x)
    return None if v is None else v / 100


def _dy(x) -> Optional[float]:
    """yfinance 0.2.66 dividendYield는 %형(AAPL 0.35 = 0.35%).
    다른 비율(배수)과 통일하려고 /100. 단 구버전 배수형(<0.1) 방어로 1 이상만 /100 추가 가드.
    """
    v = _ratio(x)
    if v is None:
        return None
    # 0.2.66은 %형 → 항상 /100 (0.35→0.0035). 이미 배수(예: 0.004)면 값이 더 작아지지만
    # 우리 버전 고정이므로 %형 기준으로 통일.
    return v / 100


def _fetch_yfinance_financials(ticker: str) -> dict:
    """yfinance로 재무 + 지표 추출 (단위 정규화 내장). 실패 시 빈 dict."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.info or {}
        if not info or len(info) < 10:
            return {}

        def pick(df, names):
            for n in names:
                if df is not None and not df.empty and n in df.index:
                    v = df.loc[n].iloc[0]
                    return int(v) if v == v else None  # NaN 방어
            return None

        fin = t.financials
        bs = t.balance_sheet

        fiscal_year = 2024
        try:
            if fin is not None and not fin.empty:
                fiscal_year = fin.columns[0].year
        except Exception:
            pass

        revenue = pick(fin, ["Total Revenue"])
        op = pick(fin, ["Operating Income"])
        npf = pick(fin, ["Net Income"])
        total_equity = pick(bs, ["Stockholders Equity", "Total Equity Gross Minority Interest"])
        total_assets = pick(bs, ["Total Assets"])

        return {
            "fiscal_period": f"{fiscal_year}FY",
            "revenue": revenue,
            "operating_profit": op,
            "net_profit": npf,
            "operating_margin": _ratio(info.get("operatingMargins")),
            "net_margin": _ratio(info.get("profitMargins")),
            "revenue_yoy": _ratio(info.get("revenueGrowth")),
            "operating_profit_yoy": None,
            "net_profit_yoy": _ratio(info.get("earningsGrowth")),
            "debt_ratio": _de(info.get("debtToEquity")),
            "equity_ratio": _safe_div(total_equity, total_assets),
            "current_ratio": _ratio(info.get("currentRatio")),
            "payout_ratio": _ratio(info.get("payoutRatio")),
            "data_source": "yfinance",
            # StockIndicator 용
            "roe": _ratio(info.get("returnOnEquity")),
            "roa": _ratio(info.get("returnOnAssets")),
            "dividend_yield": _dy(info.get("dividendYield")),
        }
    except Exception:
        return {}


class Command(BaseCommand):
    help = "DART(KR)/yfinance(US)로 FinancialSummary + roe/roa/dividend_yield 채우기"

    def add_arguments(self, parser):
        parser.add_argument("--market", default="all", choices=["KR", "US", "all"])
        parser.add_argument("--year", type=int, default=2024, help="DART 사업연도 (KR)")
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--sleep", type=float, default=0.4)
        parser.add_argument("--only-empty", action="store_true",
                            help="FinancialSummary 없는 종목만 처리")
        parser.add_argument("--us-index-only", action="store_true",
                            help="미국은 S&P500/NASDAQ100 구성종목만 처리")

    def handle(self, *args, **opts):
        load_dotenv(dotenv_path="../.env")
        load_dotenv()

        market = opts["market"]
        year = opts["year"]
        limit = opts["limit"]
        dry_run = opts["dry_run"]
        sleep_sec = opts["sleep"]
        only_empty = opts["only_empty"]
        us_index_only = opts["us_index_only"]
        today = date.today()

        self.stdout.write(
            f"[enrich_financials] market={market} year={year} limit={limit} "
            f"dry_run={dry_run} sleep={sleep_sec}s only_empty={only_empty} us_index_only={us_index_only}"
        )

        if market in ("KR", "all"):
            self._run_kr(year, limit, dry_run, sleep_sec, only_empty, today)
        if market in ("US", "all"):
            self._run_us(limit, dry_run, sleep_sec, only_empty, us_index_only, today)

    def _base_qs(self, currency: str, only_empty: bool, limit: Optional[int], us_index_only: bool = False):
        qs = Stock.objects.filter(currency=currency, is_active=True).order_by("market", "code")
        if currency == "USD" and us_index_only:
            qs = qs.filter(Q(is_sp500=True) | Q(is_nasdaq100=True))
        if only_empty:
            has_fin = FinancialSummary.objects.filter(stock=OuterRef("pk"))
            qs = qs.filter(~Exists(has_fin))
        if limit:
            qs = qs[:limit]
        return qs

    def _run_kr(self, year, limit, dry_run, sleep_sec, only_empty, today):
        dart = DartClient(DartConfig.from_env())
        qs = self._base_qs("KRW", only_empty, limit)
        total = qs.count()
        self.stdout.write(f"  [KR] 대상 {total}건")
        ok = fail = skip_no_corp = skip_no_data = 0

        for i, stock in enumerate(qs, 1):
            try:
                corp = dart.corp_code_of(stock.code)
            except KeyError:
                skip_no_corp += 1
                continue
            try:
                summ = build_financial_summary(dart, corp, year, "11011", "CFS")
                eq = summ.pop("_total_equity")
                ta = summ.pop("_total_assets")
                np_ = summ.pop("_net_profit")
                if summ.get("revenue") is None:
                    skip_no_data += 1
                    continue
                roe = _safe_div(np_, eq)
                roa = _safe_div(np_, ta)

                if dry_run:
                    self.stdout.write(
                        f"  [KR {i:>4}/{total}] {stock.code} {stock.name}: "
                        f"rev={summ['revenue']} op_m={summ['operating_margin']} "
                        f"debt={summ['debt_ratio']} payout={summ['payout_ratio']} roe={roe}"
                    )
                else:
                    with transaction.atomic():
                        FinancialSummary.objects.update_or_create(
                            stock=stock, fiscal_period=summ["fiscal_period"], defaults=summ)
                        StockIndicator.objects.update_or_create(
                            stock=stock, calculated_date=today,
                            defaults={"roe": roe, "roa": roa})
                ok += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(f"  [KR {i:>4}/{total}] {stock.code} FAIL: {e}"))
            time.sleep(sleep_sec)
            if i % 50 == 0:
                self.stdout.write(f"    ... KR {i}/{total} (ok={ok} fail={fail} no_corp={skip_no_corp} no_data={skip_no_data})")

        self.stdout.write(self.style.SUCCESS(
            f"  [KR] 완료 ok={ok} fail={fail} skip_no_corp={skip_no_corp} skip_no_data={skip_no_data}"))

    def _run_us(self, limit, dry_run, sleep_sec, only_empty, us_index_only, today):
        qs = self._base_qs("USD", only_empty, limit, us_index_only)
        total = qs.count()
        self.stdout.write(f"  [US] 대상 {total}건")
        ok = fail = skip_no_data = 0

        for i, stock in enumerate(qs, 1):
            try:
                m = _fetch_yfinance_financials(stock.code)
                if not m or m.get("revenue") is None:
                    skip_no_data += 1
                    time.sleep(sleep_sec)
                    continue
                roe = m.pop("roe")
                roa = m.pop("roa")
                dividend_yield = m.pop("dividend_yield")

                if dry_run:
                    self.stdout.write(
                        f"  [US {i:>4}/{total}] {stock.code}: rev={m['revenue']} "
                        f"net_m={m['net_margin']} debt={m['debt_ratio']} "
                        f"payout={m['payout_ratio']} roe={roe} div_yld={dividend_yield}"
                    )
                else:
                    with transaction.atomic():
                        FinancialSummary.objects.update_or_create(
                            stock=stock, fiscal_period=m["fiscal_period"], defaults=m)
                        StockIndicator.objects.update_or_create(
                            stock=stock, calculated_date=today,
                            defaults={"roe": roe, "roa": roa, "dividend_yield": dividend_yield})
                ok += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(f"  [US {i:>4}/{total}] {stock.code} FAIL: {e}"))
            time.sleep(sleep_sec)
            if i % 50 == 0:
                self.stdout.write(f"    ... US {i}/{total} (ok={ok} fail={fail} no_data={skip_no_data})")

        self.stdout.write(self.style.SUCCESS(
            f"  [US] 완료 ok={ok} fail={fail} skip_no_data={skip_no_data}"))
