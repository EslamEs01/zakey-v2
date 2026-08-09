"""Reusable admin guards (FR-105, FR-109, FR-114).

Sensitive records are protected by the **absence of a mutation path**, not by a
permission flag that could later be granted.
"""

from __future__ import annotations

from django.contrib import admin


class AppendOnlyAdmin(admin.ModelAdmin):
    """Read-only ledger: viewable, never added, changed or deleted.

    Used for StockMovement, PaymentEvent, OrderEvent and AuditLog (INV-013).
    """

    def has_add_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False


class ReadOnlyInline(admin.TabularInline):
    extra = 0
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False


class NoDeleteAdmin(admin.ModelAdmin):
    """Orders are cancelled, never deleted."""

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False


class AuditedImportExportMixin:
    """Attach the acting staff member to an import so it can be audited.

    ``django-import-export`` builds the resource without a request, so the actor
    has to be handed to it explicitly; otherwise every bulk edit lands in the
    audit log with no name against it.
    """

    def get_import_resource_classes(self, request=None):  # noqa: D102
        classes = super().get_import_resource_classes(request)
        actor = getattr(request, "user", None)
        for resource_class in classes:
            resource_class._actor = actor if getattr(actor, "is_authenticated", False) else None
        return classes


class ArchivableAdmin(admin.ModelAdmin):
    """Admin surface for the archive-not-delete policy (FR-014, FR-109).

    Deletion from the admin is routed through the guarded service so a record
    that history depends on is refused with the Arabic archive hint rather than
    a raw ``ProtectedError`` page, and so every completed deletion leaves an
    audit row naming who did it.

    Archiving and restoring are exposed as actions rather than as an editable
    ``status`` dropdown, because only the service pair keeps ``archived_at``
    consistent with ``status`` and writes the audit trail.
    """

    actions = ("archive_selected", "restore_selected")

    # -- deletion ---------------------------------------------------------
    def delete_model(self, request, obj) -> None:
        from django.contrib import messages
        from django.core.exceptions import ValidationError

        from apps.catalog.services import guarded_delete

        try:
            guarded_delete(obj, actor=request.user)
        except ValidationError as error:
            # Reported, not raised: the admin has already committed to a
            # redirect by this point, and a 500 would tell staff nothing.
            self.message_user(request, "; ".join(error.messages), level=messages.ERROR)

    def delete_queryset(self, request, queryset) -> None:
        from django.contrib import messages
        from django.core.exceptions import ValidationError

        from apps.catalog.services import guarded_delete

        refused = 0
        for obj in queryset:
            try:
                guarded_delete(obj, actor=request.user)
            except ValidationError:
                refused += 1
        if refused:
            self.message_user(
                request,
                f"تُرك {refused} سجلًا دون حذف لارتباطه بطلبات؛ استخدم الأرشفة بدلًا من ذلك.",
                level=messages.ERROR,
            )

    # -- actions ----------------------------------------------------------
    @admin.action(description="أرشفة المحدد")
    def archive_selected(self, request, queryset) -> None:
        from apps.catalog.services import bulk_archive

        count = bulk_archive(queryset, actor=request.user)
        self.message_user(request, f"تمت أرشفة {count} سجلًا.")

    @admin.action(description="استعادة المحدد كمسودة")
    def restore_selected(self, request, queryset) -> None:
        from apps.catalog.services import bulk_restore

        count = bulk_restore(queryset, actor=request.user)
        self.message_user(request, f"تمت استعادة {count} سجلًا كمسودة.")

    def get_actions(self, request):
        """Hide the lifecycle actions from staff who cannot change the model.

        Hiding is presentation only — :meth:`archive_selected` and
        :meth:`restore_selected` are still reached through Django's own action
        permission checks, so this never becomes the authorisation (FR-111).
        """
        actions = super().get_actions(request)
        if not self.has_change_permission(request):
            for name in ("archive_selected", "restore_selected"):
                actions.pop(name, None)
        return actions
