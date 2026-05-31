from django.contrib import admin

from .models import Project, ProjectMember


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "status", "created_by", "is_deleted", "created_at")
    list_filter = ("status", "is_deleted", "company", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "user", "company", "created_at")
    list_filter = ("company", "created_at")
    search_fields = ("project__name", "user__username", "user__email")