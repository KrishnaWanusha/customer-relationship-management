from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.organizations.models import Organization
from backend.apps.companies.models import Company
from backend.apps.contacts.models import Contact
from backend.apps.activity_logs.models import ActivityLog

User = get_user_model()


class BackendSecurityAndTenantIsolationTest(APITestCase):

    def setUp(self):
        # Setup 3 isolated organizations
        self.org_a = Organization.objects.create(name="Organization Alpha", slug="org-alpha")
        self.org_b = Organization.objects.create(name="Organization Beta", slug="org-beta")
        self.org_c = Organization.objects.create(name="Organization Gamma", slug="org-gamma")

        # Users for Org A
        self.admin_a = User.objects.create_user(
            email="admin_a@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.ADMIN,
        )
        self.manager_a = User.objects.create_user(
            email="manager_a@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.MANAGER,
        )
        self.staff_a = User.objects.create_user(
            email="staff_a@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.STAFF,
        )

        # Users for Org B
        self.admin_b = User.objects.create_user(
            email="admin_b@beta.com",
            password="password123",
            organization=self.org_b,
            role=User.Role.ADMIN,
        )
        self.staff_b = User.objects.create_user(
            email="staff_b@beta.com",
            password="password123",
            organization=self.org_b,
            role=User.Role.STAFF,
        )

        # Domain records for Org A
        self.company_a1 = Company.objects.create(
            name="Alpha Corp",
            organization=self.org_a,
            industry="Software",
            country="US",
        )
        self.company_a2 = Company.objects.create(
            name="Alpha Labs",
            organization=self.org_a,
            industry="Biotech",
            country="UK",
        )
        self.contact_a1 = Contact.objects.create(
            company=self.company_a1,
            organization=self.org_a,
            full_name="Alice Alpha",
            email="alice@alpha.com",
            role="Director",
        )

        # Domain records for Org B
        self.company_b1 = Company.objects.create(
            name="Beta Corp",
            organization=self.org_b,
            industry="Automotive",
            country="DE",
        )
        self.contact_b1 = Contact.objects.create(
            company=self.company_b1,
            organization=self.org_b,
            full_name="Bob Beta",
            email="bob@beta.com",
            role="Manager",
        )

        # Domain records for Org C
        self.company_c1 = Company.objects.create(
            name="Gamma Corp",
            organization=self.org_c,
            industry="Energy",
            country="JP",
        )

    # Multi-Tenant List Isolation
    def test_list_isolation_between_organizations(self):
        # User in Org A only sees Org A companies
        self.client.force_authenticate(user=self.staff_a)
        response_comp = self.client.get("/api/v1/companies/")
        self.assertEqual(response_comp.status_code, status.HTTP_200_OK)
        company_ids = [c["id"] for c in response_comp.data["data"]["results"]]
        self.assertIn(str(self.company_a1.id), company_ids)
        self.assertIn(str(self.company_a2.id), company_ids)
        self.assertNotIn(str(self.company_b1.id), company_ids)
        self.assertNotIn(str(self.company_c1.id), company_ids)

        # User in Org A only sees Org A contacts
        response_cont = self.client.get("/api/v1/contacts/")
        self.assertEqual(response_cont.status_code, status.HTTP_200_OK)
        contact_ids = [c["id"] for c in response_cont.data["data"]["results"]]
        self.assertIn(str(self.contact_a1.id), contact_ids)
        self.assertNotIn(str(self.contact_b1.id), contact_ids)

        # User in Org B only sees Org B records
        self.client.force_authenticate(user=self.staff_b)
        response_b_comp = self.client.get("/api/v1/companies/")
        b_company_ids = [c["id"] for c in response_b_comp.data["data"]["results"]]
        self.assertEqual(b_company_ids, [str(self.company_b1.id)])

    # Retrieve Isolation & IDOR Protection
    def test_retrieve_idor_protection(self):
        # Org A user attempts to directly access Org B's company
        self.client.force_authenticate(user=self.admin_a)
        res_comp = self.client.get(f"/api/v1/companies/{self.company_b1.id}/")
        self.assertEqual(res_comp.status_code, status.HTTP_404_NOT_FOUND)

        # Org A user attempts to directly access Org B's contact
        res_cont = self.client.get(f"/api/v1/contacts/{self.contact_b1.id}/")
        self.assertEqual(res_cont.status_code, status.HTTP_404_NOT_FOUND)

    # Update Isolation & IDOR Protection
    def test_update_idor_protection(self):
        self.client.force_authenticate(user=self.admin_a)

        # Attempt PATCH on Org B company
        res_comp = self.client.patch(
            f"/api/v1/companies/{self.company_b1.id}/",
            {"name": "Hacked Name"},
            format="json",
        )
        self.assertEqual(res_comp.status_code, status.HTTP_404_NOT_FOUND)
        self.company_b1.refresh_from_db()
        self.assertEqual(self.company_b1.name, "Beta Corp")

        # Attempt PUT on Org B contact
        res_cont = self.client.put(
            f"/api/v1/contacts/{self.contact_b1.id}/",
            {
                "company": str(self.company_b1.id),
                "full_name": "Hacked Contact",
                "email": "hacked@beta.com",
            },
            format="json",
        )
        self.assertEqual(res_cont.status_code, status.HTTP_404_NOT_FOUND)
        self.contact_b1.refresh_from_db()
        self.assertEqual(self.contact_b1.full_name, "Bob Beta")

    # Delete Isolation & IDOR Protection
    def test_delete_idor_protection(self):
        self.client.force_authenticate(user=self.admin_a)

        # Admin A attempts to DELETE Org B company
        res_comp = self.client.delete(f"/api/v1/companies/{self.company_b1.id}/")
        self.assertEqual(res_comp.status_code, status.HTTP_404_NOT_FOUND)
        self.company_b1.refresh_from_db()
        self.assertFalse(self.company_b1.is_deleted)

        # Admin A attempts to DELETE Org B contact
        res_cont = self.client.delete(f"/api/v1/contacts/{self.contact_b1.id}/")
        self.assertEqual(res_cont.status_code, status.HTTP_404_NOT_FOUND)
        self.contact_b1.refresh_from_db()
        self.assertFalse(self.contact_b1.is_deleted)

    # Organization ID Manipulation in Request Payloads
    def test_organization_id_manipulation_is_ignored(self):
        self.client.force_authenticate(user=self.staff_a)

        # Attempt to create company claiming Org B ownership
        res_comp = self.client.post(
            "/api/v1/companies/",
            {
                "name": "Spoofed Company",
                "organization": str(self.org_b.id),
                "industry": "Consulting",
            },
            format="json",
        )
        self.assertEqual(res_comp.status_code, status.HTTP_201_CREATED)
        new_company_id = res_comp.data["data"]["id"]
        new_company = Company.objects.get(id=new_company_id)
        # Authoritative organization is ALWAYS the user's organization
        self.assertEqual(new_company.organization, self.org_a)
        self.assertNotEqual(new_company.organization, self.org_b)

        # Attempt to create contact claiming Org B ownership
        res_cont = self.client.post(
            "/api/v1/contacts/",
            {
                "company": str(self.company_a1.id),
                "full_name": "Spoofed Contact",
                "email": "spoof@alpha.com",
                "organization": str(self.org_b.id),
            },
            format="json",
        )
        self.assertEqual(res_cont.status_code, status.HTTP_201_CREATED)
        new_contact_id = res_cont.data["data"]["id"]
        new_contact = Contact.objects.get(id=new_contact_id)
        self.assertEqual(new_contact.organization, self.org_a)

    # Cross-Tenant Foreign Key Assignment Prevention
    def test_cross_tenant_foreign_key_assignment_rejected(self):
        self.client.force_authenticate(user=self.staff_a)

        # Attempt to attach a contact in Org A to a company in Org B
        response = self.client.post(
            "/api/v1/contacts/",
            {
                "company": str(self.company_b1.id),
                "full_name": "Trojan Contact",
                "email": "trojan@alpha.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company", response.data["errors"])

    # Role-Based Access Control (RBAC) Permitted Writes & Delete Enforcement
    def test_rbac_admin_full_access(self):
        self.client.force_authenticate(user=self.admin_a)

        # Create
        res_c = self.client.post(
            "/api/v1/companies/",
            {"name": "Admin Company", "industry": "Legal"},
            format="json",
        )
        self.assertEqual(res_c.status_code, status.HTTP_201_CREATED)
        comp_id = res_c.data["data"]["id"]

        # Edit
        res_u = self.client.patch(
            f"/api/v1/companies/{comp_id}/",
            {"name": "Admin Company Updated"},
            format="json",
        )
        self.assertEqual(res_u.status_code, status.HTTP_200_OK)

        # Delete
        res_d = self.client.delete(f"/api/v1/companies/{comp_id}/")
        self.assertEqual(res_d.status_code, status.HTTP_200_OK)

    def test_rbac_manager_permitted_writes_and_delete_restriction(self):
        self.client.force_authenticate(user=self.manager_a)

        # Permitted Create
        res_c = self.client.post(
            "/api/v1/companies/",
            {"name": "Manager Company", "industry": "Sales"},
            format="json",
        )
        self.assertEqual(res_c.status_code, status.HTTP_201_CREATED)
        comp_id = res_c.data["data"]["id"]

        # Permitted Edit
        res_u = self.client.patch(
            f"/api/v1/companies/{comp_id}/",
            {"name": "Manager Company Updated"},
            format="json",
        )
        self.assertEqual(res_u.status_code, status.HTTP_200_OK)

        # Prohibited Delete -> 403 Forbidden
        res_d = self.client.delete(f"/api/v1/companies/{comp_id}/")
        self.assertEqual(res_d.status_code, status.HTTP_403_FORBIDDEN)

        # Prohibited Contact Delete -> 403 Forbidden
        res_cd = self.client.delete(f"/api/v1/contacts/{self.contact_a1.id}/")
        self.assertEqual(res_cd.status_code, status.HTTP_403_FORBIDDEN)

    def test_rbac_staff_permitted_writes_and_delete_restriction(self):
        self.client.force_authenticate(user=self.staff_a)

        # Permitted Create
        res_c = self.client.post(
            "/api/v1/companies/",
            {"name": "Staff Company", "industry": "Support"},
            format="json",
        )
        self.assertEqual(res_c.status_code, status.HTTP_201_CREATED)
        comp_id = res_c.data["data"]["id"]

        # Permitted Edit
        res_u = self.client.patch(
            f"/api/v1/companies/{comp_id}/",
            {"name": "Staff Company Updated"},
            format="json",
        )
        self.assertEqual(res_u.status_code, status.HTTP_200_OK)

        # Prohibited Delete -> 403 Forbidden
        res_d = self.client.delete(f"/api/v1/companies/{comp_id}/")
        self.assertEqual(res_d.status_code, status.HTTP_403_FORBIDDEN)

    # Soft Deletion Safety & Normal Query Exclusion
    def test_soft_deleted_records_excluded_from_normal_queries(self):
        self.client.force_authenticate(user=self.admin_a)

        # Soft delete company
        self.client.delete(f"/api/v1/companies/{self.company_a2.id}/")
        self.company_a2.refresh_from_db()
        self.assertTrue(self.company_a2.is_deleted)
        self.assertIsNotNone(self.company_a2.deleted_at)
        self.assertEqual(self.company_a2.deleted_by, self.admin_a)

        # Verify not returned in list
        res_list = self.client.get("/api/v1/companies/")
        ids = [c["id"] for c in res_list.data["data"]["results"]]
        self.assertNotIn(str(self.company_a2.id), ids)

        # Verify not accessible via retrieve
        res_ret = self.client.get(f"/api/v1/companies/{self.company_a2.id}/")
        self.assertEqual(res_ret.status_code, status.HTTP_404_NOT_FOUND)

        # Verify cannot be used to create new contact
        res_new_cont = self.client.post(
            "/api/v1/contacts/",
            {
                "company": str(self.company_a2.id),
                "full_name": "Ghost Contact",
                "email": "ghost@alpha.com",
            },
            format="json",
        )
        self.assertEqual(res_new_cont.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company", res_new_cont.data["errors"])

    # Activity Log Isolation & Auditing
    def test_activity_logging_records_every_operation(self):
        self.client.force_authenticate(user=self.admin_a)
        initial_log_count = ActivityLog.objects.filter(organization=self.org_a).count()

        # CREATE Company
        res_c = self.client.post(
            "/api/v1/companies/",
            {"name": "Audited Corp", "industry": "Audit"},
            format="json",
        )
        comp_id = res_c.data["data"]["id"]

        create_log = ActivityLog.objects.filter(
            organization=self.org_a,
            object_id=comp_id,
            action=ActivityLog.Action.CREATE,
        ).first()
        self.assertIsNotNone(create_log)
        self.assertEqual(create_log.user, self.admin_a)

        # UPDATE Company
        self.client.patch(
            f"/api/v1/companies/{comp_id}/",
            {"name": "Audited Corp Renamed"},
            format="json",
        )
        update_log = ActivityLog.objects.filter(
            organization=self.org_a,
            object_id=comp_id,
            action=ActivityLog.Action.UPDATE,
        ).first()
        self.assertIsNotNone(update_log)
        self.assertEqual(update_log.user, self.admin_a)

        # DELETE Company
        self.client.delete(f"/api/v1/companies/{comp_id}/")
        delete_log = ActivityLog.objects.filter(
            organization=self.org_a,
            object_id=comp_id,
            action=ActivityLog.Action.DELETE,
        ).first()
        self.assertIsNotNone(delete_log)
        self.assertEqual(delete_log.user, self.admin_a)

        # Verify Org B has zero logs from Org A operations
        b_logs = ActivityLog.objects.filter(organization=self.org_b, object_id=comp_id)
        self.assertEqual(b_logs.count(), 0)
