"""인기 랭킹 워밍 루프 — warm_popular_prices + warm_volume_power 를 주기 반복 실행.

별도 스케줄러(cron/Celery) 없이 이 명령 하나를 백그라운드로 띄우면 인기 랭킹의
시세(stock:rankprice:*)·체결강도(stock:volpower:*) 캐시가 계속 따뜻하게 유지된다.
한 사이클이 실패해도 루프는 죽지 않는다(다음 주기 재시도).

    python manage.py warm_loop                      # 30s 주기, size 100, 무한
    python manage.py warm_loop --interval 30 --size 100 --chunk 20
    python manage.py warm_loop --once               # 1 사이클만(검증용)

캐시 TTL이 60s라 interval은 60 미만 권장(기본 30).
운영 상시화: Linux=systemd 서비스, Windows=nssm/작업스케줄러로 이 명령을 서비스화.
"""
from __future__ import annotations

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import close_old_connections


class Command(BaseCommand):
    help = "인기 랭킹 시세+체결강도 워밍을 주기적으로 반복 실행 (단순 루프 스케줄러)"

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=30, help="사이클 간 목표 주기 초 (기본 30)")
        parser.add_argument("--size", type=int, default=100, help="워밍 대상 종목 수 (기본 100)")
        parser.add_argument("--chunk", type=int, default=20, help="초당 호출 상한 (기본 20)")
        parser.add_argument("--once", action="store_true", help="1 사이클만 실행하고 종료(검증용)")

    def handle(self, *args, **opts):
        interval, size, chunk = opts["interval"], opts["size"], opts["chunk"]
        self.stdout.write(
            f"[warm_loop] 시작 - {interval}s 주기, size={size}, chunk={chunk} (Ctrl+C 종료)")
        cycle = 0
        try:
            while True:
                cycle += 1
                close_old_connections()   # 장수명 루프: 끊긴 DB 커넥션 정리(Neon idle timeout 대비)
                t0 = time.monotonic()
                try:
                    call_command("warm_popular_prices", size=size, chunk=chunk)
                    call_command("warm_volume_power", size=size, chunk=chunk)
                except Exception as e:    # noqa: BLE001 — 한 사이클 실패가 루프를 죽이지 않게
                    self.stderr.write(f"[warm_loop] 사이클 {cycle} 실패: {e}")
                if opts["once"]:
                    break
                # 목표 주기 맞추기: 이번 사이클이 빨리 끝났으면 남은 시간 sleep
                time.sleep(max(0.0, interval - (time.monotonic() - t0)))
        except KeyboardInterrupt:
            self.stdout.write("\n[warm_loop] 종료")
