from rest_framework.permissions import SAFE_METHODS, BasePermission


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


class IsAdminRole(BasePermission):
    message = "Administrator access is required to perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)


class IsManagerRole(BasePermission):
    message = "Manager access is required to perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_manager)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and user.is_manager)


class IsStaffRole(BasePermission):
    message = "Staff access is required to perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff_role)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff_role)


class CanDeleteRecord(BasePermission):
    message = "Only administrators are permitted to delete records."

    def has_permission(self, request, view):
        if request.method == "DELETE":
            user = request.user
            return bool(user and user.is_authenticated and user.is_admin)
        return True

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            user = request.user
            return bool(user and user.is_authenticated and user.is_admin)
        return True


class CanViewActivityLogs(BasePermission):
    message = "Only administrators and managers are permitted to view activity logs."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if not (user.is_admin or user.is_manager):
            return False

        if request.method not in SAFE_METHODS:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if not (user.is_admin or user.is_manager):
            return False

        if request.method not in SAFE_METHODS:
            return False

        return True


class RoleBasedAccessPermission(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if request.method == "DELETE":
            if not user.is_admin:
                self.message = "Only administrators are permitted to delete records."
                return False

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if request.method == "DELETE":
            if not user.is_admin:
                self.message = "Only administrators are permitted to delete records."
                return False

        return True
