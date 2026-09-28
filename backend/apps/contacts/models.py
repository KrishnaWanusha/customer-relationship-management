import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django_multitenant.mixins import TenantModelMixin
from common.models import SoftDeleteModel, TenantSoftDeleteManager


def validate_phone_digits(value):
    if not value:
        return
    digits = [c for c in value if c.isdigit()]
    if not (8 <= len(digits) <= 15):
        raise ValidationError("Phone number must contain between 8 and 15 digits.")


class Contact(TenantModelMixin, SoftDeleteModel):
    tenant_id = "organization_id"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    full_name = models.CharField(max_length=255, default="")
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=50, blank=True, validators=[validate_phone_digits])
    role = models.CharField(max_length=100, blank=True)

    objects = TenantSoftDeleteManager()
    all_objects = models.Manager()

    def __init__(self, *args, **kwargs):
        first_name = kwargs.pop("first_name", None)
        last_name = kwargs.pop("last_name", None)
        position = kwargs.pop("position", None)
        if "full_name" not in kwargs and (first_name or last_name):
            kwargs["full_name"] = f"{first_name or ''} {last_name or ''}".strip()
        if "role" not in kwargs and position:
            kwargs["role"] = position
        super().__init__(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "is_deleted"]),
            models.Index(fields=["company", "is_deleted"]),
            models.Index(fields=["email"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "email"],
                condition=models.Q(is_deleted=False),
                name="unique_active_contact_email_per_company",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def first_name(self):
        parts = self.full_name.split(None, 1)
        return parts[0] if parts else ""

    @property
    def last_name(self):
        parts = self.full_name.split(None, 1)
        return parts[1] if len(parts) > 1 else ""

    @property
    def position(self):
        return self.role

    def clean(self):
        super().clean()
        if self.phone:
            validate_phone_digits(self.phone)
        if self.company_id and self.organization_id and self.company.organization_id != self.organization_id:
            raise ValidationError("Contact organization must match the company organization.")
        if self.company_id and self.email:
            qs = Contact.objects.filter(
                company_id=self.company_id,
                email__iexact=self.email.strip(),
                is_deleted=False,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"email": "A contact with this email already exists for this company."})

    def save(self, *args, **kwargs):
        if self.company_id and not self.organization_id:
            self.organization_id = self.company.organization_id
        super().save(*args, **kwargs)
