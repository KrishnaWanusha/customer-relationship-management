from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.organizations.models import Organization
from apps.organizations.models import Company

User = get_user_model()

class CompanyModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Alpha Org")
        self.user = User.objects.create_user(
            email="admin@crm.com",
            password="password123",
            organization=self.org,
        )

    def test_create_company(self):
        company = Company.objects.create(
            organization=self.org,
            name="Beta Org",
            industry="Technology",
            website="https://beta.com",
            phone="+1234567890",
        )
        self.assertEqual(company.name, "Beta Org")
        self.assertEqual(company.organization, self.org)
        self.assertFalse(company.is_deleted)
        self.assertIsNone(company.deleted_at)
        self.assertIsNone(company.deleted_by)

    def test_soft_delete_company(self):
        company = Company.objects.create(
            organization=self.org,
            name="Gamma Org",
        )
        company.soft_delete(user=self.user)

        self.assertTrue(company.is_deleted)
        self.assertIsNotNone(company.deleted_at)
        self.assertEqual(company.deleted_by, self.user)

        self.assertEqual(Company.objects.filter(id=company.id).count(), 0)
        self.assertEqual(Company.all_objects.filter(id=company.id).count(), 1)

    def test_restore_company(self):
        company = Company.objects.create(
            organization=self.org,
            name="Beta Org",
        )
        company.soft_delete(user=self.user)
        self.assertEqual(Company.objects.filter(id=company.id).count(), 0)

        company.restore()
        self.assertFalse(company.is_deleted)
        self.assertIsNone(company.deleted_at)
        self.assertIsNone(company.deleted_by)
        self.assertEqual(Company.objects.filter(id=company.id).count(), 1)
