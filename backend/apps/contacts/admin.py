from django.contrib import admin
from apps.contacts.models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "role",
        "company",
        "organization",
        "phone",
        "is_deleted",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_deleted", "organization", "company", "role")
    search_fields = ("full_name", "email", "phone", "role")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")

    def get_queryset(self, request):
        return Contact.all_objects.all()
