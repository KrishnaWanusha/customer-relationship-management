from apps.activity_logs.models import ActivityLog
from apps.activity_logs.services import create_activity_log
from .models import Contact


class ContactService:
    @staticmethod
    def create_contact(*, organization, user, validated_data):
        contact = Contact.objects.create(organization=organization, **validated_data)
        create_activity_log(
            organization=organization,
            user=user,
            action=ActivityLog.Action.CREATE,
            model_name="Contact",
            object_id=str(contact.id),
            details={
                "full_name": contact.full_name,
                "email": contact.email,
                "company_id": str(contact.company_id),
                "company_name": contact.company.name,
            },
        )
        return contact

    @staticmethod
    def update_contact(*, contact, user, validated_data):
        changed_fields = {}
        for key, value in validated_data.items():
            old_value = getattr(contact, key, None)
            if old_value != value:
                changed_fields[key] = {
                    "old": str(old_value) if old_value is not None else None,
                    "new": str(value) if value is not None else None,
                }
                setattr(contact, key, value)

        if changed_fields:
            contact.save()
            create_activity_log(
                organization=contact.organization,
                user=user,
                action=ActivityLog.Action.UPDATE,
                model_name="Contact",
                object_id=str(contact.id),
                details={"changed_fields": list(changed_fields.keys()), "changes": changed_fields},
            )
        return contact

    @staticmethod
    def delete_contact(*, contact, user):
        contact_id = str(contact.id)
        full_name = contact.full_name
        org = contact.organization
        contact.soft_delete(user=user)
        create_activity_log(
            organization=org,
            user=user,
            action=ActivityLog.Action.DELETE,
            model_name="Contact",
            object_id=contact_id,
            details={"full_name": full_name},
        )
