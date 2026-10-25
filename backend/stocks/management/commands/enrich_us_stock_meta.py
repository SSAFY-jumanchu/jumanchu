"""
US STOCK enrichment - KIS 해외 시세 + yfinance 하이브리드

채우는 필드
-----------
Stock 모델:
  - sector       <- KIS price-detail e_icod (한글 업종, 한국과 일관)
  - market_cap   <- KIS price-detail tomv (USD)
  - industry     <- yfinance .info["industry"] (영문 세분 분류)
  - homepage_url <- yfinance .info["website"]

StockIndicator 모델 (오늘 날짜):
  - per       <- KIS perx
  - pbr       <- KIS pbrx
  - eps       <- KIS epsx
  - high_52w  <- KIS h52p
  - low_52w   <- KIS l52p

사용 예
-------
    python manage.py enrich_us_stock_meta --limit 5 --dry-run
    python manage.py enrich_us_stock_meta --limit 20
    python manage.py enrich_us_stock_meta --only-empty
    python manage.py enrich_us_stock_meta              # 전체 (~1.5시간)

옵션
----
  --limit N     처리 종목 수 제한 (테스트용)
  --dry-run     DB 변경 없이 출력만
  --sleep S     호출 간 대기 (KIS 0.5s + yfinance 0.5s 기본)
  --only-empty  sector가 비어있는 종목만 (재실행 효율화)
  --no-yfinance KIS만 호출 (yfinance 차단 환경 또는 빠른 테스트용)

주의
----
- `.env`에 KIS_APP_KEY / KIS_APP_SECRET / KIS_ENV 필요
- yfinance는 야후 파이낸스 비공식 스크래핑. 가끔 None / 빈 dict 반환됨 (skip 처리)
- 5,942종목 × 약 1초 = 약 1.5시간. 진행 중간 끊겨도 --only-empty 로 재개 가능
"""
from __future__ import annotations

import time
from datetime import date
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from stocks.models import Stock, StockIndicator
from stocks.services.kis_client import KISClient, KISConfig


# Stock.market -> KIS EXCD
MARKET_TO_EXCD = {
    "NASDAQ": "NAS",
    "NYSE": "NYS",
}


def _to_float(s) -> Optional[float]:
    if s is None:
        return None
    s = str(s).strip()
    if not s or s == "-":
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return None if v == 0.0 else v


def _to_int(s) -> Optional[int]:
    if s is None:
        return None
    s = str(s).strip()
    if not s or s == "-":
        return None
    try:
        v = int(float(s))
    except ValueError:
        return None
    return None if v == 0 else v


def _fetch_yfinance_meta(ticker: str) -> dict:
    """yfinance .info에서 industry / website만 추출. 실패 시 빈 dict."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info or {}
        return {
            "industry": (info.get("industry") or "").strip(),
            "website": (info.get("website") or "").strip(),
        }
    except Exception:
        return {}


class Command(BaseCommand):
    help = "KIS price-detail + yfinance로 미국 종목 sector/industry/market_cap/PER/PBR/EPS 채우기"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="처리 종목 수 제한")
        parser.add_argument("--dry-run", action="store_true", help="DB 변경 없이 미리보기")
        parser.add_argument("--sleep", type=float, default=0.5, help="KIS 호출 간 sleep (기본 0.5)")
        parser.add_argument(
            "--only-empty",
            action="store_true",
            help="sector가 비어있는 종목만 처리 (재실행 효율화)",
        )
        parser.add_argument(
            "--no-yfinance",
            action="store_true",
            help="yfinance 호출 생략 (KIS 컬럼만 채움)",
        )

    def handle(self, *args, **opts):
        load_dotenv(dotenv_path="../.env")
        load_dotenv()

        limit = opts["limit"]
        dry_run = opts["dry_run"]
        sleep_sec = opts["sleep"]
        only_empty = opts["only_empty"]
        no_yfinance = opts["no_yfinance"]

        client = KISClient(KISConfig.from_env())
        self.stdout.write(
            f"[enrich_us_stock_meta] limit={limit} dry_run={dry_run} "
            f"sleep={sleep_sec}s only_empty={only_empty} no_yfinance={no_yfinance}"
        )

        qs = Stock.objects.filter(currency="USD", is_active=True).order_by("market", "code")
        if only_empty:
            qs = qs.filter(sector="")
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"  대상 종목: {total}건")

        today = date.today()
        ok = 0
        fail = 0

        for i, stock in enumerate(qs, 1):
            excd = MARKET_TO_EXCD.get(stock.market)
            if not excd:
                fail += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{i:>4}/{total}] {stock.code} {stock.market} 알 수 없는 시장 - skip"
                ))
                continue

            try:
                # 1) KIS price-detail
                resp = client.get_overseas_price_detail(excd, stock.code)
                out = resp.get("output", {})

                sector = (out.get("e_icod") or "").strip()
                market_cap = _to_int(out.get("tomv"))
                per = _to_float(out.get("perx"))
                pbr = _to_float(out.get("pbrx"))
                eps = _to_int(out.get("epsx"))
                high_52w = _to_int(out.get("h52p"))
                low_52w = _to_int(out.get("l52p"))

                # 2) yfinance 보완 (industry / homepage_url)
                industry = ""
                website = ""
                if not no_yfinance:
                    yf_meta = _fetch_yfinance_meta(stock.code)
                    industry = yf_meta.get("industry", "")
                    website = yf_meta.get("website", "")

                if dry_run:
                    self.stdout.write(
                        f"  [{i:>4}/{total}] {stock.code} ({stock.market}) {stock.name}: "
                        f"sector={sector!r} cap={market_cap} per={per} pbr={pbr} eps={eps} "
                        f"52w=[{low_52w},{high_52w}] industry={industry!r} url={website!r}"
                    )
                else:
                    with transaction.atomic():
                        stock.sector = sector
                        if market_cap is not None:
                            stock.market_cap = market_cap
                        if industry:
                            stock.industry = industry
                        if website:
                            stock.homepage_url = website
                        stock.save(update_fields=[
                            "sector", "market_cap", "industry", "homepage_url", "updated_at"
                        ])

                        StockIndicator.objects.update_or_create(
                            stock=stock,
                            calculated_date=today,
                            defaults={
                                "per": per,
                                "pbr": pbr,
                                "eps": eps,
                                "high_52w": high_52w,
                                "low_52w": low_52w,
                            },
                        )
                ok += 1

            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{i:>4}/{total}] {stock.code} {stock.name} FAIL: {e}"
                ))

            time.sleep(sleep_sec)

            if i % 50 == 0:
                self.stdout.write(f"    ... 진행 {i}/{total} (ok={ok} fail={fail})")

        self.stdout.write(self.style.SUCCESS(
            f"[enrich_us_stock_meta] 완료 ok={ok} fail={fail}"
        ))
