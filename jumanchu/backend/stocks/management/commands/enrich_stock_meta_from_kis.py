"""
KIS inquire-price 응답으로 Stock·StockIndicator 채우기 (KOSPI/KOSDAQ).

채우는 필드
-----------
- Stock.sector       <- bstp_kor_isnm (한글 업종명, 예: "전기·전자")
- Stock.market_cap   <- hts_avls (KIS는 "억" 단위, ×100_000_000 해서 원화 저장)
- StockIndicator.per <- per
- StockIndicator.pbr <- pbr
- StockIndicator.eps <- eps (정수)

사용 예
-------
    python manage.py enrich_stock_meta_from_kis --limit 10 --dry-run
    python manage.py enrich_stock_meta_from_kis --limit 50
    python manage.py enrich_stock_meta_from_kis            # 전체 (~1시간)

주의
----
- `.env`의 KIS_APP_KEY, KIS_APP_SECRET, KIS_ENV 필요
- KIS 분당 호출 제한 ~20회/TR → 기본 sleep 0.5s (분당 ~120회 시도, 실패 시 자동 retry 안 함)
- 한 종목 실패는 skip + 로그, 전체 계속
"""
from __future__ import annotations

import os
import time
from datetime import date
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from stocks.models import Stock, StockIndicator
from stocks.services.kis_client import KISClient, KISConfig


def _to_float(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    s = str(s).strip()
    if not s or s in ("-", "0", "0.00"):
        return None if s in ("-", "") else float(s)
    try:
        return float(s)
    except ValueError:
        return None


def _to_int(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None
    s = str(s).strip()
    if not s or s == "-":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


class Command(BaseCommand):
    help = "KIS inquire-price로 Stock.sector/market_cap + StockIndicator per/pbr/eps 채우기"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="처리 종목 수 제한 (테스트용)")
        parser.add_argument("--dry-run", action="store_true", help="DB 변경 없이 미리보기")
        parser.add_argument("--sleep", type=float, default=0.5, help="호출 간 sleep 초 (기본 0.5)")
        parser.add_argument(
            "--only-empty",
            action="store_true",
            help="sector가 비어있는 종목만 처리 (재실행 효율화)",
        )

    def handle(self, *args, **opts):
        load_dotenv(dotenv_path="../.env")
        load_dotenv()  # backend/.env 도 시도

        limit = opts["limit"]
        dry_run = opts["dry_run"]
        sleep_sec = opts["sleep"]
        only_empty = opts["only_empty"]

        client = KISClient(KISConfig.from_env())
        self.stdout.write(f"[enrich_stock_meta_from_kis] limit={limit} dry_run={dry_run} sleep={sleep_sec}s only_empty={only_empty}")

        qs = Stock.objects.filter(currency="KRW", is_active=True).order_by("market", "code")
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
            try:
                resp = client.get_current_price(stock.code)
                out = resp.get("output", {})

                bstp = (out.get("bstp_kor_isnm") or "").strip()
                hts_avls = _to_int(out.get("hts_avls"))   # 억 단위
                per = _to_float(out.get("per"))
                pbr = _to_float(out.get("pbr"))
                eps = _to_int(out.get("eps"))

                market_cap_krw = hts_avls * 100_000_000 if hts_avls else None

                if dry_run:
                    self.stdout.write(
                        f"  [{i:>4}/{total}] {stock.code} {stock.name}: "
                        f"sector={bstp!r} cap={market_cap_krw} per={per} pbr={pbr} eps={eps}"
                    )
                else:
                    with transaction.atomic():
                        stock.sector = bstp
                        if market_cap_krw is not None:
                            stock.market_cap = market_cap_krw
                        stock.save(update_fields=["sector", "market_cap", "updated_at"])

                        StockIndicator.objects.update_or_create(
                            stock=stock,
                            calculated_date=today,
                            defaults={"per": per, "pbr": pbr, "eps": eps},
                        )
                ok += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{i:>4}/{total}] {stock.code} {stock.name} FAIL: {e}"
                ))

            time.sleep(sleep_sec)

            # 진행 표시 (50건마다)
            if i % 50 == 0:
                self.stdout.write(f"    ... 진행 {i}/{total} (ok={ok} fail={fail})")

        self.stdout.write(self.style.SUCCESS(f"[enrich_stock_meta_from_kis] 완료 ok={ok} fail={fail}"))
