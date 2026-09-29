from django.db import models
from django.utils.text import slugify
from django_multitenant.mixins import TenantModelMixin


class Organization(TenantModelMixin, models.Model):
    tenant_id = "id"

    class SubscriptionPlan(models.TextChoices):
        BASIC = "Basic", "Basic"
        PRO = "Pro", "Pro"

    Plan = SubscriptionPlan

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    subscription_plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.BASIC,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.name)

    @property
    def plan(self):
        return self.subscription_plan

    @plan.setter
    def plan(self, value):
        self.subscription_plan = value

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "org"
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
