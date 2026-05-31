from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

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


class ProjectViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "restore", "assign_users"]:
            return [IsAdminOrManager()]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        queryset = Project.objects.filter(
            company=user.company,
            is_deleted=False,
        ).order_by("-created_at")

        if user.role == User.RoleChoices.EMPLOYEE:
            queryset = queryset.filter(members=user)

        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProjectCreateUpdateSerializer

        if self.action == "assign_users":
            return ProjectAssignUsersSerializer

        return ProjectListSerializer

    def list(self, request, *args, **kwargs):
        projects = self.get_queryset()
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