from rest_framework import serializers
from common.serializers import TenantModelSerializer
from .models import Company


class CompanySerializer(TenantModelSerializer):
    contacts_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "industry",
            "country",
            "logo",
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
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Company name is required.")
        return stripped
