"""
경제 캘린더(EconomicEvent) 목업 데이터 시드.

`docs/wireframe_jam/홈_시황강화_목업.html`(Investing.com 경제 캘린더 한글본)
스크린샷에서 옮긴 2026-06-09 ~ 2026-06-26 주요 경제지표 일정 78건을 삽입한다.

정규화 규칙
-----------
- country: 목업의 "우리를"(번역오류) → US, 태극기 → KR.
- title  : 과거 발표일 주석(예: "(2019년 6월)")은 노이즈라 제거.
           기준 기간("5월", "1분기", "(6월)")은 유지.
- importance: 빨간 시간 배지 = HIGH, EIA 휘발유 재고 등 = LOW, 나머지 = MEDIUM.

사용 예
-------
    python manage.py seed_economic_events            # 비어 있을 때만 삽입
    python manage.py seed_economic_events --clear     # 기존 전부 삭제 후 재삽입(멱등)
"""
from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from stocks.models import EconomicEvent

# (event_date, title, importance, country)
EVENTS = [
    (date(2026, 6, 9), "ADP 주간 고용 변동", "MEDIUM", "US"),
    (date(2026, 6, 9), "무역수지 연이율", "MEDIUM", "US"),
    (date(2026, 6, 9), "수출 APR", "LOW", "US"),
    (date(2026, 6, 9), "수입 APR", "LOW", "US"),
    (date(2026, 6, 9), "기존 주택 판매량 5월", "HIGH", "US"),
    (date(2026, 6, 9), "기존 주택 판매량 (월별) 5월", "HIGH", "US"),
    (date(2026, 6, 10), "미국 에너지정보청(EIA) 단기 에너지 전망", "LOW", "US"),
    (date(2026, 6, 10), "API 원유 재고 변동", "MEDIUM", "US"),
    (date(2026, 6, 10), "MBA 30년 만기 주택담보대출 금리", "MEDIUM", "US"),
    (date(2026, 6, 10), "핵심 인플레이션율 (월간) 5월", "HIGH", "US"),
    (date(2026, 6, 10), "5월 핵심 인플레이션율 (전년 동기 대비)", "HIGH", "US"),
    (date(2026, 6, 10), "5월 월간 인플레이션율", "HIGH", "US"),
    (date(2026, 6, 10), "5월 전년 대비 인플레이션율", "HIGH", "US"),
    (date(2026, 6, 10), "소비자물가지수 5월", "MEDIUM", "US"),
    (date(2026, 6, 10), "5월 CPI", "MEDIUM", "US"),
    (date(2026, 6, 10), "미국 에너지정보청(EIA) 원유 재고 변동", "MEDIUM", "US"),
    (date(2026, 6, 10), "미국 에너지정보청(EIA) 휘발유 재고 변동", "LOW", "US"),
    (date(2026, 6, 11), "5월 월간 예산 명세서", "MEDIUM", "US"),
    (date(2026, 6, 11), "5월 실업률", "MEDIUM", "KR"),
    (date(2026, 6, 11), "PPI 월 5월", "HIGH", "US"),
    (date(2026, 6, 11), "코어 PPI 월 5월", "MEDIUM", "US"),
    (date(2026, 6, 11), "신규 실업수당 청구 건수", "MEDIUM", "US"),
    (date(2026, 6, 12), "미시간 소비자 심리 조사 예비치 (6월)", "HIGH", "US"),
    (date(2026, 6, 15), "뉴욕 엠파이어 스테이트 제조업 지수 (6월)", "MEDIUM", "US"),
    (date(2026, 6, 15), "산업생산 월별 5월", "MEDIUM", "US"),
    (date(2026, 6, 15), "NAHB 주택시장지수 (6월)", "MEDIUM", "US"),
    (date(2026, 6, 16), "ADP 주간 고용 변동", "MEDIUM", "US"),
    (date(2026, 6, 16), "건축 허가 예비 심사 5월", "HIGH", "US"),
    (date(2026, 6, 16), "주택 착공 5월", "HIGH", "US"),
    (date(2026, 6, 16), "건축 허가 월별 예비 5월", "MEDIUM", "US"),
    (date(2026, 6, 16), "수출 가격 월별 5월", "MEDIUM", "US"),
    (date(2026, 6, 16), "주택 착공 건수 (월별) 5월", "MEDIUM", "US"),
    (date(2026, 6, 16), "수입 가격 월별 5월", "MEDIUM", "US"),
    (date(2026, 6, 17), "API 원유 재고 변동", "MEDIUM", "US"),
    (date(2026, 6, 17), "MBA 30년 만기 주택담보대출 금리", "MEDIUM", "US"),
    (date(2026, 6, 17), "5월 전월 대비 소매 판매", "HIGH", "US"),
    (date(2026, 6, 17), "소매 판매 관리 그룹 월별 5월", "MEDIUM", "US"),
    (date(2026, 6, 17), "자동차 제외 소매 판매 전월 5월", "MEDIUM", "US"),
    (date(2026, 6, 17), "월별 사업 재고 APR", "MEDIUM", "US"),
    (date(2026, 6, 17), "5월 월별 주택 매매 계약 건수", "MEDIUM", "US"),
    (date(2026, 6, 17), "5월 기준 전년 동기 대비 주택 매매 계약 건수", "MEDIUM", "US"),
    (date(2026, 6, 17), "미국 에너지정보청(EIA) 원유 재고 변동", "MEDIUM", "US"),
    (date(2026, 6, 17), "미국 에너지정보청(EIA) 휘발유 재고 변동", "LOW", "US"),
    (date(2026, 6, 18), "연준의 금리 결정", "HIGH", "US"),
    (date(2026, 6, 18), "FOMC 경제 전망", "HIGH", "US"),
    (date(2026, 6, 18), "연준 기자회견", "HIGH", "US"),
    (date(2026, 6, 18), "신규 실업수당 청구 건수", "MEDIUM", "US"),
    (date(2026, 6, 18), "필라델피아 연방준비은행 제조업 지수 (6월)", "MEDIUM", "US"),
    (date(2026, 6, 19), "순 장기 TIC 흐름 APR", "MEDIUM", "US"),
    (date(2026, 6, 23), "소비자 신뢰도 6월", "MEDIUM", "KR"),
    (date(2026, 6, 23), "ADP 주간 고용 변동", "MEDIUM", "US"),
    (date(2026, 6, 23), "S&P 글로벌 종합 PMI 잠정치 6월", "MEDIUM", "US"),
    (date(2026, 6, 23), "S&P 글로벌 제조업 구매관리자지수(PMI) 6월 잠정치", "MEDIUM", "US"),
    (date(2026, 6, 23), "S&P 글로벌 서비스 PMI 잠정치 6월", "MEDIUM", "US"),
    (date(2026, 6, 24), "API 원유 재고 변동", "MEDIUM", "US"),
    (date(2026, 6, 24), "MBA 30년 만기 주택담보대출 금리", "MEDIUM", "US"),
    (date(2026, 6, 24), "당좌예금 Q1", "MEDIUM", "US"),
    (date(2026, 6, 24), "신규 주택 판매 5월", "MEDIUM", "US"),
    (date(2026, 6, 24), "5월 월별 신규 주택 판매량", "MEDIUM", "US"),
    (date(2026, 6, 24), "미국 에너지정보청(EIA) 원유 재고 변동", "MEDIUM", "US"),
    (date(2026, 6, 24), "미국 에너지정보청(EIA) 휘발유 재고 변동", "LOW", "US"),
    (date(2026, 6, 25), "6월 기업 신뢰도", "MEDIUM", "KR"),
    (date(2026, 6, 25), "핵심 개인소비지출 물가지수 전월 대비 5월", "HIGH", "US"),
    (date(2026, 6, 25), "내구재 주문 월별 5월", "HIGH", "US"),
    (date(2026, 6, 25), "GDP 성장률 전분기 대비 최종 1분기", "HIGH", "US"),
    (date(2026, 6, 25), "개인 소득 (월별) 5월", "HIGH", "US"),
    (date(2026, 6, 25), "개인 지출 월별 5월", "HIGH", "US"),
    (date(2026, 6, 25), "시카고 연방준비은행 국가 활동 지수 5월", "MEDIUM", "US"),
    (date(2026, 6, 25), "내구재 주문량 (운송 제외) 월별 5월", "MEDIUM", "US"),
    (date(2026, 6, 25), "GDP 물가지수 전분기 대비 최종 1분기", "MEDIUM", "US"),
    (date(2026, 6, 25), "신규 실업수당 청구 건수", "MEDIUM", "US"),
    (date(2026, 6, 25), "PCE 물가지수 전월 대비 5월", "MEDIUM", "US"),
    (date(2026, 6, 25), "PCE 물가지수 전년 동기 대비 5월", "MEDIUM", "US"),
    (date(2026, 6, 26), "페드 굴스비 연설", "MEDIUM", "US"),
    (date(2026, 6, 26), "상품 무역수지 예상치 5월", "MEDIUM", "US"),
    (date(2026, 6, 26), "자동차 제외 소매 재고 전월 대비 5월", "MEDIUM", "US"),
    (date(2026, 6, 26), "도매 재고 월별 예상 5월", "MEDIUM", "US"),
    (date(2026, 6, 26), "미시간 소비자 심리 최종 보고서 (6월)", "HIGH", "US"),
]


class Command(BaseCommand):
    help = "경제 캘린더(EconomicEvent) 목업 데이터를 삽입한다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="기존 EconomicEvent를 전부 삭제한 뒤 재삽입(멱등).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = EconomicEvent.objects.all().delete()
            self.stdout.write(f"기존 데이터 삭제: {deleted}건")
        elif EconomicEvent.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "이미 데이터가 있어 건너뜀. 재삽입하려면 --clear 옵션을 쓰세요."
                )
            )
            return

        objs = [
            EconomicEvent(
                event_date=event_date,
                title=title,
                importance=importance,
                country=country,
            )
            for event_date, title, importance, country in EVENTS
        ]
        EconomicEvent.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(f"{len(objs)}건 삽입 완료"))
