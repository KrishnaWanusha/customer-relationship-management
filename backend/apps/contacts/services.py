from django.db import transaction
from apps.activity_logs.services import AuditService
from .models import Contact


class ContactService:
    @staticmethod
    @transaction.atomic
    def create_contact(*, organization, user, validated_data):
        contact = Contact.objects.create(organization=organization, **validated_data)
        AuditService.log_create(
            instance=contact,
            user=user,
            details={
                "full_name": contact.full_name,
                "email": contact.email,
                "company_id": str(contact.company_id),
                "company_name": contact.company.name,
            },
        )
        return contact

    @staticmethod
    @transaction.atomic
    def update_contact(*, contact, user, validated_data):
        changes = AuditService.apply_changes(contact, validated_data)
        if changes:
            contact.save()
            AuditService.log_update(
                instance=contact,
                user=user,
                changes=changes,
            )
        return contact

    @staticmethod
    @transaction.atomic
    def delete_contact(*, contact, user):
        full_name = contact.full_name
        contact.soft_delete(user=user)
        AuditService.log_delete(
            instance=contact,
            user=user,
            details={"full_name": full_name},
        )
