"""
페이지네이션 envelope helper.

명세 (`docs/API_스키마_v1.md` §0.2):
    { "items": T[], "page": int, "size": int, "total": int }

DRF PageNumberPagination 대신 단순 함수로 — 키 명명이 명세와 다르고
list 엔드포인트가 적어 추상화 이득 작음.
"""
from __future__ import annotations

from typing import Type

from rest_framework.serializers import Serializer


DEFAULT_SIZE = 20
MAX_SIZE = 100


def normalize_page_size(page, size) -> tuple[int, int]:
    """page≥1, 1≤size≤MAX_SIZE 로 클램프. 잘못된 입력은 기본값."""
    try:
        page = max(int(page or 1), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        size = min(max(int(size or DEFAULT_SIZE), 1), MAX_SIZE)
    except (TypeError, ValueError):
        size = DEFAULT_SIZE
    return page, size


def paginate(queryset, *, page: int, size: int,
             item_serializer_cls: Type[Serializer], context=None) -> dict:
    """envelope dict 반환. queryset은 .count() / 슬라이스 가능해야 함."""
    page, size = normalize_page_size(page, size)
    total = queryset.count()
    items_qs = queryset[(page - 1) * size: page * size]
    items = item_serializer_cls(items_qs, many=True, context=context or {}).data
    return {"items": items, "page": page, "size": size, "total": total}
