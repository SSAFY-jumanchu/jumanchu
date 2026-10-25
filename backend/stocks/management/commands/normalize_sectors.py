"""
종목 섹터명 정본화 — KR 기준 통합 분류로 정규화.

KR을 canonical로: US(세분화) 섹터를 대응 KR 섹터로 흡수 + KR 2건 개칭(오락·문화→미디어, 리츠→부동산).
Stock.sector + StockDna.sector(비정규화 복사본) 동시 갱신.
※ 외부 적재(KIS/yfinance)가 원본 섹터를 다시 넣으므로 적재 후 재실행 가능(idempotent).

사용: python manage.py normalize_sectors [--dry-run]
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from stocks.models import Stock
from recommend.models import StockDna

# 원본 섹터 → 정본(KR 기준). 이미 정본인 것(화학·제약·미디어 등)은 생략(no-op).
SECTOR_MAP = {
    # KR 개칭
    "오락·문화": "미디어",
    "리츠": "부동산",
    # US → KR 흡수
    "인터넷소프트웨어 및 IT서비스": "IT 서비스",
    "REIT's 및 부동산관리개발": "부동산",
    "건강관리장비 및 서비스": "의료·정밀기기",
    "금융서비스": "금융",
    "상업은행": "금융",
    "보험": "금융",
    "기계 및 전기장비": "기계·장비",
    "반도체 및 반도체장비": "전기·전자",
    "컴퓨터전자장비/기기": "전기·전자",
    "통신장비": "전기·전자",
    "도/소매": "유통",
    "무역회사": "유통",
    "가정 및 개인용품": "유통",
    "바이오": "제약",
    "공익사업": "전기·가스",
    "전기": "전기·가스",
    "가스": "전기·가스",
    "에너지 및 관련 서비스": "전기·가스",
    "우주항공 및 국방": "운송장비·부품",
    "자동차": "운송장비·부품",
    "자동차관련부품": "운송장비·부품",
    "음식료 및 담배생산": "음식료·담배",
    "음식료 도매": "음식료·담배",
    "여행서비스 및 제품": "일반서비스",
    "상업 및 전문서비스": "일반서비스",
    "복합기업": "일반서비스",
    "건설 및 건축제품": "건설",
    "건축자재": "건설",
    "운송인프라": "운송·창고",
    "항공사 및 항공운송": "운송·창고",
    "섬유의복 및 호화제품": "섬유·의류",
    "소재산업": "화학",
    "금속&채광": "금속",
}


class Command(BaseCommand):
    help = "종목 섹터명을 KR 기준 통합 분류로 정규화 (Stock + StockDna)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        total_s = total_d = 0
        for raw, canon in SECTOR_MAP.items():
            ns = Stock.objects.filter(sector=raw).count()
            nd = StockDna.objects.filter(sector=raw).count()
            if ns or nd:
                self.stdout.write(f"  {raw!r} → {canon!r}: stock {ns}, dna {nd}")
                if not dry:
                    Stock.objects.filter(sector=raw).update(sector=canon)
                    StockDna.objects.filter(sector=raw).update(sector=canon)
            total_s += ns
            total_d += nd
        head = "[dry-run] " if dry else ""
        self.stdout.write(self.style.SUCCESS(
            f"{head}정규화 대상: Stock {total_s}행, StockDna {total_d}행 ({len(SECTOR_MAP)} 매핑)"))
