from django.core.management.base import BaseCommand
from stocks.models import Stock, PrototypePool

class Command(BaseCommand):
    help = "원본 DB에서 유효하고 시가총액이 높은 상위 200개 종목을 모든 지표와 함께 프로토타입 풀에 적재합니다."

    def handle(self, *args, **options):
        self.stdout.write("[시작] 프로토타입 풀(시총 상위 200개 + 모든 지표 복사) 빌드를 시작합니다...")

        # 1. 원본 데이터베이스에서 필터링 및 정렬 (최대 200개 추출)
        # 💡 [:100]으로 되어 있던 부분을 [:200]으로 수정했습니다!
        top_stocks = Stock.objects.filter(
            is_valid=True, 
            market_cap__isnull=False
        ).order_by('-market_cap')[:200]

        if not top_stocks.exists():
            self.stdout.write(self.style.ERROR("[오류] 원본 Stock 테이블에 데이터가 없거나 유효한 종목이 없습니다."))
            return

        # 2. 기존 프로토타입 풀 데이터 깔끔하게 비우기
        PrototypePool.objects.all().delete()

        # 3. 데이터 매핑 및 인스턴스 생성
        pool_instances = []
        for index, stock_obj in enumerate(top_stocks, start=1):
            pool_instances.append(
                PrototypePool(
                    stock=stock_obj,          # 1:1 관계 연결 (기본키)
                    rank=index,               # 시총 순위 할당
                    
                    # Stock 모델에 있던 기존 지표값들을 그대로 복사해서 넣어줍니다!
                    code=stock_obj.code,
                    name=stock_obj.name,
                    market_cap=stock_obj.market_cap,
                    per=stock_obj.per,
                    pbr=stock_obj.pbr,
                    eps=stock_obj.eps,
                    bps=stock_obj.bps,
                    beta=stock_obj.beta
                )
            )

        # 4. Bulk Create로 한 번에 쿼리 날려서 저장 (성능 최적화)
        try:
            PrototypePool.objects.bulk_create(pool_instances)
            self.stdout.write(self.style.SUCCESS(f"[완료] 성공적으로 상위 {len(pool_instances)}개의 종목을 PrototypePool에 적재했습니다!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[오류] 프로토타입 풀 저장 중 에러 발생: {e}"))