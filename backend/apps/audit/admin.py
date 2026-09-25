from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "user", "action", "object_type", "object_id", "ip_address", "created_at")
    list_filter = ("action", "company", "created_at")
    search_fields = ("description", "object_type", "user__username", "user__email")
    readonly_fields = ("created_at",)