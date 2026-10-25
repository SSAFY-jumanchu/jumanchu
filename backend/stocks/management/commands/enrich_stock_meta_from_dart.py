"""
DART company.json 응답으로 Stock 회사 개황 메타 채우기 (KOSPI/KOSDAQ).

채우는 필드
-----------
- Stock.ceo_name     <- ceo_nm
- Stock.homepage_url <- hm_url (빈 문자열이면 덮어쓰지 않음)
- Stock.industry     <- induty_code (KSIC 숫자 코드, 예: "264")
- Stock.listed_at    <- est_dt (설립일 8자리 "20140101" → date, 상장일 근사)

사용 예
-------
    python manage.py enrich_stock_meta_from_dart --limit 3 --dry-run
    python manage.py enrich_stock_meta_from_dart --limit 10
    python manage.py enrich_stock_meta_from_dart --only-empty
    python manage.py enrich_stock_meta_from_dart            # 전체 (~15-20분)

주의
----
- `.env`의 DART_API_KEY 필요
- 첫 실행은 corp_code zip 다운로드(수 초)
- 스팩/우선주는 DART에 없어 KeyError → skip_no_corp 카운터 (실패 아님)
- DART 한도 20,000/일 → 3,577종목 1회는 안전
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from stocks.models import Stock
from stocks.services.dart_client import DartClient, DartConfig


def _parse_yyyymmdd(s: Optional[str]):
    """'20140101' 같은 8자리 문자열을 date로 변환. 형식 안 맞으면 None."""
    if not s:
        return None
    s = s.strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None


def _normalize_url(s: Optional[str]) -> str:
    """DART hm_url은 스킴 없는 경우 잦음 ('www.foo.com') → 'http://' 프리픽스."""
    if not s:
        return ""
    s = s.strip()
    if not s:
        return ""
    if s.startswith(("http://", "https://")):
        return s
    return "http://" + s


class Command(BaseCommand):
    help = "DART company.json으로 Stock.ceo_name/homepage_url/industry/listed_at 채우기"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="처리 종목 수 제한")
        parser.add_argument("--dry-run", action="store_true", help="DB 변경 없이 미리보기")
        parser.add_argument("--sleep", type=float, default=0.3, help="호출 간 sleep 초")
        parser.add_argument(
            "--only-empty",
            action="store_true",
            help="ceo_name이 비어있는 종목만 처리 (재실행 효율화)",
        )

    def handle(self, *args, **opts):
        load_dotenv(dotenv_path="../.env")
        load_dotenv()

        limit = opts["limit"]
        dry_run = opts["dry_run"]
        sleep_sec = opts["sleep"]
        only_empty = opts["only_empty"]

        client = DartClient(DartConfig.from_env())
        self.stdout.write(
            f"[enrich_stock_meta_from_dart] limit={limit} dry_run={dry_run} "
            f"sleep={sleep_sec}s only_empty={only_empty}"
        )

        qs = Stock.objects.filter(currency="KRW", is_active=True).order_by("market", "code")
        if only_empty:
            qs = qs.filter(ceo_name="")
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"  대상 종목: {total}건")

        ok = 0
        fail = 0
        skip_no_corp = 0

        for i, stock in enumerate(qs, 1):
            try:
                corp_code = client.corp_code_of(stock.code)
            except KeyError:
                skip_no_corp += 1
                continue

            try:
                info = client.get_company(corp_code)
                ceo = (info.get("ceo_nm") or "").strip()
                hm = _normalize_url(info.get("hm_url"))
                induty = (info.get("induty_code") or "").strip()
                est = _parse_yyyymmdd(info.get("est_dt"))

                if dry_run:
                    self.stdout.write(
                        f"  [{i:>4}/{total}] {stock.code} {stock.name}: "
                        f"ceo={ceo!r} url={hm!r} industry={induty!r} listed_at={est}"
                    )
                else:
                    stock.ceo_name = ceo
                    if hm:
                        stock.homepage_url = hm
                    stock.industry = induty
                    if est:
                        stock.listed_at = est
                    stock.save(update_fields=[
                        "ceo_name", "homepage_url", "industry", "listed_at", "updated_at"
                    ])
                ok += 1
            except Exception as e:
                fail += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{i:>4}/{total}] {stock.code} {stock.name} FAIL: {e}"
                ))

            time.sleep(sleep_sec)

            if i % 100 == 0:
                self.stdout.write(
                    f"    ... 진행 {i}/{total} (ok={ok} fail={fail} skip={skip_no_corp})"
                )

        self.stdout.write(self.style.SUCCESS(
            f"[enrich_stock_meta_from_dart] 완료 ok={ok} fail={fail} skip_no_corp={skip_no_corp}"
        ))
