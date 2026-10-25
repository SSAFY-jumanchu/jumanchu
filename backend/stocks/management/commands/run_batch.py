"""
배치 오케스트레이터 — 여러 management command를 **의존 순서대로** 묶어 실행. cron 등록 대상.

정책 표: docs/API_스키마_v1.5.md §10.3
의존 순서: 마스터 → 메타·플래그 → 가격 → 지표 → 재무 → DNA·장투점수.

※ `warm_volume_power`(장중 체결강도 Redis 워머)는 의존성 없고 ~30초 주기라 이 묶음에 안 넣음.
  별도 루프/워커로 **시장시간에만** 실행 (§10.3 참고).

사용:
    python manage.py run_batch daily            # 매일(장 마감 후): 가격→지표→DNA→장투점수
    python manage.py run_batch weekly           # 주 1회: 마스터→메타→플래그→섹터→재무
    python manage.py run_batch hourly           # 시간별: 뉴스 수집
    python manage.py run_batch daily --dry-run  # 실행할 단계만 출력
    python manage.py run_batch daily --fail-fast # 한 단계 실패 시 즉시 중단 (기본: 계속)

종료 코드: 실패 단계가 있으면 비-0(cron 알림용).
"""
from __future__ import annotations

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

# 묶음별 실행 순서 (의존성 보장)
PIPELINES: dict[str, list[str]] = {
    "daily": [
        "sync_stock_prices",       # KIS(KR)/yfinance(US) 일봉
        "calc_market_indicators",  # beta·volatility·52주 (가격 후)
        "calc_stock_dna",          # 4축 DNA 분위수 (지표·재무 후)
        "calc_longterm_scores",    # 장투 소계(재무·성장) (지표·재무 후)
    ],
    "weekly": [
        "sync_stock_master",
        "sync_us_stock_master",
        "enrich_stock_meta_from_dart",
        "enrich_stock_meta_from_kis",
        "enrich_us_stock_meta",
        "sync_us_index_flags",
        "normalize_sectors",
        "enrich_financials",       # 분기성이나 주간에 묶어 stale만 갱신
    ],
    "hourly": [
        "ingest_rss",              # 연합뉴스 RSS 수집·태깅
    ],
}


class Command(BaseCommand):
    help = "배치 파이프라인 묶음 실행 (cron 등록 대상). 의존 순서·실패 격리 포함."

    def add_arguments(self, parser):
        parser.add_argument("group", choices=sorted(PIPELINES), help="실행할 배치 묶음")
        parser.add_argument("--dry-run", action="store_true", help="실행 안 하고 단계만 출력")
        parser.add_argument("--fail-fast", action="store_true", help="실패 시 즉시 중단(기본: 계속)")

    def handle(self, *args, **opts):
        group = opts["group"]
        steps = PIPELINES[group]
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"[run_batch:{group}] {len(steps)}단계 - {' -> '.join(steps)}"))

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("[dry-run] 실행 안 함"))
            return

        ok: list[str] = []
        failed: list[tuple[str, str]] = []
        t_all = time.monotonic()
        for i, cmd in enumerate(steps, 1):
            self.stdout.write(f"\n--[{i}/{len(steps)}] {cmd} --------------")
            t0 = time.monotonic()
            try:
                call_command(cmd)
                ok.append(cmd)
                self.stdout.write(self.style.SUCCESS(f"[OK] {cmd} ({time.monotonic() - t0:.1f}s)"))
            except Exception as exc:  # 한 단계 실패가 전체 배치를 막지 않게
                failed.append((cmd, str(exc)))
                self.stderr.write(self.style.ERROR(f"[X] {cmd} ({time.monotonic() - t0:.1f}s): {exc}"))
                if opts["fail_fast"]:
                    raise CommandError(f"{cmd} 실패 - 중단(--fail-fast)")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n[run_batch:{group}] 완료 {time.monotonic() - t_all:.1f}s "
            f"- 성공 {len(ok)} / 실패 {len(failed)}"))
        for cmd, err in failed:
            self.stderr.write(self.style.ERROR(f"  실패: {cmd} - {err}"))
        if failed:
            raise CommandError(f"{len(failed)}개 단계 실패 (위 로그 참고)")
