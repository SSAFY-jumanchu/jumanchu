"""
[한국투자증권(KIS) API 연동을 통한 주식 메타 정보 및 지표 enrichment 스크립트]

이 스크립트는 KIS의 '주식현재가 시세(inquire-price)' API를 호출하여, 
데이터베이스에 저장되어 있는 KOSPI 및 KOSDAQ 종목들의 상세 메타데이터와 투자 지표를 업데이트합니다.

업데이트 대상 필드:
-----------------
1. Stock 모델 (기본 주식 정보)
   - sector (업종명)      <- API 응답의 'bstp_kor_isnm' (한글 업종명, 예: "전기·전자")
   - market_cap (시가총액) <- API 응답의 'hts_avls' (KIS API는 '억' 단위로 반환되므로, 100,000,000을 곱해 원화 단위로 환산 후 저장)
2. StockIndicator 모델 (주가 지표 정보 - 일자별 저장 가능 구조)
   - per (주가수익비율)    <- API 응답의 'per' (실수형 변환)
   - pbr (주가순자산비율)  <- API 응답의 'pbr' (실수형 변환)
   - eps (주당순이익)      <- API 응답의 'eps' (정수형 변환)

명령어 사용 예시:
---------------
    # 10개 종목만 테스트로 조회하고, 실제 DB에 반영하지 않고 화면에 출력만 수행 (dry-run)
    python manage.py enrich_stock_meta_from_kis --limit 10 --dry-run

    # 50개 종목에 대해서 실제 DB 반영 수행
    python manage.py enrich_stock_meta_from_kis --limit 50

    # 전체 종목 실행 (호출 제한으로 인해 약 1시간 소요될 수 있음)
    python manage.py enrich_stock_meta_from_kis

    # 업종 정보가 아직 채워지지 않은 종목만 필터링하여 실행 (중단 후 재실행 시 효율적)
    python manage.py enrich_stock_meta_from_kis --only-empty

주의 및 제한 사항:
----------------
1. `.env` 파일에 KIS_APP_KEY, KIS_APP_SECRET, KIS_ENV(실전/모의 구분)가 설정되어 있어야 합니다.
2. 한국투자증권 Open API는 일반 계정의 경우 초당/분당 호출 제한이 존재합니다 (예: 1초당 2회 또는 분당 20회 등, API 권한에 따라 다름).
   - 기본적으로 매 호출 후 0.5초 간격으로 대기(`--sleep 0.5`)하여 API 호출 제한(Rate Limit)을 우회합니다.
   - 실패 시 자동으로 재시도하지 않으며, 에러 로그를 남기고 다음 종목으로 넘어갑니다.
3. 개별 종목 조회 실패가 전체 배치 작업의 중단으로 이어지지 않도록 예외 처리가 꼼꼼하게 되어 있습니다.
"""
from __future__ import annotations

import os
import time
from datetime import date
from typing import Optional

# Django의 커스텀 관리 명령(Management Command)을 만들기 위한 기본 클래스 임포트
from django.core.management.base import BaseCommand
# DB 트랜잭션 처리를 위해 사용 (원자적 연산 보장)
from django.db import transaction
# .env 파일에서 환경 변수를 로드하기 위한 라이브러리 임포트
from dotenv import load_dotenv

# 내부 데이터베이스 모델 임포트
from stocks.models import Stock, StockIndicator
# 한국투자증권 API 통신을 위한 KISClient 및 설정 객체 임포트
from stocks.services.kis_client import KISClient, KISConfig


def _to_float(s: Optional[str]) -> Optional[float]:
    """
    문자열 데이터를 안전하게 실수(float) 타입으로 변환하는 헬퍼 함수.
    
    API 응답에서 숫자가 문자열 형태로 오거나, 값이 없는 경우("-", "", "0.00" 등)를 
    안전하게 예외 없이 처리하여 None 또는 float 값을 반환합니다.
    """
    if s is None:
        return None
    
    # 문자열 앞뒤 공백 제거
    s = str(s).strip()
    
    # 값이 비어있거나 대시('-') 표기, 혹은 특정 값이면 데이터가 없는 것으로 판단하여 처리
    if not s or s in ("-", "0", "0.00"):
        # 단, 진짜 '0'이나 '0.00'일 경우는 상황에 따라 0.0을 반환하도록 설계
        return None if s in ("-", "") else float(s)
        
    try:
        # 정상적인 실수 형태의 문자열을 float로 변환
        return float(s)
    except ValueError:
        # 숫자로 변환할 수 없는 문자열인 경우 에러를 내지 않고 안전하게 None 반환
        return None


def _to_int(s: Optional[str]) -> Optional[int]:
    """
    문자열 데이터를 안전하게 정수(int) 타입으로 변환하는 헬퍼 함수.
    
    소수점이 포함된 문자열(예: '123.0')도 정상적으로 정수(123)로 변환할 수 있도록
    먼저 float로 파싱한 후 int로 캐스팅합니다.
    """
    if s is None:
        return None
        
    # 문자열 앞뒤 공백 제거
    s = str(s).strip()
    
    # 값이 없거나 대시('-') 표기인 경우 None 반환
    if not s or s == "-":
        return None
        
    try:
        # 소수점이 포함된 문자열도 에러 없이 처리하기 위해 float로 먼저 변환 후 int로 캐스팅
        return int(float(s))
    except ValueError:
        # 숫자로 변환할 수 없는 포맷인 경우 안전하게 None 반환
        return None


class Command(BaseCommand):
    # Django management command 실행 시 --help 옵션을 주었을 때 출력되는 설명글
    help = "KIS inquire-price로 Stock.sector/market_cap + StockIndicator per/pbr/eps 채우기"

    def add_arguments(self, parser):
        """
        CLI 명령어로 실행할 때 커스텀 옵션(인자)들을 정의하는 메서드.
        """
        # --limit: 처리할 종목의 최대 개수를 지정 (예: 테스트 시 10개만 돌려보고 싶을 때)
        parser.add_argument("--limit", type=int, default=None, help="처리 종목 수 제한 (테스트용)")
        
        # --dry-run: 실제 DB에 저장하지 않고, API에서 조회한 데이터를 로그로만 확인하고 싶을 때 사용
        parser.add_argument("--dry-run", action="store_true", help="DB 변경 없이 미리보기")
        
        # --sleep: API 호출 간격(초)을 설정하여 한국투자증권 트래픽 제한(Rate Limit)을 피하도록 함
        parser.add_argument("--sleep", type=float, default=0.5, help="호출 간 sleep 초 (기본 0.5)")
        
        # --only-empty: 기존에 이미 sector(업종) 정보가 채워진 종목은 건너뛰고, 비어있는 종목들만 골라서 처리
        parser.add_argument(
            "--only-empty",
            action="store_true",
            help="sector가 비어있는 종목만 처리 (재실행 효율화)",
        )

    def handle(self, *args, **opts):
        """
        명령어가 실행되었을 때 동작하는 메인 실행 로직 메서드.
        """
        # 1. 환경 변수(.env) 로드
        # 프로젝트 루트 경로 기준 상위 디렉토리의 .env 파일을 먼저 로드해 봅니다.
        load_dotenv(dotenv_path="../.env")
        # 현재 디렉토리(backend 폴더 내부)의 .env 파일도 시도하여 로드합니다.
        load_dotenv()

        # 2. 전달받은 옵션 변수화
        limit = opts["limit"]
        dry_run = opts["dry_run"]
        sleep_sec = opts["sleep"]
        only_empty = opts["only_empty"]

        # 3. KIS API 클라이언트 초기화
        # 환경 변수로부터 앱 키, 시크릿 등을 읽어와 KISConfig 객체를 만들고, 이를 사용해 API 클라이언트를 생성합니다.
        client = KISClient(KISConfig.from_env())
        
        # 시작 로그 출력
        self.stdout.write(f"[enrich_stock_meta_from_kis] limit={limit} dry_run={dry_run} sleep={sleep_sec}s only_empty={only_empty}")

        # 4. 대상 주식 조회 (QuerySet 정의)
        # 한국 주식(currency="KRW")이면서 활성화 상태(is_active=True)인 종목들을 가져옵니다.
        # 실행 순서의 일관성을 위해 시장(market)과 종목코드(code) 순으로 정렬합니다.
        qs = Stock.objects.filter(currency="KRW", is_active=True).order_by("market", "code")
        
        # --only-empty 옵션이 켜져 있다면, 업종(sector)이 빈 문자열("")인 종목만 필터링합니다.
        if only_empty:
            qs = qs.filter(sector="")
            
        # --limit 옵션이 지정되었다면, 지정된 개수만큼 쿼리셋을 슬라이싱합니다.
        if limit:
            qs = qs[:limit]

        # 총 대상 개수 파악 및 출력
        total = qs.count()
        self.stdout.write(f"  대상 종목: {total}건")

        # StockIndicator에 저장할 오늘 날짜 계산
        today = date.today()
        
        # 작업 성공 및 실패 횟수를 카운팅하기 위한 변수
        ok = 0
        fail = 0
        
        # 5. 각 주식별로 순회하며 KIS API 호출 및 DB 반영
        # 1부터 시작하는 인덱스(i)와 함께 쿼리셋을 순회합니다.
        for i, stock in enumerate(qs, 1):
            try:
                # KIS API 클라이언트를 통해 종목코드로 현재가 및 주식 상세 정보 조회
                resp = client.get_current_price(stock.code)
                # API 응답 결과에서 실제 데이터가 담긴 'output' 딕셔너리를 추출 (없으면 빈 딕셔너리)
                out = resp.get("output", {})

                # 응답 데이터 파싱 및 타입 변환
                # bstp_kor_isnm: 업종 명칭 (공백 제거)
                bstp = (out.get("bstp_kor_isnm") or "").strip()
                # hts_avls: 시가총액 (원천 데이터는 '억' 단위이므로 정수로 파싱)
                hts_avls = _to_int(out.get("hts_avls"))
                # per, pbr, eps: 주요 투자 지표 안전하게 수치형으로 변환
                per = _to_float(out.get("per"))
                pbr = _to_float(out.get("pbr"))
                eps = _to_int(out.get("eps"))

                # 시가총액 단위를 '원(KRW)' 단위로 맞추기 위해 1억(100,000,000)을 곱해줍니다.
                market_cap_krw = hts_avls * 100_000_000 if hts_avls else None

                # --dry-run인 경우 DB 변경 없이 화면에 데이터가 어떻게 들어오는지 출력만 합니다.
                if dry_run:
                    self.stdout.write(
                        f"  [{i:>4}/{total}] {stock.code} {stock.name}: "
                        f"sector={bstp!r} cap={market_cap_krw} per={per} pbr={pbr} eps={eps}"
                    )
                else:
                    # 실제 DB 반영 시, 원자성(Atomicity)을 보장하기 위해 django의 atomic transaction 블록 사용
                    # 블록 내부의 모든 DB 작업이 성공해야만 커밋되고, 하나라도 실패하면 롤백됩니다.
                    with transaction.atomic():
                        # 1) Stock 모델 인스턴스에 가져온 메타데이터 반영
                        stock.sector = bstp
                        if market_cap_krw is not None:
                            stock.market_cap = market_cap_krw
                        # 필요한 특정 필드만 지정하여 업데이트함으로써 성능 최적화 및 타 프로세스 데이터 덮어쓰기 방지
                        stock.save(update_fields=["sector", "market_cap", "updated_at"])

                        # 2) StockIndicator 모델 인스턴스 등록 또는 업데이트
                        # 주식(stock)과 기준일자(calculated_date)가 동일한 레코드가 있으면 values(defaults)를 업데이트하고,
                        # 없으면 새로 생성(Create)합니다.
                        # 이를 통해 매일 실행 시 중복 생성 없이 당일의 최신 지표가 갱신됩니다.
                        StockIndicator.objects.update_or_create(
                            stock=stock,
                            calculated_date=today,
                            defaults={"per": per, "pbr": pbr, "eps": eps},
                        )
                # 성공 카운트 증가
                ok += 1
                
            except Exception as e:
                # API 호출이나 DB 저장 중 에러가 발생한 경우, 
                # 해당 종목에 대해서만 실패로 처리하고 전체 스크립트가 멈추지 않도록 예외 처리
                fail += 1
                self.stdout.write(self.style.WARNING(
                    f"  [{i:>4}/{total}] {stock.code} {stock.name} FAIL: {e}"
                ))

            # 6. 한국투자증권 API 호출 권한(Rate Limit) 제약을 준수하기 위해 대기(Sleep)
            time.sleep(sleep_sec)

            # 너무 잦은 화면 출력을 방지하기 위해 50건마다 현재까지의 누적 진행 상황 출력
            if i % 50 == 0:
                self.stdout.write(f"    ... 진행 {i}/{total} (ok={ok} fail={fail})")

        # 7. 전체 완료 통계 출력
        self.stdout.write(self.style.SUCCESS(f"[enrich_stock_meta_from_kis] 완료 ok={ok} fail={fail}"))
