from django.core.management.base import BaseCommand

from newses import rss, services


class Command(BaseCommand):
    help = "연합뉴스 RSS를 수집해 StockNews 저장 + 카테고리(FeedNews)/관련주(NewsRelatedStock) 태깅"

    def add_arguments(self, parser):
        parser.add_argument(
            "--category", default="all",
            help=f"수집 카테고리: {'|'.join(rss.FEEDS)}|all (기본 all)",
        )

    def handle(self, *args, **options):
        cat = options["category"]
        if cat != "all" and cat not in rss.FEEDS:
            self.stderr.write(self.style.ERROR(
                f"알 수 없는 카테고리: {cat} (가능: {list(rss.FEEDS)}|all)"))
            return
        categories = list(rss.FEEDS) if cat == "all" else [cat]
        for c in categories:
            r = services.ingest_feed(c)
            self.stdout.write(self.style.SUCCESS(
                f"[ingest:{c}] fetched={r['fetched']} new_news={r['new_news']} "
                f"new_cats={r['new_cats']} new_links={r['new_links']}"))
