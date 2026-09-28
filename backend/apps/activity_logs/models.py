from django.conf import settings
from django.db import models
from django_multitenant.mixins import TenantModelMixin
from django_multitenant.models import TenantManager


class ActivityLog(TenantModelMixin, models.Model):
    tenant_id = "organization_id"

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=100, db_index=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["organization", "-timestamp"]),
            models.Index(fields=["model_name", "object_id"]),
        ]

    def __str__(self):
        user_display = self.user.email if self.user else "System"
        return f"{user_display} {self.action} {self.model_name} #{self.object_id}"
