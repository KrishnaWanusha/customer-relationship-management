from .models import ActivityLog


def create_activity_log(*, organization, user, action, model_name, object_id, details=None):
    return ActivityLog.objects.create(
        organization=organization,
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        details=details or {},
    )
