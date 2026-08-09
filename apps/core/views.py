"""Operational endpoints (FR-006)."""

from __future__ import annotations

from django.db import connection
from django.http import HttpRequest, JsonResponse


def healthz(request: HttpRequest) -> JsonResponse:
    """Report database connectivity without leaking any configuration."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database_ok = True
    except Exception:  # noqa: BLE001 - health checks never raise
        database_ok = False

    payload = {"status": "ok" if database_ok else "degraded", "database": database_ok}
    return JsonResponse(payload, status=200 if database_ok else 503)
