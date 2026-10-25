"""
STOCK 마스터 적재 - KIS 종목코드 마스터 파일 기반 (KOSPI/KOSDAQ)

사용 예:
    python manage.py sync_stock_master                       # KOSPI + KOSDAQ
    python manage.py sync_stock_master --market KOSPI
    python manage.py sync_stock_master --limit 10            # 시장당 10건
    python manage.py sync_stock_master --dry-run

배경
----
KRX 정보데이터시스템에 Akamai 봇 차단이 걸려 pykrx / FinanceDataReader 모두
ticker_list 호출이 실패한다. 한국투자증권이 제공하는 정적 마스터 zip 파일은
인증 없이 접근 가능하므로 이걸 1차 소스로 사용.

  KOSPI : https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip
  KOSDAQ: https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip

각 zip 안에 고정폭 record 텍스트 파일이 들어있다. cp949 인코딩.
정확한 record layout은 KIS 공식 문서에 있으나 매우 복잡(200+ 필드).
이 명령은 가장 안정적인 앞쪽 3필드만 추출한다:
  0-9   (9 byte): 단축코드 (일반 종목은 6자리 + 공백 padding, ETF/펀드는 F로 시작)
  9-21  (12 byte): 표준코드 (ISIN)
  21-61 (40 byte): 한글 종목명

ETF/펀드/스팩 등 비주식은 단축코드 첫 글자로 필터링한다.

sector / industry / market_cap / listed_at / 메타 4필드는 이 명령으로
채우지 않고, 후속 KIS API 기반 enrich 명령에서 보강 예정.
"""
from __future__ import annotations

import io
import urllib.request
import zipfile
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from stocks.models import Stock


KIS_MASTER_URLS = {
    "KOSPI": "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
    "KOSDAQ": "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
}

# 고정폭 offset (KIS kospi/kosdaq_code.mst 공통 앞부분)
OFFSET_SHORT_CODE = (0, 9)
OFFSET_STD_CODE = (9, 21)
OFFSET_NAME = (21, 61)


def _download_master(market: str) -> list[bytes]:
    """KIS 마스터 zip 다운로드 → 압축 해제 → 라인 리스트(cp949 bytes) 반환."""
    url = KIS_MASTER_URLS[market]
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        inner_name = zf.namelist()[0]
        raw = zf.read(inner_name)
    return [line for line in raw.split(b"\n") if line.strip()]


def _parse_line(line: bytes) -> Optional[dict]:
    """한 record에서 short_code, std_code, name 추출. 일반 주식이 아니면 None."""
    if len(line) < OFFSET_NAME[1]:
        return None
    short = line[OFFSET_SHORT_CODE[0]:OFFSET_SHORT_CODE[1]].decode("cp949", errors="replace").strip()
    std = line[OFFSET_STD_CODE[0]:OFFSET_STD_CODE[1]].decode("cp949", errors="replace").strip()
    name = line[OFFSET_NAME[0]:OFFSET_NAME[1]].decode("cp949", errors="replace").strip()

    # 일반 주식: 6자리 숫자 코드. ETF/펀드/스팩(F, J, K 등 알파벳 prefix) 제외
    if not (len(short) == 6 and short.isdigit()):
        return None
    return {"short_code": short, "std_code": std, "name": name}


class Command(BaseCommand):
    help = "KIS 종목코드 마스터 파일로 KOSPI/KOSDAQ 종목 적재"

    def add_arguments(self, parser):
        parser.add_argument(
            "--market",
            default="KR",
            choices=["KR", "KOSPI", "KOSDAQ"],
            help="적재할 시장. KR = KOSPI+KOSDAQ (기본)",
        )
        parser.add_argument("--limit", type=int, default=None, help="시장당 적재 개수 제한 (테스트용)")
        parser.add_argument("--dry-run", action="store_true", help="DB 변경 없이 미리보기만")

    def handle(self, *args, **opts):
        market_arg = opts["market"]
        markets = ["KOSPI", "KOSDAQ"] if market_arg == "KR" else [market_arg]
        limit = opts["limit"]
        dry_run = opts["dry_run"]

        self.stdout.write(f"[sync_stock_master] 시장={markets} limit={limit} dry_run={dry_run}")

        synced_codes_by_market: dict[str, set[str]] = {}
        for market in markets:
            count, codes = self._sync_market(market, limit, dry_run)
            synced_codes_by_market[market] = codes
            self.stdout.write(self.style.SUCCESS(f"  {market}: {count}건 적재"))

        # 마스터에서 빠진 종목 비활성화 (전체 KR sync + limit 없을 때만)
        if market_arg == "KR" and not limit and not dry_run:
            for market, codes in synced_codes_by_market.items():
                deactivated = self._deactivate_missing(market, codes)
                if deactivated:
                    self.stdout.write(self.style.WARNING(
                        f"  {market} 마스터에서 사라진 종목 {deactivated}건 -> is_active=False"
                    ))

        self.stdout.write(self.style.SUCCESS("[sync_stock_master] 완료"))

    def _sync_market(self, market: str, limit: Optional[int], dry_run: bool) -> tuple[int, set[str]]:
        if market not in KIS_MASTER_URLS:
            raise CommandError(f"지원하지 않는 시장: {market}")

        self.stdout.write(f"  [{market}] 마스터 다운로드 중...")
        try:
            lines = _download_master(market)
        except Exception as e:
            raise CommandError(f"[{market}] 마스터 다운로드 실패: {e}")
        self.stdout.write(f"  [{market}] {len(lines)} record, 파싱 + 적재 시작")

        synced_codes: set[str] = set()
        count = 0
        for line in lines:
            parsed = _parse_line(line)
            if not parsed:
                continue
            if limit and count >= limit:
                break

            short = parsed["short_code"]
            name = parsed["name"]

            if dry_run:
                self.stdout.write(f"    [dry-run] {short} {name}")
                synced_codes.add(short)
                count += 1
                continue

            with transaction.atomic():
                Stock.objects.update_or_create(
                    code=short,
                    market=market,
                    defaults={
                        "name": name,
                        "currency": "KRW",
                        "kis_short_code": short,
                        "is_active": True,
                    },
                )
            synced_codes.add(short)
            count += 1

        return count, synced_codes

    def _deactivate_missing(self, market: str, synced_codes: set[str]) -> int:
        qs = Stock.objects.filter(market=market, is_active=True, currency="KRW").exclude(code__in=synced_codes)
        n = qs.count()
        if n:
            qs.update(is_active=False)
        return n
