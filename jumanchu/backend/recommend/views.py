from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
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


@extend_schema(tags=['Recommend'])
class RecommendSwipeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='오늘의 궁합 추천 (스와이프 카드)',
        parameters=[OpenApiParameter('limit', int, required=False)],
        responses={200: s.SwipeRecommendResponseSerializer},
    )
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 30))
        except (TypeError, ValueError):
            limit = 30
        limit = max(1, min(limit, 50))
        try:
            cards = services.swipe_recommendations(request.user, limit=limit)
        except services.OnboardingRequired:
            return Response({'detail': '온보딩을 먼저 완료해주세요.'},
                            status=status.HTTP_409_CONFLICT)
        body = {'items': cards, 'total': len(cards), 'generated_at': timezone.now()}
        return Response(s.SwipeRecommendResponseSerializer(body).data)


@extend_schema(tags=['Recommend'])
class LongTermReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='장투 케어 AI 리포트 (보유 종목 1개, LLM·캐시 TTL 1일)',
        parameters=[OpenApiParameter('refresh', int, required=False,
                                     description='1이면 캐시 무시·재생성')],
    )
    def get(self, request, code):
        refresh = request.query_params.get('refresh') == '1'
        try:
            data = services.longterm_report(request.user, code, force=refresh)
        except services.StockNotFound:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:  # GMS_API_KEY 없음 등
            return Response({'detail': str(exc)},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        # 궁합 카드 세부(5요소 매칭) — 리포트 LLM 캐시와 무관하게 즉석 부착
        comps = services.userfit_components(request.user, code)
        if comps and isinstance(data.get('userfit'), dict):
            data['userfit']['components'] = comps
        return Response(data)


@extend_schema(tags=['Recommend'])
class LongTermHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='종목 장투 총점 히스토리 (소계×0.7 + 궁합×0.3, 상단 종합점수와 동일, 최신 12개)')
    def get(self, request, code):
        try:
            items = services.longterm_total_history(request.user, code)
        except services.StockNotFound:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({'items': items})


@extend_schema(tags=['Recommend'])
class LongTermRankingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='개인별 장투 랭킹 (소계70% + 궁합30%, on-demand)',
        parameters=[
            OpenApiParameter('limit', int, required=False, description='기본 30, 최대 100'),
            OpenApiParameter('offset', int, required=False, description='기본 0'),
        ],
    )
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 30))
        except (TypeError, ValueError):
            limit = 30
        limit = max(1, min(limit, 100))
        try:
            offset = max(0, int(request.query_params.get('offset', 0)))
        except (TypeError, ValueError):
            offset = 0
        try:
            items = services.longterm_ranking(request.user, limit=limit, offset=offset)
        except services.OnboardingRequired:
            return Response({'detail': '온보딩을 먼저 완료해주세요.'},
                            status=status.HTTP_409_CONFLICT)
        body = {'items': items, 'total': len(items), 'limit': limit, 'offset': offset,
                'generated_at': timezone.now()}
        return Response(body)
