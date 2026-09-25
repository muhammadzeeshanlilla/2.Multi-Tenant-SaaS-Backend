from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel
from apps.companies.models import Company
from apps.accounts.models import User


class Project(BaseModel):
    class StatusChoices(models.TextChoices):
        PLANNING = "PLANNING", "Planning"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNING
    )

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="created_projects",
        null=True,
        blank=True
    )

    members = models.ManyToManyField(
        User,
        through="ProjectMember",
        related_name="assigned_projects",
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["company", "is_deleted", "status"],
                name="proj_company_del_status_idx",
            ),
        ]

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="project_members"
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="project_members"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_memberships"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")
        ordering = ["-created_at"]

    def clean(self):
        super().clean()

        errors = {}

        if self.project_id and self.company_id != self.project.company_id:
            errors["company"] = "Membership company must match the project company."

        if self.user_id and self.company_id != self.user.company_id:
            errors["user"] = "Project member must belong to the membership company."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"
