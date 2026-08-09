"""Log redaction (FR-007, NFR-012, threat T-13).

Personal data and secrets must never reach a log sink. This filter scrubs the
formatted message and injects the per-request id so log lines are correlatable
without carrying identifying data.
"""

from __future__ import annotations

import logging
import re

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Egyptian mobile numbers -> keep the operator prefix and last two digits.
    (re.compile(r"\b(01[0125])\d{6}(\d{2})\b"), r"\1******\2"),
    # Email addresses -> keep first character and domain.
    (re.compile(r"\b([A-Za-z0-9])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"), r"\1***@\2"),
    # Auth headers, scheme included. This runs *before* the generic rule below
    # because that one stops at the first whitespace: given
    # ``Authorization: Bearer <token>`` it would redact the word "Bearer" and
    # leave the token itself in the clear, which is the whole thing worth hiding.
    (
        re.compile(
            r"(?i)\b(authorization|proxy-authorization)\b(\s*[=:]\s*)"
            r"(?:bearer|basic|digest|token)?\s*\S+"
        ),
        r"\1\2[REDACTED]",
    ),
    # A bearer token written without the header name is still a bearer token.
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"), "bearer [REDACTED]"),
    # Anything that looks like a secret assignment.
    (
        re.compile(
            # ``cvv``/``cvc``/``card_number`` are here because FR-077 names them
            # explicitly. A CVV is only three digits, so it survives the
            # card-length rule below — without its own pattern it would reach
            # the log intact, which is the single worst thing this filter could
            # let through.
            r"(?i)\b(password|passwd|secret|token|api[_-]?key|csrftoken|sessionid"
            r"|cvv|cvc|security[_-]?code|card[_-]?number|pan|cardholder)"
            r"\b(\s*[=:]\s*)(\"[^\"]*\"|'[^']*'|\S+)"
        ),
        r"\1\2[REDACTED]",
    ),
    # Long digit runs (card-like) never belong in a log (FR-077).
    (re.compile(r"\b\d{13,19}\b"), "[REDACTED-NUMBER]"),
)


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            from apps.audit.middleware import get_request_id

            record.request_id = get_request_id() or "-"
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - never let logging break a request
            return True
        redacted = redact(message)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True
