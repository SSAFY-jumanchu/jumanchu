"""체결강도 워밍(warm_volume_power)을 시장시간에만 ~interval초 주기로 반복 호출하는 루프.

cron은 분 단위가 최소 주기라 "장중 ~30초 주기" 정책(API_스키마_v1.5 §10.3)을 그대로
표현할 수 없다. 이 커맨드를 한 번만 띄워 두면 내부 while 루프가 30초(기본) 주기로
``warm_volume_power``를 호출하므로 cron의 분 단위 한계를 우회한다.

시장시간 판정은 price_dispatch._is_market_open을 그대로 재사용한다(KR 또는 US 중
하나라도 열려 있으면 워밍). 시장이 닫힌 동안에는 호출하지 않고 더 길게 쉰다.

사용:
    python manage.py warm_volume_loop                      # 30초 주기, 장중에만
    python manage.py warm_volume_loop --interval 30        # 주기 지정
    python manage.py warm_volume_loop --size 120 --chunk 20 --ttl 60
    python manage.py warm_volume_loop --once               # 1회만(테스트)
    python manage.py warm_volume_loop --always             # 시장시간 무시(테스트)
"""
from __future__ import annotations

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from stocks.services.price_dispatch import _is_market_open


class Command(BaseCommand):
    help = "warm_volume_power를 시장시간에만 ~interval초 주기로 반복 호출하는 루프 (cron 분 단위 한계 우회)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval", type=int, default=30,
            help="워밍 호출 주기(초). 기본 30",
        )
        # size/chunk/ttl은 기본 None → 지정된 것만 warm_volume_power에 전달(나머지는 그 쪽 기본값 사용)
        parser.add_argument("--size", type=int, default=None, help="워밍 대상 인기 종목 수 (warm_volume_power로 전달)")
        parser.add_argument("--chunk", type=int, default=None, help="청크 크기 = 초당 호출 상한 (warm_volume_power로 전달)")
        parser.add_argument("--ttl", type=int, default=None, help="캐시 TTL 초 (warm_volume_power로 전달)")
        parser.add_argument("--once", action="store_true", help="1패스만 실행하고 종료(테스트용)")
        parser.add_argument("--always", action="store_true", help="시장시간을 무시하고 항상 워밍(테스트용)")

    def handle(self, *args, **opts):
        interval = opts["interval"]
        once = opts["once"]
        always = opts["always"]

        # size/chunk/ttl 중 None 아닌 것만 추려 하위 커맨드에 전달(기본값을 그대로 쓰게).
        passthrough = {
            k: opts[k] for k in ("size", "chunk", "ttl") if opts[k] is not None
        }

        self.stdout.write(self.style.SUCCESS(
            f"[warm_volume_loop] 시작: interval={interval}s, once={once}, always={always}, "
            f"passthrough={passthrough or '기본값'}"
        ))

        try:
            while True:
                t0 = time.monotonic()

                # KR 또는 US 중 하나라도 열렸으면 워밍(테스트 시 --always로 강제).
                market_open = always or (
                    _is_market_open("KOSPI") or _is_market_open("NASDAQ")
                )

                if market_open:
                    call_command("warm_volume_power", **passthrough)
                    wait = interval
                else:
                    # 장 마감 중에는 호출하지 않고 더 길게 쉰다(불필요한 깨어남 방지).
                    self.stdout.write("[warm_volume_loop] market closed, idling")
                    wait = max(interval, 60)

                # 1패스 테스트 모드면 즉시 종료.
                if once:
                    self.stdout.write(self.style.SUCCESS("[warm_volume_loop] --once 1패스 완료, 종료"))
                    return

                # 워밍 호출에 걸린 시간(elapsed)을 차감해 실제 주기를 interval로 유지.
                elapsed = time.monotonic() - t0
                remaining = wait - elapsed
                if remaining > 0:
                    time.sleep(remaining)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n[warm_volume_loop] 중단 신호(KeyboardInterrupt) 수신, 종료합니다."))
