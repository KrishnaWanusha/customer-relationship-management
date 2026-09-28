from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "industry", "phone", "is_deleted", "created_at")
    list_filter = ("is_deleted", "organization", "industry")
    search_fields = ("name", "industry", "phone")

    def get_queryset(self, request):
        return Company.all_objects.all()
