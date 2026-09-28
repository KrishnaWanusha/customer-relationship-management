from rest_framework import serializers


class TenantModelSerializer(serializers.ModelSerializer):
    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()
        kwargs.setdefault("organization", {})
        kwargs["organization"]["read_only"] = True
        return kwargs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["organization"] = request.user.organization
        return super().create(validated_data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return attrs

        user_org_id = getattr(request.user, "organization_id", None)
        for field_name, value in attrs.items():
            if value and hasattr(value, "organization_id"):
                if value.organization_id != user_org_id:
                    raise serializers.ValidationError(
                        {field_name: ["Referenced record does not belong to your organization."]}
                    )
        return attrs
