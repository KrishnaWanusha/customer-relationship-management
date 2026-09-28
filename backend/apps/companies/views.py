from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from common.responses import api_success
from common.views import TenantFilteredViewSetMixin
from .filters import CompanyFilter
from .models import Company
from .serializers import CompanySerializer
from .services import CompanyService


class CompanyViewSet(TenantFilteredViewSetMixin, viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CompanyFilter
    search_fields = ["name", "industry", "country"]
    ordering_fields = ["name", "industry", "country", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                contacts_count=Count(
                    "contacts",
                    filter=Q(contacts__is_deleted=False),
                    distinct=True,
                )
            )
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_success(
            data={"results": serializer.data},
            message="Companies retrieved successfully.",
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(
            data=serializer.data,
            message="Company retrieved successfully.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = CompanyService.create_company(
            organization=request.user.organization,
            user=request.user,
            validated_data=serializer.validated_data,
        )
        response_serializer = self.get_serializer(company)
        return api_success(
            data=response_serializer.data,
            message="Company created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        company = CompanyService.update_company(
            company=instance,
            user=request.user,
            validated_data=serializer.validated_data,
        )
        response_serializer = self.get_serializer(company)
        return api_success(
            data=response_serializer.data,
            message="Company updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        CompanyService.delete_company(company=instance, user=request.user)
        return api_success(
            message="Company deleted successfully.",
            status_code=status.HTTP_200_OK,
        )
