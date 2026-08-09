"""Storefront content administration (FR-096 - FR-098)."""

from __future__ import annotations

from django.contrib import admin

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
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "page", "position", "is_active")
    list_filter = ("page", "is_active")
    search_fields = ("question", "answer")
    filter_horizontal = ("products",)


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug")


@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ("label", "group", "href", "position", "is_active")
    list_filter = ("group", "is_active")
    list_editable = ("position", "is_active")


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "source", "confirmed", "created_at")
    list_filter = ("confirmed",)
    search_fields = ("email",)
    readonly_fields = ("email", "source", "ip_hash", "created_at", "updated_at")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "email", "subject", "message")
    date_hierarchy = "created_at"
    # Submitted content is never edited, only triaged.
    readonly_fields = ("name", "email", "phone", "subject", "message", "ip_hash", "created_at", "updated_at")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False
