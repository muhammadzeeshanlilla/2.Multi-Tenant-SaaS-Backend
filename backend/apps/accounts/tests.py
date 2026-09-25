from unittest.mock import patch

from django.core.cache import cache
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.companies.models import Company


STRONG_PASSWORD = "G7!vQ2#pL9@x"


class CompanyRegistrationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def registration_data(self, suffix="one", company_name="Acme Ltd"):
        return {
            "company_name": company_name,
            "company_email": f"company-{suffix}@example.com",
            "username": f"admin-{suffix}",
            "email": f"admin-{suffix}@example.com",
            "password": STRONG_PASSWORD,
            "confirm_password": STRONG_PASSWORD,
        }

    def test_successful_registration_is_atomic_and_password_is_hashed(self):
        response = self.client.post(
            "/api/auth/company-register/",
            self.registration_data(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        company = Company.objects.get(email="company-one@example.com")
        admin = User.objects.get(email="admin-one@example.com")
        self.assertEqual(admin.company, company)
        self.assertTrue(admin.check_password(STRONG_PASSWORD))
        self.assertNotEqual(admin.password, STRONG_PASSWORD)

    def test_admin_creation_failure_rolls_back_company(self):
        with patch(
            "apps.accounts.serializers.User.objects.create_user",
            side_effect=IntegrityError("simulated user creation failure"),
        ):
            response = self.client.post(
                "/api/auth/company-register/",
                self.registration_data(),
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Company.objects.filter(email="company-one@example.com").exists())
        self.assertFalse(User.objects.filter(email="admin-one@example.com").exists())

    def test_similar_company_names_receive_unique_deterministic_slugs(self):
        first = self.client.post(
            "/api/auth/company-register/",
            self.registration_data("one", "Acme Ltd"),
            format="json",
        )
        second = self.client.post(
            "/api/auth/company-register/",
            self.registration_data("two", "Acme Ltd!"),
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Company.objects.get(email="company-one@example.com").slug, "acme-ltd")
        self.assertEqual(Company.objects.get(email="company-two@example.com").slug, "acme-ltd-2")

    def test_weak_initial_admin_password_is_rejected(self):
        data = self.registration_data()
        data["password"] = data["confirm_password"] = "password"

        response = self.client.post("/api/auth/company-register/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Company.objects.exists())
        self.assertFalse(User.objects.exists())


class UserPasswordValidationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.company = Company.objects.create(
            name="Password Company",
            email="password-company@example.com",
        )
        self.admin = User.objects.create_user(
            username="password-admin",
            email="password-admin@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )
        self.client.force_authenticate(self.admin)

    def user_data(self, password):
        return {
            "username": "new-employee",
            "email": "new-employee@example.com",
            "password": password,
            "confirm_password": password,
            "role": User.RoleChoices.EMPLOYEE,
            "is_active": True,
        }

    def test_admin_created_user_rejects_weak_password(self):
        response = self.client.post(
            "/api/users/",
            self.user_data("password"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new-employee").exists())

    def test_admin_created_user_accepts_and_hashes_valid_password(self):
        response = self.client.post(
            "/api/users/",
            self.user_data(STRONG_PASSWORD),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new-employee")
        self.assertTrue(user.check_password(STRONG_PASSWORD))
        self.assertNotEqual(user.password, STRONG_PASSWORD)

    def test_password_update_rejects_weak_password(self):
        user = User.objects.create_user(
            username="existing-employee",
            email="existing-employee@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
        )

        response = self.client.patch(
            f"/api/users/{user.id}/",
            {"password": "password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertTrue(user.check_password(STRONG_PASSWORD))


class UserPaginationTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Pagination Company",
            email="pagination-company@example.com",
        )
        self.admin = User.objects.create_user(
            username="pagination-admin",
            email="pagination-admin@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )
        for number in range(3):
            User.objects.create_user(
                username=f"pagination-user-{number}",
                email=f"pagination-user-{number}@example.com",
                password=STRONG_PASSWORD,
                company=self.company,
                role=User.RoleChoices.EMPLOYEE,
            )
        self.client.force_authenticate(self.admin)

    def test_user_list_is_paginated_without_changing_data_key(self):
        response = self.client.get("/api/users/?page_size=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)
        self.assertEqual(len(response.data["data"]), 2)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_manager_can_access_paginated_user_discovery(self):
        manager = User.objects.create_user(
            username="pagination-manager",
            email="pagination-manager@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.MANAGER,
        )
        self.client.force_authenticate(manager)

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)


class ManagerUserDiscoveryTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Manager Discovery Company",
            email="manager-discovery@example.com",
        )
        self.other_company = Company.objects.create(
            name="Other Discovery Company",
            email="other-discovery@example.com",
        )
        self.admin = User.objects.create_user(
            username="discovery-admin",
            email="discovery-admin@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="discovery-manager",
            email="discovery-manager@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.MANAGER,
        )
        self.employee = User.objects.create_user(
            username="discovery-employee",
            email="discovery-employee@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
        )
        self.deleted_employee = User.objects.create_user(
            username="deleted-discovery-employee",
            email="deleted-discovery-employee@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.EMPLOYEE,
            is_deleted=True,
            is_active=False,
        )
        self.other_employee = User.objects.create_user(
            username="other-discovery-employee",
            email="other-discovery-employee@example.com",
            password=STRONG_PASSWORD,
            company=self.other_company,
            role=User.RoleChoices.EMPLOYEE,
        )

    def test_manager_lists_only_non_deleted_own_tenant_users(self):
        self.client.force_authenticate(self.manager)

        response = self.client.get("/api/users/?page_size=100")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {user["id"] for user in response.data["data"]}
        self.assertEqual(returned_ids, {self.admin.id, self.manager.id, self.employee.id})
        self.assertNotIn(self.deleted_employee.id, returned_ids)
        self.assertNotIn(self.other_employee.id, returned_ids)
        self.assertNotIn("password", response.data["data"][0])

    def test_manager_cannot_retrieve_user_details(self):
        self.client.force_authenticate(self.manager)

        own_response = self.client.get(f"/api/users/{self.employee.id}/")
        other_response = self.client.get(f"/api/users/{self.other_employee.id}/")

        self.assertEqual(own_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(other_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_cannot_create_users(self):
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            "/api/users/",
            {
                "username": "forbidden-user",
                "email": "forbidden-user@example.com",
                "password": STRONG_PASSWORD,
                "confirm_password": STRONG_PASSWORD,
                "role": User.RoleChoices.EMPLOYEE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(username="forbidden-user").exists())

    def test_manager_cannot_update_role_or_active_status(self):
        self.client.force_authenticate(self.manager)

        response = self.client.patch(
            f"/api/users/{self.employee.id}/",
            {"role": User.RoleChoices.MANAGER, "is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.role, User.RoleChoices.EMPLOYEE)
        self.assertTrue(self.employee.is_active)

    def test_manager_cannot_delete_or_restore_users(self):
        self.client.force_authenticate(self.manager)

        delete_response = self.client.delete(f"/api/users/{self.employee.id}/")
        restore_response = self.client.post(
            f"/api/users/{self.deleted_employee.id}/restore/",
            {},
            format="json",
        )

        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(restore_response.status_code, status.HTTP_403_FORBIDDEN)
        self.employee.refresh_from_db()
        self.deleted_employee.refresh_from_db()
        self.assertFalse(self.employee.is_deleted)
        self.assertTrue(self.deleted_employee.is_deleted)

    def test_employee_cannot_discover_users(self):
        self.client.force_authenticate(self.employee)

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_management_access_is_unchanged(self):
        self.client.force_authenticate(self.admin)

        list_response = self.client.get("/api/users/")
        detail_response = self.client.get(f"/api/users/{self.employee.id}/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)


class LoginAndLogoutTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.company = Company.objects.create(
            name="Authentication Company",
            email="authentication-company@example.com",
        )
        self.user = User.objects.create_user(
            username="authentication-admin",
            email="authentication-admin@example.com",
            password=STRONG_PASSWORD,
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )

    def login(self, email=None, password=STRONG_PASSWORD):
        return self.client.post(
            "/api/auth/login/",
            {"email": email or self.user.email, "password": password},
            format="json",
        )

    def authenticated_logout(self, access, refresh):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            format="json",
        )

    def test_valid_login_creates_tenant_scoped_audit_log(self):
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = AuditLog.objects.get(action=AuditLog.ActionChoices.USER_LOGIN)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.company, self.company)
        self.assertEqual(log.object_id, self.user.id)
        self.assertIsNotNone(log.created_at)

    def test_wrong_password_and_unknown_email_have_equivalent_errors(self):
        wrong_password = self.login(password="WrongPassword123!")
        unknown_email = self.login(email="unknown@example.com")

        self.assertEqual(wrong_password.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(unknown_email.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wrong_password.data, unknown_email.data)

    def test_successful_logout_blacklists_refresh_and_creates_audit_log(self):
        login = self.login().data["data"]["tokens"]

        logout = self.authenticated_logout(login["access"], login["refresh"])
        refresh_attempt = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": login["refresh"]},
            format="json",
        )

        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)
        log = AuditLog.objects.get(action=AuditLog.ActionChoices.USER_LOGOUT)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.company, self.company)

    def test_invalid_logout_token_returns_controlled_error(self):
        login = self.login().data["data"]["tokens"]

        response = self.authenticated_logout(login["access"], "not-a-refresh-token")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AuditLog.objects.filter(action=AuditLog.ActionChoices.USER_LOGOUT).exists())

    def test_logout_does_not_revoke_another_refresh_token(self):
        first = self.login().data["data"]["tokens"]
        second = self.login().data["data"]["tokens"]

        logout = self.authenticated_logout(first["access"], first["refresh"])
        second_refresh = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": second["refresh"]},
            format="json",
        )

        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        self.assertEqual(second_refresh.status_code, status.HTTP_200_OK)


class InactiveCompanyAuthenticationTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Active Company",
            email="active-company@example.com",
        )
        self.user = User.objects.create_user(
            username="company-admin",
            email="admin@example.com",
            password="StrongPass123!",
            company=self.company,
            role=User.RoleChoices.ADMIN,
        )

    def login(self):
        return self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "StrongPass123!"},
            format="json",
        )

    def test_active_company_user_can_login(self):
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"]["tokens"])

    def test_inactive_company_user_cannot_login(self):
        self.company.is_active = False
        self.company.save(update_fields=["is_active"])

        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("tokens", response.data)

    def test_existing_jwt_cannot_access_api_after_company_deactivation(self):
        login_response = self.login()
        access_token = login_response.data["data"]["tokens"]["access"]

        self.company.is_active = False
        self.company.save(update_fields=["is_active"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "User account is unavailable.")
