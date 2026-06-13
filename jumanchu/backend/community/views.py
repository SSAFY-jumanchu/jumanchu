from django.db.models import Count, F
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from community import serializers as s
from community import services
from community.models import Comment, CommunityPost


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@extend_schema(tags=['Community'])
class PostListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary='게시글 목록',
        parameters=[
            OpenApiParameter('stock_code', str, required=False),
            OpenApiParameter('category', str, required=False,
                             enum=['QUESTION', 'REVIEW', 'ANALYSIS', 'SHARE']),
            OpenApiParameter('sort', str, required=False, enum=['latest', 'popular']),
            OpenApiParameter('page', int, required=False),
            OpenApiParameter('size', int, required=False),
        ],
        responses={200: s.PostListResponseSerializer},
    )
    def get(self, request):
        qs = (
            CommunityPost.objects.select_related('user', 'stock')
            .annotate(comment_count=Count('comments'))
        )
        p = request.query_params
        if p.get('stock_code'):
            qs = qs.filter(stock__code=p['stock_code'])
        if p.get('category'):
            qs = qs.filter(category=p['category'])
        if p.get('sort') == 'popular':
            qs = qs.order_by('-like_count', '-created_at')
        else:
            qs = qs.order_by('-created_at')

        total = qs.count()
        page = max(1, _as_int(p.get('page'), 1))
        size = min(100, max(1, _as_int(p.get('size'), 20)))
        start = (page - 1) * size
        items = qs[start:start + size]

        body = {'items': items, 'page': page, 'size': size, 'total': total}
        return Response(s.PostListResponseSerializer(body).data)

    @extend_schema(summary='게시글 작성', request=s.PostWriteSerializer,
                   responses={201: s.PostSerializer})
    def post(self, request):
        req = s.PostWriteSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        try:
            post = services.create_post(request.user, req.validated_data)
        except services.StockNotFound:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        post.comment_count = 0
        return Response(s.PostSerializer(post).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Community'])
class PostDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(summary='게시글 상세 (조회수 +1)', responses={200: s.PostSerializer})
    def get(self, request, id: int):
        # 조회수 원자적 증가 (없는 글이면 0 rows → 영향 없음)
        CommunityPost.objects.filter(id=id).update(view_count=F('view_count') + 1)
        post = (
            CommunityPost.objects.select_related('user', 'stock')
            .annotate(comment_count=Count('comments'))
            .filter(id=id)
            .first()
        )
        if post is None:
            return Response({'detail': '게시글을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(s.PostSerializer(post).data)

    @extend_schema(summary='게시글 수정 (작성자만)', request=s.PostWriteSerializer,
                   responses={200: s.PostSerializer})
    def patch(self, request, id: int):
        post = CommunityPost.objects.filter(id=id).first()
        if post is None:
            return Response({'detail': '게시글을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        if post.user_id != request.user.id:
            return Response({'detail': '작성자만 수정할 수 있습니다.'},
                            status=status.HTTP_403_FORBIDDEN)
        req = s.PostWriteSerializer(data=request.data, partial=True)
        req.is_valid(raise_exception=True)
        try:
            post = services.update_post(post, req.validated_data)
        except services.StockNotFound:
            return Response({'detail': '해당 종목을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        post.comment_count = post.comments.count()
        return Response(s.PostSerializer(post).data)

    @extend_schema(summary='게시글 삭제 (작성자만)', responses={204: None})
    def delete(self, request, id: int):
        post = CommunityPost.objects.filter(id=id).first()
        if post is None:
            return Response({'detail': '게시글을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        if post.user_id != request.user.id:
            return Response({'detail': '작성자만 삭제할 수 있습니다.'},
                            status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Community'])
class CommentListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(summary='댓글 목록', responses={200: s.CommentListResponseSerializer})
    def get(self, request, post_id: int):
        if not CommunityPost.objects.filter(id=post_id).exists():
            return Response({'detail': '게시글을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        items = (
            Comment.objects.filter(post_id=post_id)
            .select_related('user')
            .order_by('created_at')
        )
        body = {'items': list(items), 'total': len(items)}
        return Response(s.CommentListResponseSerializer(body).data)

    @extend_schema(summary='댓글 작성', request=s.CommentWriteSerializer,
                   responses={201: s.CommentSerializer})
    def post(self, request, post_id: int):
        post = CommunityPost.objects.filter(id=post_id).first()
        if post is None:
            return Response({'detail': '게시글을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        req = s.CommentWriteSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        comment = Comment.objects.create(
            post=post, user=request.user, body=req.validated_data['body']
        )
        return Response(s.CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Community'])
class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='댓글 수정 (작성자만)', request=s.CommentWriteSerializer,
                   responses={200: s.CommentSerializer})
    def patch(self, request, id: int):
        comment = Comment.objects.filter(id=id).select_related('user').first()
        if comment is None:
            return Response({'detail': '댓글을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        if comment.user_id != request.user.id:
            return Response({'detail': '작성자만 수정할 수 있습니다.'},
                            status=status.HTTP_403_FORBIDDEN)
        req = s.CommentWriteSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        comment.body = req.validated_data['body']
        comment.save(update_fields=['body'])
        return Response(s.CommentSerializer(comment).data)

    @extend_schema(summary='댓글 삭제 (작성자만)', responses={204: None})
    def delete(self, request, id: int):
        comment = Comment.objects.filter(id=id).first()
        if comment is None:
            return Response({'detail': '댓글을 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
        if comment.user_id != request.user.id:
            return Response({'detail': '작성자만 삭제할 수 있습니다.'},
                            status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
