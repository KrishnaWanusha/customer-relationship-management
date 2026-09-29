from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from common.permissions import CanViewActivityLogs, IsTenantUser
from common.responses import api_success
from common.views import TenantFilteredViewSetMixin
from .filters import ActivityLogFilter
from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogViewSet(TenantFilteredViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all().select_related("user", "organization")
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsTenantUser, CanViewActivityLogs]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ActivityLogFilter
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "model_name",
        "object_id",
    ]
    ordering_fields = ["timestamp", "action", "model_name"]
    ordering = ["-timestamp"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_success(
            data={"results": serializer.data},
            message="Activity logs retrieved successfully.",
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(
            data=serializer.data,
            message="Activity log retrieved successfully.",
        )
