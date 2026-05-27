"""
US STOCK 마스터 적재 - KIS 해외 종목 마스터 파일 기반 (NASDAQ/NYSE)

사용 예:
    python manage.py sync_us_stock_master                       # NASDAQ + NYSE
    python manage.py sync_us_stock_master --market NASDAQ
    python manage.py sync_us_stock_master --limit 10            # 시장당 10건
    python manage.py sync_us_stock_master --dry-run

배경
----
한국 sync_stock_master 와 동일하게 KIS가 제공하는 정적 마스터 zip을 사용.
인증 불필요, 일자별로 갱신.

  NASDAQ: https://new.real.download.dws.co.kr/common/master/nasmst.cod.zip
  NYSE  : https://new.real.download.dws.co.kr/common/master/nysmst.cod.zip

한국 mst와 달리 해외 cod 파일은 **탭 구분 텍스트**(cp949 인코딩, 24컬럼).
파싱 확인된 컬럼 (2026-05-27 기준):
  [2]  거래소 ID  (NAS, NYS)
  [4]  Symbol     (ticker, 예: AAPL)
  [6]  한글 종목명
  [7]  영문 종목명
  [8]  증권유형   ("1"=지수, "2"=주식, "3"=ETP/ETF, "4"=워런트)
  [9]  통화       (USD)

필터링: 증권유형 == "2" 인 주식만 적재. ETF/지수/워런트는 제외.
점/하이픈 ticker (BRK.B, BF-A)는 일단 skip — 후속 enrich 단계에서 정규식 완화 검토.

sector / industry / market_cap / homepage_url / ceo_name 등 메타 필드는
이 명령으로 채우지 않고, 후속 yfinance enrichment 명령에서 보강 예정.
"""
from __future__ import annotations

import io
import urllib.request
import zipfile
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from stocks.models import Stock


KIS_US_MASTER_URLS = {
    "NASDAQ": "https://new.real.download.dws.co.kr/common/master/nasmst.cod.zip",
    "NYSE": "https://new.real.download.dws.co.kr/common/master/nysmst.cod.zip",
}

# 탭 split 결과 인덱스 (0-base)
COL_SYMBOL = 4
COL_NAME_KR = 6
COL_NAME_EN = 7
COL_SEC_TYPE = 8


def _download_us_master(market: str) -> list[str]:
    """KIS 해외 마스터 .cod zip 다운로드 → cp949 디코드 → line 리스트 반환."""
    url = KIS_US_MASTER_URLS[market]
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        inner_name = zf.namelist()[0]
        raw = zf.read(inner_name)
    text = raw.decode("cp949", errors="replace")
    return [ln for ln in text.splitlines() if ln.strip()]


def _parse_line(line: str) -> Optional[dict]:
    """탭 split 후 주식(증권유형=="2")만 통과. ticker 알파벳만 허용."""
    parts = line.split("\t")
    if len(parts) <= COL_SEC_TYPE:
        return None
    if parts[COL_SEC_TYPE].strip() != "2":
        return None
    symbol = parts[COL_SYMBOL].strip()
    name_en = parts[COL_NAME_EN].strip()
    name_kr = parts[COL_NAME_KR].strip()
    # BRK.B, BF-A 같은 점/하이픈 ticker는 일단 skip
    if not symbol or not symbol.isalpha():
        return None
    return {"symbol": symbol, "name": name_en or name_kr}


class Command(BaseCommand):
    help = "KIS 해외 마스터로 NASDAQ/NYSE 미국 종목 적재 (주식만)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--market",
            default="US",
            choices=["US", "NASDAQ", "NYSE"],
            help="적재할 시장. US = NASDAQ+NYSE (기본)",
        )
        parser.add_argument("--limit", type=int, default=None, help="시장당 적재 개수 제한 (테스트용)")
        parser.add_argument("--dry-run", action="store_true", help="DB 변경 없이 미리보기만")

    def handle(self, *args, **opts):
        market_arg = opts["market"]
        markets = ["NASDAQ", "NYSE"] if market_arg == "US" else [market_arg]
        limit = opts["limit"]
        dry_run = opts["dry_run"]

        self.stdout.write(f"[sync_us_stock_master] 시장={markets} limit={limit} dry_run={dry_run}")

        synced_codes_by_market: dict[str, set[str]] = {}
        for market in markets:
            count, codes = self._sync_market(market, limit, dry_run)
            synced_codes_by_market[market] = codes
            self.stdout.write(self.style.SUCCESS(f"  {market}: {count}건 적재"))

        # 마스터에서 빠진 종목 비활성화 (전체 US sync + limit 없을 때만)
        if market_arg == "US" and not limit and not dry_run:
            for market, codes in synced_codes_by_market.items():
                deactivated = self._deactivate_missing(market, codes)
                if deactivated:
                    self.stdout.write(self.style.WARNING(
                        f"  {market} 마스터에서 사라진 종목 {deactivated}건 -> is_active=False"
                    ))

        self.stdout.write(self.style.SUCCESS("[sync_us_stock_master] 완료"))

    def _sync_market(self, market: str, limit: Optional[int], dry_run: bool) -> tuple[int, set[str]]:
        if market not in KIS_US_MASTER_URLS:
            raise CommandError(f"지원하지 않는 시장: {market}")

        self.stdout.write(f"  [{market}] 마스터 다운로드 중...")
        try:
            lines = _download_us_master(market)
        except Exception as e:
            raise CommandError(f"[{market}] 마스터 다운로드 실패: {e}")
        self.stdout.write(f"  [{market}] {len(lines)} record, 파싱 + 적재 시작")

        synced_codes: set[str] = set()
        count = 0
        skipped_non_stock = 0
        skipped_bad_ticker = 0

        for line in lines:
            parts = line.split("\t")
            # 증권유형 != "2" 카운터
            if len(parts) > COL_SEC_TYPE and parts[COL_SEC_TYPE].strip() != "2":
                skipped_non_stock += 1
                continue

            parsed = _parse_line(line)
            if not parsed:
                skipped_bad_ticker += 1
                continue
            if limit and count >= limit:
                break

            symbol = parsed["symbol"]
            name = parsed["name"]

            if dry_run:
                self.stdout.write(f"    [dry-run] {symbol} {name}")
                synced_codes.add(symbol)
                count += 1
                continue

            try:
                with transaction.atomic():
                    Stock.objects.update_or_create(
                        code=symbol,
                        market=market,
                        defaults={
                            "name": name,
                            "currency": "USD",
                            "kis_short_code": symbol,
                            "is_active": True,
                        },
                    )
                synced_codes.add(symbol)
                count += 1
            except Exception as e:
                # kis_short_code unique 충돌 등 — skip + 경고
                self.stdout.write(self.style.WARNING(
                    f"    [{market}] {symbol} 적재 실패: {e}"
                ))

        self.stdout.write(
            f"  [{market}] 주식 외 {skipped_non_stock}건, 부적격 ticker {skipped_bad_ticker}건 skip"
        )
        return count, synced_codes

    def _deactivate_missing(self, market: str, synced_codes: set[str]) -> int:
        qs = Stock.objects.filter(
            market=market, is_active=True, currency="USD"
        ).exclude(code__in=synced_codes)
        n = qs.count()
        if n:
            qs.update(is_active=False)
        return n
