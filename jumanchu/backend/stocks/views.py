from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from stocks import serializers as s


def _stub():
    return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


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
        return _stub()


@extend_schema(tags=['Stock'])
class StockDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id='stocks_detail',
        summary='종목 상세',
        responses={200: s.StockDetailResponseSerializer},
    )
    def get(self, request, code: str):
        return _stub()


@extend_schema(tags=['Stock'])
class StockPriceView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='현재가 (Redis 3초 캐시)',
        responses={200: s.StockPriceResponseSerializer},
    )
    def get(self, request, code: str):
        return _stub()


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
