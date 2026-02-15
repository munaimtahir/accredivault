from django.urls import path
from .views import (
    LoginView,
    RefreshView,
    MeView,
    UserListView,
    UserDetailView,
    UserResetPasswordView,
)

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/refresh', RefreshView.as_view(), name='auth-refresh'),
    path('auth/me', MeView.as_view(), name='auth-me'),
    path('users', UserListView.as_view(), name='users-list'),
    path('users/<int:user_id>', UserDetailView.as_view(), name='users-detail'),
    path('users/<int:user_id>/reset-password', UserResetPasswordView.as_view(), name='users-reset-password'),
]
