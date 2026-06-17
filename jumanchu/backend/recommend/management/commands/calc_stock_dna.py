"""
종목 4축 DNA(분위수 정규화) 일배치 적재 - StockDna.

전제: StockIndicator(beta/pbr) + FinancialSummary(net_profit_yoy/debt_ratio/current_ratio)가 선적재되어 있어야 함.
      ※ beta와 pbr은 소스가 달라 서로 다른 indicator 행에 들어있다 → 각각 "값이 있는 최신 행"을 따로 수집.
대상: 활성 종목 중 FinancialSummary 행이 있는 종목만 → ETF/ETN/우선주/리츠는 FS 행이 없어 자동 제외.

계산식 (한국/미국 시장별로 분리 정규화)
------
volatility   = pct(beta)                          변동성 (beta 높을수록 ↑)
value_score  = pct(1/PBR)                         저평가 (PBR 낮을수록 ↑)
growth_score = pct(net_profit_yoy)                성장성 (순이익 YoY 높을수록 ↑) — 값 없으면 중립 0.5
stability    = avg(pct(↓부채비율), pct(↑유동비율))  안정성 (재무 건전성) — 둘 다 없으면 중립 0.5
sector       = stock.sector 복사

엣지 제외(continue): beta<=0(인버스) · pbr<=0(자본잠식) · beta/pbr 값 없음
pct() = 동일 시장(KRW/USD) 풀 내 분위수, 동점은 평균순위 → 0~1

사용 예
-------
    python manage.py calc_stock_dna --dry-run --limit 50
    python manage.py calc_stock_dna
"""
from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from stocks.models import Stock, StockIndicator, FinancialSummary
from recommend.models import StockDna

NEUTRAL = 0.5


def _percentile_ranks(items: list[tuple[int, float]]) -> dict[int, float]:
    """[(stock_id, value)] -> {stock_id: 분위수 0~1}. 동점은 평균순위 기반."""
    srt = sorted(items, key=lambda x: x[1])
    n = len(srt)
    out: dict[int, float] = {}
    i = 0
    while i < n:
        j = i
        while j < n and srt[j][1] == srt[i][1]:
            j += 1
        pct = ((i + 1) + j) / 2.0 / n  # 평균순위(1-based) / n
        for k in range(i, j):
            out[srt[k][0]] = pct
        i = j
    return out


def _latest_map(value_rows) -> dict[int, float]:
    """(stock_id, value) 행들(stock_id asc, 날짜 desc 정렬 전제)에서 종목별 최신값 1개."""
    out: dict[int, float] = {}
    for sid, val in value_rows:
        if sid not in out:
            out[sid] = val
    return out


class Command(BaseCommand):
    help = "FinancialSummary 보유 활성종목의 4축 DNA를 시장별 분위수로 적재 (일배치)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        limit = opts["limit"]
        today = date.today()

        qs = Stock.objects.filter(
            is_active=True, id__in=FinancialSummary.objects.values("stock_id"),
        ).order_by("currency", "code")
        if limit:
            qs = qs[:limit]
        meta = {sid: (cur, sec) for sid, cur, sec in qs.values_list("id", "currency", "sector")}
        ids = list(meta.keys())
        self.stdout.write(f"[calc_stock_dna] 대상 {len(ids)}건 (FinancialSummary 보유 활성종목)")

        # beta·pbr은 서로 다른 indicator 행에 저장됨 → 각각 값이 있는 최신 행을 따로 수집
        beta_map = _latest_map(
            StockIndicator.objects.filter(stock_id__in=ids, beta__isnull=False)
            .order_by("stock_id", "-calculated_date").values_list("stock_id", "beta"))
        pbr_map = _latest_map(
            StockIndicator.objects.filter(stock_id__in=ids, pbr__isnull=False)
            .order_by("stock_id", "-calculated_date").values_list("stock_id", "pbr"))
        # 재무 지표(성장·안정성)는 FinancialSummary에서 종목별 최신 회계기간 값
        np_map = _latest_map(
            FinancialSummary.objects.filter(stock_id__in=ids, net_profit_yoy__isnull=False)
            .order_by("stock_id", "-fiscal_period").values_list("stock_id", "net_profit_yoy"))
        debt_map = _latest_map(
            FinancialSummary.objects.filter(stock_id__in=ids, debt_ratio__isnull=False)
            .order_by("stock_id", "-fiscal_period").values_list("stock_id", "debt_ratio"))
        curr_map = _latest_map(
            FinancialSummary.objects.filter(stock_id__in=ids, current_ratio__isnull=False)
            .order_by("stock_id", "-fiscal_period").values_list("stock_id", "current_ratio"))

        # 1) 원천값 조립 + 엣지 제외
        rows = []  # [{stock_id, region, sector, beta, inv_pbr, np_yoy, debt, current}]
        skipped = 0
        for sid in ids:
            beta = beta_map.get(sid)
            pbr = pbr_map.get(sid)
            if beta is None or beta <= 0 or pbr is None or pbr <= 0:
                skipped += 1  # 인버스(beta<=0)·자본잠식(pbr<=0)·값없음
                continue
            currency, sec = meta[sid]
            np_yoy = np_map.get(sid)
            debt = debt_map.get(sid)
            curr = curr_map.get(sid)
            rows.append({
                "stock_id": sid,
                "region": "KR" if currency == "KRW" else "US",
                "sector": sec,
                "beta": float(beta),
                "inv_pbr": 1.0 / float(pbr),
                "np_yoy": None if np_yoy is None else float(np_yoy),
                "debt": None if debt is None else float(debt),
                "current": None if curr is None else float(curr),
            })

        # 2) 시장(KR/US)별 분위수 정규화
        dna = {}  # stock_id -> defaults dict
        for region in ("KR", "US"):
            grp = [r for r in rows if r["region"] == region]
            if not grp:
                continue
            vol = _percentile_ranks([(r["stock_id"], r["beta"]) for r in grp])
            val = _percentile_ranks([(r["stock_id"], r["inv_pbr"]) for r in grp])
            grw = _percentile_ranks([(r["stock_id"], r["np_yoy"]) for r in grp if r["np_yoy"] is not None])
            # 안정성: 부채비율(낮을수록↑) + 유동비율(높을수록↑) 분위수의 평균, 있는 지표만
            debt_pct = _percentile_ranks([(r["stock_id"], -r["debt"]) for r in grp if r["debt"] is not None])
            curr_pct = _percentile_ranks([(r["stock_id"], r["current"]) for r in grp if r["current"] is not None])

            stab_neutral = 0
            for r in grp:
                sid = r["stock_id"]
                comps = []
                if sid in debt_pct:
                    comps.append(debt_pct[sid])
                if sid in curr_pct:
                    comps.append(curr_pct[sid])
                if comps:
                    stability = sum(comps) / len(comps)
                else:
                    stability = NEUTRAL
                    stab_neutral += 1
                dna[sid] = {
                    "volatility": round(vol[sid], 4),
                    "value_score": round(val[sid], 4),
                    "growth_score": round(grw.get(sid, NEUTRAL), 4),  # 값 없으면 중립 0.5
                    "stability": round(stability, 4),
                    "sector": r["sector"],
                }
            self.stdout.write(
                f"  [{region}] 정규화 {len(grp)}건 "
                f"(성장 중립 {len(grp) - len(grw)} / 안정성 중립 {stab_neutral})"
            )

        if dry_run:
            for sid, d in list(dna.items())[:5]:
                self.stdout.write(f"    {sid}: {d}")
            self.stdout.write(self.style.WARNING(
                f"[dry-run] 적재 안 함. 정규화 {len(dna)}건, 엣지제외 {skipped}건"))
            return

        # 3) upsert
        created = updated = 0
        with transaction.atomic():
            for sid, d in dna.items():
                _, is_new = StockDna.objects.update_or_create(
                    stock_id=sid, calculated_date=today, defaults=d,
                )
                if is_new:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"[calc_stock_dna] 완료: {len(dna)}건 적재 (created {created}, updated {updated}), 엣지제외 {skipped}"))
