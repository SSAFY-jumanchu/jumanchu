from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from diary import serializers as s
from diary import services
from diary.models import StockDiary


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@extend_schema(tags=['Diary'])
class DiaryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='내 일기 목록',
        parameters=[
            OpenApiParameter('stock_code', str, required=False),
            OpenApiParameter('action_type', str, required=False, enum=['BUY', 'SELL', 'WATCH']),
            OpenApiParameter('page', int, required=False),
            OpenApiParameter('size', int, required=False),
        ],
        responses={200: s.DiaryListResponseSerializer},
    )
    def get(self, request):
        qs = StockDiary.objects.filter(user=request.user).select_related('stock', 'order')
        p = request.query_params
        if p.get('stock_code'):
            qs = qs.filter(stock__code=p['stock_code'])
        if p.get('action_type'):
            qs = qs.filter(action_type=p['action_type'])
        qs = qs.order_by('-diary_date', '-id')

        total = qs.count()
        page = max(1, _as_int(p.get('page'), 1))
        size = min(100, max(1, _as_int(p.get('size'), 20)))
        start = (page - 1) * size
        items = qs[start:start + size]

        body = {'items': items, 'page': page, 'size': size, 'total': total}
        return Response(s.DiaryListResponseSerializer(body).data)

    @extend_schema(
        summary='일기 작성',
        request=s.StockDiaryWriteSerializer,
        responses={201: s.StockDiarySerializer},
    )
    def post(self, request):
        req = s.StockDiaryWriteSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        try:
            diary = services.create_diary(request.user, req.validated_data)
        except services.StockNotFound:
            return Response(
                {'detail': '해당 종목을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except services.OrderNotOwned:
            return Response(
                {'detail': '연결할 주문이 없거나 본인 주문이 아닙니다.', 'code': 'INVALID_ORDER'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(s.StockDiarySerializer(diary).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Diary'])
class DiaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_owned(self, request, id: int):
        return (
            StockDiary.objects.filter(id=id, user=request.user)
            .select_related('stock', 'order')
            .first()
        )

    @extend_schema(summary='일기 상세', responses={200: s.StockDiarySerializer})
    def get(self, request, id: int):
        diary = self._get_owned(request, id)
        if diary is None:
            return Response({'detail': '일기를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(s.StockDiarySerializer(diary).data)

    @extend_schema(
        summary='일기 수정',
        request=s.StockDiaryWriteSerializer,
        responses={200: s.StockDiarySerializer},
    )
    def patch(self, request, id: int):
        diary = self._get_owned(request, id)
        if diary is None:
            return Response({'detail': '일기를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        req = s.StockDiaryWriteSerializer(data=request.data, partial=True)
        req.is_valid(raise_exception=True)
        try:
            diary = services.update_diary(diary, request.user, req.validated_data)
        except services.StockNotFound:
            return Response(
                {'detail': '해당 종목을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except services.OrderNotOwned:
            return Response(
                {'detail': '연결할 주문이 없거나 본인 주문이 아닙니다.', 'code': 'INVALID_ORDER'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(s.StockDiarySerializer(diary).data)

    @extend_schema(summary='일기 삭제', responses={204: None})
    def delete(self, request, id: int):
        diary = self._get_owned(request, id)
        if diary is None:
            return Response({'detail': '일기를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        diary.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
