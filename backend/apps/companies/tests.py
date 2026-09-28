import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from apps.activity_logs.models import ActivityLog
from apps.companies.models import Company
from apps.organizations.models import Organization

User = get_user_model()


class CompanyModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Alpha Org", slug="alpha-org")
        self.user = User.objects.create_user(
            email="admin@crm.com",
            password="password123",
            organization=self.org,
        )

    def test_create_company_with_uuid_and_relationships(self):
        company = Company.objects.create(
            organization=self.org,
            name="Beta Org",
            industry="Technology",
            country="Sri Lanka",
            website="https://beta.com",
            phone="+1234567890",
        )
        self.assertIsInstance(company.id, uuid.UUID)
        self.assertEqual(company.name, "Beta Org")
        self.assertEqual(company.country, "Sri Lanka")
        self.assertEqual(company.organization, self.org)
        self.assertIn(company, self.org.companies.all())
        self.assertFalse(company.is_deleted)
        self.assertIsNone(company.deleted_at)
        self.assertIsNone(company.deleted_by)

    def test_soft_delete_company(self):
        company = Company.objects.create(
            organization=self.org,
            name="Gamma Org",
            country="Japan",
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
            name="Delta Org",
        )
        company.soft_delete(user=self.user)
        self.assertEqual(Company.objects.filter(id=company.id).count(), 0)

        company.restore()
        self.assertFalse(company.is_deleted)
        self.assertIsNone(company.deleted_at)
        self.assertIsNone(company.deleted_by)
        self.assertEqual(Company.objects.filter(id=company.id).count(), 1)


class CompanyAPITest(APITestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name="Tenant Alpha", slug="tenant-alpha")
        self.org_b = Organization.objects.create(name="Tenant Beta", slug="tenant-beta")

        self.admin_user_a = User.objects.create_user(
            email="admin@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.ADMIN,
        )
        self.manager_user_a = User.objects.create_user(
            email="manager@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.MANAGER,
        )
        self.staff_user_a = User.objects.create_user(
            email="staff@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.STAFF,
        )

        self.admin_user_b = User.objects.create_user(
            email="admin@beta.com",
            password="password123",
            organization=self.org_b,
            role=User.Role.ADMIN,
        )

        self.company_a1 = Company.objects.create(
            organization=self.org_a,
            name="Alpha Corp",
            industry="Technology",
            country="Sri Lanka",
            phone="111-222-3333",
            website="https://alphacorp.com",
        )
        self.company_a2 = Company.objects.create(
            organization=self.org_a,
            name="Alpha Logistics",
            industry="Transportation",
            country="Singapore",
            phone="444-555-6666",
            website="https://alphalogistics.com",
        )
        self.company_b1 = Company.objects.create(
            organization=self.org_b,
            name="Beta Finance",
            industry="Finance",
            country="Japan",
            phone="777-888-9999",
            website="https://betafinance.com",
        )

    def test_unauthenticated_request_rejected(self):
        response = self.client.get("/api/v1/companies/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_list_companies_pagination_and_tenant_isolation(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.get("/api/v1/companies/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Data retrieved successfully.")

        results = response.data["data"]["results"]
        company_names = [c["name"] for c in results]
        self.assertIn("Alpha Corp", company_names)
        self.assertIn("Alpha Logistics", company_names)
        self.assertNotIn("Beta Finance", company_names)

        pagination = response.data["data"]["pagination"]
        self.assertEqual(pagination["count"], 2)
        self.assertEqual(pagination["current_page"], 1)

    def test_retrieve_company_success(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.get(f"/api/v1/companies/{self.company_a1.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["id"], str(self.company_a1.id))
        self.assertEqual(response.data["data"]["name"], "Alpha Corp")
        self.assertEqual(response.data["data"]["country"], "Sri Lanka")
        self.assertEqual(response.data["data"]["contacts_count"], 0)

    def test_cross_tenant_retrieve_returns_404(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.get(f"/api/v1/companies/{self.company_b1.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])

    def test_create_company_success_with_activity_log(self):
        self.client.force_authenticate(user=self.manager_user_a)
        payload = {
            "name": "Alpha Health",
            "industry": "Healthcare",
            "country": "Sri Lanka",
            "phone": "999-000-1111",
            "website": "https://alphahealth.com",
            "organization": self.org_b.id,  # Attempt cross-tenant injection
        }

        response = self.client.post("/api/v1/companies/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        created_id = response.data["data"]["id"]
        company = Company.objects.get(id=created_id)

        # Organization is authoritatively assigned from user
        self.assertEqual(company.organization, self.org_a)
        self.assertEqual(company.name, "Alpha Health")

        # Activity log was created
        log = ActivityLog.objects.filter(
            organization=self.org_a,
            action=ActivityLog.Action.CREATE,
            model_name="Company",
            object_id=str(company.id),
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.manager_user_a)
        self.assertEqual(log.details["name"], "Alpha Health")

    def test_create_company_validation_missing_name(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.post("/api/v1/companies/", {"name": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("name", response.data["errors"])

    def test_update_company_put(self):
        self.client.force_authenticate(user=self.manager_user_a)
        payload = {
            "name": "Alpha Corp International",
            "industry": "Enterprise Software",
            "country": "Sri Lanka",
            "phone": "111-222-3333",
            "website": "https://alphacorp.com",
        }
        response = self.client.put(f"/api/v1/companies/{self.company_a1.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["name"], "Alpha Corp International")

        self.company_a1.refresh_from_db()
        self.assertEqual(self.company_a1.name, "Alpha Corp International")

        log = ActivityLog.objects.filter(
            organization=self.org_a,
            action=ActivityLog.Action.UPDATE,
            model_name="Company",
            object_id=str(self.company_a1.id),
        ).first()
        self.assertIsNotNone(log)
        self.assertIn("name", log.details["changed_fields"])

    def test_partial_update_company_patch(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.patch(
            f"/api/v1/companies/{self.company_a1.id}/",
            {"industry": "AI & Cloud"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["industry"], "AI & Cloud")

        self.company_a1.refresh_from_db()
        self.assertEqual(self.company_a1.industry, "AI & Cloud")

    def test_cross_tenant_update_returns_404(self):
        self.client.force_authenticate(user=self.manager_user_a)
        response = self.client.patch(
            f"/api/v1/companies/{self.company_b1.id}/",
            {"name": "Hacked Beta"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_soft_delete_company(self):
        self.client.force_authenticate(user=self.admin_user_a)
        response = self.client.delete(f"/api/v1/companies/{self.company_a1.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Record is soft-deleted
        self.company_a1.refresh_from_db()
        self.assertTrue(self.company_a1.is_deleted)
        self.assertEqual(self.company_a1.deleted_by, self.admin_user_a)
        self.assertIsNotNone(self.company_a1.deleted_at)

        # Excluded from normal list
        list_response = self.client.get("/api/v1/companies/")
        names = [c["name"] for c in list_response.data["data"]["results"]]
        self.assertNotIn("Alpha Corp", names)

        # Activity log was generated
        log = ActivityLog.objects.filter(
            organization=self.org_a,
            action=ActivityLog.Action.DELETE,
            model_name="Company",
            object_id=str(self.company_a1.id),
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin_user_a)

    def test_manager_cannot_delete_company(self):
        self.client.force_authenticate(user=self.manager_user_a)
        response = self.client.delete(f"/api/v1/companies/{self.company_a1.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])

        self.company_a1.refresh_from_db()
        self.assertFalse(self.company_a1.is_deleted)

    def test_staff_cannot_delete_company(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.delete(f"/api/v1/companies/{self.company_a1.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])

        self.company_a1.refresh_from_db()
        self.assertFalse(self.company_a1.is_deleted)

    def test_search_companies(self):
        self.client.force_authenticate(user=self.staff_user_a)

        # Search by name
        res1 = self.client.get("/api/v1/companies/?search=Logistics")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        results1 = res1.data["data"]["results"]
        self.assertEqual(len(results1), 1)
        self.assertEqual(results1[0]["name"], "Alpha Logistics")

        # Search by country
        res2 = self.client.get("/api/v1/companies/?search=Sri Lanka")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        results2 = res2.data["data"]["results"]
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["name"], "Alpha Corp")

    def test_filter_companies(self):
        self.client.force_authenticate(user=self.staff_user_a)

        # Filter by industry
        res1 = self.client.get("/api/v1/companies/?industry=technology")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        results1 = res1.data["data"]["results"]
        self.assertEqual(len(results1), 1)
        self.assertEqual(results1[0]["name"], "Alpha Corp")

        # Filter by country
        res2 = self.client.get("/api/v1/companies/?country=Singapore")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        results2 = res2.data["data"]["results"]
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["name"], "Alpha Logistics")
