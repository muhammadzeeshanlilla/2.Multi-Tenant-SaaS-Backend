from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from apps.tasks.models import Task
from apps.projects.models import Project
from apps.accounts.models import User


class TaskListSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "company",
            "project",
            "assigned_to",
            "status",
            "priority",
            "due_date",
            "created_by",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.DictField())
    def get_company(self, obj):
        return {
            "id": obj.company.id,
            "name": obj.company.name,
            "slug": obj.company.slug,
        }

    @extend_schema_field(serializers.DictField())
    def get_project(self, obj):
        return {
            "id": obj.project.id,
            "name": obj.project.name,
            "status": obj.project.status,
        }

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_assigned_to(self, obj):
        if not obj.assigned_to:
            return None

        return {
            "id": obj.assigned_to.id,
            "username": obj.assigned_to.username,
            "email": obj.assigned_to.email,
            "role": obj.assigned_to.role,
        }

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_created_by(self, obj):
        if not obj.created_by:
            return None

        return {
            "id": obj.created_by.id,
            "username": obj.created_by.username,
            "email": obj.created_by.email,
            "role": obj.created_by.role,
        }


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(write_only=True)
    assigned_to_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Task
        fields = [
            "project_id",
            "title",
            "description",
            "assigned_to_id",
            "status",
            "priority",
            "due_date",
        ]

    def validate_project_id(self, value):
        request = self.context.get("request")

        project = Project.objects.filter(
            id=value,
            company=request.user.company,
            is_deleted=False,
        ).first()

        if not project:
            raise serializers.ValidationError(
                "Project not found or does not belong to your company."
            )

        return value

    def validate_assigned_to_id(self, value):
        request = self.context.get("request")

        if value is None:
            return value

        user = User.objects.filter(
            id=value,
            company=request.user.company,
            is_deleted=False,
            is_active=True,
        ).first()

        if not user:
            raise serializers.ValidationError(
                "Assigned user not found or does not belong to your company."
            )

        return value

    def validate(self, attrs):
        request = self.context.get("request")

        project_id = attrs.get(
            "project_id",
            self.instance.project_id if self.instance else None,
        )
        assigned_to_id = attrs.get(
            "assigned_to_id",
            self.instance.assigned_to_id if self.instance else None,
        )

        if project_id:
            project = Project.objects.filter(
                id=project_id,
                company=request.user.company,
                is_deleted=False,
            ).first()

            if not project:
                raise serializers.ValidationError({
                    "project_id": "Project not found or does not belong to your company."
                })

        if assigned_to_id is not None:
            assigned_user = User.objects.filter(
                id=assigned_to_id,
                company=request.user.company,
                is_deleted=False,
                is_active=True,
            ).first()

            if not assigned_user:
                raise serializers.ValidationError({
                    "assigned_to_id": "Assigned user not found or does not belong to your company."
                })

            if not project.members.filter(id=assigned_user.id).exists():
                raise serializers.ValidationError({
                    "assigned_to_id": "This user is not assigned to this project."
                })

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        project_id = validated_data.pop("project_id")
        assigned_to_id = validated_data.pop("assigned_to_id", None)

        project = Project.objects.get(
            id=project_id,
            company=request.user.company,
            is_deleted=False,
        )

        assigned_user = None
        if assigned_to_id:
            assigned_user = User.objects.get(
                id=assigned_to_id,
                company=request.user.company,
                is_deleted=False,
                is_active=True,
            )

        task = Task.objects.create(
            company=request.user.company,
            project=project,
            assigned_to=assigned_user,
            created_by=request.user,
            **validated_data,
        )

        return task

    def update(self, instance, validated_data):
        request = self.context.get("request")

        project_id = validated_data.pop("project_id", None)
        assigned_to_was_supplied = "assigned_to_id" in validated_data
        assigned_to_id = validated_data.pop("assigned_to_id", None)

        if project_id:
            project = Project.objects.get(
                id=project_id,
                company=request.user.company,
                is_deleted=False,
            )
            instance.project = project

        if assigned_to_was_supplied:
            if assigned_to_id is None:
                instance.assigned_to = None
            else:
                assigned_user = User.objects.get(
                    id=assigned_to_id,
                    company=request.user.company,
                    is_deleted=False,
                    is_active=True,
                )
                instance.assigned_to = assigned_user

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class TaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.StatusChoices.choices)
