from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.organizations.models import Organization

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Alpha Org")

    def test_create_user_with_role_and_organization(self):
        user = User.objects.create_user(
            email="staff@crm.com",
            password="securepassword123",
            first_name="Krishna",
            last_name="Wanusha",
            role=User.Role.STAFF,
            organization=self.org,
        )
        self.assertEqual(user.email, "staff@crm.com")
        self.assertEqual(user.full_name, "Krishna Wanusha")
        self.assertEqual(user.organization, self.org)
        self.assertEqual(user.role, User.Role.STAFF)
        self.assertTrue(user.is_staff_role)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_manager)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("securepassword123"))

    def test_create_manager_user(self):
        manager = User.objects.create_user(
            email="manager@crm.com",
            password="securepassword123",
            role=User.Role.MANAGER,
            organization=self.org,
        )
        self.assertTrue(manager.is_manager)
        self.assertFalse(manager.is_admin)

    def test_create_admin_user(self):
        admin = User.objects.create_user(
            email="admin@crm.com",
            password="securepassword123",
            role=User.Role.ADMIN,
            organization=self.org,
        )
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_manager)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="super@crm.com",
            password="superpassword123",
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_admin)
        self.assertEqual(superuser.role, User.Role.ADMIN)

    def test_email_normalization(self):
        user = User.objects.create_user(
            email="USER@Example.COM",
            password="password123",
        )
        self.assertEqual(user.email, "USER@example.com")

    def test_email_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="")


class AuthAPITest(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Alpha Corp")
        self.user = User.objects.create_user(
            email="alex@alpha.com",
            password="securepassword123",
            first_name="Alex",
            last_name="Ward",
            role=User.Role.STAFF,
            organization=self.org,
        )

    def test_login_success(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "alex@alpha.com", "password": "securepassword123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], "alex@alpha.com")
        self.assertEqual(response.data["data"]["user"]["organization"]["name"], "Alpha Corp")

        cookie = response.cookies.get(settings.AUTH_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie["httponly"])

    def test_login_invalid_password(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "alex@alpha.com", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "alex@alpha.com", "password": "securepassword123"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])

    def test_token_refresh_via_cookie(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies[settings.AUTH_COOKIE_NAME] = str(refresh)

        response = self.client.post("/api/v1/auth/refresh/", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])

    def test_token_refresh_missing_token(self):
        response = self.client.post("/api/v1/auth/refresh/", format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])

    def test_token_refresh_invalid_token(self):
        self.client.cookies[settings.AUTH_COOKIE_NAME] = "invalid_token_string"
        response = self.client.post("/api/v1/auth/refresh/", format="json")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["success"])

    def test_logout_clears_cookie(self):
        self.client.cookies[settings.AUTH_COOKIE_NAME] = "dummy_token"
        response = self.client.post("/api/v1/auth/logout/", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        cookie = response.cookies.get(settings.AUTH_COOKIE_NAME)
        self.assertEqual(cookie.value, "")

    def test_current_user_me_authenticated(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], "alex@alpha.com")

    def test_current_user_me_unauthenticated(self):
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_email(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "nobody@nowhere.com", "password": "securepassword123"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid email or password.")

    def test_login_missing_credentials(self):
        response = self.client.post("/api/v1/auth/login/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("email", response.data["errors"])
        self.assertIn("password", response.data["errors"])

    def test_token_refresh_inactive_user_rejected(self):
        refresh = RefreshToken.for_user(self.user)
        self.user.is_active = False
        self.user.save()

        self.client.cookies[settings.AUTH_COOKIE_NAME] = str(refresh)
        response = self.client.post("/api/v1/auth/refresh/", format="json")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["success"])
        self.assertIn("User account is disabled", response.data["message"])

    def test_token_refresh_inactive_organization_rejected(self):
        refresh = RefreshToken.for_user(self.user)
        self.org.is_active = False
        self.org.save()

        self.client.cookies[settings.AUTH_COOKIE_NAME] = str(refresh)
        response = self.client.post("/api/v1/auth/refresh/", format="json")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["success"])
        self.assertIn("Organization account is disabled", response.data["message"])

    def test_protected_endpoints_unauthenticated(self):
        endpoints = [
            ("get", "/api/v1/auth/me/"),
            ("get", "/api/v1/companies/"),
            ("post", "/api/v1/companies/"),
            ("get", "/api/v1/contacts/"),
            ("post", "/api/v1/contacts/"),
        ]
        for method, endpoint in endpoints:
            client_method = getattr(self.client, method)
            response = client_method(endpoint)
            self.assertEqual(
                response.status_code,
                401,
                f"Endpoint {method.upper()} {endpoint} should require authentication.",
            )

    def test_protected_endpoints_malformed_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid.jwt.token")
        response = self.client.get("/api/v1/companies/")
        self.assertEqual(response.status_code, 401)

