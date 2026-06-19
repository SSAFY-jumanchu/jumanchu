from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from stocks.models import NewsRelatedStock, Stock, StockNews
from portfolio.models import Holding
from recommend.models import UserLikedStock
from newses import services
from newses.models import FeedNews, NewsSector
from newses.naver_news import NaverArticle, _press_from_url, extract_body, MAX_BODY_CHARS
from newses import rss
from newses.rss import FeedArticle
from newses.views import (
    FeedNewsView, HoldingsNewsView, SectorNewsView, StockNewsSearchView,
    StockNewsView, WatchlistNewsView,
)
from newses.topic_sector import (
    CANONICAL_SECTORS, TOPIC_KEYWORDS, extract_topic_sectors,
)

_LOCMEM_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

_RSS_BYTES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<rss version="2.0"><channel><title>c</title>'
    '<item><title>테스트 기사</title><link>https://example.com/a</link>'
    '<pubDate>Thu, 18 Jun 2026 09:00:00 +0900</pubDate>'
    '<description>요약</description></item>'
    '</channel></rss>'
).encode('utf-8')

_FAKE_ARTICLE = {
    'title': '삼성전자 신고가',
    'url': 'https://n.example/1',
    'source': '이데일리',
    'published_at': '2026-06-18T09:00:00+00:00',
    'summary': '요약 스니펫',
    'body': '',
}


def _feed_article(title, url, summary=''):
    return FeedArticle(
        title=title, url=url,
        published_at=datetime(2026, 6, 18, 9, 0, tzinfo=dt_timezone.utc),
        summary=summary, body='', author='기자', source='연합뉴스TV', category='경제',
    )


class StockNewsSearchViewTests(SimpleTestCase):
    """검색어 기반 뷰 — DB 미사용이라 SimpleTestCase + 네트워크 모킹."""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_missing_query_returns_400(self):
        response = StockNewsSearchView.as_view()(self.factory.get('/api/v1/news/'))
        self.assertEqual(response.status_code, 400)

    @patch('newses.services.search_stock_news', return_value=[_FAKE_ARTICLE])
    def test_returns_items(self, mock_search):
        request = self.factory.get('/api/v1/news/', {'query': '삼성전자'})
        response = StockNewsSearchView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['query'], '삼성전자')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['items'][0]['title'], '삼성전자 신고가')
        self.assertIn('content', response.data['items'][0])   # 본문 필드 노출
        mock_search.assert_called_once()

    @patch('newses.services.search_stock_news', return_value=[_FAKE_ARTICLE])
    def test_content_param_requests_full_body(self, mock_search):
        req = self.factory.get('/api/v1/news/', {'query': '삼성전자', 'content': 'true'})
        StockNewsSearchView.as_view()(req)
        self.assertTrue(mock_search.call_args.kwargs['with_body'])

    @patch('newses.services.search_stock_news', side_effect=RuntimeError('키 없음'))
    def test_missing_credentials_returns_503(self, _mock):
        request = self.factory.get('/api/v1/news/', {'query': '삼성전자'})
        response = StockNewsSearchView.as_view()(request)
        self.assertEqual(response.status_code, 503)


class StockNewsViewTests(TestCase):
    """종목 코드 기반 뷰 — Stock 조회가 있어 TestCase(DB)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.stock = Stock.objects.create(
            code='005930', name='삼성전자', market='KOSPI', sector='반도체', currency='KRW'
        )

    @patch('newses.services.search_stock_news', return_value=[_FAKE_ARTICLE])
    def test_known_code_returns_stock_and_news(self, mock_search):
        request = self.factory.get('/api/v1/news/stocks/005930/')
        response = StockNewsView.as_view()(request, code='005930')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stock']['name'], '삼성전자')
        self.assertEqual(response.data['stock']['sector'], '반도체')
        self.assertEqual(response.data['count'], 1)
        mock_search.assert_called_once_with('삼성전자', display=10, sort='date', with_body=False)

    def test_unknown_code_returns_404(self):
        request = self.factory.get('/api/v1/news/stocks/999999/')
        response = StockNewsView.as_view()(request, code='999999')
        self.assertEqual(response.status_code, 404)


class IngestFeedTests(TestCase):
    """RSS 수집 → StockNews + FeedNews(카테고리) + 관련주 + NewsSector(섹터 신호)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        Stock.objects.create(code='005930', name='삼성전자', market='KOSPI',
                             sector='반도체', currency='KRW')

    @patch('newses.rss.fetch_feed')
    def test_ingest_persists_category_links_and_sectors(self, mock_fetch):
        mock_fetch.return_value = [
            _feed_article('삼성전자 신고가 경신', 'https://y.example/1'),  # 엔티티
            _feed_article('한은 기준금리 동결', 'https://y.example/2'),    # 토픽(금리)
        ]
        result = services.ingest_feed('economy')

        self.assertEqual(result['new_news'], 2)
        self.assertEqual(result['new_cats'], 2)
        self.assertEqual(result['new_sectors'], 2)  # 반도체(엔티티) + 금융(토픽)
        self.assertEqual(FeedNews.objects.filter(category='economy').count(), 2)
        # 엔티티: 삼성전자 → 관련주 링크 + 섹터(반도체)
        self.assertEqual(NewsRelatedStock.objects.get().stock.code, '005930')
        sam = StockNews.objects.get(url='https://y.example/1')
        self.assertEqual([sg.sector for sg in sam.sectors.all()], ['반도체'])
        # 토픽: '금리' 거시 뉴스 → 관련주 없음, 섹터 신호(금융)만
        rate = StockNews.objects.get(url='https://y.example/2')
        self.assertFalse(rate.related_stocks.exists())
        self.assertEqual([sg.sector for sg in rate.sectors.all()], ['금융'])

    @patch('newses.rss.fetch_feed')
    def test_ingest_is_idempotent(self, mock_fetch):
        mock_fetch.return_value = [_feed_article('삼성전자 신고가', 'https://y.example/1')]
        services.ingest_feed('economy')
        second = services.ingest_feed('economy')

        self.assertEqual(second['new_news'], 0)
        self.assertEqual(second['new_cats'], 0)
        self.assertEqual(second['new_links'], 0)
        self.assertEqual(second['new_sectors'], 0)
        self.assertEqual(NewsSector.objects.count(), 1)

    @patch('newses.rss.fetch_feed')
    def test_cross_posted_article_gets_multiple_categories(self, mock_fetch):
        mock_fetch.return_value = [_feed_article('美 전쟁 우려에 방산주 들썩', 'https://y.example/9')]
        services.ingest_feed('world')
        services.ingest_feed('politics')

        self.assertEqual(StockNews.objects.count(), 1)  # url 기준 dedup
        cats = set(FeedNews.objects.values_list('category', flat=True))
        self.assertEqual(cats, {'world', 'politics'})

    @patch('newses.rss.fetch_feed')
    def test_feed_endpoint_returns_sector_signals(self, mock_fetch):
        mock_fetch.return_value = [_feed_article('삼성전자 신고가', 'https://y.example/1')]
        services.ingest_feed('economy')

        response = FeedNewsView.as_view()(
            self.factory.get('/api/v1/news/feed/economy/'), category='economy'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['category'], 'economy')
        self.assertEqual(response.data['count'], 1)
        item = response.data['items'][0]
        self.assertIn('economy', item['categories'])
        self.assertEqual(item['related_stocks'][0]['code'], '005930')
        self.assertEqual(item['sectors'][0]['sector'], '반도체')

    @patch('newses.rss.fetch_feed')
    def test_by_sector_endpoint_returns_topic_news(self, mock_fetch):
        mock_fetch.return_value = [_feed_article('한은 기준금리 동결', 'https://y.example/2')]
        services.ingest_feed('economy')

        response = SectorNewsView.as_view()(
            self.factory.get('/api/v1/news/by-sector/', {'sector': '금융'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['sector'], '금융')
        self.assertEqual(response.data['count'], 1)

    def test_by_sector_invalid_returns_400(self):
        response = SectorNewsView.as_view()(
            self.factory.get('/api/v1/news/by-sector/', {'sector': '없는섹터'})
        )
        self.assertEqual(response.status_code, 400)


class TopicSectorTests(SimpleTestCase):
    """토픽→섹터 키워드 레이어 (순수 함수)."""

    def test_keywords_map_only_to_canonical_sectors(self):
        canon = set(CANONICAL_SECTORS)
        bad = {s for sectors in TOPIC_KEYWORDS.values() for s in sectors if s not in canon}
        self.assertEqual(bad, set(), f"정본 22 섹터 밖 매핑: {bad}")

    def test_war_headline_maps_to_defense(self):
        tags = extract_topic_sectors('美 국방 "유럽 방위는 유럽이 주도해야"')
        self.assertTrue(tags)
        self.assertEqual(tags[0].sector, '운송장비·부품')
        self.assertEqual(tags[0].stock_codes, [])

    def test_rate_headline_maps_to_finance(self):
        tags = extract_topic_sectors('한국은행 기준금리 동결…대출 금리 영향은')
        self.assertIn('금융', [t.sector for t in tags])

    def test_oil_maps_to_chemical_and_utility(self):
        sectors = [t.sector for t in extract_topic_sectors('중동 리스크에 국제 유가 급등')]
        self.assertIn('화학', sectors)
        self.assertIn('전기·가스', sectors)

    def test_no_topic_returns_empty(self):
        self.assertEqual(extract_topic_sectors('홍명보호, 멕시코전 준비 완료'), [])


class PressSourceTests(SimpleTestCase):
    """originallink 도메인 → 언론사명 역산."""

    def test_known_domains(self):
        self.assertEqual(_press_from_url('https://www.edaily.co.kr/news/x'), '이데일리')
        self.assertEqual(_press_from_url('https://biz.chosun.com/site/x'), '조선비즈')
        self.assertEqual(_press_from_url('https://stock.hankyung.com/a'), '한국경제')
        # 정확매칭이 .chosun.com 서브도메인 폴백을 이김
        self.assertEqual(_press_from_url('https://it.chosun.com/x'), 'IT조선')
        self.assertEqual(_press_from_url('https://www.tokenpost.kr/x'), '토큰포스트')

    def test_unknown_domain_falls_back_to_host(self):
        self.assertEqual(_press_from_url('https://unknown.example.com/a'), 'unknown.example.com')

    def test_empty(self):
        self.assertEqual(_press_from_url(''), '')


def _naver_article(title='제목', source='이데일리', url='https://www.edaily.co.kr/a'):
    return NaverArticle(
        title, 'https://n.naver/x', url,
        datetime(2026, 6, 18, 9, 0, tzinfo=dt_timezone.utc), '요약', '', source,
    )


@override_settings(CACHES=_LOCMEM_CACHE)
class AggregatedNewsTests(TestCase):
    """관심/보유 종목 뉴스 집계 (네이버 search_news 모킹)."""

    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username='newsu', password='pw', nickname='뉴스유저', birth_year=1990,
            email='n@e.com',
        )
        self.s1 = Stock.objects.create(code='005930', name='삼성전자', market='KOSPI',
                                       sector='전기·전자', currency='KRW')
        self.s2 = Stock.objects.create(code='000660', name='SK하이닉스', market='KOSPI',
                                       sector='전기·전자', currency='KRW')

    @patch('newses.services.search_news')
    def test_watchlist_news_aggregates_with_badges(self, mock_search):
        mock_search.side_effect = [
            [_naver_article(url='https://news/1')],
            [_naver_article(url='https://news/2')],
        ]
        UserLikedStock.objects.create(user=self.user, stock=self.s1)
        UserLikedStock.objects.create(user=self.user, stock=self.s2)

        request = self.factory.get('/api/v1/news/watchlist/')
        force_authenticate(request, user=self.user)
        response = WatchlistNewsView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)  # 서로 다른 기사 2건
        self.assertEqual(
            {it['stock']['code'] for it in response.data['items']}, {'005930', '000660'}
        )
        self.assertEqual(response.data['items'][0]['source'], '이데일리')

    @patch('newses.services.search_news', return_value=[_naver_article(url='https://same/x')])
    def test_aggregation_dedups_market_wide_article(self, mock_search):
        # 같은 기사가 두 종목 검색에 겹쳐 나와도 url 기준 1건만
        UserLikedStock.objects.create(user=self.user, stock=self.s1)
        UserLikedStock.objects.create(user=self.user, stock=self.s2)

        request = self.factory.get('/api/v1/news/watchlist/')
        force_authenticate(request, user=self.user)
        response = WatchlistNewsView.as_view()(request)

        self.assertEqual(response.data['count'], 1)

    @patch('newses.services.search_news', return_value=[_naver_article()])
    def test_holdings_news_aggregates(self, mock_search):
        Holding.objects.create(user=self.user, stock=self.s1, quantity=10)

        request = self.factory.get('/api/v1/news/holdings/')
        force_authenticate(request, user=self.user)
        response = HoldingsNewsView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['items'][0]['stock']['name'], '삼성전자')

    def test_watchlist_news_requires_auth(self):
        response = WatchlistNewsView.as_view()(self.factory.get('/api/v1/news/watchlist/'))
        self.assertEqual(response.status_code, 401)


@override_settings(CACHES=_LOCMEM_CACHE)
class NewsCacheTests(SimpleTestCase):
    """search_stock_news 캐시 동작 (LocMem로 격리)."""

    def setUp(self):
        cache.clear()

    @patch('newses.services.search_news', return_value=[_naver_article(url='https://c/1')])
    def test_search_stock_news_is_cached(self, mock_search):
        first = services.search_stock_news('삼성전자', display=5)
        second = services.search_stock_news('삼성전자', display=5)
        self.assertEqual(first, second)
        mock_search.assert_called_once()  # 2번째는 캐시에서

    @patch('newses.services.search_news', return_value=[_naver_article(url='https://c/2')])
    def test_distinct_params_not_shared(self, mock_search):
        services.search_stock_news('삼성전자', display=5)
        services.search_stock_news('삼성전자', display=10)  # 다른 display → 다른 키
        self.assertEqual(mock_search.call_count, 2)


class BodyExtractionTests(SimpleTestCase):
    """본문 추출 + 2000자 컷."""

    def test_truncates_to_max(self):
        html = '<article id="dic_area">' + ('가' * 5000) + '</article>'
        self.assertEqual(len(extract_body(html)), MAX_BODY_CHARS)

    def test_empty_when_no_container(self):
        self.assertEqual(extract_body('<div>본문 컨테이너 없음</div>'), '')


class FetchFeedTests(SimpleTestCase):
    """여러 매체 RSS 병합 + 실패 내성 (rss.fetch_feed)."""

    @patch('newses.rss._get', return_value=_RSS_BYTES)
    def test_combines_all_sources_with_source_name(self, mock_get):
        arts = rss.fetch_feed('economy')
        n = len(rss.FEEDS['economy'])
        self.assertEqual(len(arts), n)                                   # 매체당 1건
        self.assertEqual({a.source for a in arts}, {s for s, _ in rss.FEEDS['economy']})
        self.assertEqual(mock_get.call_count, n)

    @patch('newses.rss._get', side_effect=RuntimeError('network'))
    def test_resilient_when_all_fail(self, mock_get):
        self.assertEqual(rss.fetch_feed('economy'), [])                  # 예외 없이 빈 리스트

    def test_unknown_category_raises(self):
        with self.assertRaises(ValueError):
            rss.fetch_feed('nope')
