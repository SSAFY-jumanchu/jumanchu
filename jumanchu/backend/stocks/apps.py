import logging
import os
import sys
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class StocksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stocks'

    def ready(self):
        # 서버가 뜨는 순간 인기랭킹 워머(warm_loop)를 백그라운드 데몬 스레드로 같이 기동.
        # 데몬이라 서버가 죽으면 같이 죽음 → 별도 스케줄러/창 없이 시세캐시가 늘 따뜻.
        if not self._should_start_warmer():
            return
        threading.Thread(
            target=self._run_warmer, name='popular-warmer', daemon=True
        ).start()

    @staticmethod
    def _should_start_warmer() -> bool:
        """워머를 이 프로세스에서 띄울지 판정.

        - DISABLE_WARMER=1  → 끔(테스트·CI·끄고 싶을 때).
        - runserver(개발)   → autoreload 자식(RUN_MAIN)에서만 1번. --noreload면 그대로.
                              → migrate/shell/makemigrations/test 등엔 안 뜸(argv에 runserver 없음).
        - 배포(gunicorn 등) → RUN_WARMER=1 일 때만(워커 1개에만 거는 걸 권장).
        """
        if os.environ.get('DISABLE_WARMER') == '1':
            return False
        argv = sys.argv
        if 'runserver' in argv:
            use_reloader = '--noreload' not in argv
            # reloader 켜져 있으면 부모(감시) 프로세스 RUN_MAIN 미설정 → 자식만 실행(중복 방지)
            if use_reloader and os.environ.get('RUN_MAIN') != 'true':
                return False
            return True
        return os.environ.get('RUN_WARMER') == '1'

    @staticmethod
    def _run_warmer():
        import time

        from django.core.management import call_command

        time.sleep(2)  # 서버 부팅(포트 바인딩)과 첫 KIS 버스트가 겹치지 않게 살짝 양보
        try:
            # 무한 루프 커맨드 — 데몬 스레드에서 프로세스가 살아있는 동안 계속 워밍
            call_command('warm_loop', interval=30, size=100, chunk=20)
        except Exception:  # noqa: BLE001 — 워머가 죽어도 웹서버는 살아야 함
            logger.exception('popular-warmer 비정상 종료')
