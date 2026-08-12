"""Audit administration — read-only for everyone, superusers included (FR-114)."""

from __future__ import annotations

from django.contrib import admin

from import_export.admin import ExportMixin

from apps.core.admin_mixins import AppendOnlyAdmin
from apps.core.resources import AuditLogResource

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(ExportMixin, AppendOnlyAdmin):
    resource_classes = (AuditLogResource,)
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
