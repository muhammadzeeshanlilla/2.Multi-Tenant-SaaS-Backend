from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "company",
        "project",
        "assigned_to",
        "status",
        "priority",
        "is_deleted",
        "created_at",
    )
    list_filter = ("status", "priority", "is_deleted", "company", "created_at")
    search_fields = ("title", "description", "project__name")
    readonly_fields = ("created_at", "updated_at")