from django.urls import path

from portfolio import views

urlpatterns = [
    # Order
    path('orders/preview/', views.OrderPreviewView.as_view(), name='order-preview'),
    path('orders/', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:id>/', views.OrderDetailView.as_view(), name='order-detail'),

    # Portfolio
    path('portfolio/', views.PortfolioSummaryView.as_view(), name='portfolio-summary'),
    path('portfolio/holdings/', views.HoldingsListView.as_view(), name='portfolio-holdings'),
    path('portfolio/holdings/<str:code>/', views.HoldingDetailView.as_view(), name='portfolio-holding-detail'),
    path('portfolio/balance/', views.BalanceView.as_view(), name='portfolio-balance'),
    path('portfolio/allocation/', views.AllocationView.as_view(), name='portfolio-allocation'),
    path('portfolio/milestones/', views.MilestonesView.as_view(), name='portfolio-milestones'),
]
