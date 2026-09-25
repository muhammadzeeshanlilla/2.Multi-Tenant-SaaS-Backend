from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.companies.models import Company
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task


class TaskTenantConsistencyModelTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A", email="a@example.com")
        self.company_b = Company.objects.create(name="Company B", email="b@example.com")
        self.creator_a = User.objects.create_user(
            username="creator-a",
            email="creator-a@example.com",
            password="StrongPass123!",
            company=self.company_a,
            role=User.RoleChoices.ADMIN,
        )
        self.creator_b = User.objects.create_user(
            username="creator-b",
            email="creator-b@example.com",
            password="StrongPass123!",
            company=self.company_b,
            role=User.RoleChoices.ADMIN,
        )
        self.employee_a = User.objects.create_user(
            username="employee-a",
            email="employee-a@example.com",
            password="StrongPass123!",
            company=self.company_a,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.employee_b = User.objects.create_user(
            username="employee-b",
            email="employee-b@example.com",
            password="StrongPass123!",
            company=self.company_b,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.project_a = Project.objects.create(
            company=self.company_a,
            name="Project A",
            created_by=self.creator_a,
        )
        self.project_b = Project.objects.create(
            company=self.company_b,
            name="Project B",
            created_by=self.creator_b,
        )
        ProjectMember.objects.create(
            company=self.company_a,
            project=self.project_a,
            user=self.employee_a,
        )

    def test_valid_same_company_task_creation(self):
        task = Task.objects.create(
            company=self.company_a,
            project=self.project_a,
            title="Valid Task",
            assigned_to=self.employee_a,
            created_by=self.creator_a,
        )

        self.assertIsNotNone(task.pk)

    def test_cross_company_project_is_rejected(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(
                company=self.company_a,
                project=self.project_b,
                title="Invalid Project",
                created_by=self.creator_a,
            )

    def test_cross_company_assignee_is_rejected(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(
                company=self.company_a,
                project=self.project_a,
                title="Invalid Assignee",
                assigned_to=self.employee_b,
                created_by=self.creator_a,
            )

    def test_cross_company_creator_is_rejected(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(
                company=self.company_a,
                project=self.project_a,
                title="Invalid Creator",
                created_by=self.creator_b,
            )

    def test_cross_company_project_membership_is_rejected(self):
        with self.assertRaises(ValidationError):
            ProjectMember.objects.create(
                company=self.company_a,
                project=self.project_a,
                user=self.employee_b,
            )

    def test_same_company_non_member_assignee_is_rejected(self):
        non_member = User.objects.create_user(
            username="non-member-a",
            email="non-member-a@example.com",
            password="StrongPass123!",
            company=self.company_a,
            role=User.RoleChoices.EMPLOYEE,
        )

        with self.assertRaises(ValidationError):
            Task.objects.create(
                company=self.company_a,
                project=self.project_a,
                title="Invalid Membership",
                assigned_to=non_member,
                created_by=self.creator_a,
            )

    def test_duplicate_project_membership_is_rejected(self):
        with self.assertRaises(ValidationError):
            ProjectMember.objects.create(
                company=self.company_a,
                project=self.project_a,
                user=self.employee_a,
            )

    def test_active_task_cannot_be_created_under_deleted_project_directly(self):
        self.project_a.is_deleted = True
        self.project_a.save(update_fields=["is_deleted"])

        with self.assertRaises(ValidationError):
            Task.objects.create(
                company=self.company_a,
                project=self.project_a,
                title="Invalid Deleted Parent",
                created_by=self.creator_a,
            )


class TaskIntegrityAPITests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Task Company",
            email="tasks@example.com",
        )
        self.admin = User.objects.create_user(
            username="task-admin",
            email="task-admin@example.com",
            password="StrongPass123!",
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )
        self.employee = User.objects.create_user(
            username="task-employee",
            email="task-employee@example.com",
            password="StrongPass123!",
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.other_employee = User.objects.create_user(
            username="other-employee",
            email="other-employee@example.com",
            password="StrongPass123!",
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.project = Project.objects.create(
            company=self.company,
            name="Active Project",
            created_by=self.admin,
        )
        self.other_project = Project.objects.create(
            company=self.company,
            name="Other Project",
            created_by=self.admin,
        )
        self.deleted_project = Project.objects.create(
            company=self.company,
            name="Deleted Project",
            created_by=self.admin,
            is_deleted=True,
        )
        ProjectMember.objects.create(
            company=self.company,
            project=self.project,
            user=self.employee,
        )
        self.task = Task.objects.create(
            company=self.company,
            project=self.project,
            title="Existing Task",
            assigned_to=self.employee,
            created_by=self.admin,
        )
        other_company = Company.objects.create(
            name="Other Task Company",
            email="other-tasks@example.com",
        )
        other_admin = User.objects.create_user(
            username="other-task-admin",
            email="other-task-admin@example.com",
            password="StrongPass123!",
            company=other_company,
            role=User.RoleChoices.ADMIN,
        )
        other_project = Project.objects.create(
            company=other_company,
            name="Other Tenant Project",
            created_by=other_admin,
        )
        self.other_tenant_task = Task.objects.create(
            company=other_company,
            project=other_project,
            title="Other Tenant Task",
            created_by=other_admin,
        )
        self.client.force_authenticate(self.admin)
        self.email_patcher = patch("apps.tasks.views.send_task_assignment_email.delay")
        self.email_patcher.start()
        self.addCleanup(self.email_patcher.stop)

    def test_task_below_active_project_is_visible(self):
        response = self.client.get("/api/tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data["data"]], [self.task.id])

    def test_cross_company_task_detail_is_not_exposed(self):
        response = self.client.get(f"/api/tasks/{self.other_tenant_task.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_below_deleted_project_is_not_visible_or_retrievable(self):
        hidden_task = Task.objects.create(
            company=self.company,
            project=self.deleted_project,
            title="Hidden Task",
            created_by=self.admin,
            is_deleted=True,
        )
        Task.objects.filter(pk=hidden_task.pk).update(is_deleted=False)

        list_response = self.client.get("/api/tasks/")
        retrieve_response = self.client.get(f"/api/tasks/{hidden_task.id}/")

        self.assertNotIn(hidden_task.id, [item["id"] for item in list_response.data["data"]])
        self.assertEqual(retrieve_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_create_task_below_deleted_project(self):
        response = self.client.post(
            "/api/tasks/",
            {"project_id": self.deleted_project.id, "title": "Invalid Task"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_restore_task_below_deleted_project(self):
        deleted_task = Task.objects.create(
            company=self.company,
            project=self.deleted_project,
            title="Deleted Child",
            created_by=self.admin,
            is_deleted=True,
        )

        response = self.client.post(f"/api/tasks/{deleted_task.id}/restore/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        deleted_task.refresh_from_db()
        self.assertTrue(deleted_task.is_deleted)

    def test_cannot_move_task_to_deleted_project(self):
        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"project_id": self.deleted_project.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_assignee_only_with_valid_membership(self):
        ProjectMember.objects.create(
            company=self.company,
            project=self.project,
            user=self.other_employee,
        )

        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"assigned_to_id": self.other_employee.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.other_employee)

    def test_patch_assignee_only_with_invalid_membership(self):
        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"assigned_to_id": self.other_employee.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.employee)

    def test_patch_project_only_when_current_assignee_remains_valid(self):
        ProjectMember.objects.create(
            company=self.company,
            project=self.other_project,
            user=self.employee,
        )

        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"project_id": self.other_project.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.project, self.other_project)

    def test_patch_project_only_when_current_assignee_becomes_invalid(self):
        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"project_id": self.other_project.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.task.refresh_from_db()
        self.assertEqual(self.task.project, self.project)

    def test_explicit_null_unassigns_task(self):
        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"assigned_to_id": None},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.assigned_to)

    def test_omitted_assignee_preserves_existing_assignment(self):
        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"title": "Renamed Task"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.employee)

    def test_task_filters_remain_tenant_scoped(self):
        Task.objects.create(
            company=self.company,
            project=self.project,
            title="Completed Assigned Task",
            assigned_to=self.employee,
            created_by=self.admin,
            status=Task.StatusChoices.COMPLETED,
        )
        Task.objects.create(
            company=self.company,
            project=self.other_project,
            title="Completed Unassigned Task",
            created_by=self.admin,
            status=Task.StatusChoices.COMPLETED,
        )

        response = self.client.get(
            f"/api/tasks/?status=COMPLETED&project={self.project.id}&assignee={self.employee.id}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["data"][0]["title"], "Completed Assigned Task")

    def test_invalid_task_filter_returns_controlled_error(self):
        response = self.client.get("/api/tasks/?project=not-a-number")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
