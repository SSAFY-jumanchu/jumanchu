"""커뮤니티 서비스.

커밋 A: 게시글 작성/수정의 종목 해석. (댓글 CRUD는 단순해서 view에서 처리)
좋아요 토글·팔로우는 커밋 B에서 추가 예정.
"""
from __future__ import annotations

from community.models import CommunityPost
from stocks.models import Stock


class StockNotFound(Exception):
    """종목 코드에 해당하는 (활성) 종목이 없음."""


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
