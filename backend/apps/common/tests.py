from unittest.mock import Mock, patch

from django.db import transaction
from django.test import SimpleTestCase, TestCase, override_settings
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.common.jobs import enqueue_after_commit
from apps.companies.models import Company
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task


class BrowserAndSchemaReadinessTests(SimpleTestCase):
    @override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"])
    def test_configured_frontend_origin_receives_cors_header(self):
        response = self.client.options(
            "/api/auth/login/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )

        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:3000",
        )

    @override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"])
    def test_unconfigured_origin_does_not_receive_cors_header(self):
        response = self.client.options(
            "/api/auth/login/",
            HTTP_ORIGIN="https://untrusted.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )

        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    def test_openapi_schema_contains_public_api_contract(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        paths = schema["paths"]

        expected_paths = {
            "/api/auth/company-register/",
            "/api/auth/login/",
            "/api/auth/logout/",
            "/api/auth/me/",
            "/api/auth/token/refresh/",
            "/api/users/",
            "/api/users/{id}/",
            "/api/projects/",
            "/api/projects/{id}/",
            "/api/projects/{id}/assign-users/",
            "/api/tasks/",
            "/api/tasks/{id}/",
            "/api/tasks/{id}/status/",
            "/api/audit-logs/",
        }

        self.assertTrue(expected_paths.issubset(paths.keys()))
        self.assertIn("jwtAuth", schema["components"]["securitySchemes"])


class BackgroundJobTransactionTests(TestCase):
    def test_job_is_not_published_when_transaction_rolls_back(self):
        task = Mock()

        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                enqueue_after_commit(task, value="test")
                raise RuntimeError("force rollback")

        task.delay.assert_not_called()

    @override_settings(BACKGROUND_JOBS_ENABLED=False)
    def test_disabled_jobs_do_not_contact_celery_after_commit(self):
        task = Mock()
        task.name = "test.disabled"

        with self.assertLogs("apps.common.jobs", level="INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                enqueue_after_commit(task, value="test")

        task.delay.assert_not_called()

    @override_settings(BACKGROUND_JOBS_ENABLED=True)
    def test_unexpected_publisher_programming_error_is_not_hidden(self):
        task = Mock()
        task.delay.side_effect = ValueError("invalid task arguments")

        with self.assertRaises(ValueError):
            with self.captureOnCommitCallbacks(execute=True):
                enqueue_after_commit(task, value="test")


class AssignmentNotificationSafetyTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Notification Company",
            email="notifications@example.com",
        )
        self.admin = User.objects.create_user(
            username="notification-admin",
            email="notification-admin@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )
        self.employee = User.objects.create_user(
            username="notification-employee",
            email="notification-employee@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.project = Project.objects.create(
            company=self.company,
            name="Notification Project",
            created_by=self.admin,
        )
        ProjectMember.objects.create(
            company=self.company,
            project=self.project,
            user=self.employee,
        )
        self.client.force_authenticate(self.admin)

    def task_data(self, title):
        return {
            "project_id": self.project.id,
            "title": title,
            "assigned_to_id": self.employee.id,
        }

    @override_settings(BACKGROUND_JOBS_ENABLED=True)
    def test_normal_task_assignment_publishes_notification_after_commit(self):
        with patch("apps.tasks.views.send_task_assignment_email.delay") as publish:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    "/api/tasks/",
                    self.task_data("Normal Notification"),
                    format="json",
                )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        publish.assert_called_once()

    @override_settings(BACKGROUND_JOBS_ENABLED=True)
    def test_broker_failure_does_not_rollback_or_crash_task_creation(self):
        with patch(
            "apps.tasks.views.send_task_assignment_email.delay",
            side_effect=RuntimeError(
                "Retry limit exceeded while trying to reconnect to the Celery "
                "result store backend. The Celery application must be restarted."
            ),
        ) as publish:
            with self.assertLogs("apps.common.jobs", level="ERROR"):
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(
                        "/api/tasks/",
                        self.task_data("Broker Failure Task"),
                        format="json",
                    )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Task.objects.filter(title="Broker Failure Task").exists())
        publish.assert_called_once()

    @override_settings(BACKGROUND_JOBS_ENABLED=True)
    def test_project_assignment_uses_post_commit_notification(self):
        with patch("apps.projects.views.send_project_assignment_email.delay") as publish:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    f"/api/projects/{self.project.id}/assign-users/",
                    {"user_ids": [self.employee.id]},
                    format="json",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        publish.assert_called_once()

    @override_settings(BACKGROUND_JOBS_ENABLED=False)
    def test_project_assignment_succeeds_without_contacting_celery(self):
        with patch("apps.projects.views.send_project_assignment_email.delay") as publish:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    f"/api/projects/{self.project.id}/assign-users/",
                    {"user_ids": [self.employee.id]},
                    format="json",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            ProjectMember.objects.filter(
                project=self.project,
                user=self.employee,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                company=self.company,
                action=AuditLog.ActionChoices.PROJECT_USERS_ASSIGNED,
                object_id=self.project.id,
            ).exists()
        )
        publish.assert_not_called()

    @override_settings(BACKGROUND_JOBS_ENABLED=False)
    def test_assigned_task_creation_succeeds_without_contacting_celery(self):
        with patch("apps.tasks.views.send_task_assignment_email.delay") as publish:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    "/api/tasks/",
                    self.task_data("No Redis Creation"),
                    format="json",
                )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="No Redis Creation")
        self.assertEqual(task.assigned_to, self.employee)
        self.assertTrue(
            AuditLog.objects.filter(
                company=self.company,
                action=AuditLog.ActionChoices.TASK_CREATED,
                object_id=task.id,
            ).exists()
        )
        publish.assert_not_called()

    @override_settings(BACKGROUND_JOBS_ENABLED=False)
    def test_task_assignment_update_succeeds_without_contacting_celery(self):
        task = Task.objects.create(
            company=self.company,
            project=self.project,
            title="No Redis Assignment",
            created_by=self.admin,
        )

        with patch("apps.tasks.views.send_task_assignment_email.delay") as publish:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.patch(
                    f"/api/tasks/{task.id}/",
                    {"assigned_to_id": self.employee.id},
                    format="json",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.assigned_to, self.employee)
        self.assertTrue(
            AuditLog.objects.filter(
                company=self.company,
                action=AuditLog.ActionChoices.TASK_UPDATED,
                object_id=task.id,
            ).exists()
        )
        publish.assert_not_called()
