from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.organizations.models import Organization
from .models import ActivityLog
from .services import create_activity_log

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
