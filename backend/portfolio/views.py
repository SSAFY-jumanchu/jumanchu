from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from diary.models import StockDiary
from portfolio import serializers as s
from portfolio import services
from portfolio.models import Account, Order


def _as_int(value, default: int) -> int:
    """쿼리 파라미터를 정수로. 비거나 형식 오류면 default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_date_safe(value):
    """YYYY-MM-DD → date. 비었거나 형식/값이 잘못되면 None (500 방지)."""
    if not value:
        return None
    try:
        return parse_date(value)
    except ValueError:
        return None


def _price_unavailable():
    """KIS 현재가 조회 실패 → 503."""
    return Response(
        {'detail': 'KIS 외부 API 오류', 'code': 'EXTERNAL_API_ERROR'},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@extend_schema(tags=['Order'])
class OrderPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='매매 시뮬레이션',
        request=s.OrderPreviewRequestSerializer,
        responses={200: s.OrderPreviewResponseSerializer},
    )
    def post(self, request):
        req = s.OrderPreviewRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        try:
            result = services.preview_order(request.user, **req.validated_data)
        except services.StockNotFound:
            return Response(
                {'detail': '해당 종목을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except services.PriceUnavailable:
            return Response(
                {'detail': 'KIS 외부 API 오류', 'code': 'EXTERNAL_API_ERROR'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(s.OrderPreviewResponseSerializer(result).data)


@extend_schema(tags=['Order'])
class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='매매 주문 실행',
        request=s.OrderCreateRequestSerializer,
        responses={201: s.OrderCreateResponseSerializer},
    )
    def post(self, request):
        req = s.OrderCreateRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        data = req.validated_data
        run = services.execute_buy if data['side'] == Order.Side.BUY else services.execute_sell
        try:
            result = run(request.user, data['stock_code'], data['quantity'], data['idempotency_key'])
        except services.StockNotFound:
            return Response(
                {'detail': '해당 종목을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except services.InsufficientBalance as exc:
            return Response(
                {'detail': str(exc), 'code': 'INSUFFICIENT_BALANCE'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except services.InsufficientHolding as exc:
            return Response(
                {'detail': str(exc), 'code': 'INSUFFICIENT_HOLDING'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except services.PriceUnavailable:
            return Response(
                {'detail': 'KIS 외부 API 오류', 'code': 'EXTERNAL_API_ERROR'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            s.OrderCreateResponseSerializer(result).data,
            status=status.HTTP_201_CREATED,
        )

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
        qs = Order.objects.filter(user=request.user).select_related('stock')
        p = request.query_params
        if p.get('side'):
            qs = qs.filter(side=p['side'])
        if p.get('stock_code'):
            qs = qs.filter(stock__code=p['stock_code'])
        if p.get('status'):
            qs = qs.filter(status=p['status'])
        date_from = _parse_date_safe(p.get('from'))
        date_to = _parse_date_safe(p.get('to'))
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        qs = qs.order_by('-created_at')

        total = qs.count()
        page = max(1, _as_int(p.get('page'), 1))
        size = min(100, max(1, _as_int(p.get('size'), 20)))
        start = (page - 1) * size
        items = qs[start:start + size]

        body = {'items': items, 'page': page, 'size': size, 'total': total}
        return Response(s.OrderListResponseSerializer(body).data)


@extend_schema(tags=['Order'])
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='orders_detail',
        summary='주문 상세',
        responses={200: s.OrderDetailResponseSerializer},
    )
    def get(self, request, id: int):
        order = (
            Order.objects.filter(id=id, user=request.user).select_related('stock').first()
        )
        if order is None:
            return Response(
                {'detail': '주문을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        related_diary_id = (
            StockDiary.objects.filter(order=order, user=request.user)
            .values_list('id', flat=True)
            .first()
        )
        body = {'order': order, 'stock': order.stock, 'related_diary_id': related_diary_id}
        return Response(s.OrderDetailResponseSerializer(body).data)


@extend_schema(tags=['Portfolio'])
class PortfolioSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='포트폴리오 통합 조회 (홈 위젯용)',
        responses={200: s.PortfolioSummaryResponseSerializer},
    )
    def get(self, request):
        try:
            result = services.portfolio_summary(request.user)
        except services.PriceUnavailable:
            return _price_unavailable()
        return Response(s.PortfolioSummaryResponseSerializer(result).data)


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
        p = request.query_params
        try:
            result = services.holdings_list(
                request.user,
                sort=p.get('sort', 'value'),
                order=p.get('order', 'desc'),
            )
        except services.PriceUnavailable:
            return _price_unavailable()
        return Response(s.HoldingsListResponseSerializer(result).data)


@extend_schema(tags=['Portfolio'])
class HoldingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='portfolio_holding_detail',
        summary='특정 종목 보유 상세 (Order 내역 포함)',
        responses={200: s.HoldingDetailResponseSerializer},
    )
    def get(self, request, code: str):
        try:
            result = services.holding_detail(request.user, code)
        except services.StockNotFound:
            return Response(
                {'detail': '해당 종목을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except services.PriceUnavailable:
            return _price_unavailable()
        if result is None:
            return Response(
                {'detail': '보유하지 않은 종목입니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(s.HoldingDetailResponseSerializer(result).data)


@extend_schema(tags=['Portfolio'])
class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Account 잔액',
        responses={200: s.BalanceResponseSerializer},
    )
    def get(self, request):
        account, _ = Account.objects.get_or_create(user=request.user)
        return Response(s.BalanceResponseSerializer({'account': account}).data)


@extend_schema(tags=['Portfolio'])
class AllocationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='자산 배분 (섹터/종목별)',
        responses={200: s.AllocationResponseSerializer},
    )
    def get(self, request):
        try:
            result = services.allocation(request.user)
        except services.PriceUnavailable:
            return _price_unavailable()
        return Response(s.AllocationResponseSerializer(result).data)


@extend_schema(tags=['Portfolio'])
class MilestonesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='자산 마일스톤 (수익 기준 달성/다음목표/진행률)',
        responses={200: s.MilestonesResponseSerializer},
    )
    def get(self, request):
        try:
            result = services.milestones(request.user)
        except services.PriceUnavailable:
            return _price_unavailable()
        return Response(s.MilestonesResponseSerializer(result).data)
