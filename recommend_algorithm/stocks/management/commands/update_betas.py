from django.core.management.base import BaseCommand
from stocks.services import update_prototype_pool_betas


class Command(BaseCommand):
    help = "정제된 200개 프로토타입 풀 주식의 통계적 베타값 계산 및 업데이트"

    def handle(self, *args, **kwargs):
        update_prototype_pool_betas()
        self.stdout.write(self.style.SUCCESS("[완료] 200개 종목 베타값 적재 프로세스 완료!"))