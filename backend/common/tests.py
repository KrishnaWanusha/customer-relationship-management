from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import RequestFactory, TestCase
from common.storage import PrivateMediaStorage, generate_presigned_url, get_s3_client
from backend.apps.accounts.serializers import UserSerializer
from backend.apps.companies.models import Company
from backend.apps.contacts.models import Contact
from backend.apps.organizations.models import Organization
from common.permissions import (
    CanDeleteRecord,
    CanViewActivityLogs,
    IsAdminRole,
    IsManagerRole,
    IsStaffRole,
    IsTenantUser,
    RoleBasedAccessPermission,
)
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


class RoleBasedAccessControlTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name="RBAC Org", slug="rbac-org")

        self.admin_user = User.objects.create_user(
            email="admin@rbac.com",
            password="password123",
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.manager_user = User.objects.create_user(
            email="manager@rbac.com",
            password="password123",
            organization=self.org,
            role=User.Role.MANAGER,
        )
        self.staff_user = User.objects.create_user(
            email="staff@rbac.com",
            password="password123",
            organization=self.org,
            role=User.Role.STAFF,
        )
        self.company = Company.objects.create(name="RBAC Company", organization=self.org)

    def test_is_admin_role_permission(self):
        perm = IsAdminRole()
        req = self.factory.get("/")

        req.user = self.admin_user
        self.assertTrue(perm.has_permission(req, None))

        req.user = self.manager_user
        self.assertFalse(perm.has_permission(req, None))

        req.user = self.staff_user
        self.assertFalse(perm.has_permission(req, None))

    def test_is_manager_role_permission(self):
        perm = IsManagerRole()
        req = self.factory.get("/")

        req.user = self.manager_user
        self.assertTrue(perm.has_permission(req, None))

        req.user = self.admin_user
        self.assertFalse(perm.has_permission(req, None))

        req.user = self.staff_user
        self.assertFalse(perm.has_permission(req, None))

    def test_is_staff_role_permission(self):
        perm = IsStaffRole()
        req = self.factory.get("/")

        req.user = self.staff_user
        self.assertTrue(perm.has_permission(req, None))

        req.user = self.manager_user
        self.assertFalse(perm.has_permission(req, None))

        req.user = self.admin_user
        self.assertFalse(perm.has_permission(req, None))

    def test_crm_rbac_admin_full_access(self):
        perm = RoleBasedAccessPermission()

        for method, req_func in [
            ("GET", self.factory.get),
            ("POST", self.factory.post),
            ("PUT", self.factory.put),
            ("PATCH", self.factory.patch),
            ("DELETE", self.factory.delete),
        ]:
            req = req_func("/")
            req.user = self.admin_user
            self.assertTrue(perm.has_permission(req, None), f"Admin should have {method} permission")
            self.assertTrue(perm.has_object_permission(req, None, self.company), f"Admin should have {method} object permission")

    def test_crm_rbac_manager_cannot_delete(self):
        perm = RoleBasedAccessPermission()

        # Manager can read, create, update
        for method, req_func in [
            ("GET", self.factory.get),
            ("POST", self.factory.post),
            ("PUT", self.factory.put),
            ("PATCH", self.factory.patch),
        ]:
            req = req_func("/")
            req.user = self.manager_user
            self.assertTrue(perm.has_permission(req, None), f"Manager should have {method} permission")
            self.assertTrue(perm.has_object_permission(req, None, self.company), f"Manager should have {method} object permission")

        # Manager CANNOT delete
        del_req = self.factory.delete("/")
        del_req.user = self.manager_user
        self.assertFalse(perm.has_permission(del_req, None))
        self.assertFalse(perm.has_object_permission(del_req, None, self.company))

    def test_crm_rbac_staff_cannot_delete(self):
        perm = RoleBasedAccessPermission()

        # Staff can read, create, update
        for method, req_func in [
            ("GET", self.factory.get),
            ("POST", self.factory.post),
            ("PUT", self.factory.put),
            ("PATCH", self.factory.patch),
        ]:
            req = req_func("/")
            req.user = self.staff_user
            self.assertTrue(perm.has_permission(req, None), f"Staff should have {method} permission")
            self.assertTrue(perm.has_object_permission(req, None, self.company), f"Staff should have {method} object permission")

        # Staff CANNOT delete
        del_req = self.factory.delete("/")
        del_req.user = self.staff_user
        self.assertFalse(perm.has_permission(del_req, None))
        self.assertFalse(perm.has_object_permission(del_req, None, self.company))

    def test_can_delete_record_permission(self):
        perm = CanDeleteRecord()

        # Non-delete methods pass
        req = self.factory.get("/")
        req.user = self.staff_user
        self.assertTrue(perm.has_permission(req, None))

        # Delete method strictly checks admin
        del_req = self.factory.delete("/")
        del_req.user = self.admin_user
        self.assertTrue(perm.has_permission(del_req, None))
        self.assertTrue(perm.has_object_permission(del_req, None, self.company))

        del_req.user = self.manager_user
        self.assertFalse(perm.has_permission(del_req, None))
        self.assertFalse(perm.has_object_permission(del_req, None, self.company))

        del_req.user = self.staff_user
        self.assertFalse(perm.has_permission(del_req, None))
        self.assertFalse(perm.has_object_permission(del_req, None, self.company))

    def test_activity_log_permission(self):
        perm = CanViewActivityLogs()

        get_req = self.factory.get("/")
        post_req = self.factory.post("/")

        # Admin can view logs, cannot mutate
        get_req.user = self.admin_user
        post_req.user = self.admin_user
        self.assertTrue(perm.has_permission(get_req, None))
        self.assertFalse(perm.has_permission(post_req, None))

        # Manager can view logs, cannot mutate
        get_req.user = self.manager_user
        post_req.user = self.manager_user
        self.assertTrue(perm.has_permission(get_req, None))
        self.assertFalse(perm.has_permission(post_req, None))

        # Staff CANNOT view logs
        get_req.user = self.staff_user
        post_req.user = self.staff_user
        self.assertFalse(perm.has_permission(get_req, None))
        self.assertFalse(perm.has_permission(post_req, None))

    def test_user_serializer_exposes_role_capabilities_for_frontend_ux(self):
        admin_data = UserSerializer(self.admin_user).data
        self.assertTrue(admin_data["can_delete"])
        self.assertTrue(admin_data["can_view_activity_logs"])

        manager_data = UserSerializer(self.manager_user).data
        self.assertFalse(manager_data["can_delete"])
        self.assertTrue(manager_data["can_view_activity_logs"])

        staff_data = UserSerializer(self.staff_user).data
        self.assertFalse(staff_data["can_delete"])
        self.assertFalse(staff_data["can_view_activity_logs"])


class S3StorageConfigurationTest(TestCase):
    def test_private_media_storage_settings(self):
        with patch("common.storage.settings") as mock_settings:
            mock_settings.AWS_STORAGE_BUCKET_NAME = "secure-crm-bucket"
            mock_settings.AWS_QUERYSTRING_EXPIRE = 1800
            storage = PrivateMediaStorage()

            self.assertEqual(storage.default_acl, "private")
            self.assertFalse(storage.file_overwrite)
            self.assertFalse(storage.custom_domain)
            self.assertTrue(storage.querystring_auth)
            self.assertEqual(storage.querystring_expire, 1800)

    def test_missing_aws_configuration_behavior(self):
        # Missing bucket name when initializing PrivateMediaStorage
        with patch("common.storage.settings") as mock_settings:
            mock_settings.AWS_STORAGE_BUCKET_NAME = ""
            with self.assertRaises(ImproperlyConfigured) as ctx:
                PrivateMediaStorage()
            self.assertIn("AWS_STORAGE_BUCKET_NAME must be configured", str(ctx.exception))

        # Missing bucket name when generating presigned URL
        with patch("common.storage.settings") as mock_settings:
            mock_settings.AWS_STORAGE_BUCKET_NAME = ""
            with self.assertRaises(ImproperlyConfigured) as ctx:
                generate_presigned_url("organizations/1/companies/2/logos/img.png")
            self.assertIn("AWS_STORAGE_BUCKET_NAME must be configured", str(ctx.exception))

    @patch("common.storage.get_s3_client")
    def test_generate_presigned_url(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://secure-crm-bucket.s3.amazonaws.com/test.png?sig=abc"
        mock_get_client.return_value = mock_client

        with patch("common.storage.settings") as mock_settings:
            mock_settings.AWS_STORAGE_BUCKET_NAME = "secure-crm-bucket"
            mock_settings.AWS_QUERYSTRING_EXPIRE = 3600

            url = generate_presigned_url("logos/test.png", expiration=1800)
            mock_client.generate_presigned_url.assert_called_once_with(
                ClientMethod="get_object",
                Params={"Bucket": "secure-crm-bucket", "Key": "logos/test.png"},
                ExpiresIn=1800,
            )
            self.assertEqual(url, "https://secure-crm-bucket.s3.amazonaws.com/test.png?sig=abc")

    @patch("boto3.client")
    def test_get_s3_client_respects_settings(self, mock_boto3_client):
        with patch("common.storage.settings") as mock_settings:
            mock_settings.AWS_S3_REGION_NAME = "eu-west-1"
            mock_settings.AWS_ACCESS_KEY_ID = "test-access-key"
            mock_settings.AWS_SECRET_ACCESS_KEY = "test-secret-key"
            mock_settings.AWS_S3_ENDPOINT_URL = "https://custom-s3.endpoint.com"

            get_s3_client()
            mock_boto3_client.assert_called_once_with(
                "s3",
                region_name="eu-west-1",
                aws_access_key_id="test-access-key",
                aws_secret_access_key="test-secret-key",
                endpoint_url="https://custom-s3.endpoint.com",
            )



