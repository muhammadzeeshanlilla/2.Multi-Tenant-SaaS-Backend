from django.urls import path

from apps.audit.views import AuditLogListAPIView


urlpatterns = [
    path("", AuditLogListAPIView.as_view(), name="audit-log-list"),
]