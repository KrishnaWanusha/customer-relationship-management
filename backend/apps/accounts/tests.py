from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Organization

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Stark Industries")

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
