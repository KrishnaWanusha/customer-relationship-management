from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from common.responses import api_success
from common.views import TenantFilteredViewSetMixin
from .filters import ContactFilter
from .models import Contact
from .serializers import ContactSerializer
from .services import ContactService


class ContactViewSet(TenantFilteredViewSetMixin, viewsets.ModelViewSet):
    queryset = Contact.objects.select_related("company", "organization").all()
    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ContactFilter
    search_fields = ["full_name", "email", "role", "company__name"]
    ordering_fields = ["full_name", "email", "role", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return api_success(
            data={"results": serializer.data},
            message="Contacts retrieved successfully.",
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(
            data=serializer.data,
            message="Contact retrieved successfully.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = ContactService.create_contact(
            organization=request.user.organization,
            user=request.user,
            validated_data=serializer.validated_data,
        )
        response_serializer = self.get_serializer(contact)
        return api_success(
            data=response_serializer.data,
            message="Contact created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contact = ContactService.update_contact(
            contact=instance,
            user=request.user,
            validated_data=serializer.validated_data,
        )
        response_serializer = self.get_serializer(contact)
        return api_success(
            data=response_serializer.data,
            message="Contact updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        ContactService.delete_contact(contact=instance, user=request.user)
        return api_success(
            message="Contact deleted successfully.",
            status_code=status.HTTP_200_OK,
        )
