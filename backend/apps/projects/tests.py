from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.companies.models import Company
from apps.projects.models import Project, ProjectMember


class ProjectDateValidationTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Project Company",
            email="projects@example.com",
        )
        self.admin = User.objects.create_user(
            username="project-admin",
            email="project-admin@example.com",
            password="StrongPass123!",
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )
        self.client.force_authenticate(self.admin)

    def test_valid_dates_are_accepted(self):
        response = self.client.post(
            "/api/projects/",
            {
                "name": "Valid Dates",
                "start_date": "2026-09-01",
                "end_date": "2026-09-30",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_invalid_dates_is_rejected(self):
        response = self.client.post(
            "/api/projects/",
            {
                "name": "Invalid Dates",
                "start_date": "2026-09-30",
                "end_date": "2026-09-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_start_date_creating_invalid_range_is_rejected(self):
        project = Project.objects.create(
            company=self.company,
            name="Start Date Test",
            start_date="2026-09-01",
            end_date="2026-09-30",
            created_by=self.admin,
        )

        response = self.client.patch(
            f"/api/projects/{project.id}/",
            {"start_date": "2026-10-01"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_end_date_creating_invalid_range_is_rejected(self):
        project = Project.objects.create(
            company=self.company,
            name="End Date Test",
            start_date="2026-09-01",
            end_date="2026-09-30",
            created_by=self.admin,
        )

        response = self.client.patch(
            f"/api/projects/{project.id}/",
            {"end_date": "2026-08-31"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProjectFilteringAndPaginationTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Project Filter Company",
            email="project-filter@example.com",
        )
        self.other_company = Company.objects.create(
            name="Other Project Company",
            email="other-project-filter@example.com",
        )
        self.admin = User.objects.create_user(
            username="project-filter-admin",
            email="project-filter-admin@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )
        other_admin = User.objects.create_user(
            username="other-project-admin",
            email="other-project-admin@example.com",
            password="G7!vQ2#pL9@x",
            company=self.other_company,
            role=User.RoleChoices.ADMIN,
        )
        Project.objects.create(
            company=self.company,
            name="Active One",
            status=Project.StatusChoices.ACTIVE,
            created_by=self.admin,
        )
        Project.objects.create(
            company=self.company,
            name="Active Two",
            status=Project.StatusChoices.ACTIVE,
            created_by=self.admin,
        )
        Project.objects.create(
            company=self.company,
            name="Planning",
            status=Project.StatusChoices.PLANNING,
            created_by=self.admin,
        )
        self.other_tenant_project = Project.objects.create(
            company=self.other_company,
            name="Other Tenant Active",
            status=Project.StatusChoices.ACTIVE,
            created_by=other_admin,
        )
        self.client.force_authenticate(self.admin)

    def test_project_status_filter_is_tenant_scoped_and_paginated(self):
        response = self.client.get("/api/projects/?status=ACTIVE&page_size=1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertIsNotNone(response.data["next"])

    def test_invalid_project_status_returns_controlled_error(self):
        response = self.client.get("/api/projects/?status=INVALID")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cross_company_project_detail_is_not_exposed(self):
        response = self.client.get(f"/api/projects/{self.other_tenant_project.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_employee_cannot_create_project(self):
        employee = User.objects.create_user(
            username="project-filter-employee",
            email="project-filter-employee@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.client.force_authenticate(employee)

        response = self.client.post(
            "/api/projects/",
            {"name": "Forbidden Project"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ManagerProjectMembershipTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Manager Membership Company",
            email="manager-membership@example.com",
        )
        self.other_company = Company.objects.create(
            name="Other Membership Company",
            email="other-membership@example.com",
        )
        self.manager = User.objects.create_user(
            username="membership-manager",
            email="membership-manager@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company,
            role=User.RoleChoices.MANAGER,
        )
        self.employee = User.objects.create_user(
            username="membership-employee",
            email="membership-employee@example.com",
            password="G7!vQ2#pL9@x",
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.other_employee = User.objects.create_user(
            username="other-membership-employee",
            email="other-membership-employee@example.com",
            password="G7!vQ2#pL9@x",
            company=self.other_company,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.project = Project.objects.create(
            company=self.company,
            name="Manager Project",
            created_by=self.manager,
        )
        self.client.force_authenticate(self.manager)

    def test_manager_discovers_and_assigns_same_tenant_user(self):
        discovery = self.client.get("/api/users/?page_size=100")
        discovered_ids = {user["id"] for user in discovery.data["data"]}

        response = self.client.post(
            f"/api/projects/{self.project.id}/assign-users/",
            {"user_ids": [self.employee.id]},
            format="json",
        )

        self.assertEqual(discovery.status_code, status.HTTP_200_OK)
        self.assertIn(self.employee.id, discovered_ids)
        self.assertNotIn(self.other_employee.id, discovered_ids)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            ProjectMember.objects.filter(
                project=self.project,
                user=self.employee,
                company=self.company,
            ).exists()
        )

    def test_manager_cannot_assign_cross_tenant_user(self):
        response = self.client.post(
            f"/api/projects/{self.project.id}/assign-users/",
            {"user_ids": [self.other_employee.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ProjectMember.objects.filter(project=self.project).exists())

    def test_manager_can_clear_all_project_members(self):
        ProjectMember.objects.create(
            company=self.company,
            project=self.project,
            user=self.employee,
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/assign-users/",
            {"user_ids": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ProjectMember.objects.filter(project=self.project).exists())
