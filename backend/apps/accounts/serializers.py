from django.contrib.auth import authenticate
from rest_framework import serializers
from apps.organizations.models import Organization
from .models import User


class OrganizationSimpleSerializer(serializers.ModelSerializer):
    plan = serializers.CharField(source="subscription_plan", read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "subscription_plan", "plan", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSimpleSerializer(read_only=True)
    can_delete = serializers.BooleanField(read_only=True)
    can_view_activity_logs = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "organization",
            "can_delete",
            "can_view_activity_logs",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "can_delete", "can_view_activity_logs"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not user:
            raise serializers.ValidationError({"non_field_errors": ["Invalid email or password."]})
        if not user.is_active:
            raise serializers.ValidationError({"non_field_errors": ["User account is disabled."]})

        attrs["user"] = user
        return attrs
