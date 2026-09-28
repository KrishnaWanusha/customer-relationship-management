from django.test import TestCase
from .models import Organization


class OrganizationModelTest(TestCase):
    def test_create_organization(self):
        org = Organization.objects.create(name="Alpha Org")
        self.assertEqual(org.name, "Alpha Org")
        self.assertEqual(org.slug, "alpha-org")
        self.assertTrue(org.is_active)
        self.assertEqual(str(org), "Alpha Org")

    def test_organization_slug_uniqueness(self):
        org1 = Organization.objects.create(name="Beta Group")
        org2 = Organization.objects.create(name="Beta Group")
        self.assertEqual(org1.slug, "beta-group")
        self.assertEqual(org2.slug, "beta-group-1")
