from django.db import transaction
from apps.activity_logs.services import AuditService
from .models import Company


class CompanyService:
    @staticmethod
    @transaction.atomic
    def create_company(*, organization, user, validated_data):
        company = Company.objects.create(organization=organization, **validated_data)
        AuditService.log_create(
            instance=company,
            user=user,
            details={
                "name": company.name,
                "industry": company.industry,
                "country": company.country,
            },
        )
        return company

    @staticmethod
    @transaction.atomic
    def update_company(*, company, user, validated_data):
        changes = AuditService.apply_changes(company, validated_data)
        if changes:
            company.save()
            AuditService.log_update(
                instance=company,
                user=user,
                changes=changes,
            )
        return company

    @staticmethod
    @transaction.atomic
    def delete_company(*, company, user):
        company_name = company.name
        company.soft_delete(user=user)
        AuditService.log_delete(
            instance=company,
            user=user,
            details={"name": company_name},
        )
