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
    class PostType(models.TextChoices):
        FREE = "FREE", "자유"
        STOCK = "STOCK", "종목"
        PF = "PF", "포트폴리오"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    stock = models.ForeignKey(
        "stocks.Stock",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    post_type = models.CharField(max_length=8, choices=PostType.choices, default=PostType.FREE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["post_type", "-created_at"]),
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
