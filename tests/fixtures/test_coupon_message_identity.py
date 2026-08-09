"""The coupon rejection message is the prototype's own (FR-086, T-1608).

FR-086 requires an exhausted or expired coupon to fail closed **with the
existing Arabic rejection message** — not with a new string that happens to
sound similar. Proving "existing" means comparing against the approved dataset,
which is the one thing `apps/` is forbidden to read: `RUNTIME_ROOTS` in
`tests/test_backend_boundary.py` blocks any module under `apps/`, `storefront/`
or `config/` from naming the dataset, so that `fixture_provider.py` cannot
quietly come back as a request-time source of truth.

So this assertion lives here, under `tests/`, where reading the dataset as a
**test oracle** is exactly what it is for. The behavioural half of FR-086 — that
both refusals actually raise that message — stays in
`apps/core/tests/test_coupon_rules.py::TestExhaustedOrExpiredFailsClosed`.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings

from apps.promotions.services import REJECTED_MESSAGE

DATASET = Path(settings.BASE_DIR, "apps/core/seed_data/approved-catalogue.json")


def test_the_rejection_message_is_the_label_the_approved_prototype_already_shows():
    """FR-086: `REJECTED_MESSAGE` is `site.couponPrototype.rejectedLabel`, verbatim.

    Both halves matter. Comparing against the dataset proves the string was
    inherited rather than invented; pinning the literal proves the dataset itself
    was not edited to match a string someone changed in the code.
    """
    payload = json.loads(DATASET.read_text(encoding="utf-8"))

    assert REJECTED_MESSAGE == payload["site"]["couponPrototype"]["rejectedLabel"]
    assert REJECTED_MESSAGE == "الكود غير صالح في العرض التجريبي."
