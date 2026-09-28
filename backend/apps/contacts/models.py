from django.core.exceptions import ValidationError
from django.db import models
from common.models import SoftDeleteModel


class Contact(SoftDeleteModel):
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
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "email"],
                condition=models.Q(is_deleted=False),
                name="unique_active_contact_email_per_company",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        super().clean()
        if self.company_id and self.organization_id and self.company.organization_id != self.organization_id:
            raise ValidationError("Contact organization must match the company organization.")

    def save(self, *args, **kwargs):
        if self.company_id and not self.organization_id:
            self.organization_id = self.company.organization_id
        self.clean()
        super().save(*args, **kwargs)
