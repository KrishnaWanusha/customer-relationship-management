import uuid
from datetime import date, datetime
from django.core.exceptions import PermissionDenied
from django.db import models
from .models import ActivityLog


def serialize_audit_value(value):
    """
    Serializes complex Python and Django objects into JSON-compatible primitives.
    """
    if value is None:
        return None
    if isinstance(value, models.Model):
        return str(value.pk)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool, list, dict)):
        return value
    return str(value)


class AuditService:

    @classmethod
    def apply_changes(cls, instance, validated_data):
        changes = {}
        for key, new_val in validated_data.items():
            old_val = getattr(instance, key, None)
            if old_val != new_val:
                changes[key] = {
                    "old": serialize_audit_value(old_val),
                    "new": serialize_audit_value(new_val),
                }
                setattr(instance, key, new_val)

        if changes:
            return {
                "changed_fields": list(changes.keys()),
                "changes": changes,
            }
        return {}

    @classmethod
    def log_action(
        cls,
        *,
        instance,
        user,
        action,
        details=None,
    ):
        if not user or not getattr(user, "is_authenticated", False):
            raise PermissionDenied("An authenticated user is required for activity logging.")

        user_org_id = getattr(user, "organization_id", None)
        instance_org_id = getattr(instance, "organization_id", None)

        if not user_org_id:
            raise PermissionDenied("Acting user has no assigned organization.")

        if instance_org_id and str(user_org_id) != str(instance_org_id):
            raise PermissionDenied("Tenant mismatch: user organization does not match target object organization.")

        organization = getattr(instance, "organization", None) or getattr(user, "organization", None)
        model_name = instance._meta.model_name.capitalize()
        object_id = str(instance.pk or instance.id)

        return ActivityLog.objects.create(
            organization=organization,
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            details=details or {},
        )

    @classmethod
    def log_create(cls, *, instance, user, details=None):
        return cls.log_action(
            instance=instance,
            user=user,
            action=ActivityLog.Action.CREATE,
            details=details,
        )

    @classmethod
    def log_update(cls, *, instance, user, changes=None, details=None):
        log_details = details or {}
        if changes:
            log_details.update(changes)
        return cls.log_action(
            instance=instance,
            user=user,
            action=ActivityLog.Action.UPDATE,
            details=log_details,
        )

    @classmethod
    def log_delete(cls, *, instance, user, details=None):
        return cls.log_action(
            instance=instance,
            user=user,
            action=ActivityLog.Action.DELETE,
            details=details,
        )


def create_activity_log(*, organization, user, action, model_name, object_id, details=None):
    if user and getattr(user, "organization_id", None):
        user_org_id = str(user.organization_id)
        target_org_id = str(organization.id if hasattr(organization, "id") else organization)
        if user_org_id != target_org_id:
            raise PermissionDenied("Tenant mismatch between user and target organization.")

    return ActivityLog.objects.create(
        organization=organization,
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        details=details or {},
    )
