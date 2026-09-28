from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "industry",
        "country",
        "is_deleted",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_deleted", "organization", "industry", "country")
    search_fields = ("name", "industry", "country", "phone")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")

    def get_queryset(self, request):
        return Company.all_objects.all()
