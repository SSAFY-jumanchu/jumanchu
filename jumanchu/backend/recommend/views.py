from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recommend import serializers as s
from recommend import services


@extend_schema(tags=['Watchlist'])
class WatchlistView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='관심종목 목록', responses={200: s.WatchlistListResponseSerializer})
    def get(self, request):
        items = services.watchlist_items(request.user)
        body = {'items': items, 'total': len(items)}
        return Response(s.WatchlistListResponseSerializer(body).data)

    @extend_schema(
        summary='관심종목 추가',
        request=s.WatchlistAddRequestSerializer,
        responses={201: s.WatchlistItemSerializer},
    )
    def post(self, request):
        req = s.WatchlistAddRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        try:
            item = services.add_watchlist(request.user, req.validated_data['stock_code'])
        except services.StockNotFound:
            return Response(
                {'detail': '해당 종목을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(s.WatchlistItemSerializer(item).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Watchlist'])
class WatchlistItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='관심종목 제거', responses={204: None})
    def delete(self, request, code: str):
        removed = services.remove_watchlist(request.user, code)
        if not removed:
            return Response(
                {'detail': '관심종목에 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
