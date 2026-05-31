from rest_framework import serializers

from apps.projects.models import Project, ProjectMember
from apps.accounts.models import User


class ProjectListSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "status",
            "start_date",
            "end_date",
            "company",
            "created_by",
            "members",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

    def get_company(self, obj):
        return {
            "id": obj.company.id,
            "name": obj.company.name,
            "slug": obj.company.slug,
        }

    def get_created_by(self, obj):
        if not obj.created_by:
            return None

        return {
            "id": obj.created_by.id,
            "username": obj.created_by.username,
            "email": obj.created_by.email,
            "role": obj.created_by.role,
        }

    def get_members(self, obj):
        members = obj.members.filter(is_deleted=False)

        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
            for user in members
        ]


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "status",
            "start_date",
            "end_date",
        ]

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date cannot be before start date."
            })

        return attrs


class ProjectAssignUsersSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

    def validate_user_ids(self, value):
        request = self.context.get("request")

        users = User.objects.filter(
            id__in=value,
            company=request.user.company,
            is_deleted=False,
            is_active=True,
        )

        if users.count() != len(set(value)):
            raise serializers.ValidationError(
                "One or more users are invalid or do not belong to your company."
            )

        return value