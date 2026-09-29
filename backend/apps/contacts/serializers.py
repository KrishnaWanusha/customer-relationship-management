from rest_framework import serializers
from apps.companies.models import Company
from common.serializers import TenantModelSerializer
from .models import Contact, validate_phone_digits


class ContactSerializer(TenantModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    class Meta:
        model = Contact
        fields = [
            "id",
            "company",
            "company_name",
            "organization",
            "full_name",
            "email",
            "phone",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "company_name",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "full_name": {"required": True, "allow_blank": False},
        }

    def validate_full_name(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Full name is required.")
        return stripped

    def validate_phone(self, value):
        if value:
            validate_phone_digits(value)
        return value

    def validate_company(self, value):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            user_org_id = getattr(request.user, "organization_id", None)
            if value.organization_id != user_org_id:
                raise serializers.ValidationError("Selected company does not belong to your organization.")
        if getattr(value, "is_deleted", False):
            raise serializers.ValidationError("Cannot associate contact with a deleted company.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        company = attrs.get("company", getattr(self.instance, "company", None))
        email = attrs.get("email", getattr(self.instance, "email", None))

        if company and email:
            normalized_email = email.strip()
            qs = Contact.objects.filter(
                company=company,
                email__iexact=normalized_email,
                is_deleted=False,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"email": "A contact with this email already exists for this company."}
                )

        return attrs
