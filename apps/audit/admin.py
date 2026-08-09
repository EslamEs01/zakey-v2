"""Audit administration — read-only for everyone, superusers included (FR-114)."""

from __future__ import annotations

from django.contrib import admin

from apps.core.admin_mixins import AppendOnlyAdmin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(AppendOnlyAdmin):
    list_display = ("created_at", "actor", "action", "object_repr", "request_id")
    list_filter = ("action", "content_type")
    search_fields = ("object_repr", "object_id", "request_id", "actor__email")
    date_hierarchy = "created_at"
    readonly_fields = (
        "actor", "action", "content_type", "object_id", "object_repr",
        "changes", "request_id", "ip_hash", "created_at",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("actor", "content_type")
