from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    CompanyRegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
)


urlpatterns = [
    path("company-register/", CompanyRegisterAPIView.as_view(), name="company-register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
]
