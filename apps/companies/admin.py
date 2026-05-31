from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "email", "is_active", "created_at")
    search_fields = ("name", "email", "slug")
    list_filter = ("is_active", "created_at")
    readonly_fields = ("created_at", "updated_at")