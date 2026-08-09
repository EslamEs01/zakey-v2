"""Append-only audit log for every staff mutation (FR-113, FR-114, INV-013).

Immutability is enforced in code, not by convention: ``save()`` and ``delete()``
are overridden so a persisted row can never be updated or removed — not by
staff, not by superusers, not by any ORM path. That is stronger than a
permission flag, which could be granted.
"""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.db import models


class ImmutableRecordError(ValidationError):
    """Raised when an AuditLog row is updated or deleted (FR-114, INV-013)."""


class AuditAction(models.TextChoices):
    CREATE = "create", "إنشاء"
    UPDATE = "update", "تعديل"
    DELETE = "delete", "حذف"
    ARCHIVE = "archive", "أرشفة"
    STATUS_CHANGE = "status_change", "تغيير حالة"
    STOCK_ADJUST = "stock_adjust", "تسوية مخزون"
    PRICE_CHANGE = "price_change", "تغيير سعر"
    PAYMENT_RECORD = "payment_record", "تسجيل دفعة"
    REFUND = "refund", "استرجاع"
    PERMISSION_CHANGE = "permission_change", "تغيير صلاحيات"
    LOGIN = "login", "دخول"
    LOGIN_FAILED = "login_failed", "محاولة دخول فاشلة"
    LOGOUT = "logout", "خروج"
    PERMISSION_DENIED = "permission_denied", "رفض صلاحية"


class AuditLog(models.Model):
    """One immutable record per auditable mutation.

    Intentionally does NOT inherit TimeStampedModel: an immutable row has no
    ``updated_at``, and the absence of an update path is the feature.
    """

    actor = models.ForeignKey(
        "accounts.User",
        verbose_name="المنفّذ",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(
        "الإجراء", max_length=32, choices=AuditAction.choices, db_index=True
    )
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        verbose_name="نوع المحتوى",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    object_id = models.CharField("معرّف العنصر", max_length=64, blank=True, default="")
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.CharField("عنوان العنصر", max_length=255, blank=True, default="")
    changes = models.JSONField(
        "التغييرات",
        default=dict,
        blank=True,
        help_text="القيم قبل وبعد التعديل مع حذف الحقول الحساسة.",
    )
    request_id = models.CharField("معرّف الطلب", max_length=64, blank=True, default="")
    ip_hash = models.CharField(
        "بصمة عنوان IP",
        max_length=64,
        blank=True,
        default="",
        help_text="هاش فقط؛ لا يُخزَّن عنوان IP الخام أبدًا.",
    )
    created_at = models.DateTimeField("أنشئ في", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "سجل تدقيق"
        verbose_name_plural = "سجل التدقيق"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["content_type", "object_id", "-created_at"],
                name="audit_object_time_idx",
            ),
            models.Index(fields=["action", "-created_at"], name="audit_action_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_action_display()} — {self.object_repr or self.object_id}"

    def save(self, *args, **kwargs):
        # Append-only contract: a persisted row has no update path, and no
        # caller is exempt — superusers included (INV-013).
        if self.pk is not None:
            raise ImmutableRecordError("سجلات التدقيق غير قابلة للتعديل.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableRecordError("سجلات التدقيق غير قابلة للحذف.")
