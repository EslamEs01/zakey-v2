"""Customer administration with contact masking (FR-112)."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Address, CustomerProfile, User


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ("label", "full_name", "governorate", "city", "street", "building", "is_default")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_active", "is_staff", "is_superuser", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("الصلاحيات", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تواريخ", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone_display", "email_verified", "phone_verified", "created_at")
    list_filter = ("email_verified", "phone_verified", "accepts_marketing")
    search_fields = ("full_name", "user__email", "phone")
    readonly_fields = ("created_at", "updated_at")
    inlines = (AddressInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    @admin.display(description="البريد")
    def email(self, obj):
        return obj.user.email

    @admin.display(description="الموبايل")
    def phone_display(self, obj):
        """Masked unless the viewer holds accounts.view_full_contact (FR-112)."""
        request = getattr(self, "_request", None)
        if request is not None and request.user.has_perm("accounts.view_full_contact"):
            return obj.phone
        return obj.masked_phone

    def changelist_view(self, request, extra_context=None):
        self._request = request
        return super().changelist_view(request, extra_context)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("customer", "label", "governorate", "city", "is_default")
    list_filter = ("governorate", "is_default")
    search_fields = ("customer__full_name", "city", "street")
    autocomplete_fields = ("customer",)
