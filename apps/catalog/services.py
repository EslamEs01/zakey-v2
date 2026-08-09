"""Catalogue lifecycle services (FR-014, FR-109).

Anything an order can reference is **archived, not deleted**, so order history
stays truthful when the catalogue moves on (FR-067). Deletion of such a record
is blocked twice: once here with a clear Arabic message, and once at the
database by ``on_delete=PROTECT`` foreign keys, so the guard holds even against
a shell session or a careless staff action.

Archiving and deleting are different operations and the distinction is
load-bearing:

* **Archiving** is always allowed. It is a status change, so every foreign key
  a purchase depends on survives it, and history keeps resolving.
* **Deleting** is allowed only while nothing historical points at the record.
  ``PROTECT`` decides that, not this module — this module only translates the
  database's refusal into a message a human can act on.

Restoring is deliberately asymmetric with archiving: a restored record comes
back as a **draft**, never straight back to published. Un-archiving something
should not silently re-expose it to customers; a human has to publish it again.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services import record_audit
from apps.core.models import PublicationStatus

_ARCHIVE_HINT = "لا يمكن حذف سجل مرتبط بطلبات؛ قم بأرشفته بدلًا من حذفه (FR-109)."


def archivable_models() -> tuple[type, ...]:
    """Every entity the archive-not-delete policy governs (FR-014).

    Derived from the model layer rather than hand-listed, so a new
    ``PublishableModel`` subclass is covered the day it is added instead of the
    day someone remembers to update a constant.
    """
    from apps.core.models import PublishableModel

    from . import models as catalog_models

    return tuple(
        candidate
        for candidate in vars(catalog_models).values()
        if isinstance(candidate, type)
        and issubclass(candidate, PublishableModel)
        and not candidate._meta.abstract
    )


def _assert_archivable(obj) -> None:
    from apps.core.models import PublishableModel

    if not isinstance(obj, PublishableModel):
        raise ValidationError(
            f"{obj._meta.verbose_name} لا يدعم الأرشفة؛ استخدم حذفًا محروسًا بدلًا من ذلك."
        )


# ---------------------------------------------------------------------------
# Guarded deletion
# ---------------------------------------------------------------------------


def guarded_delete(obj, *, actor=None) -> None:
    """Delete a record only when history does not depend on it (FR-109).

    This is the single sanctioned delete entry point for catalogue records. It
    surfaces the database's PROTECT as a clear, Arabic, archive-offering
    message instead of a raw integrity error. A record referenced by any order,
    cart or reservation is rejected and left completely untouched.

    The audit row is written *before* the delete, inside the same transaction,
    because afterwards there is no object left to describe. A refused delete
    rolls that row back with everything else, so the log records deletions that
    happened, not deletions that were attempted.
    """
    label = str(obj)
    try:
        with transaction.atomic():
            record_audit(
                actor,
                AuditAction.DELETE,
                obj,
                {"model": obj._meta.label, "repr": label},
            )
            obj.delete()
    except ProtectedError as exc:
        raise ValidationError(_ARCHIVE_HINT) from exc


def delete_product(product, *, actor=None) -> None:
    """Backwards-compatible alias for :func:`guarded_delete`."""
    guarded_delete(product, actor=actor)


# ---------------------------------------------------------------------------
# Archiving and restoration
# ---------------------------------------------------------------------------


@transaction.atomic
def archive(obj, *, actor=None) -> None:
    """Archive a record in place of deleting it (FR-014).

    Always allowed, including for records referenced by orders, because history
    reads snapshot columns rather than the live catalogue. The record keeps its
    primary key, its slug and every relation, and simply leaves the published
    facade (FR-013).
    """
    _assert_archivable(obj)
    if obj.status == PublicationStatus.ARCHIVED:
        return

    previous = obj.status
    obj.status = PublicationStatus.ARCHIVED
    obj.archived_at = timezone.now()
    obj.save(update_fields=["status", "archived_at", "updated_at"])
    record_audit(
        actor,
        AuditAction.ARCHIVE,
        obj,
        {"status": {"from": previous, "to": PublicationStatus.ARCHIVED}},
    )


@transaction.atomic
def restore(obj, *, actor=None) -> None:
    """Bring an archived record back as a **draft** (FR-014).

    Never straight back to published: the person restoring it has to decide,
    explicitly, that customers should see it again.
    """
    _assert_archivable(obj)
    if obj.status != PublicationStatus.ARCHIVED:
        raise ValidationError("لا يمكن استعادة سجل غير مؤرشف.")

    obj.status = PublicationStatus.DRAFT
    obj.archived_at = None
    obj.save(update_fields=["status", "archived_at", "updated_at"])
    record_audit(
        actor,
        AuditAction.STATUS_CHANGE,
        obj,
        {"status": {"from": PublicationStatus.ARCHIVED, "to": PublicationStatus.DRAFT}},
    )


def archive_product(product, *, actor=None) -> None:
    """Backwards-compatible alias for :func:`archive`."""
    archive(product, actor=actor)


def _locked(queryset):
    """Re-query ``queryset``'s rows by primary key, then lock them.

    Callers hand us whatever queryset they already had — the admin's, for
    instance, which carries ``select_related("category", "brand")``. ``brand``
    is nullable, so that is a LEFT OUTER JOIN, and PostgreSQL refuses
    ``SELECT ... FOR UPDATE`` on the nullable side of one. Reducing to bare
    primary keys first drops every inherited join, so the lock is taken on the
    rows we are actually about to write and nothing else.
    """
    model = queryset.model
    return model._base_manager.filter(
        pk__in=list(queryset.values_list("pk", flat=True))
    ).select_for_update()


@transaction.atomic
def bulk_archive(queryset, *, actor=None) -> int:
    """Archive a queryset in one guarded operation (FR-014).

    Guarded rather than raw: rows are locked and archived one at a time through
    :func:`archive`, so each one gets its own audit record. A raw
    ``QuerySet.update()`` would be faster and would leave no evidence of who
    archived what.
    """
    records = list(_locked(queryset))
    for record in records:
        archive(record, actor=actor)
    return len(records)


def bulk_archive_products(queryset, *, actor=None) -> int:
    """Backwards-compatible alias for :func:`bulk_archive`."""
    return bulk_archive(queryset, actor=actor)


@transaction.atomic
def bulk_restore(queryset, *, actor=None) -> int:
    """Restore every archived record in ``queryset`` as a draft."""
    records = [
        record
        for record in _locked(queryset)
        if record.status == PublicationStatus.ARCHIVED
    ]
    for record in records:
        restore(record, actor=actor)
    return len(records)
