from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from portfolio import serializers as s


def _stub():
    return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@extend_schema(tags=['Order'])
class OrderPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='매매 시뮬레이션',
        request=s.OrderPreviewRequestSerializer,
        responses={200: s.OrderPreviewResponseSerializer},
    )
    def post(self, request):
        return _stub()


@extend_schema(tags=['Order'])
class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='매매 주문 실행',
        request=s.OrderCreateRequestSerializer,
        responses={201: s.OrderCreateResponseSerializer},
    )
    def post(self, request):
        return _stub()

    @extend_schema(
        operation_id='orders_list',
        summary='주문 내역 조회',
        parameters=[
            OpenApiParameter('side', str, required=False, enum=['BUY', 'SELL']),
            OpenApiParameter('stock_code', str, required=False),
            OpenApiParameter('status', str, required=False, enum=['PENDING', 'FILLED', 'FAILED']),
            OpenApiParameter('from', str, required=False, description='YYYY-MM-DD'),
            OpenApiParameter('to', str, required=False, description='YYYY-MM-DD'),
            OpenApiParameter('page', int, required=False),
            OpenApiParameter('size', int, required=False),
        ],
        responses={200: s.OrderListResponseSerializer},
    )
    def get(self, request):
        return _stub()


@extend_schema(tags=['Order'])
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='orders_detail',
        summary='주문 상세',
        responses={200: s.OrderDetailResponseSerializer},
    )
    def get(self, request, id: int):
        return _stub()


@extend_schema(tags=['Portfolio'])
class PortfolioSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='포트폴리오 통합 조회 (홈 위젯용)',
        responses={200: s.PortfolioSummaryResponseSerializer},
    )
    def get(self, request):
        return _stub()


@extend_schema(tags=['Portfolio'])
class HoldingsListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='portfolio_holdings_list',
        summary='보유 종목 리스트',
        parameters=[
            OpenApiParameter('sort', str, required=False,
                             enum=['value', 'profit_loss', 'profit_loss_rate', 'code']),
            OpenApiParameter('order', str, required=False, enum=['asc', 'desc']),
        ],
        responses={200: s.HoldingsListResponseSerializer},
    )
    def get(self, request):
        return _stub()


@extend_schema(tags=['Portfolio'])
class HoldingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='portfolio_holding_detail',
        summary='특정 종목 보유 상세 (Order 내역 포함)',
        responses={200: s.HoldingDetailResponseSerializer},
    )
    def get(self, request, code: str):
        return _stub()


@extend_schema(tags=['Portfolio'])
class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Account 잔액',
        responses={200: s.BalanceResponseSerializer},
    )
    def get(self, request):
        return _stub()


@extend_schema(tags=['Portfolio'])
class AllocationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='자산 배분 (섹터/종목별)',
        responses={200: s.AllocationResponseSerializer},
    )
    def get(self, request):
        return _stub()
