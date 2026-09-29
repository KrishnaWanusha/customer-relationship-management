import os
import uuid
from django.db import models
from django_multitenant.mixins import TenantModelMixin
from common.models import SoftDeleteModel, TenantSoftDeleteManager
from .validators import validate_company_logo


def company_logo_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".png"

    org_id = str(instance.organization_id) if getattr(instance, "organization_id", None) else "unassigned"
    company_id = str(instance.id) if getattr(instance, "id", None) else uuid.uuid4().hex
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"organizations/{org_id}/companies/{company_id}/logos/{safe_name}"


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
    logo = models.ImageField(
        upload_to=company_logo_upload_path,
        validators=[validate_company_logo],
        null=True,
        blank=True,
    )
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

    def get_logo_url(self):
        if not self.logo:
            return None
        try:
            return self.logo.url
        except Exception:
            return None
