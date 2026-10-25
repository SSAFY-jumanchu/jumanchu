"""
종목 장투 점수(재무·성장 소계) 일배치 적재 - LongTermScore.

전제: FinancialSummary(마진/부채/유동/YoY) + StockIndicator(roe)가 선적재돼 있어야 함.
대상: 활성 종목 중 FinancialSummary 행이 있는 종목 (calc_stock_dna와 동일 기준).
계산: recommend.scoring.financial_score / growth_score / stock_subtotal (정율 산식 포팅).
      ⚠️ DB는 비율을 fraction(0.1088) 저장 → ×100 환산해 %로 넘긴다.
저장: total_score = 종목 소계(재무·성장). **개인 궁합 30%는 여기 없음** — ②랭킹에서 결합.

사용 예
    python manage.py calc_longterm_scores --dry-run --limit 50
    python manage.py calc_longterm_scores
"""
from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from stocks.models import Stock, StockIndicator, FinancialSummary
from recommend.models import LongTermScore
from recommend import scoring


def _latest_map(value_rows) -> dict[int, float]:
    """(stock_id, value) 행들(stock_id asc, 날짜 desc 정렬 전제)에서 종목별 최신값 1개."""
    out: dict[int, float] = {}
    for sid, val in value_rows:
        if sid not in out:
            out[sid] = val
    return out


def _x100(v) -> float | None:
    """DB의 fraction(0.1088) → 점수 산식이 받는 %(10.88). None은 그대로."""
    return None if v is None else float(v) * 100


class Command(BaseCommand):
    help = "FinancialSummary 보유 활성종목의 장투 소계(재무·성장)를 적재 (일배치)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        limit = opts["limit"]
        today = date.today()

        qs = Stock.objects.filter(
            is_active=True, id__in=FinancialSummary.objects.values("stock_id"),
        ).order_by("code")
        if limit:
            qs = qs[:limit]
        ids = list(qs.values_list("id", flat=True))
        self.stdout.write(f"[calc_longterm_scores] 대상 {len(ids)}건 (FinancialSummary 보유 활성종목)")

        # FinancialSummary: 종목별 최신 회계기간(-fiscal_period) 값 (calc_stock_dna와 동일 방식)
        def fin_map(field):
            return _latest_map(
                FinancialSummary.objects.filter(stock_id__in=ids, **{f"{field}__isnull": False})
                .order_by("stock_id", "-fiscal_period").values_list("stock_id", field))

        op_margin = fin_map("operating_margin")
        net_margin = fin_map("net_margin")
        debt = fin_map("debt_ratio")
        current = fin_map("current_ratio")
        rev_yoy = fin_map("revenue_yoy")
        op_yoy = fin_map("operating_profit_yoy")
        np_yoy = fin_map("net_profit_yoy")
        # StockIndicator: 종목별 최신(-calculated_date) roe
        roe_map = _latest_map(
            StockIndicator.objects.filter(stock_id__in=ids, roe__isnull=False)
            .order_by("stock_id", "-calculated_date").values_list("stock_id", "roe"))

        # 종목별 점수 산출 (입력은 ×100 환산해 %로)
        rows: dict[int, dict] = {}
        skipped = 0
        for sid in ids:
            fs = scoring.financial_score(
                debt_ratio=_x100(debt.get(sid)),
                current_ratio=_x100(current.get(sid)),
                operating_margin=_x100(op_margin.get(sid)),
                net_margin=_x100(net_margin.get(sid)),
                roe=_x100(roe_map.get(sid)),
            )
            gs = scoring.growth_score(
                revenue_yoy=_x100(rev_yoy.get(sid)),
                operating_profit_yoy=_x100(op_yoy.get(sid)),
                net_profit_yoy=_x100(np_yoy.get(sid)),
            )
            sub = scoring.stock_subtotal(fs, gs)
            if sub is None:
                skipped += 1  # 재무·성장 둘 다 데이터 없음
                continue
            rows[sid] = {
                "financial_score": None if fs is None else round(fs, 2),
                "growth_score": None if gs is None else round(gs, 2),
                "total_score": round(sub, 2),
            }

        if dry_run:
            for sid, d in list(rows.items())[:5]:
                self.stdout.write(f"    {sid}: {d}")
            self.stdout.write(self.style.WARNING(
                f"[dry-run] 적재 안 함. 산출 {len(rows)}건, 데이터없음 제외 {skipped}건"))
            return

        created = updated = 0
        with transaction.atomic():
            for sid, d in rows.items():
                _, is_new = LongTermScore.objects.update_or_create(
                    stock_id=sid, calculated_date=today, defaults=d,
                )
                created += is_new
                updated += not is_new

        self.stdout.write(self.style.SUCCESS(
            f"[calc_longterm_scores] 완료: {len(rows)}건 적재 "
            f"(created {created}, updated {updated}), 데이터없음 제외 {skipped}"))
