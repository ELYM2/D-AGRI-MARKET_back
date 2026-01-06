from django.urls import path
from .views import (
    RegisterView,
    MeView,
    LogoutView,
    ChangePasswordView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('password/change/', ChangePasswordView.as_view(), name='auth-password-change'),
]
