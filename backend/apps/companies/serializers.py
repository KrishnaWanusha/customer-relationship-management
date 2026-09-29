from rest_framework import serializers
from common.serializers import TenantModelSerializer
from .models import Company
from .validators import validate_company_logo


class CompanySerializer(TenantModelSerializer):
    contacts_count = serializers.IntegerField(read_only=True, default=0)
    logo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "industry",
            "country",
            "logo",
            "logo_url",
            "website",
            "phone",
            "address",
            "organization",
            "contacts_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "contacts_count",
            "logo_url",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Company name is required.")
        return stripped

    def validate_logo(self, value):
        if value:
            validate_company_logo(value)
        return value

    def get_logo_url(self, obj):
        url = obj.get_logo_url()
        if not url:
            return None
        request = self.context.get("request")
        if request is not None and not url.startswith("http"):
            return request.build_absolute_uri(url)
        return url

