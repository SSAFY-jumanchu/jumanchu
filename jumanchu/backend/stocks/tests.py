"""Stock 조회 API (list/detail/price) 통합·단위 테스트."""
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase

from stocks.models import Stock
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
