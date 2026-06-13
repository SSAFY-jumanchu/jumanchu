"""커뮤니티 게시글/댓글 CRUD 테스트 — SCRUM-26 (커밋 A)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from community.models import Comment, CommunityPost
from stocks.models import Stock

User = get_user_model()


def _make_user(username="poster"):
    return User.objects.create(username=username, nickname=username, birth_year=1995)


def _make_stock(code="A0001"):
    return Stock.objects.create(code=code, name="테스트", market="KOSPI", currency="KRW")


def _post(user, stock, **kw):
    return CommunityPost.objects.create(
        user=user, stock=stock, category="QUESTION",
        title=kw.get("title", "제목"), body=kw.get("body", "내용"),
    )


class PostTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.stock = _make_stock("A0001")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_post(self):
        resp = self.client.post(
            reverse("post-list-create"),
            {"stock_code": "A0001", "category": "ANALYSIS", "title": "삼성 분석", "body": "저평가"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["title"], "삼성 분석")
        self.assertEqual(resp.data["stock_code"], "A0001")
        self.assertEqual(resp.data["comment_count"], 0)

    def test_create_post_invalid_stock_404(self):
        resp = self.client.post(
            reverse("post-list-create"),
            {"stock_code": "ZZZZ", "title": "x", "body": "y"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_create_post_requires_auth(self):
        anon = APIClient()
        resp = anon.post(
            reverse("post-list-create"),
            {"stock_code": "A0001", "title": "x", "body": "y"},
            format="json",
        )
        self.assertIn(resp.status_code, (401, 403))

    def test_list_public_and_filter_category(self):
        _post(self.user, self.stock)
        p2 = _post(self.user, self.stock)
        p2.category = "REVIEW"
        p2.save()
        anon = APIClient()  # 비로그인도 목록 조회 가능
        resp = anon.get(reverse("post-list-create"), {"category": "REVIEW"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["items"][0]["category"], "REVIEW")

    def test_detail_increments_view_count(self):
        post = _post(self.user, self.stock)
        self.client.get(reverse("post-detail", kwargs={"id": post.id}))
        self.client.get(reverse("post-detail", kwargs={"id": post.id}))
        post.refresh_from_db()
        self.assertEqual(post.view_count, 2)

    def test_update_post_owner(self):
        post = _post(self.user, self.stock)
        resp = self.client.patch(
            reverse("post-detail", kwargs={"id": post.id}),
            {"title": "수정됨"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, "수정됨")

    def test_update_post_non_owner_403(self):
        post = _post(self.user, self.stock)
        other = _make_user("other")
        client2 = APIClient()
        client2.force_authenticate(user=other)
        resp = client2.patch(
            reverse("post-detail", kwargs={"id": post.id}),
            {"title": "해킹"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_delete_post_owner(self):
        post = _post(self.user, self.stock)
        resp = self.client.delete(reverse("post-detail", kwargs={"id": post.id}))
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(CommunityPost.objects.filter(id=post.id).exists())

    def test_delete_post_non_owner_403(self):
        post = _post(self.user, self.stock)
        other = _make_user("other")
        client2 = APIClient()
        client2.force_authenticate(user=other)
        resp = client2.delete(reverse("post-detail", kwargs={"id": post.id}))
        self.assertEqual(resp.status_code, 403)


class CommentTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.stock = _make_stock("A0001")
        self.post = _post(self.user, self.stock)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        resp = self.client.post(
            reverse("comment-list-create", kwargs={"post_id": self.post.id}),
            {"body": "좋은 분석이네요"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["body"], "좋은 분석이네요")
        self.assertEqual(resp.data["post_id"], self.post.id)

    def test_comment_on_missing_post_404(self):
        resp = self.client.post(
            reverse("comment-list-create", kwargs={"post_id": 99999}),
            {"body": "x"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_list_comments(self):
        Comment.objects.create(post=self.post, user=self.user, body="c1")
        Comment.objects.create(post=self.post, user=self.user, body="c2")
        resp = self.client.get(
            reverse("comment-list-create", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total"], 2)

    def test_post_comment_count_reflects_comments(self):
        Comment.objects.create(post=self.post, user=self.user, body="c1")
        resp = self.client.get(reverse("post-detail", kwargs={"id": self.post.id}))
        self.assertEqual(resp.data["comment_count"], 1)

    def test_update_comment_owner(self):
        comment = Comment.objects.create(post=self.post, user=self.user, body="원본")
        resp = self.client.patch(
            reverse("comment-detail", kwargs={"id": comment.id}),
            {"body": "수정"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.body, "수정")

    def test_delete_comment_non_owner_403(self):
        comment = Comment.objects.create(post=self.post, user=self.user, body="원본")
        other = _make_user("other")
        client2 = APIClient()
        client2.force_authenticate(user=other)
        resp = client2.delete(reverse("comment-detail", kwargs={"id": comment.id}))
        self.assertEqual(resp.status_code, 403)
