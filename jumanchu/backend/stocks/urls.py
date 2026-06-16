from django.urls import path

from stocks import views

urlpatterns = [
    path('stocks/', views.StockListView.as_view(), name='stock-list'),
    path('stocks/<str:code>/', views.StockDetailView.as_view(), name='stock-detail'),
    path('stocks/<str:code>/price/', views.StockPriceView.as_view(), name='stock-price'),
    path('stocks/<str:code>/orderbook/', views.StockOrderBookView.as_view(), name='stock-orderbook'),
    path('stocks/<str:code>/chart/', views.StockChartView.as_view(), name='stock-chart'),
    path('stocks/<str:code>/financials/', views.StockFinancialsView.as_view(), name='stock-financials'),
    path('stocks/<str:code>/posts/', views.StockPostsView.as_view(), name='stock-posts'),
    path('markets/summary/', views.MarketSummaryView.as_view(), name='markets-summary'),
    path('economic-events/', views.EconomicEventListView.as_view(), name='economic-events'),
]
