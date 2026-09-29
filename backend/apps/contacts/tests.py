import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from backend.apps.organizations.models import Organization
from backend.apps.companies.models import Company
from backend.apps.contacts.models import Contact

User = get_user_model()


class ContactModelTest(TestCase):
    def setUp(self):
        self.org1 = Organization.objects.create(name="Org One", slug="org-one")
        self.org2 = Organization.objects.create(name="Org Two", slug="org-two")
        self.company1 = Company.objects.create(name="Company Alpha", organization=self.org1)
        self.company2 = Company.objects.create(name="Company Beta", organization=self.org2)
        self.user = User.objects.create_user(
            email="user@orgone.com",
            password="password123",
            organization=self.org1,
        )

    def test_contact_uuid_and_relationships(self):
        contact = Contact.objects.create(
            company=self.company1,
            organization=self.org1,
            full_name="Jane Doe",
            email="jane.doe@alpha.com",
            phone="+1234567890",
            role="Director",
        )
        self.assertIsInstance(contact.id, uuid.UUID)
        self.assertEqual(contact.company, self.company1)
        self.assertEqual(contact.organization, self.org1)
        self.assertIn(contact, self.company1.contacts.all())
        self.assertIn(contact, self.org1.contacts.all())
        self.assertFalse(contact.is_deleted)
        self.assertEqual(contact.role, "Director")

    def test_create_contact_auto_sets_organization_from_company(self):
        contact = Contact.objects.create(
            company=self.company1,
            full_name="Krishna Wanusha",
            email="krishna@alpha.com",
        )
        self.assertEqual(contact.organization, self.org1)
        self.assertEqual(contact.full_name, "Krishna Wanusha")

    def test_contact_organization_mismatch_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            contact = Contact(
                organization=self.org2,
                company=self.company1,
                full_name="Cross Tenant",
                email="cross@alpha.com",
            )
            contact.full_clean()

    def test_phone_validation_optional(self):
        # Phone is optional (empty/blank permitted)
        contact = Contact(
            company=self.company1,
            organization=self.org1,
            full_name="No Phone",
            email="nophone@alpha.com",
            phone="",
        )
        contact.full_clean()
        contact.save()
        self.assertEqual(contact.phone, "")

    def test_phone_validation_valid_digits(self):
        # 8 digits
        c1 = Contact(
            company=self.company1,
            organization=self.org1,
            full_name="Eight Digits",
            email="p8@alpha.com",
            phone="12345678",
        )
        c1.full_clean()

        # 15 digits with international prefix and formatting
        c2 = Contact(
            company=self.company1,
            organization=self.org1,
            full_name="Fifteen Digits",
            email="p15@alpha.com",
            phone="+123456789012345",
        )
        c2.full_clean()

    def test_phone_validation_invalid_digits(self):
        # Too short: 7 digits
        with self.assertRaises(ValidationError):
            c_short = Contact(
                company=self.company1,
                organization=self.org1,
                full_name="Too Short",
                email="short@alpha.com",
                phone="1234567",
            )
            c_short.full_clean()

        # Too long: 16 digits
        with self.assertRaises(ValidationError):
            c_long = Contact(
                company=self.company1,
                organization=self.org1,
                full_name="Too Long",
                email="long@alpha.com",
                phone="1234567890123456",
            )
            c_long.full_clean()

        # No digits
        with self.assertRaises(ValidationError):
            c_nan = Contact(
                company=self.company1,
                organization=self.org1,
                full_name="No Digits",
                email="nan@alpha.com",
                phone="letters-only",
            )
            c_nan.full_clean()

    def test_unique_email_per_company_constraint(self):
        Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Alice Smith",
            email="alice@alpha.com",
        )

        # Model clean check
        with self.assertRaises(ValidationError):
            duplicate_contact = Contact(
                organization=self.org1,
                company=self.company1,
                full_name="Alice Duplicate",
                email="alice@alpha.com",
            )
            duplicate_contact.full_clean()

        # DB constraint check
        with self.assertRaises(IntegrityError):
            Contact.objects.create(
                organization=self.org1,
                company=self.company1,
                full_name="Alice Duplicate",
                email="alice@alpha.com",
            )

    def test_same_email_allowed_in_different_companies(self):
        contact1 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Bob Taylor",
            email="bob@example.com",
        )
        contact2 = Contact.objects.create(
            organization=self.org2,
            company=self.company2,
            full_name="Bob Taylor",
            email="bob@example.com",
        )
        self.assertEqual(contact1.email, contact2.email)
        self.assertNotEqual(contact1.company, contact2.company)

    def test_soft_delete_allows_recreating_same_email(self):
        contact1 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Charlie Brown",
            email="charlie@alpha.com",
        )
        contact1.soft_delete(user=self.user)
        self.assertTrue(contact1.is_deleted)
        self.assertEqual(Contact.objects.filter(id=contact1.id).count(), 0)

        # Re-creating same email in the company is allowed since contact1 is deleted
        contact2 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Charlie Brown New",
            email="charlie@alpha.com",
        )
        self.assertEqual(contact2.email, "charlie@alpha.com")
        self.assertEqual(Contact.objects.filter(company=self.company1, email="charlie@alpha.com").count(), 1)
        self.assertEqual(Contact.all_objects.filter(company=self.company1, email="charlie@alpha.com").count(), 2)


class ContactAPITest(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient

        self.client = APIClient()
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

        self.company_a1 = Company.objects.create(
            organization=self.org_a,
            name="Alpha Corp",
            industry="Technology",
        )
        self.company_a2 = Company.objects.create(
            organization=self.org_a,
            name="Alpha Health",
            industry="Healthcare",
        )
        self.deleted_company_a = Company.objects.create(
            organization=self.org_a,
            name="Alpha Deleted",
        )
        self.deleted_company_a.soft_delete(user=self.admin_user_a)

        self.company_b1 = Company.objects.create(
            organization=self.org_b,
            name="Beta Corp",
            industry="Finance",
        )

        self.contact_a1 = Contact.objects.create(
            company=self.company_a1,
            organization=self.org_a,
            full_name="Alice Smith",
            email="alice@alphacorp.com",
            phone="12345678",
            role="Manager",
        )
        self.contact_a2 = Contact.objects.create(
            company=self.company_a1,
            organization=self.org_a,
            full_name="Bob Jones",
            email="bob@alphacorp.com",
            phone="+1234567890",
            role="Engineer",
        )
        self.contact_b1 = Contact.objects.create(
            company=self.company_b1,
            organization=self.org_b,
            full_name="Charlie Beta",
            email="charlie@betacorp.com",
            phone="87654321",
            role="Lead",
        )

    def test_unauthenticated_request_rejected(self):
        response = self.client.get("/api/v1/contacts/")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["success"])

    def test_list_contacts_pagination_and_tenant_isolation(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.get("/api/v1/contacts/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Data retrieved successfully.")

        results = response.data["data"]["results"]
        contact_names = [c["full_name"] for c in results]
        self.assertIn("Alice Smith", contact_names)
        self.assertIn("Bob Jones", contact_names)
        self.assertNotIn("Charlie Beta", contact_names)

        pagination = response.data["data"]["pagination"]
        self.assertEqual(pagination["count"], 2)
        self.assertEqual(pagination["current_page"], 1)

    def test_retrieve_contact_success(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.get(f"/api/v1/contacts/{self.contact_a1.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["id"], str(self.contact_a1.id))
        self.assertEqual(response.data["data"]["full_name"], "Alice Smith")
        self.assertEqual(response.data["data"]["company_name"], "Alpha Corp")

    def test_cross_tenant_retrieve_returns_404(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.get(f"/api/v1/contacts/{self.contact_b1.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["success"])

    def test_create_contact_success_with_activity_log(self):
        from backend.apps.activity_logs.models import ActivityLog

        self.client.force_authenticate(user=self.manager_user_a)
        payload = {
            "company": str(self.company_a1.id),
            "full_name": "Dave Miller",
            "email": "dave@alphacorp.com",
            "phone": "+9876543210",
            "role": "Consultant",
            "organization": self.org_b.id,  # Attempt cross-tenant spoofing
        }

        response = self.client.post("/api/v1/contacts/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])

        created_id = response.data["data"]["id"]
        contact = Contact.objects.get(id=created_id)

        # Authoritative organization assigned
        self.assertEqual(contact.organization, self.org_a)
        self.assertEqual(contact.full_name, "Dave Miller")
        self.assertEqual(contact.company, self.company_a1)

        # Activity log created
        log = ActivityLog.objects.filter(
            organization=self.org_a,
            action=ActivityLog.Action.CREATE,
            model_name="Contact",
            object_id=str(contact.id),
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.manager_user_a)

    def test_create_contact_cross_tenant_company_rejected(self):
        self.client.force_authenticate(user=self.staff_user_a)
        payload = {
            "company": str(self.company_b1.id),
            "full_name": "Bad Actor",
            "email": "bad@actor.com",
        }
        response = self.client.post("/api/v1/contacts/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("company", response.data["errors"])

    def test_create_contact_deleted_company_rejected(self):
        self.client.force_authenticate(user=self.staff_user_a)
        payload = {
            "company": str(self.deleted_company_a.id),
            "full_name": "Deleted Company Contact",
            "email": "deleted@company.com",
        }
        response = self.client.post("/api/v1/contacts/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("company", response.data["errors"])

    def test_create_contact_required_fields_validation(self):
        self.client.force_authenticate(user=self.staff_user_a)

        # Missing full_name, email, company
        response = self.client.post("/api/v1/contacts/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("full_name", response.data["errors"])
        self.assertIn("email", response.data["errors"])
        self.assertIn("company", response.data["errors"])

    def test_create_contact_company_scoped_email_uniqueness(self):
        self.client.force_authenticate(user=self.staff_user_a)

        # Attempt to create contact with Alice's email in same company -> rejected
        payload = {
            "company": str(self.company_a1.id),
            "full_name": "Alice Duplicate",
            "email": "alice@alphacorp.com",
        }
        response = self.client.post("/api/v1/contacts/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("email", response.data["errors"])

        # Creating contact with same email in DIFFERENT company within same org -> allowed
        payload_diff_company = {
            "company": str(self.company_a2.id),
            "full_name": "Alice in Company A2",
            "email": "alice@alphacorp.com",
        }
        response_diff = self.client.post("/api/v1/contacts/", payload_diff_company, format="json")
        self.assertEqual(response_diff.status_code, 201)
        self.assertTrue(response_diff.data["success"])

    def test_create_contact_phone_validation(self):
        self.client.force_authenticate(user=self.staff_user_a)

        # Valid phone (optional/empty)
        res_empty = self.client.post(
            "/api/v1/contacts/",
            {
                "company": str(self.company_a2.id),
                "full_name": "No Phone Contact",
                "email": "nophone@alpha2.com",
                "phone": "",
            },
            format="json",
        )
        self.assertEqual(res_empty.status_code, 201)

        # Invalid phone: too short (< 8 digits)
        res_short = self.client.post(
            "/api/v1/contacts/",
            {
                "company": str(self.company_a2.id),
                "full_name": "Short Phone",
                "email": "short@alpha2.com",
                "phone": "1234567",
            },
            format="json",
        )
        self.assertEqual(res_short.status_code, 400)
        self.assertIn("phone", res_short.data["errors"])

        # Invalid phone: too long (> 15 digits)
        res_long = self.client.post(
            "/api/v1/contacts/",
            {
                "company": str(self.company_a2.id),
                "full_name": "Long Phone",
                "email": "long@alpha2.com",
                "phone": "1234567890123456",
            },
            format="json",
        )
        self.assertEqual(res_long.status_code, 400)
        self.assertIn("phone", res_long.data["errors"])

    def test_update_contact_put_and_patch(self):
        from backend.apps.activity_logs.models import ActivityLog

        self.client.force_authenticate(user=self.manager_user_a)

        # Full update (PUT)
        put_payload = {
            "company": str(self.company_a1.id),
            "full_name": "Alice Smith Updated",
            "email": "alice.updated@alphacorp.com",
            "phone": "+1122334455",
            "role": "Senior Manager",
        }
        res_put = self.client.put(f"/api/v1/contacts/{self.contact_a1.id}/", put_payload, format="json")
        self.assertEqual(res_put.status_code, 200)
        self.assertTrue(res_put.data["success"])
        self.assertEqual(res_put.data["data"]["full_name"], "Alice Smith Updated")

        # Partial update (PATCH)
        res_patch = self.client.patch(
            f"/api/v1/contacts/{self.contact_a1.id}/",
            {"role": "Director of Operations"},
            format="json",
        )
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data["data"]["role"], "Director of Operations")

        self.contact_a1.refresh_from_db()
        self.assertEqual(self.contact_a1.role, "Director of Operations")

        # Activity log was created
        log = ActivityLog.objects.filter(
            organization=self.org_a,
            action=ActivityLog.Action.UPDATE,
            model_name="Contact",
            object_id=str(self.contact_a1.id),
        ).first()
        self.assertIsNotNone(log)

    def test_cross_tenant_update_returns_404(self):
        self.client.force_authenticate(user=self.manager_user_a)
        response = self.client.patch(
            f"/api/v1/contacts/{self.contact_b1.id}/",
            {"full_name": "Hacked Contact"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_can_soft_delete_contact(self):
        from backend.apps.activity_logs.models import ActivityLog

        self.client.force_authenticate(user=self.admin_user_a)
        response = self.client.delete(f"/api/v1/contacts/{self.contact_a1.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        self.contact_a1.refresh_from_db()
        self.assertTrue(self.contact_a1.is_deleted)
        self.assertEqual(self.contact_a1.deleted_by, self.admin_user_a)
        self.assertIsNotNone(self.contact_a1.deleted_at)

        # Excluded from normal list
        list_res = self.client.get("/api/v1/contacts/")
        names = [c["full_name"] for c in list_res.data["data"]["results"]]
        self.assertNotIn("Alice Smith", names)

        # Activity log was created
        log = ActivityLog.objects.filter(
            organization=self.org_a,
            action=ActivityLog.Action.DELETE,
            model_name="Contact",
            object_id=str(self.contact_a1.id),
        ).first()
        self.assertIsNotNone(log)

    def test_manager_cannot_delete_contact(self):
        self.client.force_authenticate(user=self.manager_user_a)
        response = self.client.delete(f"/api/v1/contacts/{self.contact_a1.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["success"])

        self.contact_a1.refresh_from_db()
        self.assertFalse(self.contact_a1.is_deleted)

    def test_staff_cannot_delete_contact(self):
        self.client.force_authenticate(user=self.staff_user_a)
        response = self.client.delete(f"/api/v1/contacts/{self.contact_a1.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["success"])

        self.contact_a1.refresh_from_db()
        self.assertFalse(self.contact_a1.is_deleted)

    def test_search_contacts(self):
        self.client.force_authenticate(user=self.staff_user_a)

        # Search by full_name
        res1 = self.client.get("/api/v1/contacts/?search=Jones")
        self.assertEqual(res1.status_code, 200)
        results1 = res1.data["data"]["results"]
        self.assertEqual(len(results1), 1)
        self.assertEqual(results1[0]["full_name"], "Bob Jones")

        # Search by role
        res2 = self.client.get("/api/v1/contacts/?search=Manager")
        self.assertEqual(res2.status_code, 200)
        results2 = res2.data["data"]["results"]
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["full_name"], "Alice Smith")

    def test_filter_contacts(self):
        self.client.force_authenticate(user=self.staff_user_a)

        # Filter by company
        res1 = self.client.get(f"/api/v1/contacts/?company={self.company_a1.id}")
        self.assertEqual(res1.status_code, 200)
        results1 = res1.data["data"]["results"]
        self.assertEqual(len(results1), 2)

        # Filter by role
        res2 = self.client.get("/api/v1/contacts/?role=Engineer")
        self.assertEqual(res2.status_code, 200)
        results2 = res2.data["data"]["results"]
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["full_name"], "Bob Jones")

