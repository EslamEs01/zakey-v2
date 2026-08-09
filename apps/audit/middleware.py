"""Request correlation for audit records and logs (FR-113, FR-115).

A single request id ties an AuditLog row to the log lines it produced. Stored in
a ContextVar so services deep in the call stack can record it without threading
the request object through every signature.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Callable

from django.http import HttpRequest, HttpResponse

_request_id: ContextVar[str | None] = ContextVar("zakey_request_id", default=None)
_actor_id: ContextVar[int | None] = ContextVar("zakey_actor_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def get_actor_id() -> int | None:
    return _actor_id.get()


class RequestIDMiddleware:
    """Assign a request id and remember the acting user for the request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = uuid.uuid4().hex
        request.request_id = request_id
        id_token = _request_id.set(request_id)

        user = getattr(request, "user", None)
        actor_id = user.pk if user is not None and user.is_authenticated else None
        actor_token = _actor_id.set(actor_id)
        try:
            response = self.get_response(request)
        finally:
            _request_id.reset(id_token)
            _actor_id.reset(actor_token)
        return response
