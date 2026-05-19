from django.core.management.base import BaseCommand
from stocks.services import collect_all_stocks


class Command(BaseCommand):
    help = "코스피 전체 데이터 수집"

    def handle(self, *args, **kwargs):
        collect_all_stocks()
        self.stdout.write(self.style.SUCCESS("🎉 완료"))