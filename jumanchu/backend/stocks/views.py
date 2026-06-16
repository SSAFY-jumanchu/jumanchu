from datetime import date, datetime, timedelta
from decimal import InvalidOperation
from zoneinfo import ZoneInfo

import requests
from django.core.cache import cache
from django.db.models import Count, F, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from stocks import serializers as s
from stocks.models import EconomicEvent, Stock, StockPrice
from stocks.pagination import paginate
from stocks.services.market_summary import market_summary
from stocks.services.price_dispatch import (
    build_today_candle, fetch_minute_candles, fetch_price, get_cache_ttl,
)


PERIOD_INTERVAL_MAP = {
    "1d":  {"1m", "5m", "15m", "1h"},
    "1w":  {"15m", "1h", "1d"},
    "1m":  {"1d", "1w", "1mo"},
    "3m":  {"1d", "1w", "1mo"},
    "1y":  {"1d", "1w", "1mo"},
    "5y":  {"1d", "1w", "1mo"},
}
PERIOD_TO_DAYS = {"1d": 1, "1w": 7, "1m": 30, "3m": 90, "1y": 365, "5y": 1825}
MINUTE_INTERVALS = {"1m", "5m", "15m", "1h"}
DAY_INTERVALS = {"1d", "1w", "1mo"}
_KST = ZoneInfo("Asia/Seoul")


def _stub():
    return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


def _safe_date(value):
    """YYYY-MM-DD → date. 비었거나 형식/값이 잘못되면 None (500 방지)."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _db_price_to_candle(p: StockPrice) -> dict:
    """StockPrice 행 → Candle dict (자정 KST)."""
    return {
        "time": datetime.combine(p.price_date, datetime.min.time(), tzinfo=_KST),
        "open": p.open, "high": p.high, "low": p.low, "close": p.close,
        "volume": p.volume,
    }


def _aggregate_ohlc(window: list[dict]) -> dict:
    return {
        "time": window[0]["time"],
        "open": window[0]["open"],
        "high": max(r["high"] for r in window),
        "low": min(r["low"] for r in window),
        "close": window[-1]["close"],
        "volume": sum(r["volume"] for r in window),
    }


def _resample_daily(rows: list[dict], interval: str) -> list[dict]:
    """일봉 → 주봉/월봉. 1d면 그대로."""
    if interval == "1d" or not rows:
        return rows
    if interval == "1w":
        key_fn = lambda r: r["time"].isocalendar()[:2]  # (year, week)
    elif interval == "1mo":
        key_fn = lambda r: (r["time"].year, r["time"].month)
    else:
        return rows

    out, buf, cur = [], [], None
    for r in rows:
        k = key_fn(r)
        if cur is not None and k != cur:
            out.append(_aggregate_ohlc(buf))
            buf = []
        buf.append(r)
        cur = k
    if buf:
        out.append(_aggregate_ohlc(buf))
    return out


def _parse_bool(v):
    if v is None:
        return None
    s_ = str(v).strip().lower()
    if s_ in ('true', '1', 'yes'):
        return True
    if s_ in ('false', '0', 'no'):
        return False
    return None


def _stock_by_code(code: str):
    """code 단독 lookup. (code, market) 충돌 시 시총 큰 쪽 우선. 없으면 None."""
    return (
        Stock.objects.filter(code=code, is_active=True)
        .order_by(F('market_cap').desc(nulls_last=True), 'market')
        .first()
    )


@extend_schema(tags=['Stock'])
class StockListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id='stocks_list',
        summary='종목 목록·검색',
        parameters=[
            OpenApiParameter('q', str, required=False, description='종목명/코드 검색'),
            OpenApiParameter('market', str, required=False, enum=['KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE']),
            OpenApiParameter('sector', str, required=False),
            OpenApiParameter('is_sp500', bool, required=False),
            OpenApiParameter('is_nasdaq100', bool, required=False),
            OpenApiParameter('sort', str, required=False, enum=['name', 'market_cap', 'volume']),
            OpenApiParameter('page', int, required=False),
            OpenApiParameter('size', int, required=False),
        ],
        responses={200: s.StockListResponseSerializer},
    )
    def get(self, request):
        qs = Stock.objects.filter(is_active=True)

        q = request.query_params.get('q')
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))

        market = request.query_params.get('market')
        if market:
            if market not in Stock.Market.values:
                return Response(
                    {'detail': f'유효하지 않은 market 값: {market}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(market=market)

        sector = request.query_params.get('sector')
        if sector:
            qs = qs.filter(sector__iexact=sector)

        is_sp500 = _parse_bool(request.query_params.get('is_sp500'))
        if is_sp500 is not None:
            qs = qs.filter(is_sp500=is_sp500)

        is_nasdaq100 = _parse_bool(request.query_params.get('is_nasdaq100'))
        if is_nasdaq100 is not None:
            qs = qs.filter(is_nasdaq100=is_nasdaq100)

        # 정렬. volume은 DB 컬럼 없어 market_cap 폴백 (followup §2.2 후속)
        sort = request.query_params.get('sort', 'name')
        if sort == 'market_cap' or sort == 'volume':
            qs = qs.order_by(F('market_cap').desc(nulls_last=True), 'name')
        else:
            qs = qs.order_by('name')

        data = paginate(
            qs,
            page=request.query_params.get('page'),
            size=request.query_params.get('size'),
            item_serializer_cls=s.StockSerializer,
        )
        return Response(data)


@extend_schema(tags=['Stock'])
class StockDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id='stocks_detail',
        summary='종목 상세',
        responses={200: s.StockDetailResponseSerializer},
    )
    def get(self, request, code: str):
        stock = _stock_by_code(code)
        if not stock:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # Watchlist 모델 미존재 (v2) — 인스턴스에 속성 주입해 직렬화 통과.
        stock.is_in_watchlist = False
        return Response({'stock': s.StockDetailSerializer(stock).data})


@extend_schema(tags=['Stock'])
class StockPriceView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='현재가 (장중 3s / 장외 60s 캐시)',
        responses={200: s.StockPriceResponseSerializer},
    )
    def get(self, request, code: str):
        stock = _stock_by_code(code)
        if not stock:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        cache_key = f'stock:price:{stock.market}:{stock.code}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, headers={'Cache-Control': f'max-age={get_cache_ttl(stock)}'})

        try:
            price_dict = fetch_price(stock)
        except (requests.HTTPError, requests.Timeout, RuntimeError, KeyError,
                ValueError, InvalidOperation):
            return Response(
                {'detail': 'KIS 외부 API 오류', 'code': 'EXTERNAL_API_ERROR'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        body = {'price': s.StockPriceSerializer(price_dict).data}
        ttl = get_cache_ttl(stock)
        cache.set(cache_key, body, timeout=ttl)
        return Response(body, headers={'Cache-Control': f'max-age={ttl}'})


@extend_schema(tags=['Stock'])
class StockOrderBookView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='호가창 (Redis 1초 캐시)',
        responses={200: s.OrderBookResponseSerializer},
    )
    def get(self, request, code: str):
        return _stub()


@extend_schema(tags=['Stock'])
class StockChartView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='캔들 차트 (일봉/주봉/월봉=DB, 분봉=KIS, 장중 today 합성)',
        parameters=[
            OpenApiParameter('period', str, required=False,
                             enum=['1d', '1w', '1m', '3m', '1y', '5y']),
            OpenApiParameter('interval', str, required=False,
                             enum=['1m', '5m', '15m', '1h', '1d', '1w', '1mo']),
        ],
        responses={200: s.ChartResponseSerializer},
    )
    def get(self, request, code: str):
        stock = _stock_by_code(code)
        if not stock:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)

        period = request.query_params.get('period', '1d')
        interval = request.query_params.get('interval', '5m')

        if period not in PERIOD_INTERVAL_MAP:
            return Response({'detail': f'유효하지 않은 period: {period}',
                             'code': 'INVALID_PERIOD'},
                            status=status.HTTP_400_BAD_REQUEST)
        if interval not in PERIOD_INTERVAL_MAP[period]:
            return Response(
                {'detail': f'period={period}에 허용되지 않는 interval: {interval}',
                 'code': 'INVALID_INTERVAL_FOR_PERIOD'},
                status=status.HTTP_400_BAD_REQUEST)

        cache_key = f'stock:chart:{stock.market}:{stock.code}:{period}:{interval}'
        ttl = 300 if interval in MINUTE_INTERVALS else 3600
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, headers={'Cache-Control': f'max-age={ttl}'})

        try:
            if interval in MINUTE_INTERVALS:
                candles = fetch_minute_candles(stock, interval)
            else:
                days = PERIOD_TO_DAYS[period]
                start = date.today() - timedelta(days=days)
                qs = (StockPrice.objects
                      .filter(stock=stock, price_date__gte=start)
                      .order_by('price_date'))
                candles = [_db_price_to_candle(p) for p in qs]
                # B 패턴: 장중이면 today 한 칸 합성해 append (1w/1mo는 resample이 받아 합산)
                today_c = build_today_candle(stock)
                if today_c and (not candles
                                or candles[-1]['time'].date() != date.today()):
                    candles.append(today_c)
                candles = _resample_daily(candles, interval)
        except (requests.HTTPError, requests.Timeout, RuntimeError,
                KeyError, ValueError, InvalidOperation):
            return Response(
                {'detail': 'KIS 외부 API 오류', 'code': 'EXTERNAL_API_ERROR'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE)

        body = {
            'stock_code': stock.code,
            'period': period,
            'interval': interval,
            'candles': s.CandleSerializer(candles, many=True).data,
            'generated_at': timezone.now(),
        }
        cache.set(cache_key, body, timeout=ttl)
        return Response(body, headers={'Cache-Control': f'max-age={ttl}'})


@extend_schema(tags=['Stock'])
class StockFinancialsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='재무 요약 + 투자 지표 (DART)',
        parameters=[
            OpenApiParameter('type', str, required=False, enum=['quarterly', 'annual']),
            OpenApiParameter('limit', int, required=False),
        ],
        responses={200: s.FinancialsResponseSerializer},
    )
    def get(self, request, code: str):
        return _stub()


@extend_schema(tags=['Stock'])
class StockPostsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='종목 언급 커뮤니티 글',
        parameters=[
            OpenApiParameter('page', int, required=False),
            OpenApiParameter('size', int, required=False),
        ],
        responses={200: s.StockPostsResponseSerializer},
    )
    def get(self, request, code: str):
        stock = _stock_by_code(code)
        if stock is None:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        from community.models import CommunityPost

        qs = (
            CommunityPost.objects.filter(stock=stock)
            .select_related('user')
            .annotate(comment_count=Count('comments'))
            .order_by('-created_at')
        )
        data = paginate(
            qs,
            page=request.query_params.get('page'),
            size=request.query_params.get('size'),
            item_serializer_cls=s.PostSummarySerializer,
        )
        return Response(data)


@extend_schema(tags=['Stock'])
class MarketSummaryView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='시장 요약 (홈 상단)',
        responses={200: s.MarketSummaryResponseSerializer},
    )
    def get(self, request):
        cached = cache.get('markets:summary')
        if cached is not None:
            return Response(cached)
        try:
            data = market_summary()
        except (requests.HTTPError, requests.Timeout, RuntimeError, KeyError) as e:
            return Response(
                {'detail': f'시장 데이터 조회 실패: {e}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        body = s.MarketSummaryResponseSerializer(data).data
        cache.set('markets:summary', body, timeout=10)  # 명세: Redis 10s TTL
        return Response(body)


@extend_schema(tags=['Market'])
class EconomicEventListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='경제 캘린더 (경제지표 발표 일정)',
        parameters=[
            OpenApiParameter('country', str, required=False, enum=['US', 'KR']),
            OpenApiParameter('importance', str, required=False, enum=['HIGH', 'MEDIUM', 'LOW']),
            OpenApiParameter('from', str, required=False, description='YYYY-MM-DD (event_date 이상)'),
            OpenApiParameter('to', str, required=False, description='YYYY-MM-DD (event_date 이하)'),
            OpenApiParameter('page', int, required=False),
            OpenApiParameter('size', int, required=False),
        ],
        responses={200: s.EconomicEventListResponseSerializer},
    )
    def get(self, request):
        qs = EconomicEvent.objects.all()
        p = request.query_params
        if p.get('country'):
            qs = qs.filter(country=p['country'])
        if p.get('importance'):
            qs = qs.filter(importance=p['importance'])
        date_from = _safe_date(p.get('from'))
        date_to = _safe_date(p.get('to'))
        if date_from:
            qs = qs.filter(event_date__gte=date_from)
        if date_to:
            qs = qs.filter(event_date__lte=date_to)

        data = paginate(
            qs,
            page=p.get('page'),
            size=p.get('size'),
            item_serializer_cls=s.EconomicEventSerializer,
        )
        return Response(data)
