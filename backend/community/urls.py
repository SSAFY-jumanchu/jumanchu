from django.urls import path

from community import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:id>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:id>/', views.CommentDetailView.as_view(), name='comment-detail'),

    path('posts/<int:id>/like/', views.PostLikeView.as_view(), name='post-like'),
    path('comments/<int:id>/like/', views.CommentLikeView.as_view(), name='comment-like'),
    path('users/<int:user_id>/follow/', views.FollowView.as_view(), name='follow'),
    path('users/<int:user_id>/followers/', views.FollowersView.as_view(), name='followers'),
    path('users/<int:user_id>/following/', views.FollowingView.as_view(), name='following'),
]

