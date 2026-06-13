from django.urls import path

from recommend import views

urlpatterns = [
    path('watchlist/', views.WatchlistView.as_view(), name='watchlist'),
    path('watchlist/<str:code>/', views.WatchlistItemView.as_view(), name='watchlist-item'),
]
