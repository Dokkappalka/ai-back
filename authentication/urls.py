"""
URL configuration for authentication endpoints.
"""
from django.urls import path
from .views import login_view, logout_view, user_profile_view, CookieTokenRefreshView

app_name = 'authentication'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', user_profile_view, name='user_profile'),
]

