"""인기 종목 체결강도(거래비율) Redis 워밍 — 랭킹 거래비율 컬럼용.

인기 풀(거래량 순위 KR+US, 최대 --size)의 체결강도를 KIS에서 **초당 ≤chunk로 페이싱**
조회해 `stock:volpower:*` 캐시에 적재한다. 랭킹 엔드포인트(popular_ranking)는 이 캐시를
읽기만 하고(라이브 KIS 0콜), 워밍 사이클 사이 새로 진입한 종목(캐시 미스)만 요청 경로에서
소량(≤8개) 즉석 채운다(_attach_volume_power).

cron/스케줄러로 ~30s 주기 실행 권장 (KIS 분당 한도는 청크 페이싱으로 관리).

사용:
    python manage.py warm_volume_power                       # top120, 초당 20, TTL 60
    python manage.py warm_volume_power --size 120 --chunk 20 --ttl 60
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from django.core.management.base import BaseCommand

from stocks.services.market_summary import popular_universe
from stocks.services.price_dispatch import (
    VOLPOWER_EMPTY, VOLPOWER_TTL, fetch_volume_power, volpower_key)


class Command(BaseCommand):
    help = "인기 종목 체결강도를 KIS에서 초당 ≤chunk로 페이싱 조회해 Redis 워밍 (랭킹 거래비율 컬럼용)"

    def add_arguments(self, parser):
        parser.add_argument("--size", type=int, default=120, help="워밍 대상 인기 종목 수 (기본 120)")
        parser.add_argument("--chunk", type=int, default=20, help="청크 크기 = 초당 호출 상한 (기본 20)")
        parser.add_argument("--ttl", type=int, default=VOLPOWER_TTL, help="캐시 TTL 초 (기본 60)")

    def handle(self, *args, **opts):
        size, chunk, ttl = opts["size"], opts["chunk"], opts["ttl"]
        pairs = popular_universe(size)
        self.stdout.write(f"[warm_volume_power] 대상 {len(pairs)}종목 (초당 <={chunk}, TTL {ttl}s)")

        warmed = 0
        # 청크를 동시 호출(스레드 안전) → 실제 초당 chunk. cache.set은 메인스레드에서.
        with ThreadPoolExecutor(max_workers=min(chunk, 8)) as ex:   # 동시 TLS 제한 → 서버 경합↓
            for i in range(0, len(pairs), chunk):
                t0 = time.monotonic()
                batch = pairs[i:i + chunk]
                results = list(ex.map(lambda mc: fetch_volume_power(*mc), batch))
                for (market, code), vp in zip(batch, results):
                    # 음성(None: US 장마감 등)도 캐시 → 요청 경로가 라이브 재조회 안 하게
                    cache.set(volpower_key(market, code), vp or VOLPOWER_EMPTY, timeout=ttl)
                    if vp is not None:
                        warmed += 1
                if i + chunk < len(pairs):
                    time.sleep(max(0.0, 1.0 - (time.monotonic() - t0)))

        self.stdout.write(self.style.SUCCESS(
            f"[warm_volume_power] 완료: {warmed}/{len(pairs)} 적재"))
