from django.urls import path

from accounts import views

urlpatterns = [
    path('signup', views.SignupView.as_view(), name='auth-signup'),
    path('login', views.LoginView.as_view(), name='auth-login'),
    path('logout', views.LogoutView.as_view(), name='auth-logout'),
    path('token/refresh', views.TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('me', views.MeView.as_view(), name='auth-me'),
    path('onboarding', views.OnboardingView.as_view(), name='auth-onboarding'),
    path('password/reset', views.PasswordResetView.as_view(), name='auth-password-reset'),
]
