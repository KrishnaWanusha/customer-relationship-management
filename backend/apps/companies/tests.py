import io
import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from PIL import Image
from backend.apps.activity_logs.models import ActivityLog
from backend.apps.companies.models import Company, company_logo_upload_path
from backend.apps.companies.validators import validate_company_logo
from backend.apps.organizations.models import Organization

User = get_user_model()


def create_test_image(img_format="PNG", size=(50, 50), color="blue"):
    file_obj = io.BytesIO()
    image = Image.new("RGB", size, color=color)
    image.save(file_obj, format=img_format)
    file_obj.seek(0)
    return file_obj.read()


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


class CompanyLogoUploadAndStorageTest(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Stark Industries")
        self.admin = User.objects.create_user(
            email="tony@stark.com",
            password="password123",
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.admin)

    def test_validate_company_logo_success(self):
        png_data = create_test_image(img_format="PNG")
        uploaded_png = SimpleUploadedFile("logo.png", png_data, content_type="image/png")
        # Should not raise
        validate_company_logo(uploaded_png)

        jpeg_data = create_test_image(img_format="JPEG")
        uploaded_jpeg = SimpleUploadedFile("logo.jpg", jpeg_data, content_type="image/jpeg")
        # Should not raise
        validate_company_logo(uploaded_jpeg)

    def test_validate_company_logo_file_size_exceeded(self):
        # 3MB oversized file
        oversized_data = b"x" * (3 * 1024 * 1024)
        uploaded = SimpleUploadedFile("large_logo.png", oversized_data, content_type="image/png")
        with self.assertRaises(ValidationError) as ctx:
            validate_company_logo(uploaded)
        self.assertIn("exceeds the 2MB limit", str(ctx.exception))

    def test_validate_company_logo_invalid_extension(self):
        img_data = create_test_image(img_format="PNG")
        uploaded = SimpleUploadedFile("logo.svg", img_data, content_type="image/svg+xml")
        with self.assertRaises(ValidationError) as ctx:
            validate_company_logo(uploaded)
        self.assertIn("Unsupported file extension", str(ctx.exception))

    def test_validate_company_logo_corrupt_or_fake_image(self):
        fake_data = b"This is plain text, not a valid image."
        uploaded = SimpleUploadedFile("fake_logo.png", fake_data, content_type="image/png")
        with self.assertRaises(ValidationError) as ctx:
            validate_company_logo(uploaded)
        self.assertIn("not a valid or readable image", str(ctx.exception))

    def test_upload_path_configuration(self):
        company = Company.objects.create(
            name="Stark Tech",
            organization=self.org,
        )
        path = company_logo_upload_path(company, "original_user_logo.PNG")
        expected_prefix = f"organizations/{self.org.id}/companies/{company.id}/logos/"

        self.assertTrue(path.startswith(expected_prefix))
        self.assertNotIn("original_user_logo", path)
        self.assertTrue(path.endswith(".png"))

    def test_api_create_company_with_logo(self):
        img_data = create_test_image(img_format="PNG")
        logo_file = SimpleUploadedFile("stark_logo.png", img_data, content_type="image/png")

        response = self.client.post(
            "/api/v1/companies/",
            {
                "name": "Stark Aerospace",
                "industry": "Aerospace",
                "country": "US",
                "logo": logo_file,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]
        self.assertIsNotNone(data["logo"])
        self.assertIsNotNone(data["logo_url"])
        self.assertEqual(data["logo"], data["logo_url"])

        # Check DB
        company = Company.objects.get(id=data["id"])
        self.assertTrue(bool(company.logo))
        self.assertTrue(company.logo.name.startswith(f"organizations/{self.org.id}/companies/{company.id}/logos/"))

    def test_api_create_company_with_invalid_logo(self):
        fake_file = SimpleUploadedFile("bad_logo.png", b"Not an image", content_type="image/png")
        response = self.client.post(
            "/api/v1/companies/",
            {
                "name": "Invalid Logo Corp",
                "logo": fake_file,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("logo", response.data["errors"])

    def test_api_update_company_logo(self):
        company = Company.objects.create(
            name="Stark Energy",
            organization=self.org,
        )
        img_data = create_test_image(img_format="JPEG", color="red")
        new_logo = SimpleUploadedFile("arc_reactor.jpg", img_data, content_type="image/jpeg")

        response = self.client.patch(
            f"/api/v1/companies/{company.id}/",
            {"logo": new_logo},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        company.refresh_from_db()
        self.assertTrue(bool(company.logo))
        self.assertTrue(company.logo.name.endswith(".jpg"))

    def test_api_company_logo_representation_null_when_empty(self):
        company = Company.objects.create(
            name="No Logo Corp",
            organization=self.org,
        )
        response = self.client.get(f"/api/v1/companies/{company.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertIsNone(data["logo"])
        self.assertIsNone(data["logo_url"])
