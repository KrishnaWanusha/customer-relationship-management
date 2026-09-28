from django_multitenant.utils import set_current_tenant, unset_current_tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "user") and request.user.is_authenticated and getattr(request.user, "organization", None):
            set_current_tenant(request.user.organization)
        else:
            unset_current_tenant()

        response = self.get_response(request)
        unset_current_tenant()
        return response
