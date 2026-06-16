"""Stock 조회 API (list/detail/price/chart) 통합·단위 테스트."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase

from stocks.models import EconomicEvent, Stock, StockPrice
from stocks.services.price_dispatch import (
    WARNINGS_ALL_FALSE,
    _is_market_open,
    get_cache_ttl,
)


def _kr_price_dict(stock):
    return {
        'stock_code': stock.code,
        'current': Decimal('68000'),
        'open': Decimal('67500'),
        'high': Decimal('68500'),
        'low': Decimal('67000'),
        'prev_close': Decimal('67500'),
        'change': Decimal('500'),
        'change_rate': 0.74,
        'volume': 10000000,
        'trading_value': Decimal('680000000000'),
        'upper_limit': Decimal('87750'),
        'lower_limit': Decimal('47250'),
        'warnings': dict(WARNINGS_ALL_FALSE),
        'fetched_at': timezone.now(),
    }


def _us_price_dict(stock):
    return {
        'stock_code': stock.code,
        'current': Decimal('200.00'),
        'open': Decimal('198.50'),
        'high': Decimal('201.20'),
        'low': Decimal('198.00'),
        'prev_close': Decimal('199.00'),
        'change': Decimal('1.00'),
        'change_rate': 0.5025,
        'volume': 50000000,
        'trading_value': Decimal('10000000000'),
        'upper_limit': Decimal('0'),
        'lower_limit': Decimal('0'),
        'warnings': dict(WARNINGS_ALL_FALSE),
        'fetched_at': timezone.now(),
    }


class StockListTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Stock.objects.create(code='005930', market='KOSPI', name='삼성전자',
                             currency='KRW', market_cap=400_000_000_000_000)
        Stock.objects.create(code='000660', market='KOSPI', name='SK하이닉스',
                             currency='KRW', market_cap=100_000_000_000_000)
        Stock.objects.create(code='AAPL', market='NASDAQ', name='Apple Inc.',
                             currency='USD', market_cap=3_000_000_000_000)
        Stock.objects.create(code='ZZZZ', market='NASDAQ', name='Zeta', currency='USD',
                             market_cap=None, is_active=True)

    def test_list_basic(self):
        url = reverse('stock-list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        body = res.json()
        self.assertEqual(set(body.keys()), {'items', 'page', 'size', 'total'})
        self.assertEqual(body['total'], 4)
        self.assertEqual(len(body['items']), 4)

    def test_list_search(self):
        url = reverse('stock-list')
        res = self.client.get(url, {'q': '삼성'})
        self.assertEqual(res.status_code, 200)
        codes = [it['code'] for it in res.json()['items']]
        self.assertEqual(codes, ['005930'])

    def test_list_filter_market(self):
        url = reverse('stock-list')
        res = self.client.get(url, {'market': 'NASDAQ'})
        self.assertEqual(res.status_code, 200)
        for it in res.json()['items']:
            self.assertEqual(it['market'], 'NASDAQ')

    def test_list_invalid_market(self):
        url = reverse('stock-list')
        res = self.client.get(url, {'market': 'FOO'})
        self.assertEqual(res.status_code, 400)

    def test_list_pagination(self):
        url = reverse('stock-list')
        res = self.client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['total'], 4)
        self.assertEqual(body['size'], 2)
        self.assertEqual(len(body['items']), 2)

    def test_list_sort_market_cap_nulls_last(self):
        url = reverse('stock-list')
        res = self.client.get(url, {'sort': 'market_cap'})
        self.assertEqual(res.status_code, 200)
        codes = [it['code'] for it in res.json()['items']]
        # 시총 큰 순. None인 ZZZZ는 마지막
        self.assertEqual(codes, ['005930', '000660', 'AAPL', 'ZZZZ'])


class StockDetailTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.stock = Stock.objects.create(
            code='005930', market='KOSPI', name='삼성전자', currency='KRW',
            sector='전기·전자', industry='반도체', market_cap=400_000_000_000_000,
        )

    def test_detail_ok(self):
        res = self.client.get(reverse('stock-detail', kwargs={'code': '005930'}))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn('stock', body)
        self.assertEqual(body['stock']['code'], '005930')
        self.assertFalse(body['stock']['is_in_watchlist'])

    def test_detail_not_found(self):
        res = self.client.get(reverse('stock-detail', kwargs={'code': 'ZZZZZZ'}))
        self.assertEqual(res.status_code, 404)


class StockPriceTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.kr = Stock.objects.create(code='005930', market='KOSPI',
                                       name='삼성전자', currency='KRW')
        cls.us = Stock.objects.create(code='AAPL', market='NASDAQ',
                                       name='Apple Inc.', currency='USD')

    def setUp(self):
        cache.clear()

    def test_price_kr(self):
        with patch('stocks.views.fetch_price', return_value=_kr_price_dict(self.kr)) as m:
            res = self.client.get(reverse('stock-price', kwargs={'code': '005930'}))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn('price', body)
        self.assertEqual(body['price']['stock_code'], '005930')
        self.assertEqual(m.call_count, 1)

    def test_price_us(self):
        with patch('stocks.views.fetch_price', return_value=_us_price_dict(self.us)):
            res = self.client.get(reverse('stock-price', kwargs={'code': 'AAPL'}))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['price']['stock_code'], 'AAPL')
        self.assertEqual(float(body['price']['change']), 1.0)

    def test_price_cache_hit(self):
        with patch('stocks.views.fetch_price', return_value=_kr_price_dict(self.kr)) as m:
            self.client.get(reverse('stock-price', kwargs={'code': '005930'}))
            self.client.get(reverse('stock-price', kwargs={'code': '005930'}))
        # 두 번째 호출은 캐시 hit이라 fetch_price 호출 X
        self.assertEqual(m.call_count, 1)

    def test_price_kis_failure(self):
        with patch('stocks.views.fetch_price', side_effect=RuntimeError('KIS down')):
            res = self.client.get(reverse('stock-price', kwargs={'code': '005930'}))
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.json().get('code'), 'EXTERNAL_API_ERROR')


class MarketHoursTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.kr = Stock.objects.create(code='005930', market='KOSPI',
                                       name='삼성전자', currency='KRW')
        cls.us = Stock.objects.create(code='AAPL', market='NASDAQ',
                                       name='Apple Inc.', currency='USD')

    def test_kr_open_weekday_10am_kst(self):
        kst_mon_10 = datetime(2026, 6, 1, 10, 0, tzinfo=ZoneInfo('Asia/Seoul'))
        self.assertTrue(_is_market_open(self.kr.market, kst_mon_10))

    def test_kr_closed_saturday(self):
        kst_sat_10 = datetime(2026, 5, 30, 10, 0, tzinfo=ZoneInfo('Asia/Seoul'))
        self.assertFalse(_is_market_open(self.kr.market, kst_sat_10))

    def test_us_open_weekday_10_30am_et(self):
        et_mon = datetime(2026, 6, 1, 10, 30, tzinfo=ZoneInfo('America/New_York'))
        self.assertTrue(_is_market_open(self.us.market, et_mon))

    @freeze_time('2026-06-01 01:00:00')  # KST 월 10:00 (장중)
    def test_get_cache_ttl_kr_open(self):
        self.assertEqual(get_cache_ttl(self.kr), 3)

    @freeze_time('2026-05-30 01:00:00')  # KST 토 10:00 (장외)
    def test_get_cache_ttl_kr_closed(self):
        self.assertEqual(get_cache_ttl(self.kr), 60)


def _today_synth_candle(stock):
    """build_today_candle mock 반환값. 'time'은 timezone-aware."""
    return {
        'time': timezone.now(),
        'open': Decimal('100'),
        'high': Decimal('110'),
        'low': Decimal('95'),
        'close': Decimal('105'),
        'volume': 12345,
    }


def _minute_candles_mock(stock, interval='1m'):
    base = datetime(2026, 6, 1, 9, 0, tzinfo=ZoneInfo('Asia/Seoul'))
    return [
        {'time': base, 'open': Decimal('100'), 'high': Decimal('102'),
         'low': Decimal('99'), 'close': Decimal('101'), 'volume': 1000},
        {'time': base + timedelta(minutes=1),
         'open': Decimal('101'), 'high': Decimal('103'),
         'low': Decimal('100'), 'close': Decimal('102'), 'volume': 2000},
    ]


class StockChartTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.kr = Stock.objects.create(code='005930', market='KOSPI',
                                       name='삼성전자', currency='KRW')
        # 일봉 5일치 (2026-05-25~05-29, 월요일=2026-06-01 이전)
        for i, d in enumerate(['2026-05-25', '2026-05-26', '2026-05-27',
                                '2026-05-28', '2026-05-29']):
            StockPrice.objects.create(
                stock=cls.kr, price_date=date.fromisoformat(d),
                open=Decimal(67000 + i * 100), high=Decimal(68000 + i * 100),
                low=Decimal(66500 + i * 100), close=Decimal(67500 + i * 100),
                volume=1000000 + i * 1000,
            )

    def setUp(self):
        cache.clear()

    def test_chart_daily_kr_no_synth(self):
        """interval=1d + 장외 시간 → DB 일봉만, today 합성 없음."""
        with patch('stocks.views.build_today_candle', return_value=None):
            res = self.client.get(
                reverse('stock-chart', kwargs={'code': '005930'}),
                {'period': '1m', 'interval': '1d'},
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['stock_code'], '005930')
        self.assertEqual(body['period'], '1m')
        self.assertEqual(body['interval'], '1d')
        self.assertEqual(len(body['candles']), 5)
        # 오래된 것부터 정렬
        times = [c['time'] for c in body['candles']]
        self.assertEqual(times, sorted(times))

    def test_chart_today_synth_during_market_hours(self):
        """장중이면 today 한 칸 append 되어 6개."""
        with patch('stocks.views.build_today_candle',
                    side_effect=lambda stock: _today_synth_candle(stock)):
            res = self.client.get(
                reverse('stock-chart', kwargs={'code': '005930'}),
                {'period': '1m', 'interval': '1d'},
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(len(body['candles']), 6)
        # 마지막이 today 합성 (close=105)
        self.assertEqual(float(body['candles'][-1]['close']), 105.0)

    def test_chart_minute_kr_mock_kis(self):
        """분봉은 KIS 호출(mock) → candles 반환."""
        with patch('stocks.views.fetch_minute_candles',
                    side_effect=lambda stock, interval: _minute_candles_mock(stock, interval)) as m:
            res = self.client.get(
                reverse('stock-chart', kwargs={'code': '005930'}),
                {'period': '1d', 'interval': '5m'},
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['interval'], '5m')
        self.assertEqual(len(body['candles']), 2)
        self.assertEqual(m.call_count, 1)

    def test_chart_cache_hit(self):
        """동일 키 2회 호출 → 2회차 캐시 hit (fetch 1번만)."""
        with patch('stocks.views.fetch_minute_candles',
                    side_effect=lambda stock, interval: _minute_candles_mock(stock, interval)) as m:
            self.client.get(reverse('stock-chart', kwargs={'code': '005930'}),
                            {'period': '1d', 'interval': '5m'})
            self.client.get(reverse('stock-chart', kwargs={'code': '005930'}),
                            {'period': '1d', 'interval': '5m'})
        self.assertEqual(m.call_count, 1)

    def test_chart_invalid_period_interval(self):
        """period=1d × interval=1d → 400 INVALID_INTERVAL_FOR_PERIOD."""
        res = self.client.get(
            reverse('stock-chart', kwargs={'code': '005930'}),
            {'period': '1d', 'interval': '1d'},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get('code'), 'INVALID_INTERVAL_FOR_PERIOD')

    def test_chart_invalid_period(self):
        """알 수 없는 period → 400 INVALID_PERIOD."""
        res = self.client.get(
            reverse('stock-chart', kwargs={'code': '005930'}),
            {'period': '10y', 'interval': '1d'},
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get('code'), 'INVALID_PERIOD')

    def test_chart_404(self):
        res = self.client.get(reverse('stock-chart', kwargs={'code': 'ZZZZZZ'}))
        self.assertEqual(res.status_code, 404)

    def test_chart_503_on_kis_failure(self):
        """분봉 호출 시 KIS 예외 → 503 EXTERNAL_API_ERROR."""
        with patch('stocks.views.fetch_minute_candles',
                    side_effect=RuntimeError('KIS down')):
            res = self.client.get(
                reverse('stock-chart', kwargs={'code': '005930'}),
                {'period': '1d', 'interval': '5m'},
            )
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.json().get('code'), 'EXTERNAL_API_ERROR')


class EconomicEventTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        EconomicEvent.objects.create(
            event_date=date(2026, 6, 9), title='ADP 고용', importance='MEDIUM', country='US')
        EconomicEvent.objects.create(
            event_date=date(2026, 6, 10), title='CPI', importance='HIGH', country='US')
        EconomicEvent.objects.create(
            event_date=date(2026, 6, 11), title='실업률', importance='MEDIUM', country='KR')
        EconomicEvent.objects.create(
            event_date=date(2026, 6, 15), title='NAHB', importance='LOW', country='US')

    def test_list_public_and_envelope(self):
        # 비로그인도 조회 가능(AllowAny) + envelope 모양
        res = self.client.get(reverse('economic-events'))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(set(body.keys()), {'items', 'page', 'size', 'total'})
        self.assertEqual(body['total'], 4)
        # event_date 오름차순 정렬
        dates = [it['event_date'] for it in body['items']]
        self.assertEqual(dates, sorted(dates))

    def test_filter_country(self):
        res = self.client.get(reverse('economic-events'), {'country': 'KR'})
        self.assertEqual(res.json()['total'], 1)
        self.assertEqual(res.json()['items'][0]['country'], 'KR')

    def test_filter_importance(self):
        res = self.client.get(reverse('economic-events'), {'importance': 'HIGH'})
        self.assertEqual(res.json()['total'], 1)
        self.assertEqual(res.json()['items'][0]['title'], 'CPI')

    def test_filter_date_range(self):
        res = self.client.get(reverse('economic-events'),
                              {'from': '2026-06-10', 'to': '2026-06-11'})
        self.assertEqual(res.json()['total'], 2)

    def test_malformed_date_ignored(self):
        # 잘못된 날짜로 500 안 나고 200, 필터 무시
        res = self.client.get(reverse('economic-events'), {'from': '2026-13-99'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['total'], 4)


class StockPostsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        from community.models import CommunityPost
        User = get_user_model()
        cls.stock = Stock.objects.create(code='005930', market='KOSPI',
                                          name='삼성전자', currency='KRW')
        other = Stock.objects.create(code='000660', market='KOSPI',
                                      name='SK하이닉스', currency='KRW')
        u = User.objects.create(username='u1', nickname='유저1', birth_year=1995)
        CommunityPost.objects.create(user=u, stock=cls.stock, category='ANALYSIS',
                                     title='삼성 분석', body='좋음')
        CommunityPost.objects.create(user=u, stock=cls.stock, category='QUESTION',
                                     title='삼성 질문', body='?')
        CommunityPost.objects.create(user=u, stock=other, category='SHARE',
                                     title='하이닉스 글', body='x')

    def test_posts_for_stock_only(self):
        # 비로그인 OK(AllowAny), 그 종목 글만
        res = self.client.get(reverse('stock-posts', kwargs={'code': '005930'}))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(set(body.keys()), {'items', 'page', 'size', 'total'})
        self.assertEqual(body['total'], 2)
        item = body['items'][0]
        self.assertEqual(item['author_nickname'], '유저1')
        self.assertIn('comment_count', item)
        self.assertIn('like_count', item)

    def test_posts_stock_404(self):
        res = self.client.get(reverse('stock-posts', kwargs={'code': 'ZZZZZZ'}))
        self.assertEqual(res.status_code, 404)
