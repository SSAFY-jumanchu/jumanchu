from django.urls import path

from diary import views

urlpatterns = [
    path('diaries/', views.DiaryListCreateView.as_view(), name='diary-list-create'),
    path('diaries/<int:id>/', views.DiaryDetailView.as_view(), name='diary-detail'),
]
