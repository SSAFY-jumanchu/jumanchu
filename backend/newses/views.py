from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from stocks.models import Stock

from newses import rss
from newses import serializers as s
from newses import services
from newses.topic_sector import CANONICAL_SECTORS

# 두 뷰가 공유하는 쿼리 파라미터 (display/sort/body)
_COMMON_PARAMS = [
    OpenApiParameter('display', int, description='기사 수 (기본 10, 1~100)'),
    OpenApiParameter('sort', str, description='date(최신, 기본) | sim(정확도)'),
    OpenApiParameter('content', bool,
                     description='true면 기사 본문(news.naver.com 호스팅분, 최대 2000자) 포함 (느림)'),
]


def _clamp_int(raw, *, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(raw)))
    except (TypeError, ValueError):
        return default


def _news_params(request) -> tuple[int, str, bool]:
    display = _clamp_int(request.query_params.get('display'), default=10, lo=1, hi=100)
    sort = request.query_params.get('sort') or 'date'
    if sort not in ('date', 'sim'):
        sort = 'date'
    raw = (request.query_params.get('content') or request.query_params.get('body') or '')
    with_body = raw.lower() in ('1', 'true', 'yes')
    return display, sort, with_body


def _fetch_news(query: str, display: int, sort: str, with_body: bool):
    """(items, error_response) 반환. 성공 시 error_response 는 None."""
    try:
        items = services.search_stock_news(
            query, display=display, sort=sort, with_body=with_body
        )
        return items, None
    except RuntimeError as e:
        # 키 미설정 등 설정 오류
        return None, Response({'detail': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        # 외부 제공자(네이버) 호출 실패: 네트워크/4xx·5xx/JSON 파싱 등
        return None, Response({'detail': '뉴스 제공자(네이버) 호출에 실패했습니다.'},
                              status=status.HTTP_502_BAD_GATEWAY)


@extend_schema(tags=['News'])
class StockNewsSearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='종목/키워드 뉴스 검색 (네이버 검색 API)',
        parameters=[
            OpenApiParameter('query', str, required=True,
                             description='종목명 또는 검색어 (예: 삼성전자, 경제)'),
            *_COMMON_PARAMS,
        ],
        responses={200: s.NewsListResponseSerializer},
    )
    def get(self, request):
        query = (request.query_params.get('query') or '').strip()
        if not query:
            return Response({'detail': 'query 파라미터가 필요합니다.'},
                            status=status.HTTP_400_BAD_REQUEST)

        items, err = _fetch_news(query, *_news_params(request))
        if err is not None:
            return err

        body = {'query': query, 'count': len(items), 'items': items}
        return Response(s.NewsListResponseSerializer(body).data)


@extend_schema(tags=['News'])
class StockNewsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='종목 코드로 그 종목 뉴스',
        parameters=_COMMON_PARAMS,
        responses={200: s.StockNewsResponseSerializer},
    )
    def get(self, request, code: str):
        stock = Stock.objects.filter(code=code).first()
        if stock is None:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)

        items, err = _fetch_news(stock.name, *_news_params(request))
        if err is not None:
            return err

        body = {
            'stock': {
                'code': stock.code, 'name': stock.name,
                'market': stock.market, 'sector': stock.sector,
            },
            'count': len(items),
            'items': items,
        }
        return Response(s.StockNewsResponseSerializer(body).data)


@extend_schema(tags=['News'])
class FeedNewsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='피드 뉴스 (연합뉴스 RSS: economy/politics/world) + 관련주 태깅',
        parameters=[OpenApiParameter('limit', int, description='개수 (기본 20, 1~50)')],
        responses={200: s.FeedNewsResponseSerializer},
    )
    def get(self, request, category: str):
        if category not in rss.FEEDS:
            return Response(
                {'detail': f'알 수 없는 카테고리: {category}. 가능: {list(rss.FEEDS)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = _clamp_int(request.query_params.get('limit'), default=20, lo=1, hi=50)
        items = services.feed_news(category=category, limit=limit)
        body = {'category': category, 'count': len(items), 'items': items}
        return Response(s.FeedNewsResponseSerializer(body).data)


@extend_schema(tags=['News'])
class SectorNewsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='섹터 신호 기준 뉴스 (NewsSector: 엔티티+토픽 병합)',
        parameters=[
            OpenApiParameter('sector', str, required=True,
                             description='정본 22 섹터 중 하나 (예: 운송장비·부품)'),
            OpenApiParameter('limit', int, description='개수 (기본 20, 1~50)'),
        ],
        responses={200: s.FeedNewsResponseSerializer},
    )
    def get(self, request):
        sector = (request.query_params.get('sector') or '').strip()
        if sector not in CANONICAL_SECTORS:
            return Response(
                {'detail': f'정본 22 섹터 중 하나여야 합니다 (받은 값: {sector or "(빈값)"})'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = _clamp_int(request.query_params.get('limit'), default=20, lo=1, hi=50)
        items = services.feed_news(sector=sector, limit=limit)
        body = {'sector': sector, 'category': None, 'count': len(items), 'items': items}
        return Response(s.FeedNewsResponseSerializer(body).data)


@extend_schema(tags=['News'])
class WatchlistNewsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='관심종목 뉴스 (네이버, 종목별 병합)',
        parameters=[OpenApiParameter('limit', int, description='개수 (기본 10, 1~30)')],
        responses={200: s.StockNewsFeedResponseSerializer},
    )
    def get(self, request):
        limit = _clamp_int(request.query_params.get('limit'), default=10, lo=1, hi=30)
        items = services.watchlist_news(request.user, limit=limit)
        return Response(s.StockNewsFeedResponseSerializer({'count': len(items), 'items': items}).data)


@extend_schema(tags=['News'])
class HoldingsNewsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='보유종목 뉴스 (네이버, 종목별 병합)',
        parameters=[OpenApiParameter('limit', int, description='개수 (기본 10, 1~30)')],
        responses={200: s.StockNewsFeedResponseSerializer},
    )
    def get(self, request):
        limit = _clamp_int(request.query_params.get('limit'), default=10, lo=1, hi=30)
        items = services.holdings_news(request.user, limit=limit)
        return Response(s.StockNewsFeedResponseSerializer({'count': len(items), 'items': items}).data)
