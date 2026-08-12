"""Storefront content administration (FR-096 - FR-098)."""

from __future__ import annotations

from django.contrib import admin

from import_export.admin import ExportMixin, ImportExportModelAdmin

from apps.core.admin_mixins import AuditedImportExportMixin
from apps.core.resources import (
    ContactMessageResource,
    FAQResource,
    NavigationItemResource,
    NewsletterSubscriptionResource,
    StaticPageResource,
)

from .models import (
    FAQ,
    Banner,
    ContactMessage,
    HomeSection,
    NavigationItem,
    NewsletterSubscription,
    Partner,
    StaticPage,
)


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ("key", "heading", "position", "is_active")
    list_editable = ("position", "is_active")


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "position", "is_active", "starts_at", "ends_at")
    list_editable = ("position", "is_active")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "is_active")
    list_editable = ("position", "is_active")


@admin.register(FAQ)
class FAQAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (FAQResource,)
    list_display = ("question", "page", "position", "is_active")
    list_filter = ("page", "is_active")
    search_fields = ("question", "answer")
    filter_horizontal = ("products",)


@admin.register(StaticPage)
class StaticPageAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (StaticPageResource,)
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug")


@admin.register(NavigationItem)
class NavigationItemAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (NavigationItemResource,)
    list_display = ("label", "group", "href", "position", "is_active")
    list_filter = ("group", "is_active")
    list_editable = ("position", "is_active")


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = (NewsletterSubscriptionResource,)
    list_display = ("email", "source", "confirmed", "created_at")
    list_filter = ("confirmed",)
    search_fields = ("email",)
    readonly_fields = ("email", "source", "ip_hash", "created_at", "updated_at")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = (ContactMessageResource,)
    list_display = ("subject", "name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "email", "subject", "message")
    date_hierarchy = "created_at"
    # Submitted content is never edited, only triaged.
    readonly_fields = ("name", "email", "phone", "subject", "message", "ip_hash", "created_at", "updated_at")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False
