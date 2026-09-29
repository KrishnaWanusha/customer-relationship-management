from rest_framework import serializers
from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "organization",
            "user",
            "user_email",
            "user_name",
            "action",
            "model_name",
            "object_id",
            "details",
            "timestamp",
        ]
        read_only_fields = fields

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return "System"

    def get_user_name(self, obj):
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.email
        return "System"
