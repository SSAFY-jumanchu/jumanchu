from django.conf import settings
from django.db import models


class SharedPortfolio(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shared_portfolios"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_public", "-view_count"]),
        ]

    def __str__(self):
        return self.title


class SharedPortfolioItem(models.Model):
    portfolio = models.ForeignKey(
        SharedPortfolio, on_delete=models.CASCADE, related_name="items"
    )
    stock = models.ForeignKey("stocks.Stock", on_delete=models.RESTRICT, related_name="shared_items")
    weight = models.DecimalField(max_digits=6, decimal_places=4)

    class Meta:
        indexes = [
            models.Index(fields=["portfolio"]),
        ]

    def __str__(self):
        return f"{self.portfolio_id}: {self.stock_id} {self.weight}"


class CommunityPost(models.Model):
    class Category(models.TextChoices):
        QUESTION = "QUESTION", "질문"
        REVIEW = "REVIEW", "후기"
        ANALYSIS = "ANALYSIS", "분석"
        SHARE = "SHARE", "공유"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    # STOCK 전용: 모든 글이 종목에 속함. DB는 nullable, 필수는 serializer에서 강제.
    stock = models.ForeignKey(
        "stocks.Stock",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.QUESTION)
    title = models.CharField(max_length=200)
    body = models.TextField()
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)  # 비정규화: 인기순 정렬, 좋아요 ±1
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["stock"]),
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["post", "created_at"]),
        ]

    def __str__(self):
        return f"comment by {self.user_id} on {self.post_id}"


class PostLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_likes"
    )
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="postlike_user_post_unique"),
        ]

    def __str__(self):
        return f"{self.user_id} likes {self.post_id}"


class CommentLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_likes"
    )
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "comment"], name="commentlike_user_comment_unique"
            ),
        ]

    def __str__(self):
        return f"{self.user_id} likes comment {self.comment_id}"


class Follow(models.Model):
    """팔로우 — 유저↔유저 다대다 (중개 테이블)."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="follow_follower_following_unique"
            ),
        ]

    def __str__(self):
        return f"{self.follower_id} follows {self.following_id}"
