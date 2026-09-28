from rest_framework.permissions import IsAuthenticated
from django_multitenant.utils import set_current_tenant, unset_current_tenant
from .permissions import IsTenantUser


class TenantFilteredViewSetMixin:
    permission_classes = [IsAuthenticated, IsTenantUser]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_authenticated and getattr(request.user, "organization", None):
            set_current_tenant(request.user.organization)

    def finalize_response(self, request, response, *args, **kwargs):
        unset_current_tenant()
        return super().finalize_response(request, response, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated or not getattr(user, "organization_id", None):
            return qs.none()
        return qs.filter(organization=user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
