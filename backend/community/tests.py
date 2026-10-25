"""커뮤니티 게시글/댓글 CRUD 테스트 — SCRUM-26 (커밋 A)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from community.models import Comment, CommunityPost, Follow
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


class LikeFollowTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.stock = _make_stock("A0001")
        self.post = _post(self.user, self.stock)
        self.comment = Comment.objects.create(post=self.post, user=self.user, body="c")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_post_like_toggle(self):
        url = reverse("post-like", kwargs={"id": self.post.id})
        r1 = self.client.post(url)
        self.assertEqual(r1.status_code, 200)
        self.assertTrue(r1.data["liked"])
        self.assertEqual(r1.data["like_count"], 1)
        r2 = self.client.post(url)  # 다시 누르면 취소
        self.assertFalse(r2.data["liked"])
        self.assertEqual(r2.data["like_count"], 0)

    def test_post_like_missing_404(self):
        r = self.client.post(reverse("post-like", kwargs={"id": 99999}))
        self.assertEqual(r.status_code, 404)

    def test_is_liked_in_detail(self):
        self.client.post(reverse("post-like", kwargs={"id": self.post.id}))
        r = self.client.get(reverse("post-detail", kwargs={"id": self.post.id}))
        self.assertTrue(r.data["is_liked"])

    def test_comment_like_toggle(self):
        url = reverse("comment-like", kwargs={"id": self.comment.id})
        r1 = self.client.post(url)
        self.assertTrue(r1.data["liked"])
        self.assertEqual(r1.data["like_count"], 1)
        r2 = self.client.post(url)
        self.assertFalse(r2.data["liked"])
        self.assertEqual(r2.data["like_count"], 0)

    def test_follow_and_unfollow(self):
        target = _make_user("target")
        r = self.client.post(reverse("follow", kwargs={"user_id": target.id}))
        self.assertEqual(r.status_code, 204)
        self.assertTrue(Follow.objects.filter(follower=self.user, following=target).exists())
        r2 = self.client.delete(reverse("follow", kwargs={"user_id": target.id}))
        self.assertEqual(r2.status_code, 204)
        self.assertFalse(Follow.objects.filter(follower=self.user, following=target).exists())

    def test_follow_self_400(self):
        r = self.client.post(reverse("follow", kwargs={"user_id": self.user.id}))
        self.assertEqual(r.status_code, 400)

    def test_follow_missing_user_404(self):
        r = self.client.post(reverse("follow", kwargs={"user_id": 99999}))
        self.assertEqual(r.status_code, 404)

    def test_unfollow_when_not_following_404(self):
        target = _make_user("target")
        r = self.client.delete(reverse("follow", kwargs={"user_id": target.id}))
        self.assertEqual(r.status_code, 404)

    def test_followers_and_following_lists(self):
        target = _make_user("target")
        self.client.post(reverse("follow", kwargs={"user_id": target.id}))
        r = self.client.get(reverse("followers", kwargs={"user_id": target.id}))
        self.assertEqual(r.data["total"], 1)
        self.assertEqual(r.data["items"][0]["user_id"], self.user.id)
        r2 = self.client.get(reverse("following", kwargs={"user_id": self.user.id}))
        self.assertEqual(r2.data["total"], 1)
        self.assertEqual(r2.data["items"][0]["user_id"], target.id)

    def test_like_count_two_users(self):
        url = reverse("post-like", kwargs={"id": self.post.id})
        self.client.post(url)
        other = _make_user("other2")
        c2 = APIClient()
        c2.force_authenticate(user=other)
        c2.post(url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 2)
