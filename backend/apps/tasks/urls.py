from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tasks.views import TaskViewSet


router = DefaultRouter()
router.register("", TaskViewSet, basename="tasks")


urlpatterns = [
    path("", include(router.urls)),
]