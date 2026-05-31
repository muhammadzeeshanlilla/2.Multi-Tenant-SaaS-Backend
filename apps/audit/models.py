from django.db import models

from apps.companies.models import Company
from apps.accounts.models import User


class AuditLog(models.Model):
    class ActionChoices(models.TextChoices):
        USER_LOGIN = "USER_LOGIN", "User Login"
        USER_LOGOUT = "USER_LOGOUT", "User Logout"
        USER_CREATED = "USER_CREATED", "User Created"

        PROJECT_CREATED = "PROJECT_CREATED", "Project Created"
        PROJECT_UPDATED = "PROJECT_UPDATED", "Project Updated"
        PROJECT_DELETED = "PROJECT_DELETED", "Project Deleted"
        PROJECT_RESTORED = "PROJECT_RESTORED", "Project Restored"

        TASK_CREATED = "TASK_CREATED", "Task Created"
        TASK_UPDATED = "TASK_UPDATED", "Task Updated"
        TASK_DELETED = "TASK_DELETED", "Task Deleted"
        TASK_RESTORED = "TASK_RESTORED", "Task Restored"
        TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED", "Task Status Changed"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=50,
        choices=ActionChoices.choices
    )

    object_type = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} - {self.user}"