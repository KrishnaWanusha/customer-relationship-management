from django.contrib import admin
from apps.contacts.models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "company", "organization", "is_deleted", "created_at")
    list_filter = ("is_deleted", "organization", "company")
    search_fields = ("first_name", "last_name", "email", "phone")

    def get_queryset(self, request):
        return Contact.all_objects.all()
