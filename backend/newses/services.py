"""newses 서비스 — 네이버 검색 API 호출 래퍼.

view 는 얇게 두고 외부 호출/가공은 여기서 처리한다. (recommend.services 패턴)
"""

from __future__ import annotations

from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from stocks.models import NewsRelatedStock, Stock, StockNews

from portfolio.models import Holding
from recommend.models import UserLikedStock

from newses import rss
from newses.models import FeedNews, NewsSector
from newses.naver_news import build_query, enrich_bodies, search_news
from newses.news_sector import StockRef, extract_sectors
from newses.topic_sector import extract_topic_sectors

# 집계(관심/보유) 시 종목당 네이버 호출 1회 → 호출 폭주/지연 방지 상한
_MAX_AGG_STOCKS = 15

_KST = ZoneInfo("Asia/Seoul")


def _news_ttl() -> int:
    """외부 뉴스 캐시 TTL: 장중(평일 09:00~15:30 KST) 60초, 장외 300초."""
    now = timezone.now().astimezone(_KST)
    in_session = now.weekday() < 5 and (9, 0) <= (now.hour, now.minute) <= (15, 30)
    return 60 if in_session else 300


def _cache_get(key):
    try:
        return cache.get(key)
    except Exception:
        return None  # 캐시 백엔드 장애(Redis 다운 등) → 캐시 미사용으로 폴백


def _cache_set(key, value, ttl):
    try:
        cache.set(key, value, ttl)
    except Exception:
        pass


def search_stock_news(
    query: str,
    *,
    display: int = 10,
    sort: str = "date",
    with_body: bool = False,
    limit: int = 8,
) -> list[dict]:
    """종목명/검색어로 네이버 뉴스 조회 → dict 리스트.

    with_body=False: 검색 스니펫(summary)만 — 빠름(네이버 호출 1회).
    with_body=True : news.naver.com 호스팅 기사 본문 전체까지 — 느림(기사당 추가 호출).
    외부 호출이라 캐시(장중 1분/장외 5분) 적용 — 종목상세·검색·집계가 공유.
    """
    cache_key = f"news:naver:{query}:{display}:{sort}:{int(with_body)}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    articles = search_news(build_query(query), display=display, sort=sort)
    if with_body:
        # 본문 채움: news.naver.com 호스팅 기사만 추출(상한 limit개, 최대 2000자).
        # 비호스팅 기사는 전체 결과에 그대로 두되 본문은 빈값(요약으로 대체).
        articles = enrich_bodies(articles, limit=limit)
    result = [a.to_dict() for a in articles]
    _cache_set(cache_key, result, _news_ttl())
    return result


def _load_stock_refs() -> list[StockRef]:
    """DB Stock → 알고리즘 입력 StockRef 목록 (code/name/sector)."""
    return [
        StockRef(code, name, sector)
        for code, name, sector in Stock.objects.values_list("code", "name", "sector")
    ]


@transaction.atomic
def ingest_feed(category: str = "economy") -> dict:
    """RSS 피드 수집 → StockNews 저장 → 관련주 태깅. 재실행 안전(idempotent).

    - StockNews 는 url 기준 dedup(get_or_create).
    - 이미 관련주가 달린 기존 뉴스는 재태깅 스킵(중복 방지·가벼움).
    - 종목 미언급 거시 뉴스는 태그 0개로 저장만 됨(정상).
    """
    articles = rss.fetch_feed(category)
    stock_refs = _load_stock_refs()
    by_code = {s.code: s for s in Stock.objects.all()}

    new_news = 0
    new_cats = 0
    new_links = 0
    new_sectors = 0
    for a in articles:
        if not a.url:
            continue
        news, created = StockNews.objects.get_or_create(
            url=a.url,
            defaults={
                "title": a.title[:300],
                "source": a.source[:50],
                "published_at": a.published_at or timezone.now(),
            },
        )
        if created:
            new_news += 1

        # 카테고리 부여 (한 기사가 여러 피드에 걸칠 수 있음 → 누적, idempotent)
        _, cat_created = FeedNews.objects.get_or_create(news=news, category=category)
        new_cats += int(cat_created)

        # 태깅: 이미 처리된 기존 뉴스는 스킵(내용 불변). 과거 미태깅 뉴스는 1회 백필.
        if not created and (news.related_stocks.exists() or news.sectors.exists()):
            continue
        body_text = a.summary or a.body
        entity_tags = extract_sectors(a.title, stock_refs, summary=body_text)
        topic_tags = extract_topic_sectors(a.title, summary=body_text)

        # (1) 관련주 링크 — 엔티티 매칭으로 잡힌 구체 종목
        for tag in entity_tags:
            score = Decimal(str(round(tag.score, 3)))
            for code in tag.stock_codes:
                stock = by_code.get(code)
                if stock is None:
                    continue
                _, link_created = NewsRelatedStock.objects.get_or_create(
                    news=news, stock=stock,
                    defaults={"relevance_score": score},
                )
                new_links += int(link_created)

        # (2) 섹터 신호 — 엔티티+토픽 병합(섹터별 최대 점수). 추천 매칭용 단일 소스.
        sector_scores: dict[str, float] = {}
        for tag in (*entity_tags, *topic_tags):
            if tag.sector:
                sector_scores[tag.sector] = max(sector_scores.get(tag.sector, 0.0), tag.score)
        for sector, sc in sector_scores.items():
            _, sec_created = NewsSector.objects.get_or_create(
                news=news, sector=sector,
                defaults={"score": Decimal(str(round(sc, 3)))},
            )
            new_sectors += int(sec_created)

    return {
        "fetched": len(articles),
        "new_news": new_news,
        "new_cats": new_cats,
        "new_links": new_links,
        "new_sectors": new_sectors,
    }


def feed_news(*, category: str | None = None, sector: str | None = None,
              limit: int = 20) -> list[dict]:
    """저장된 피드 뉴스 + 카테고리 + 관련주 + 섹터 신호(NewsSector).

    category 지정 시 해당 피드만, sector 지정 시 그 섹터 신호를 가진 뉴스만.
    """
    qs = StockNews.objects.all()
    if category:
        qs = qs.filter(feed_categories__category=category)
    if sector:
        qs = qs.filter(sectors__sector=sector)
    qs = (
        qs.order_by("-published_at")
        .prefetch_related("feed_categories", "related_stocks__stock", "sectors")
        .distinct()[:limit]
    )
    out: list[dict] = []
    for n in qs:
        related = [
            {
                "code": rel.stock.code,
                "name": rel.stock.name,
                "sector": rel.stock.sector,
                "relevance_score": float(rel.relevance_score),
            }
            for rel in n.related_stocks.all()
        ]
        sectors = sorted(
            ({"sector": sg.sector, "score": float(sg.score)} for sg in n.sectors.all()),
            key=lambda x: -x["score"],
        )
        out.append({
            "title": n.title,
            "url": n.url,
            "source": n.source,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "categories": sorted({fc.category for fc in n.feed_categories.all()}),
            "related_stocks": related,
            "sectors": sectors,
        })
    return out


def stocks_news(stocks, *, per_stock: int = 3, limit: int = 10, sort: str = "date") -> list[dict]:
    """여러 종목 → 종목별 네이버 뉴스 병합. 각 item에 stock 배지 부착, 최신순 top limit.

    종목당 네트워크 1회(캐시 적용 — 반복/공유 호출은 캐시에서 응답) → 호출부에서 종목 수 제한.

    시장 전체 기사가 여러 종목 검색에 겹쳐 나오므로 url 기준으로 중복 제거한다
    (배지는 먼저 매칭된 종목 = 종목 순회 순서상 첫 종목).
    """
    items: list[dict] = []
    seen_urls: set[str] = set()
    for st in stocks:
        try:
            arts = search_stock_news(st.name, display=per_stock, sort=sort)  # 종목별 캐시 재사용
        except Exception:
            continue  # 한 종목 실패가 전체를 막지 않음
        for d in arts[:per_stock]:
            url = d["url"]
            if url in seen_urls:        # 중복 기사 → 1건만 유지
                continue
            seen_urls.add(url)
            items.append({**d, "stock": {"code": st.code, "name": st.name}})
    items.sort(key=lambda d: d["published_at"] or "", reverse=True)
    return items[:limit]


def watchlist_news(user, *, per_stock: int = 3, limit: int = 10) -> list[dict]:
    """유저 관심종목(UserLikedStock) → 종목별 네이버 뉴스 병합."""
    stocks = [
        liked.stock
        for liked in UserLikedStock.objects.filter(user=user, is_active=True)
        .select_related("stock").order_by("-liked_at")[:_MAX_AGG_STOCKS]
    ]
    return stocks_news(stocks, per_stock=per_stock, limit=limit)


def holdings_news(user, *, per_stock: int = 3, limit: int = 10) -> list[dict]:
    """유저 보유종목(Holding) → 종목별 네이버 뉴스 병합."""
    stocks = [
        h.stock
        for h in Holding.objects.filter(user=user, quantity__gt=0)
        .select_related("stock").order_by("-updated_at")[:_MAX_AGG_STOCKS]
    ]
    return stocks_news(stocks, per_stock=per_stock, limit=limit)
