from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.companies.models import Company


class AuditLoggingAndAccessTests(APITestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Audit A", email="audit-a@example.com")
        self.company_b = Company.objects.create(name="Audit B", email="audit-b@example.com")
        self.admin_a = User.objects.create_user(
            username="audit-admin-a",
            email="audit-admin-a@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company_a,
            role=User.RoleChoices.ADMIN,
        )
        self.manager_a = User.objects.create_user(
            username="audit-manager-a",
            email="audit-manager-a@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company_a,
            role=User.RoleChoices.MANAGER,
        )
        self.employee_a = User.objects.create_user(
            username="audit-employee-a",
            email="audit-employee-a@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company_a,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.admin_b = User.objects.create_user(
            username="audit-admin-b",
            email="audit-admin-b@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company_b,
            role=User.RoleChoices.ADMIN,
        )

    def test_project_and_task_mutations_create_complete_audit_logs(self):
        self.client.force_authenticate(self.admin_a)
        project_create = self.client.post(
            "/api/projects/",
            {"name": "Audited Project"},
            format="json",
        )
        project_id = project_create.data["data"]["id"]
        self.client.patch(
            f"/api/projects/{project_id}/",
            {"description": "Updated"},
            format="json",
        )
        task_create = self.client.post(
            "/api/tasks/",
            {"project_id": project_id, "title": "Audited Task"},
            format="json",
        )
        task_id = task_create.data["data"]["id"]
        self.client.patch(
            f"/api/tasks/{task_id}/",
            {"title": "Updated Audited Task"},
            format="json",
        )
        self.client.delete(f"/api/tasks/{task_id}/")
        self.client.delete(f"/api/projects/{project_id}/")

        expected_actions = {
            AuditLog.ActionChoices.PROJECT_CREATED,
            AuditLog.ActionChoices.PROJECT_UPDATED,
            AuditLog.ActionChoices.PROJECT_DELETED,
            AuditLog.ActionChoices.TASK_CREATED,
            AuditLog.ActionChoices.TASK_UPDATED,
            AuditLog.ActionChoices.TASK_DELETED,
        }
        logs = AuditLog.objects.filter(company=self.company_a, action__in=expected_actions)

        self.assertEqual(set(logs.values_list("action", flat=True)), expected_actions)
        for log in logs:
            self.assertEqual(log.user, self.admin_a)
            self.assertIsNotNone(log.object_id)
            self.assertIsNotNone(log.created_at)

    def test_admin_sees_only_own_company_logs(self):
        own_log = AuditLog.objects.create(
            company=self.company_a,
            user=self.admin_a,
            action=AuditLog.ActionChoices.USER_LOGIN,
        )
        AuditLog.objects.create(
            company=self.company_b,
            user=self.admin_b,
            action=AuditLog.ActionChoices.USER_LOGIN,
        )
        self.client.force_authenticate(self.admin_a)

        response = self.client.get("/api/audit-logs/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["data"][0]["id"], own_log.id)

    def test_manager_cannot_access_audit_logs(self):
        self.client.force_authenticate(self.manager_a)

        response = self.client.get("/api/audit-logs/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_access_audit_logs(self):
        self.client.force_authenticate(self.employee_a)

        response = self.client.get("/api/audit-logs/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_object_id_manipulation_does_not_expose_audit_log(self):
        other_log = AuditLog.objects.create(
            company=self.company_b,
            user=self.admin_b,
            action=AuditLog.ActionChoices.USER_LOGIN,
        )
        self.client.force_authenticate(self.admin_a)

        response = self.client.get(f"/api/audit-logs/{other_log.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_audit_logs_cannot_be_created_through_api(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.post(
            "/api/audit-logs/",
            {"action": AuditLog.ActionChoices.USER_LOGIN},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_audit_action_filter_is_tenant_scoped_and_paginated(self):
        for _ in range(3):
            AuditLog.objects.create(
                company=self.company_a,
                user=self.admin_a,
                action=AuditLog.ActionChoices.PROJECT_CREATED,
            )
        AuditLog.objects.create(
            company=self.company_a,
            user=self.admin_a,
            action=AuditLog.ActionChoices.TASK_CREATED,
        )
        AuditLog.objects.create(
            company=self.company_b,
            user=self.admin_b,
            action=AuditLog.ActionChoices.PROJECT_CREATED,
        )
        self.client.force_authenticate(self.admin_a)

        response = self.client.get(
            "/api/audit-logs/?action=PROJECT_CREATED&page_size=2"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["data"]), 2)
        self.assertIsNotNone(response.data["next"])
