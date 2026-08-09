"""Egyptian mobile validation (FR-051).

Reproduces the storefront behaviour exactly so a number accepted in the browser
is accepted by the server and vice versa::

    // static/src/js/utilities/dom.js:31-39
    let digits = value.replace(/[^\\d+]/g, "");
    if (digits.startsWith("+20")) digits = `0${digits.slice(3)}`;
    else if (digits.startsWith("20") && digits.length === 12) digits = `0${digits.slice(2)}`;
    return /^01[0125]\\d{8}$/.test(digits);

Arabic-Indic and Extended Arabic-Indic digits are folded first, matching
``normalizeArabicDigits`` at static/src/js/pages/checkout.js:139-143.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

EGYPTIAN_MOBILE_RE = re.compile(r"^01[0125]\d{8}$")

_ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"
_EXTENDED_ARABIC_INDIC = "۰۱۲۳۴۵۶۷۸۹"
_DIGIT_TRANSLATION = {
    **{ord(ch): str(i) for i, ch in enumerate(_ARABIC_INDIC)},
    **{ord(ch): str(i) for i, ch in enumerate(_EXTENDED_ARABIC_INDIC)},
}

INVALID_MOBILE_MESSAGE = "اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا."


def fold_arabic_digits(value: str) -> str:
    return value.translate(_DIGIT_TRANSLATION)


def normalize_egyptian_mobile(value: str) -> str:
    """Normalise to the canonical ``01XXXXXXXXX`` form.

    Returns the best-effort normalised string; validation is a separate step so
    callers can report the original input in an error message.
    """
    if not value:
        return ""
    digits = re.sub(r"[^\d+]", "", fold_arabic_digits(str(value)))
    if digits.startswith("+20"):
        digits = "0" + digits[3:]
    elif digits.startswith("20") and len(digits) == 12:
        digits = "0" + digits[2:]
    return digits


def is_valid_egyptian_mobile(value: str) -> bool:
    return bool(EGYPTIAN_MOBILE_RE.match(normalize_egyptian_mobile(value)))


def validate_egyptian_mobile(value: str) -> None:
    """Django validator raising the storefront's Arabic message (FR-060)."""
    if not is_valid_egyptian_mobile(value):
        raise ValidationError(INVALID_MOBILE_MESSAGE, code="invalid_egyptian_mobile")
