from apps.activity_logs.models import ActivityLog
from apps.activity_logs.services import create_activity_log
from .models import Company


class CompanyService:
    @staticmethod
    def create_company(*, organization, user, validated_data):
        company = Company.objects.create(organization=organization, **validated_data)
        create_activity_log(
            organization=organization,
            user=user,
            action=ActivityLog.Action.CREATE,
            model_name="Company",
            object_id=str(company.id),
            details={"name": company.name, "industry": company.industry, "country": company.country},
        )
        return company

    @staticmethod
    def update_company(*, company, user, validated_data):
        changed_fields = {}
        for key, value in validated_data.items():
            old_value = getattr(company, key, None)
            if old_value != value:
                changed_fields[key] = {"old": str(old_value) if old_value is not None else None, "new": str(value) if value is not None else None}
                setattr(company, key, value)

        if changed_fields:
            company.save()
            create_activity_log(
                organization=company.organization,
                user=user,
                action=ActivityLog.Action.UPDATE,
                model_name="Company",
                object_id=str(company.id),
                details={"changed_fields": list(changed_fields.keys()), "changes": changed_fields},
            )
        return company

    @staticmethod
    def delete_company(*, company, user):
        company_id = str(company.id)
        company_name = company.name
        org = company.organization
        company.soft_delete(user=user)
        create_activity_log(
            organization=org,
            user=user,
            action=ActivityLog.Action.DELETE,
            model_name="Company",
            object_id=company_id,
            details={"name": company_name},
        )
