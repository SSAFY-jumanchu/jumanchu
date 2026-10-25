from django.urls import path

from recommend import views

urlpatterns = [
    path('watchlist/', views.WatchlistView.as_view(), name='watchlist'),
    path('watchlist/<str:code>/', views.WatchlistItemView.as_view(), name='watchlist-item'),
    path('recommendations/', views.RecommendSwipeView.as_view(), name='recommend-swipe'),
    path('longterm/ranking/', views.LongTermRankingView.as_view(), name='longterm-ranking'),
    path('longterm/<str:code>/report/', views.LongTermReportView.as_view(), name='longterm-report'),
    path('longterm/<str:code>/history/', views.LongTermHistoryView.as_view(), name='longterm-history'),
]
