from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """객체 소유자(obj.user)만 접근 허용. (정책: docs/인증_권한_정책.md §4.3)

    portfolio/diary/community 등 user-scoped 객체 뷰에서 IsAuthenticated 와 함께 사용.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
