import uuid
from django.db import models
from django_multitenant.mixins import TenantModelMixin
from common.models import SoftDeleteModel, TenantSoftDeleteManager


class Company(TenantModelMixin, SoftDeleteModel):
    tenant_id = "organization_id"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="companies",
    )
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    website = models.URLField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)

    objects = TenantSoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "companies"
        indexes = [
            models.Index(fields=["organization", "is_deleted"]),
        ]

    def __str__(self):
        return self.name
