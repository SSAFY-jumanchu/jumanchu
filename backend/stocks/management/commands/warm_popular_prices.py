"""인기 랭킹(시총상위100) 시세 Redis 워밍 — 랭킹 거래대금/현재가/등락률용.

랭킹 후보(DB 시총상위100)의 실시간 시세를 KIS에서 **초당 ≤chunk로 페이싱** 조회해
`stock:rankprice:*`(60s) 캐시에 적재한다. popular_ranking은 이 캐시를 읽기만 하고(라이브 0콜),
워밍 사이 새로 든 종목(캐시 미스)만 요청 경로에서 소량(≤12) 즉석 채운다.

체결강도 워밍(warm_volume_power)과 같은 시총상위100 universe를 공유한다.
cron/스케줄러로 ~30s 주기 실행 권장.

사용:
    python manage.py warm_popular_prices                 # top100, 초당 20
    python manage.py warm_popular_prices --size 100 --chunk 20
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from django.core.management.base import BaseCommand

from stocks.services.market_summary import popular_universe_stocks
from stocks.services.price_dispatch import fetch_rank_price


class Command(BaseCommand):
    help = "인기 랭킹(시총상위100) 시세를 KIS에서 초당 ≤chunk로 페이싱 조회해 Redis 워밍"

    def add_arguments(self, parser):
        parser.add_argument("--size", type=int, default=100, help="워밍 대상 종목 수 (기본 100)")
        parser.add_argument("--chunk", type=int, default=20, help="청크 크기 = 초당 호출 상한 (기본 20)")

    def handle(self, *args, **opts):
        size, chunk = opts["size"], opts["chunk"]
        stocks = popular_universe_stocks(size)
        self.stdout.write(f"[warm_popular_prices] 대상 {len(stocks)}종목 (초당 <={chunk})")

        warmed = 0
        # 청크를 동시 호출(KIS는 requests.get 기반·토큰 캐시라 스레드 안전) → 순차(~3/s)가 아닌 실제 초당 chunk.
        with ThreadPoolExecutor(max_workers=min(chunk, 8)) as ex:   # 동시 TLS 제한 → 서버 경합↓
            for i in range(0, len(stocks), chunk):
                t0 = time.monotonic()
                results = list(ex.map(fetch_rank_price, stocks[i:i + chunk]))
                warmed += sum(1 for r in results if r is not None)
                # 다음 청크 전, 1초보다 빨리 끝났으면 sleep → 초당 <=chunk 보장
                if i + chunk < len(stocks):
                    time.sleep(max(0.0, 1.0 - (time.monotonic() - t0)))

        self.stdout.write(self.style.SUCCESS(
            f"[warm_popular_prices] 완료: {warmed}/{len(stocks)} 적재"))
