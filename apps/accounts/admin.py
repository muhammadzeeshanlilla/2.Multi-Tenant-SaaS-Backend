from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "company", "role", "is_active", "is_deleted")
    list_filter = ("role", "is_active", "is_deleted", "company")
    search_fields = ("username", "email")
    ordering = ("-created_at",)

    fieldsets = UserAdmin.fieldsets + (
        ("Company & Role Info", {
            "fields": ("company", "role", "is_deleted")
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Company & Role Info", {
            "fields": ("company", "role", "is_deleted")
        }),
    )