from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "company",
            "user",
            "action",
            "object_type",
            "object_id",
            "description",
            "ip_address",
            "created_at",
        ]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_user(self, obj):
        if not obj.user:
            return None

        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "email": obj.user.email,
            "role": obj.user.role,
        }

    @extend_schema_field(serializers.DictField())
    def get_company(self, obj):
        return {
            "id": obj.company.id,
            "name": obj.company.name,
            "slug": obj.company.slug,
        }
