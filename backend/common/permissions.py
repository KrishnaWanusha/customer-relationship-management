from rest_framework.permissions import BasePermission


class IsTenantUser(BasePermission):
    message = "You must belong to an active organization to access this resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(user.organization_id and user.organization.is_active)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated or not user.organization_id:
            return False
        return getattr(obj, "organization_id", None) == user.organization_id
