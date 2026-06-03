"""
S&P500 / NASDAQ100 구성종목 플래그 적재.

Wikipedia 구성종목 표에서 ticker 리스트를 받아, 이미 적재된 미국 Stock의
is_sp500 / is_nasdaq100 플래그를 채운다. (sync_us_stock_master로 전체 미국 종목이
적재된 뒤 실행)

또한 인덱스(S&P500/NASDAQ100)에 없는 USD 종목은 is_active=False로 내려, 데이터 범위를
KOSPI+KOSDAQ+S&P500+NASDAQ100로 정리한다 (일봉 누락 파악 단순화).

출처
----
S&P500   : https://en.wikipedia.org/wiki/List_of_S%26P_500_companies (Symbol 컬럼)
NASDAQ100: https://en.wikipedia.org/wiki/Nasdaq-100 (Ticker 컬럼)

의존성: pandas + lxml (read_html). requirements.txt 참조.

주의
----
- 점 ticker(BRK.B, BF.B)는 우리 마스터에 없음(sync_us_stock_master가 isalpha 필터) → 매칭 안 됨, 로그만.
- 멱등: 매번 전체 USD 종목의 플래그를 재계산(매칭 안 되면 False)하므로 재실행 안전.

사용 예
-------
    python manage.py sync_us_index_flags --dry-run
    python manage.py sync_us_index_flags
"""
from __future__ import annotations

import io
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from stocks.models import Stock


SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ100_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def _parse_sp500() -> set[str]:
    import pandas as pd
    df = pd.read_html(io.StringIO(_fetch(SP500_URL)))[0]
    return {str(s).strip() for s in df["Symbol"].tolist()}


def _parse_nasdaq100() -> set[str]:
    import pandas as pd
    for t in pd.read_html(io.StringIO(_fetch(NASDAQ100_URL))):
        cols = [str(c) for c in t.columns]
        col = "Ticker" if "Ticker" in cols else ("Symbol" if "Symbol" in cols else None)
        if col:
            return {str(s).strip() for s in t[col].tolist()}
    return set()


class Command(BaseCommand):
    help = "Wikipedia 구성종목으로 Stock.is_sp500 / is_nasdaq100 플래그 채우기 + 비인덱스 USD 종목 is_active=False(범위 정리)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]

        try:
            sp = _parse_sp500()
            ndx = _parse_nasdaq100()
        except Exception as e:
            raise CommandError(f"Wikipedia 파싱 실패: {e}")

        self.stdout.write(f"[sync_us_index_flags] S&P500={len(sp)} NASDAQ100={len(ndx)} (dry_run={dry_run})")

        usd = Stock.objects.filter(currency="USD")
        sp_hit = ndx_hit = changed = in_scope_count = total = 0

        for stock in usd:
            total += 1
            is_sp = stock.code in sp
            is_ndx = stock.code in ndx
            in_scope = is_sp or is_ndx  # 인덱스 구성종목만 범위 안 (= is_active)
            if is_sp:
                sp_hit += 1
            if is_ndx:
                ndx_hit += 1
            if in_scope:
                in_scope_count += 1
            if (stock.is_sp500 != is_sp or stock.is_nasdaq100 != is_ndx
                    or stock.is_active != in_scope):
                changed += 1
                if not dry_run:
                    stock.is_sp500 = is_sp
                    stock.is_nasdaq100 = is_ndx
                    stock.is_active = in_scope
                    stock.save(update_fields=["is_sp500", "is_nasdaq100",
                                              "is_active", "updated_at"])

        # 매칭 안 된 Wikipedia ticker (점 ticker 등)
        db_codes = set(usd.values_list("code", flat=True))
        missed = sorted((sp | ndx) - db_codes)

        self.stdout.write(self.style.SUCCESS(
            f"[sync_us_index_flags] {'(dry-run) ' if dry_run else ''}"
            f"sp500 매칭={sp_hit} nasdaq100 매칭={ndx_hit} 변경={changed} "
            f"in_scope(is_active)={in_scope_count} deactivated={total - in_scope_count}"
        ))
        if missed:
            self.stdout.write(self.style.WARNING(
                f"  마스터에 없어 매칭 실패 {len(missed)}건 (점 ticker 등): {missed[:20]}"
            ))
