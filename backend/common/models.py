from django.conf import settings
from django.db import models
from django.utils import timezone
from django_multitenant.mixins import TenantManagerMixin, TenantModelMixin


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self, deleted_by=None):
        return self.update(
            is_deleted=True,
            deleted_at=timezone.now(),
            deleted_by=deleted_by,
        )

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)


class TenantSoftDeleteQuerySet(SoftDeleteQuerySet):
    def for_tenant(self, organization):
        if not organization:
            return self.none()
        return self.filter(organization=organization)

    def for_user(self, user):
        if not user or not user.is_authenticated or not getattr(user, "organization_id", None):
            return self.none()
        return self.filter(organization=user.organization)


class TenantSoftDeleteManager(TenantManagerMixin, SoftDeleteManager):
    _queryset_class = TenantSoftDeleteQuerySet

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()

    def deleted(self):
        return self.all_with_deleted().filter(is_deleted=True)

    def for_tenant(self, organization):
        return self._queryset_class(self.model, using=self._db).for_tenant(organization).filter(is_deleted=False)

    def for_user(self, user):
        return self._queryset_class(self.model, using=self._db).for_user(user).filter(is_deleted=False)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(TimeStampedModel):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])

    def delete(self, using=None, keep_parents=False, user=None):
        self.soft_delete(user=user)
