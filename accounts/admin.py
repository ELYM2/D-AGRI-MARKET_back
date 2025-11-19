from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_seller", "business_name", "phone", "city")
    list_filter = ("is_seller",)
    search_fields = ("user__username", "user__email", "business_name", "phone")
    fieldsets = (
        ("Informations utilisateur", {
            "fields": ("user", "phone", "address", "city", "postal_code")
        }),
        ("Informations vendeur", {
            "fields": (
                "is_seller",
                "business_name",
                "business_description",
                "business_address",
                "business_city",
                "business_postal_code",
                "total_sales"
            )
        }),
    )
    readonly_fields = ("total_sales",)
