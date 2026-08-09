"""The single write path for audit records (FR-113).

Services record an audit entry through :func:`record_audit` so every row gets
the current request id and actor from the request context without threading
the request object through the call stack.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType

from apps.audit.middleware import get_actor_id, get_request_id
from apps.audit.models import AuditLog

MAX_OBJECT_REPR_LENGTH = 200


def record_audit(actor, action: str, obj, changes: dict | None = None, request_id: str | None = None) -> AuditLog:
    """Append one immutable AuditLog row describing a mutation of ``obj``.

    ``request_id`` and ``actor`` fall back to the request context when not
    given explicitly, so callers deep in the stack still record correctly.
    """
    if actor is None:
        actor_id = get_actor_id()
        if actor_id is not None:
            from django.apps import apps

            actor = apps.get_model("accounts.User").objects.filter(pk=actor_id).first()

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        content_type=ContentType.objects.get_for_model(obj) if obj is not None else None,
        object_id=str(obj.pk) if obj is not None else "",
        object_repr=str(obj)[:MAX_OBJECT_REPR_LENGTH] if obj is not None else "",
        changes=changes or {},
        request_id=request_id if request_id is not None else (get_request_id() or ""),
    )
