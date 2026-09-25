from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel
from apps.companies.models import Company
from apps.accounts.models import User
from apps.projects.models import Project


class Task(BaseModel):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    class PriorityChoices(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )

    priority = models.CharField(
        max_length=20,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM
    )

    due_date = models.DateField(blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["company", "is_deleted", "status"],
                name="task_company_del_status_idx",
            ),
            models.Index(
                fields=["company", "assigned_to", "is_deleted"],
                name="task_company_assignee_idx",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if self.project_id:
            if self.company_id != self.project.company_id:
                errors["project"] = "Task company must match the project company."

            if not self.is_deleted and self.project.is_deleted:
                errors["project"] = "Active tasks cannot belong to a deleted project."

        if self.assigned_to_id:
            if self.company_id != self.assigned_to.company_id:
                errors["assigned_to"] = "Assigned user must belong to the task company."
            elif self.project_id and not self.project.members.filter(
                id=self.assigned_to_id,
                is_active=True,
                is_deleted=False,
            ).exists():
                errors["assigned_to"] = "Assigned user must be an active project member."

        if self.created_by_id and self.company_id != self.created_by.company_id:
            errors["created_by"] = "Task creator must belong to the task company."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title
