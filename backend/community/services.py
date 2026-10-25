"""커뮤니티 서비스.

커밋 A: 게시글 작성/수정의 종목 해석. (댓글 CRUD는 단순해서 view에서 처리)
좋아요 토글·팔로우는 커밋 B에서 추가 예정.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import F

from community.models import Comment, CommentLike, CommunityPost, Follow, PostLike
from stocks.models import Stock

User = get_user_model()


class StockNotFound(Exception):
    """종목 코드에 해당하는 (활성) 종목이 없음."""


class PostNotFound(Exception):
    """게시글 없음."""


class CommentNotFound(Exception):
    """댓글 없음."""


class UserNotFound(Exception):
    """대상 사용자 없음."""


class CannotFollowSelf(Exception):
    """자기 자신은 팔로우할 수 없음."""


def _resolve_stock(stock_code: str) -> Stock:
    stock = Stock.objects.filter(code=stock_code, is_active=True).first()
    if stock is None:
        raise StockNotFound(stock_code)
    return stock


def create_post(user, data: dict) -> CommunityPost:
    stock = _resolve_stock(data["stock_code"])
    return CommunityPost.objects.create(
        user=user,
        stock=stock,
        category=data.get("category", CommunityPost.Category.QUESTION),
        title=data["title"],
        body=data["body"],
    )


def update_post(post: CommunityPost, data: dict) -> CommunityPost:
    """부분 수정. data에 들어온 필드만 갱신."""
    if "stock_code" in data:
        post.stock = _resolve_stock(data["stock_code"])
    for field in ("category", "title", "body"):
        if field in data:
            setattr(post, field, data[field])
    post.save()
    return post


# ───────────────────────── 좋아요 (토글) ─────────────────────────


def toggle_post_like(user, post_id: int) -> dict:
    """게시글 좋아요 토글. like_count는 F()로 원자적 ±1 (비정규화)."""
    if not CommunityPost.objects.filter(id=post_id).exists():
        raise PostNotFound(post_id)
    with transaction.atomic():
        deleted, _ = PostLike.objects.filter(user=user, post_id=post_id).delete()
        if deleted:
            CommunityPost.objects.filter(id=post_id).update(like_count=F("like_count") - 1)
            liked = False
        else:
            try:
                PostLike.objects.create(user=user, post_id=post_id)
                CommunityPost.objects.filter(id=post_id).update(like_count=F("like_count") + 1)
            except IntegrityError:
                pass  # 동시 좋아요 race — 이미 존재(다른 요청이 카운트 처리)
            liked = True
    like_count = CommunityPost.objects.values_list("like_count", flat=True).get(id=post_id)
    return {"liked": liked, "like_count": like_count}


def toggle_comment_like(user, comment_id: int) -> dict:
    """댓글 좋아요 토글. 댓글엔 비정규화 카운트가 없어 매번 COUNT."""
    if not Comment.objects.filter(id=comment_id).exists():
        raise CommentNotFound(comment_id)
    deleted, _ = CommentLike.objects.filter(user=user, comment_id=comment_id).delete()
    if deleted:
        liked = False
    else:
        try:
            CommentLike.objects.create(user=user, comment_id=comment_id)
        except IntegrityError:
            pass
        liked = True
    like_count = CommentLike.objects.filter(comment_id=comment_id).count()
    return {"liked": liked, "like_count": like_count}


# ───────────────────────── 팔로우 ─────────────────────────


def follow_user(follower, target_id: int) -> None:
    if follower.id == target_id:
        raise CannotFollowSelf()
    target = User.objects.filter(id=target_id).first()
    if target is None:
        raise UserNotFound(target_id)
    Follow.objects.get_or_create(follower=follower, following=target)


def unfollow_user(follower, target_id: int) -> bool:
    """언팔. 끊었으면 True, 원래 팔로우 안 했으면 False."""
    deleted, _ = Follow.objects.filter(
        follower=follower, following_id=target_id
    ).delete()
    return deleted > 0


def followers_of(user_id: int) -> list:
    """이 유저를 팔로우하는 사람들(UserBriefSerializer 모양)."""
    follows = Follow.objects.filter(following_id=user_id).select_related("follower")
    return [
        {"user_id": f.follower_id, "nickname": f.follower.nickname} for f in follows
    ]


def following_of(user_id: int) -> list:
    """이 유저가 팔로우하는 사람들."""
    follows = Follow.objects.filter(follower_id=user_id).select_related("following")
    return [
        {"user_id": f.following_id, "nickname": f.following.nickname} for f in follows
    ]
