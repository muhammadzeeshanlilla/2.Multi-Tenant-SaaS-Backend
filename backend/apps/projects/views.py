from django.db import transaction
from django.db.models import Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from apps.audit.models import AuditLog
from apps.audit.utils import create_audit_log

from apps.projects.models import Project, ProjectMember
from apps.projects.serializers import (
    ProjectListSerializer,
    ProjectCreateUpdateSerializer,
    ProjectAssignUsersSerializer,
)
from apps.accounts.permissions import IsAdminOrManager
from apps.accounts.models import User

from apps.common.tasks import send_project_assignment_email
from apps.common.jobs import enqueue_after_commit


@extend_schema_view(
    list=extend_schema(
        summary="List tenant-scoped projects",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                enum=[choice for choice, _ in Project.StatusChoices.choices],
                description="Filter by project status.",
            ),
        ],
    ),
    create=extend_schema(summary="Create a project (Admin or Manager)"),
    retrieve=extend_schema(summary="Retrieve a tenant-scoped project"),
    update=extend_schema(summary="Replace project fields (Admin or Manager)"),
    partial_update=extend_schema(summary="Update project fields (Admin or Manager)"),
    destroy=extend_schema(summary="Soft delete a project (Admin or Manager)"),
)
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.none()

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "restore",
            "assign_users",
        ]:
            return [IsAdminOrManager()]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        queryset = Project.objects.filter(
            company=user.company,
            is_deleted=False,
        ).select_related(
            "company",
            "created_by",
        ).prefetch_related(
            Prefetch(
                "members",
                queryset=User.objects.filter(is_deleted=False),
                to_attr="active_members",
            )
        ).order_by("-created_at")

        if user.role == User.RoleChoices.EMPLOYEE:
            queryset = queryset.filter(members=user)

        project_status = self.request.query_params.get("status")
        if project_status:
            valid_statuses = {choice for choice, _ in Project.StatusChoices.choices}
            if project_status not in valid_statuses:
                raise ValidationError({"status": "Invalid project status."})
            queryset = queryset.filter(status=project_status)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProjectCreateUpdateSerializer

        if self.action == "assign_users":
            return ProjectAssignUsersSerializer

        return ProjectListSerializer

    def list(self, request, *args, **kwargs):
        projects = self.get_queryset()
        page = self.paginate_queryset(projects)

        if page is not None:
            serializer = ProjectListSerializer(page, many=True)
            self.paginator.response_message = "Projects fetched successfully."
            return self.get_paginated_response(serializer.data)

        serializer = ProjectListSerializer(projects, many=True)

        return Response(
            {
                "success": True,
                "message": "Projects fetched successfully.",
                "count": projects.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            project = serializer.save(
                company=request.user.company,
                created_by=request.user,
            )

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.PROJECT_CREATED,
                object_type="Project",
                object_id=project.id,
                description=f"Project '{project.name}' was created by {request.user.username}.",
            )

            return Response(
                {
                    "success": True,
                    "message": "Project created successfully.",
                    "data": ProjectListSerializer(project).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "message": "Project creation failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def retrieve(self, request, *args, **kwargs):
        project = self.get_object()

        return Response(
            {
                "success": True,
                "message": "Project fetched successfully.",
                "data": ProjectListSerializer(project).data,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        serializer = self.get_serializer(project, data=request.data, partial=False)

        if serializer.is_valid():
            project = serializer.save()

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.PROJECT_UPDATED,
                object_type="Project",
                object_id=project.id,
                description=f"Project '{project.name}' was updated by {request.user.username}.",
            )

            return Response(
                {
                    "success": True,
                    "message": "Project updated successfully.",
                    "data": ProjectListSerializer(project).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Project update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        project = self.get_object()
        serializer = self.get_serializer(project, data=request.data, partial=True)

        if serializer.is_valid():
            project = serializer.save()

            create_audit_log(
                request=request,
                action=AuditLog.ActionChoices.PROJECT_UPDATED,
                object_type="Project",
                object_id=project.id,
                description=f"Project '{project.name}' was updated by {request.user.username}.",
            )

            return Response(
                {
                    "success": True,
                    "message": "Project updated successfully.",
                    "data": ProjectListSerializer(project).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Project update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()

        project.is_deleted = True
        project.save()

        create_audit_log(
            request=request,
            action=AuditLog.ActionChoices.PROJECT_DELETED,
            object_type="Project",
            object_id=project.id,
            description=f"Project '{project.name}' was deleted by {request.user.username}.",
        )

        return Response(
            {
                "success": True,
                "message": "Project deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        project = Project.objects.filter(
            id=pk,
            company=request.user.company,
            is_deleted=True,
        ).first()

        if not project:
            return Response(
                {
                    "success": False,
                    "message": "Deleted project not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        project.is_deleted = False
        project.save()

        create_audit_log(
            request=request,
            action=AuditLog.ActionChoices.PROJECT_RESTORED,
            object_type="Project",
            object_id=project.id,
            description=f"Project '{project.name}' was restored by {request.user.username}.",
        )

        return Response(
            {
                "success": True,
                "message": "Project restored successfully.",
                "data": ProjectListSerializer(project).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="assign-users")
    def assign_users(self, request, pk=None):
        project = self.get_object()

        serializer = ProjectAssignUsersSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            user_ids = serializer.validated_data["user_ids"]

            with transaction.atomic():
                ProjectMember.objects.filter(project=project).delete()

                users = User.objects.filter(
                    id__in=user_ids,
                    company=request.user.company,
                    is_deleted=False,
                    is_active=True,
                )

                for user in users:
                    ProjectMember.objects.create(
                        company=request.user.company,
                        project=project,
                        user=user,
                    )

                    if user.email:
                        enqueue_after_commit(
                            send_project_assignment_email,
                            user_email=user.email,
                            username=user.username,
                            project_name=project.name,
                            assigned_by=request.user.username,
                            assigned_by_role=request.user.role,
                        )

                create_audit_log(
                    request=request,
                    action=AuditLog.ActionChoices.PROJECT_USERS_ASSIGNED,
                    object_type="Project",
                    object_id=project.id,
                    description=f"Users were assigned to project '{project.name}' by {request.user.username}.",
                )

            return Response(
                {
                    "success": True,
                    "message": "Users assigned to project successfully.",
                    "data": ProjectListSerializer(project).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "User assignment failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
