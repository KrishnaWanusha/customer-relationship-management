import django_filters
from .models import Contact


class ContactFilter(django_filters.FilterSet):
    full_name = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="icontains")
    company = django_filters.UUIDFilter(field_name="company_id")
    role = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Contact
        fields = ["full_name", "email", "company", "role"]
