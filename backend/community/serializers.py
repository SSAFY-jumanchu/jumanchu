from rest_framework import serializers

from community.models import Comment, CommunityPost


class PostSerializer(serializers.ModelSerializer):
    """게시글 응답(읽기). comment_count는 view에서 annotate(또는 직접 set)."""

    user_id = serializers.IntegerField(read_only=True)
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    stock_code = serializers.CharField(source='stock.code', read_only=True, allow_null=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True, allow_null=True)
    comment_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = CommunityPost
        fields = ['id', 'user_id', 'nickname', 'stock_code', 'stock_name',
                  'category', 'title', 'body', 'view_count', 'like_count',
                  'comment_count', 'is_liked', 'created_at']


class PostWriteSerializer(serializers.Serializer):
    """게시글 작성/수정 입력. 모든 글은 종목에 속함(stock_code 필수)."""

    stock_code = serializers.CharField()
    category = serializers.ChoiceField(choices=CommunityPost.Category.choices, required=False)
    title = serializers.CharField(max_length=200)
    body = serializers.CharField()


class PostListResponseSerializer(serializers.Serializer):
    items = PostSerializer(many=True)
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    total = serializers.IntegerField()


class CommentSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post_id', 'user_id', 'nickname', 'body', 'created_at']


class CommentWriteSerializer(serializers.Serializer):
    body = serializers.CharField()


class CommentListResponseSerializer(serializers.Serializer):
    items = CommentSerializer(many=True)
    total = serializers.IntegerField()


class LikeToggleResponseSerializer(serializers.Serializer):
    liked = serializers.BooleanField()
    like_count = serializers.IntegerField()


class UserBriefSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    nickname = serializers.CharField()


class FollowListResponseSerializer(serializers.Serializer):
    items = UserBriefSerializer(many=True)
    total = serializers.IntegerField()
