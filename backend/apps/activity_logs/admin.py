from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "organization", "user", "action", "model_name", "object_id")
    list_filter = ("action", "model_name", "organization", "timestamp")
    search_fields = ("model_name", "object_id", "user__email")
    readonly_fields = ("organization", "user", "action", "model_name", "object_id", "details", "timestamp")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
