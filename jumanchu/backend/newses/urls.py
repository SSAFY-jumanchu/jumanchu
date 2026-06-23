from django.urls import path

from newses import views

urlpatterns = [
    path('news/', views.StockNewsSearchView.as_view(), name='news-search'),
    path('news/economy/', views.FeedNewsView.as_view(), {'category': 'economy'}, name='news-economy'),
    path('news/feed/<str:category>/', views.FeedNewsView.as_view(), name='news-feed'),
    path('news/by-sector/', views.SectorNewsView.as_view(), name='news-by-sector'),
    path('news/watchlist/', views.WatchlistNewsView.as_view(), name='news-watchlist'),
    path('news/holdings/', views.HoldingsNewsView.as_view(), name='news-holdings'),
    path('news/stocks/<str:code>/', views.StockNewsView.as_view(), name='news-stock'),
]
