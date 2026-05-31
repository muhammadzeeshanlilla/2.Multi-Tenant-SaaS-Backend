from django.urls import path

from apps.accounts.views import CompanyRegisterAPIView


urlpatterns = [
    path("company-register/", CompanyRegisterAPIView.as_view(), name="company-register"),
]