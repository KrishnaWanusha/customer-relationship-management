from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.organizations.models import Organization
from backend.apps.companies.models import Company
from backend.apps.companies.services import CompanyService
from backend.apps.contacts.models import Contact
from backend.apps.contacts.services import ContactService
from .models import ActivityLog
from .services import AuditService, create_activity_log

User = get_user_model()


class ActivityLogModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Delta Org")
        self.user = User.objects.create_user(
            email="manager@crm.com",
            password="password123",
            organization=self.org,
            role=User.Role.MANAGER,
        )

    def test_create_activity_log(self):
        log = ActivityLog.objects.create(
            organization=self.org,
            user=self.user,
            action=ActivityLog.Action.CREATE,
            model_name="Company",
            object_id="42",
            details={"name": "New Company Inc"},
        )
        self.assertEqual(log.organization, self.org)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, ActivityLog.Action.CREATE)
        self.assertEqual(log.model_name, "Company")
        self.assertEqual(log.object_id, "42")
        self.assertEqual(log.details, {"name": "New Company Inc"})
        self.assertIsNotNone(log.timestamp)

    def test_create_activity_log_via_service(self):
        log = create_activity_log(
            organization=self.org,
            user=self.user,
            action=ActivityLog.Action.DELETE,
            model_name="Contact",
            object_id=99,
        )
        self.assertEqual(log.action, ActivityLog.Action.DELETE)
        self.assertEqual(log.object_id, "99")
        self.assertEqual(log.details, {})

    def test_activity_log_with_null_user_system_action(self):
        log = ActivityLog.objects.create(
            organization=self.org,
            user=None,
            action=ActivityLog.Action.UPDATE,
            model_name="Company",
            object_id="1",
        )
        self.assertIn("System", str(log))


class AuditServiceTest(TestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name="Alpha Org")
        self.org_b = Organization.objects.create(name="Beta Org")
        self.user_a = User.objects.create_user(
            email="admin_a@alpha.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.ADMIN,
        )
        self.user_b = User.objects.create_user(
            email="admin_b@beta.com",
            password="password123",
            organization=self.org_b,
            role=User.Role.ADMIN,
        )
        self.company = Company.objects.create(
            name="Acme Corp",
            organization=self.org_a,
            industry="Tech",
            country="US",
        )

    def test_log_create_via_audit_service(self):
        log = AuditService.log_create(
            instance=self.company,
            user=self.user_a,
            details={"name": self.company.name},
        )
        self.assertEqual(log.organization, self.org_a)
        self.assertEqual(log.user, self.user_a)
        self.assertEqual(log.action, ActivityLog.Action.CREATE)
        self.assertEqual(log.model_name, "Company")
        self.assertEqual(log.object_id, str(self.company.id))
        self.assertEqual(log.details, {"name": "Acme Corp"})
        self.assertIsNotNone(log.timestamp)

    def test_log_update_diff_tracking(self):
        changes = AuditService.apply_changes(
            self.company,
            {"name": "Acme Global", "country": "CA"},
        )
        self.company.save()
        log = AuditService.log_update(
            instance=self.company,
            user=self.user_a,
            changes=changes,
        )
        self.assertEqual(log.action, ActivityLog.Action.UPDATE)
        self.assertEqual(log.model_name, "Company")
        self.assertEqual(log.object_id, str(self.company.id))
        self.assertIn("changed_fields", log.details)
        self.assertIn("name", log.details["changed_fields"])
        self.assertIn("country", log.details["changed_fields"])
        self.assertEqual(log.details["changes"]["name"]["old"], "Acme Corp")
        self.assertEqual(log.details["changes"]["name"]["new"], "Acme Global")

    def test_log_delete_via_audit_service(self):
        company_id = str(self.company.id)
        self.company.soft_delete(user=self.user_a)
        log = AuditService.log_delete(
            instance=self.company,
            user=self.user_a,
            details={"name": self.company.name},
        )
        self.assertEqual(log.action, ActivityLog.Action.DELETE)
        self.assertEqual(log.model_name, "Company")
        self.assertEqual(log.object_id, company_id)

    def test_tenant_safety_rejects_cross_tenant_logging(self):
        with self.assertRaises(PermissionDenied):
            AuditService.log_create(
                instance=self.company,
                user=self.user_b,  # User from Org B targeting Org A object
            )

    def test_rejects_unauthenticated_or_non_org_user(self):
        user_no_org = User.objects.create_user(
            email="orphan@nowhere.com",
            password="password123",
            role=User.Role.STAFF,
        )
        with self.assertRaises(PermissionDenied):
            AuditService.log_create(instance=self.company, user=user_no_org)

    def test_atomic_rollback_on_audit_logging_failure(self):
        initial_company_count = Company.objects.count()
        initial_log_count = ActivityLog.objects.count()

        with patch.object(AuditService, "log_create", side_effect=IntegrityError("Audit DB Error")):
            with self.assertRaises(IntegrityError):
                CompanyService.create_company(
                    organization=self.org_a,
                    user=self.user_a,
                    validated_data={"name": "Failed Atomic Co", "industry": "Finance", "country": "US"},
                )

        self.assertEqual(Company.objects.count(), initial_company_count)
        self.assertEqual(ActivityLog.objects.count(), initial_log_count)
        self.assertFalse(Company.objects.filter(name="Failed Atomic Co").exists())


class CompanyAutomaticLoggingAPITest(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Cyberdyne Systems")
        self.admin = User.objects.create_user(
            email="admin@cyberdyne.com",
            password="password123",
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.admin)

    def test_company_creation_automatic_logging(self):
        response = self.client.post(
            "/api/v1/companies/",
            {"name": "Robotics Corp", "industry": "Robotics", "country": "US"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        company_id = response.data["data"]["id"]

        log = ActivityLog.objects.filter(
            model_name="Company",
            object_id=company_id,
            action=ActivityLog.Action.CREATE,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.organization, self.org)
        self.assertEqual(log.details.get("name"), "Robotics Corp")
        self.assertIsNotNone(log.timestamp)

    def test_company_update_automatic_logging(self):
        company = Company.objects.create(
            name="Robotics Corp",
            organization=self.org,
            industry="Robotics",
            country="US",
        )
        response = self.client.patch(
            f"/api/v1/companies/{company.id}/",
            {"name": "Robotics Innovations", "country": "JP"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        log = ActivityLog.objects.filter(
            model_name="Company",
            object_id=str(company.id),
            action=ActivityLog.Action.UPDATE,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.organization, self.org)
        self.assertIn("name", log.details.get("changed_fields", []))
        self.assertIn("country", log.details.get("changed_fields", []))
        self.assertEqual(log.details["changes"]["name"]["old"], "Robotics Corp")
        self.assertEqual(log.details["changes"]["name"]["new"], "Robotics Innovations")

    def test_company_soft_delete_automatic_logging(self):
        company = Company.objects.create(
            name="To Delete Corp",
            organization=self.org,
            industry="Retail",
            country="UK",
        )
        response = self.client.delete(f"/api/v1/companies/{company.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        log = ActivityLog.objects.filter(
            model_name="Company",
            object_id=str(company.id),
            action=ActivityLog.Action.DELETE,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.organization, self.org)
        self.assertEqual(log.details.get("name"), "To Delete Corp")

        self.assertTrue(ActivityLog.objects.filter(object_id=str(company.id)).exists())


class ContactAutomaticLoggingAPITest(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Wayne Enterprises")
        self.admin = User.objects.create_user(
            email="bruce@wayne.com",
            password="password123",
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.company = Company.objects.create(
            name="Wayne Tech",
            organization=self.org,
            industry="Defense",
            country="US",
        )
        self.client.force_authenticate(user=self.admin)

    def test_contact_creation_automatic_logging(self):
        response = self.client.post(
            "/api/v1/contacts/",
            {
                "company": str(self.company.id),
                "full_name": "Lucius Fox",
                "email": "lucius@wayne.com",
                "phone": "1234567890",
                "role": "CEO",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contact_id = response.data["data"]["id"]

        log = ActivityLog.objects.filter(
            model_name="Contact",
            object_id=contact_id,
            action=ActivityLog.Action.CREATE,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.organization, self.org)
        self.assertEqual(log.details.get("full_name"), "Lucius Fox")
        self.assertEqual(log.details.get("email"), "lucius@wayne.com")
        self.assertIsNotNone(log.timestamp)

    def test_contact_update_automatic_logging(self):
        contact = Contact.objects.create(
            company=self.company,
            organization=self.org,
            full_name="Alfred Pennyworth",
            email="alfred@wayne.com",
            role="Butler",
        )
        response = self.client.patch(
            f"/api/v1/contacts/{contact.id}/",
            {"role": "Chief Butler", "phone": "9876543210"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        log = ActivityLog.objects.filter(
            model_name="Contact",
            object_id=str(contact.id),
            action=ActivityLog.Action.UPDATE,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.organization, self.org)
        self.assertIn("role", log.details.get("changed_fields", []))
        self.assertEqual(log.details["changes"]["role"]["old"], "Butler")
        self.assertEqual(log.details["changes"]["role"]["new"], "Chief Butler")

    def test_contact_soft_delete_automatic_logging(self):
        contact = Contact.objects.create(
            company=self.company,
            organization=self.org,
            full_name="Rachel Dawes",
            email="rachel@wayne.com",
            role="Attorney",
        )
        response = self.client.delete(f"/api/v1/contacts/{contact.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        log = ActivityLog.objects.filter(
            model_name="Contact",
            object_id=str(contact.id),
            action=ActivityLog.Action.DELETE,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.organization, self.org)
        self.assertEqual(log.details.get("full_name"), "Rachel Dawes")

        self.assertTrue(ActivityLog.objects.filter(object_id=str(contact.id)).exists())


class ActivityLogAPITest(APITestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name="Stark Industries")
        self.org_b = Organization.objects.create(name="Hammer Tech")

        self.admin_a = User.objects.create_user(
            email="tony@stark.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.ADMIN,
        )
        self.manager_a = User.objects.create_user(
            email="pepper@stark.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.MANAGER,
        )
        self.staff_a = User.objects.create_user(
            email="happy@stark.com",
            password="password123",
            organization=self.org_a,
            role=User.Role.STAFF,
        )
        self.admin_b = User.objects.create_user(
            email="justin@hammer.com",
            password="password123",
            organization=self.org_b,
            role=User.Role.ADMIN,
        )

        # Create activity logs for Org A
        self.log_a1 = ActivityLog.objects.create(
            organization=self.org_a,
            user=self.admin_a,
            action=ActivityLog.Action.CREATE,
            model_name="Company",
            object_id="101",
            details={"name": "Arc Reactor Corp"},
        )
        self.log_a2 = ActivityLog.objects.create(
            organization=self.org_a,
            user=self.manager_a,
            action=ActivityLog.Action.UPDATE,
            model_name="Contact",
            object_id="202",
            details={"name": "James Rhodes"},
        )
        # Create activity log for Org B
        self.log_b1 = ActivityLog.objects.create(
            organization=self.org_b,
            user=self.admin_b,
            action=ActivityLog.Action.CREATE,
            model_name="Company",
            object_id="303",
            details={"name": "Drones Inc"},
        )

    def test_admin_can_list_activity_logs(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get("/api/v1/activity-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 2)
        log_ids = [r["id"] for r in results]
        self.assertIn(self.log_a1.id, log_ids)
        self.assertIn(self.log_a2.id, log_ids)
        self.assertNotIn(self.log_b1.id, log_ids)

    def test_manager_can_list_activity_logs(self):
        self.client.force_authenticate(user=self.manager_a)
        response = self.client.get("/api/v1/activity-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 2)

    def test_staff_cannot_view_activity_logs(self):
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get("/api/v1/activity-logs/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_isolation_org_b_cannot_see_org_a_logs(self):
        self.client.force_authenticate(user=self.admin_b)
        response = self.client.get("/api/v1/activity-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.log_b1.id)
        # Attempt direct retrieve of Org A log
        detail_response = self.client.get(f"/api/v1/activity-logs/{self.log_a1.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_action_and_model_name(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get("/api/v1/activity-logs/?action=CREATE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["action"], "CREATE")

        response_model = self.client.get("/api/v1/activity-logs/?model_name=Contact")
        self.assertEqual(response_model.status_code, status.HTTP_200_OK)
        results_model = response_model.data["data"]["results"]
        self.assertEqual(len(results_model), 1)
        self.assertEqual(results_model[0]["model_name"], "Contact")

