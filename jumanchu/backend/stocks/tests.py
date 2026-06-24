"""Stock 조회 API (list/detail/price/chart) 통합·단위 테스트."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase

from stocks.models import EconomicEvent, FinancialSummary, Stock, StockIndicator, StockPrice
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


class StockOrderBookTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.kr = Stock.objects.create(code='005930', market='KOSPI',
                                       name='삼성전자', currency='KRW')

    def setUp(self):
        cache.clear()

    @staticmethod
    def _ob(code):
        return {
            'stock_code': code,
            'asks': [{'price': Decimal('334000'), 'quantity': 9911},
                     {'price': Decimal('334500'), 'quantity': 33396}],
            'bids': [{'price': Decimal('333500'), 'quantity': 17159}],
            'total_ask_quantity': 166817,
            'total_bid_quantity': 218109,
            'is_market_open': True,
            'fetched_at': timezone.now(),
        }

    def test_orderbook_kr(self):
        with patch('stocks.views.fetch_orderbook', return_value=self._ob('005930')) as m:
            res = self.client.get(reverse('stock-orderbook', kwargs={'code': '005930'}))
        self.assertEqual(res.status_code, 200)
        ob = res.json()['orderbook']
        self.assertEqual(ob['stock_code'], '005930')
        self.assertEqual(len(ob['asks']), 2)
        self.assertEqual(float(ob['asks'][0]['price']), 334000.0)
        self.assertEqual(ob['asks'][0]['quantity'], 9911)
        self.assertEqual(ob['total_bid_quantity'], 218109)
        self.assertTrue(ob['is_market_open'])
        self.assertEqual(m.call_count, 1)

    def test_orderbook_cache_hit(self):
        with patch('stocks.views.fetch_orderbook', return_value=self._ob('005930')) as m:
            self.client.get(reverse('stock-orderbook', kwargs={'code': '005930'}))
            self.client.get(reverse('stock-orderbook', kwargs={'code': '005930'}))
        self.assertEqual(m.call_count, 1)  # 2번째는 캐시 hit이라 fetch_orderbook 호출 X

    def test_orderbook_not_found_404(self):
        res = self.client.get(reverse('stock-orderbook', kwargs={'code': 'ZZZZZZ'}))
        self.assertEqual(res.status_code, 404)

    def test_orderbook_kis_failure_503(self):
        with patch('stocks.views.fetch_orderbook', side_effect=RuntimeError('KIS down')):
            res = self.client.get(reverse('stock-orderbook', kwargs={'code': '005930'}))
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.json().get('code'), 'EXTERNAL_API_ERROR')


class VolumePowerEnrichTests(APITestCase):
    """인기 랭킹 체결강도(거래비율) 부착 — 워밍 캐시 우선 + 미스 즉석 채움(캡)."""

    def setUp(self):
        cache.clear()

    def test_cache_hit_and_miss_fill(self):
        from stocks.services.market_summary import _attach_volume_power
        from stocks.services.price_dispatch import volpower_key
        cache.set(volpower_key('KOSPI', '005930'),
                  {'volume_power': 120.0, 'buy_ratio': 54.5, 'sell_ratio': 45.5})
        items = [{'market': 'KOSPI', 'code': '005930'},   # 캐시 히트
                 {'market': 'KOSPI', 'code': '000660'}]    # 미스 → fetch None
        with patch('stocks.services.market_summary.fetch_volume_power', return_value=None) as m:
            out = _attach_volume_power(items)
        self.assertEqual(out[0]['volume_power'], 120.0)    # 캐시값 그대로
        self.assertEqual(out[0]['buy_ratio'], 54.5)
        self.assertIsNone(out[1]['volume_power'])          # 미스+fetch None → null
        self.assertEqual(m.call_count, 1)                  # 미스 1개만 즉석 호출

    def test_miss_fill_capped(self):
        from stocks.services.market_summary import _attach_volume_power, _VOLPOWER_FILL_LIMIT
        items = [{'market': 'KOSPI', 'code': f'{i:06d}'} for i in range(20)]  # 전부 미스
        vp = {'volume_power': 100.0, 'buy_ratio': 50.0, 'sell_ratio': 50.0}
        with patch('stocks.services.market_summary.fetch_volume_power', return_value=vp) as m:
            out = _attach_volume_power(items)
        self.assertEqual(m.call_count, _VOLPOWER_FILL_LIMIT)  # 즉석 호출은 N개로 제한
        self.assertEqual(sum(1 for it in out if it['volume_power'] is not None),
                         _VOLPOWER_FILL_LIMIT)


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


def _market_client_mock():
    """get_kis_client() 대체 — 지수 + 한국·미국 순위 KIS 호출을 캔드 응답으로 (실호출 금지)."""
    client = MagicMock()
    # 지수
    dom_idx = {
        '0001': {'bstp_nmix_prpr': '8726.60', 'bstp_nmix_prdy_vrss': '180.62',
                 'bstp_nmix_prdy_ctrt': '2.11'},
        '1001': {'bstp_nmix_prpr': '870.50', 'bstp_nmix_prdy_vrss': '-5.20',
                 'bstp_nmix_prdy_ctrt': '-0.59'},
    }
    ovs_idx = {
        'COMP': {'ovrs_nmix_prpr': '26562.23', 'ovrs_nmix_prdy_clpr': '26683.94'},
        'SPX': {'ovrs_nmix_prpr': '7543.57', 'ovrs_nmix_prdy_clpr': '7554.29'},
    }
    client.get_domestic_index.side_effect = lambda iscd: {'output': dom_idx[iscd]}
    client.get_overseas_index.side_effect = lambda iscd, d1, d2: {'output1': ovs_idx[iscd]}

    # 한국 등락률 순위 (0 상승 / 1 하락) + 거래량 순위
    def kr_fluct(sort):
        if sort == '0':
            return {'output': [{'stck_shrn_iscd': '068270', 'hts_kor_isnm': '셀트리온',
                                'stck_prpr': '200000', 'prdy_vrss': '30000', 'prdy_ctrt': '17.6'}]}
        return {'output': [{'stck_shrn_iscd': '005930', 'hts_kor_isnm': '삼성전자',
                            'stck_prpr': '70000', 'prdy_vrss': '-5000', 'prdy_ctrt': '-6.6'}]}
    client.get_domestic_fluctuation.side_effect = kr_fluct
    client.get_domestic_volume_rank.return_value = {'output': [
        {'mksc_shrn_iscd': 'Q530036', 'hts_kor_isnm': '삼성인버스2X',
         'stck_prpr': '2000', 'prdy_vrss': '10', 'prdy_ctrt': '0.5'},   # DB에 없음 → 제외
        {'mksc_shrn_iscd': '252670', 'hts_kor_isnm': 'KODEX인버스',
         'stck_prpr': '5000', 'prdy_vrss': '-100', 'prdy_ctrt': '-2.0'}]}

    # 미국 랭킹은 거래량 순위 풀에서 파생. PENNY(DB없음)/DEAD(is_active=False)는 필터돼야 함
    client.get_overseas_volume_rank.return_value = {'output2': [
        {'symb': 'TSLA', 'name': '테슬라', 'last': '250.00', 'diff': '5.00', 'sign': '2', 'rate': '+2.0'},
        {'symb': 'NVDA', 'name': '엔비디아', 'last': '1200.00', 'diff': '100.00', 'sign': '2', 'rate': '+9.1'},
        {'symb': 'AAPL', 'name': '애플', 'last': '150.00', 'diff': '10.00', 'sign': '5', 'rate': '-6.2'},
        {'symb': 'DEAD', 'name': '상폐예정', 'last': '3.00', 'diff': '1.00', 'sign': '5', 'rate': '-25.0'},
        {'symb': 'PENNY', 'name': '동전주', 'last': '0.50', 'diff': '0.30', 'sign': '2', 'rate': '+150.0'}]}
    return client


class MarketSummaryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # 미국 랭킹 필터용 — DB에 있고 is_active인 종목만 노출돼야 함
        for code, name, active in [('NVDA', '엔비디아', True), ('AAPL', '애플', True),
                                   ('TSLA', '테슬라', True), ('DEAD', '상폐예정', False)]:
            Stock.objects.create(code=code, market='NASDAQ', name=name,
                                 currency='USD', is_active=active)
        # 한국 랭킹 필터용 — Q530036(ETN)은 DB에 없어 랭킹에서 빠져야 함
        for code, name in [('068270', '셀트리온'), ('005930', '삼성전자'), ('252670', 'KODEX인버스')]:
            Stock.objects.create(code=code, market='KOSPI', name=name, currency='KRW')

    def setUp(self):
        cache.clear()

    def test_market_summary_ok(self):
        with patch('stocks.services.market_summary.get_kis_client',
                   return_value=_market_client_mock()):
            res = self.client.get(reverse('markets-summary'))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(set(body.keys()), {'indices', 'kr', 'us', 'fetched_at'})
        # 지수 4개 (국내 직접 / 해외 현재가·전일종가로 등락률 계산)
        idx = {i['code']: i for i in body['indices']}
        self.assertEqual(set(idx), {'KOSPI', 'KOSDAQ', 'COMP', 'SPX'})
        self.assertAlmostEqual(idx['KOSPI']['change_rate'], 2.11, places=2)
        self.assertLess(idx['COMP']['change_rate'], 0)  # 26562.23 < 26683.94
        # 한국 랭킹
        self.assertEqual(set(body['kr']), {'top_gainers', 'top_losers', 'most_active'})
        self.assertEqual(body['kr']['top_gainers'][0]['code'], '068270')
        self.assertEqual(body['kr']['top_gainers'][0]['name'], '셀트리온')
        self.assertEqual(body['kr']['top_losers'][0]['code'], '005930')
        self.assertEqual(Decimal(body['kr']['top_losers'][0]['change']), Decimal('-5000.0000'))
        self.assertEqual(body['kr']['most_active'][0]['code'], '252670')  # mksc_shrn_iscd 사용
        self.assertNotIn('Q530036', [r['code'] for r in body['kr']['most_active']])  # ETN(DB없음) 제외
        # 미국 랭킹 — 거래량 풀(우리 활성 종목)에서 파생. PENNY(DB없음)/DEAD(비활성) 제외
        us = body['us']
        self.assertEqual([r['code'] for r in us['most_active']], ['TSLA', 'NVDA', 'AAPL'])  # 거래량순
        self.assertEqual(us['top_gainers'][0]['code'], 'NVDA')   # 등락률 최고
        self.assertEqual(Decimal(us['top_gainers'][0]['change']), Decimal('100.0000'))
        self.assertEqual(us['top_losers'][0]['code'], 'AAPL')    # 등락률 최저, sign 5 → 음수
        self.assertEqual(Decimal(us['top_losers'][0]['change']), Decimal('-10.0000'))
        self.assertNotIn('PENNY', [r['code'] for r in us['most_active']])
        self.assertNotIn('DEAD', [r['code'] for r in us['most_active']])

    def test_market_summary_cache_hit(self):
        client = _market_client_mock()
        with patch('stocks.services.market_summary.get_kis_client', return_value=client):
            self.client.get(reverse('markets-summary'))
            self.client.get(reverse('markets-summary'))
        # 2번째는 캐시 hit → 국내지수 KIS 호출은 1라운드(코스피·코스닥 2건)만
        self.assertEqual(client.get_domestic_index.call_count, 2)

    def test_market_summary_kr_failure_resilient(self):
        client = _market_client_mock()
        client.get_domestic_fluctuation.side_effect = RuntimeError('KIS down')
        with patch('stocks.services.market_summary.get_kis_client', return_value=client):
            res = self.client.get(reverse('markets-summary'))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        # KR 랭킹은 실패로 빈 리스트, 미국은 살아있음
        self.assertEqual(body['kr'], {'top_gainers': [], 'top_losers': [], 'most_active': []})
        self.assertEqual(body['us']['top_gainers'][0]['code'], 'NVDA')


class StockFinancialsTests(APITestCase):
    """재무 요약 + 투자 지표 API (/stocks/<code>/financials/)."""

    @classmethod
    def setUpTestData(cls):
        cls.stock = Stock.objects.create(code='005930', market='KOSPI', name='삼성전자',
                                         currency='KRW', market_cap=400_000_000_000_000)
        Stock.objects.create(code='000001', market='KOSPI', name='무데이터', currency='KRW')
        # 지표: per/pbr/eps/roe는 펀더멘털 행(옛 날짜), beta/52주는 시장 행(최신) — 병합 검증
        StockIndicator.objects.create(stock=cls.stock, calculated_date=date(2026, 5, 26),
                                      per=14.2, pbr=1.18, eps=22324, roe=8.57, dividend_yield=1.8)
        StockIndicator.objects.create(stock=cls.stock, calculated_date=date(2026, 6, 3),
                                      beta=1.27, high_52w=323000, low_52w=55600)
        # 재무 요약: 연간 2개
        FinancialSummary.objects.create(stock=cls.stock, fiscal_period='2024FY', data_source='DART',
                                        net_profit=34_000_000_000_000, net_profit_yoy=10.0, debt_ratio=24.8)
        FinancialSummary.objects.create(stock=cls.stock, fiscal_period='2023FY', data_source='DART',
                                        net_profit=15_000_000_000_000, debt_ratio=26.0)

    def test_indicator_merged_across_rows(self):
        res = self.client.get(reverse('stock-financials', args=['005930']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ind = res.data['indicator']
        self.assertEqual(ind['per'], 14.2)        # 펀더멘털 행
        self.assertEqual(ind['eps'], 22324)
        self.assertEqual(ind['beta'], 1.27)       # 시장 행 — 다른 행이지만 병합됨
        self.assertEqual(ind['high_52w'], 323000)

    def test_summaries_latest_first(self):
        res = self.client.get(reverse('stock-financials', args=['005930']))
        summ = res.data['summaries']
        self.assertEqual(len(summ), 2)
        self.assertEqual(summ[0]['fiscal_period'], '2024FY')
        self.assertEqual(summ[0]['debt_ratio'], 24.8)
        self.assertEqual(res.data['type'], 'annual')

    def test_quarterly_type_falls_back_when_empty(self):
        res = self.client.get(reverse('stock-financials', args=['005930']), {'type': 'quarterly'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data['summaries']), 1)  # 분기 없음 → 전체 fallback

    def test_404_unknown_code(self):
        res = self.client.get(reverse('stock-financials', args=['999999']))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_data_graceful(self):
        res = self.client.get(reverse('stock-financials', args=['000001']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data['indicator'])
        self.assertEqual(list(res.data['summaries']), [])
