from django.test import TestCase
from .models import Organization


class OrganizationModelTest(TestCase):
    def test_create_organization(self):
        org = Organization.objects.create(name="Alpha Org")
        self.assertEqual(org.name, "Alpha Org")
        self.assertEqual(org.slug, "alpha-org")
        self.assertTrue(org.is_active)
        self.assertEqual(str(org), "Alpha Org")

    def test_organization_subscription_plan(self):
        # Default plan should be Basic
        org_default = Organization.objects.create(name="Default Plan Org")
        self.assertEqual(org_default.subscription_plan, Organization.SubscriptionPlan.BASIC)
        self.assertEqual(org_default.plan, "Basic")

        # Explicit Pro plan
        org_pro = Organization.objects.create(
            name="Pro Plan Org",
            subscription_plan=Organization.SubscriptionPlan.PRO,
        )
        self.assertEqual(org_pro.subscription_plan, Organization.SubscriptionPlan.PRO)
        self.assertEqual(org_pro.plan, "Pro")

        # Plan property setter
        org_default.plan = Organization.SubscriptionPlan.PRO
        org_default.save()
        org_default.refresh_from_db()
        self.assertEqual(org_default.subscription_plan, "Pro")

    def test_organization_created_at_timestamp(self):
        org = Organization.objects.create(name="Timestamped Org")
        self.assertIsNotNone(org.created_at)
        self.assertIsNotNone(org.updated_at)
