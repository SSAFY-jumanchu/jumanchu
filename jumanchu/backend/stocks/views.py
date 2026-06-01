from decimal import InvalidOperation

import requests
from django.core.cache import cache
from django.db.models import F, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from stocks import serializers as s
from stocks.models import Stock
from stocks.pagination import paginate
from stocks.services.price_dispatch import fetch_price, get_cache_ttl


def _stub():
    return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


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
        summary='캔들 차트',
        parameters=[
            OpenApiParameter('period', str, required=False,
                             enum=['1d', '1w', '1m', '3m', '1y', '5y']),
            OpenApiParameter('interval', str, required=False,
                             enum=['1m', '5m', '15m', '1h', '1d', '1w', '1mo']),
        ],
        responses={200: s.ChartResponseSerializer},
    )
    def get(self, request, code: str):
        return _stub()


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
        return _stub()


@extend_schema(tags=['Stock'])
class MarketSummaryView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='시장 요약 (홈 상단)',
        responses={200: s.MarketSummaryResponseSerializer},
    )
    def get(self, request):
        return _stub()
