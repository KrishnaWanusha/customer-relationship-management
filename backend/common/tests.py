from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from apps.organizations.models import Organization
from apps.companies.models import Company
from apps.contacts.models import Contact
from common.permissions import IsTenantUser
from common.serializers import TenantModelSerializer

User = get_user_model()


class CompanyTestSerializer(TenantModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "organization"]


class ContactTestSerializer(TenantModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "first_name", "last_name", "email", "company", "organization"]


class TenantIsolationArchitectureTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.org_a = Organization.objects.create(name="Tenant Alpha", slug="tenant-alpha")
        self.org_b = Organization.objects.create(name="Tenant Beta", slug="tenant-beta")

        self.user_a = User.objects.create_user(
            email="alice@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.ADMIN,
        )
        self.user_b = User.objects.create_user(
            email="bob@beta.com",
            password="password123",
            organization=self.org_b,
            role=User.Role.ADMIN,
        )

        self.company_a = Company.objects.create(name="Alpha Corp", organization=self.org_a)
        self.company_b = Company.objects.create(name="Beta Industries", organization=self.org_b)

        self.contact_a = Contact.objects.create(
            company=self.company_a,
            organization=self.org_a,
            first_name="Alice",
            last_name="Smith",
            email="alice@smith.com",
        )
        self.contact_b = Contact.objects.create(
            company=self.company_b,
            organization=self.org_b,
            first_name="Bob",
            last_name="Jones",
            email="bob@jones.com",
        )

    # Layer 1: Queryset & Manager Isolation
    def test_manager_for_user_scoping(self):
        companies_a = Company.objects.for_user(self.user_a)
        self.assertIn(self.company_a, companies_a)
        self.assertNotIn(self.company_b, companies_a)

        contacts_a = Contact.objects.for_user(self.user_a)
        self.assertIn(self.contact_a, contacts_a)
        self.assertNotIn(self.contact_b, contacts_a)

    def test_manager_for_tenant_scoping(self):
        companies_b = Company.objects.for_tenant(self.org_b)
        self.assertIn(self.company_b, companies_b)
        self.assertNotIn(self.company_a, companies_b)

        self.assertEqual(Company.objects.for_tenant(None).count(), 0)

    def test_unauthenticated_or_no_org_user_gets_empty_queryset(self):
        user_no_org = User.objects.create_user(email="no_org@example.com", password="password123")
        self.assertEqual(Company.objects.for_user(user_no_org).count(), 0)
        self.assertEqual(Company.objects.for_user(None).count(), 0)

    # Layer 2: Permissions & Object-Level Protection
    def test_is_tenant_user_permission(self):
        permission = IsTenantUser()
        request = self.factory.get("/")

        request.user = self.user_a
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, self.company_a))
        self.assertFalse(permission.has_object_permission(request, None, self.company_b))

    def test_inactive_organization_denies_permission(self):
        permission = IsTenantUser()
        request = self.factory.get("/")

        self.org_a.is_active = False
        self.org_a.save()

        request.user = self.user_a
        self.assertFalse(permission.has_permission(request, None))

    # Layer 3: Serializer Validation & Organization Override
    def test_serializer_ignores_frontend_supplied_organization_id(self):
        request = self.factory.post("/")
        request.user = self.user_a

        # Attacker tries to create a company under Org B
        serializer = CompanyTestSerializer(
            data={"name": "Hacked Corp", "organization": self.org_b.id},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        created_company = serializer.save()

        # Backend authoritatively assigns user_a's organization (Org A)
        self.assertEqual(created_company.organization, self.org_a)
        self.assertNotEqual(created_company.organization, self.org_b)

    def test_serializer_blocks_cross_tenant_foreign_key_injection(self):
        request = self.factory.post("/")
        request.user = self.user_a

        # Attacker from Org A tries to create a Contact attached to Org B's company
        serializer = ContactTestSerializer(
            data={
                "first_name": "Injected",
                "last_name": "Contact",
                "email": "injected@example.com",
                "company": self.company_b.id,
            },
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("company", serializer.errors)
        self.assertEqual(
            str(serializer.errors["company"][0]),
            "Referenced record does not belong to your organization.",
        )

    # Layer 4: Model-Level Integrity Validation
    def test_model_clean_rejects_cross_tenant_relationship(self):
        with self.assertRaises(ValidationError):
            contact = Contact(
                organization=self.org_a,
                company=self.company_b,
                first_name="Bad",
                last_name="Actor",
                email="bad@actor.com",
            )
            contact.full_clean()

    # Layer 5: Soft-Delete Isolation
    def test_soft_delete_does_not_leak_cross_tenant(self):
        self.company_a.soft_delete(user=self.user_a)

        # Org B queries should not reveal Org A's deleted company
        self.assertNotIn(self.company_a, Company.objects.for_user(self.user_b))
        self.assertNotIn(self.company_a, Company.all_objects.filter(organization=self.org_b))

    # Layer 6: django-multitenant Global Scoping & Middleware
    def test_global_query_filtering_with_current_tenant(self):
        from django_multitenant.utils import set_current_tenant, unset_current_tenant

        try:
            set_current_tenant(self.org_a)
            companies = list(Company.objects.all())
            self.assertIn(self.company_a, companies)
            self.assertNotIn(self.company_b, companies)

            contacts = list(Contact.objects.all())
            self.assertIn(self.contact_a, contacts)
            self.assertNotIn(self.contact_b, contacts)

            set_current_tenant(self.org_b)
            companies_b = list(Company.objects.all())
            self.assertIn(self.company_b, companies_b)
            self.assertNotIn(self.company_a, companies_b)
        finally:
            unset_current_tenant()

    def test_tenant_middleware_lifecycle(self):
        from common.middleware import TenantMiddleware
        from django_multitenant.utils import get_current_tenant, unset_current_tenant

        captured_tenants = []

        def dummy_get_response(request):
            captured_tenants.append(get_current_tenant())
            return None

        middleware = TenantMiddleware(dummy_get_response)
        request = self.factory.get("/")
        request.user = self.user_a

        try:
            middleware(request)
            self.assertEqual(len(captured_tenants), 1)
            self.assertEqual(captured_tenants[0], self.org_a)
            self.assertIsNone(get_current_tenant())
        finally:
            unset_current_tenant()

    def test_tenant_column_cannot_be_mutated(self):
        from django.db import NotSupportedError
        from django_multitenant.utils import set_current_tenant, unset_current_tenant

        try:
            set_current_tenant(self.org_a)
            company = Company.objects.get(id=self.company_a.id)
            company.organization = self.org_b
            with self.assertRaises(NotSupportedError):
                company.save()
        finally:
            unset_current_tenant()

