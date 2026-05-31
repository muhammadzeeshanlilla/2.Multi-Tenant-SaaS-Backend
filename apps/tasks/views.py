from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.utils import create_audit_log
from apps.audit.models import AuditLog
from apps.tasks.models import Task
from apps.tasks.serializers import (
    TaskListSerializer,
    TaskCreateUpdateSerializer,
    TaskStatusUpdateSerializer,
)
from apps.accounts.models import User
from apps.accounts.permissions import IsAdminOrManager


class TaskViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "restore"]:
            return [IsAdminOrManager()]

        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        queryset = Task.objects.filter(
            company=user.company,
            is_deleted=False,
        ).order_by("-created_at")

        if user.role == User.RoleChoices.EMPLOYEE:
            queryset = queryset.filter(assigned_to=user)

        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TaskCreateUpdateSerializer

        if self.action == "status":
            return TaskStatusUpdateSerializer

        return TaskListSerializer

    def list(self, request, *args, **kwargs):
        tasks = self.get_queryset()
        serializer = TaskListSerializer(tasks, many=True)

        return Response(
            {
                "success": True,
                "message": "Tasks fetched successfully.",
                "count": tasks.count(),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            task = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Task created successfully.",
                    "data": TaskListSerializer(task).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "message": "Task creation failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()

        return Response(
            {
                "success": True,
                "message": "Task fetched successfully.",
                "data": TaskListSerializer(task).data,
            },
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        task = self.get_object()

        serializer = self.get_serializer(
            task,
            data=request.data,
            context={"request": request},
            partial=False,
        )

        if serializer.is_valid():
            task = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Task updated successfully.",
                    "data": TaskListSerializer(task).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Task update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()

        serializer = self.get_serializer(
            task,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            task = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Task updated successfully.",
                    "data": TaskListSerializer(task).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Task update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()

        task.is_deleted = True
        task.save()

        create_audit_log(
        request=request,
        action=AuditLog.ActionChoices.TASK_DELETED,
        object_type="Task",
        object_id=task.id,
        description=f"Task '{task.title}' was deleted by {request.user.username}.",
        )

        return Response(
            {
                "success": True,
                "message": "Task deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        task = Task.objects.filter(
            id=pk,
            company=request.user.company,
            is_deleted=True,
        ).first()

        if not task:
            return Response(
                {
                    "success": False,
                    "message": "Deleted task not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        task.is_deleted = False
        task.save()

        create_audit_log(
        request=request,
        action=AuditLog.ActionChoices.TASK_RESTORED,
        object_type="Task",
        object_id=task.id,
        description=f"Task '{task.title}' was restored by {request.user.username}.",
        )

        return Response(
            {
                "success": True,
                "message": "Task restored successfully.",
                "data": TaskListSerializer(task).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], url_path="status")
    def status(self, request, pk=None):
        task = self.get_object()

        user = request.user

        if user.role == User.RoleChoices.EMPLOYEE and task.assigned_to != user:
            return Response(
                {
                    "success": False,
                    "message": "You can update only your own assigned task status.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TaskStatusUpdateSerializer(data=request.data)

        if serializer.is_valid():
            task.status = serializer.validated_data["status"]
            task.save()

            create_audit_log(
            request=request,
            action=AuditLog.ActionChoices.TASK_STATUS_CHANGED,
            object_type="Task",
            object_id=task.id,
            description=f"Task '{task.title}' status changed to {task.status} by {request.user.username}.",
   )

            return Response(
                {
                    "success": True,
                    "message": "Task status updated successfully.",
                    "data": TaskListSerializer(task).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Task status update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )