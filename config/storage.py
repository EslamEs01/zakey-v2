"""Static file storage for production (FR-004).

Hashed, manifest-backed static files, with strict lookup disabled.

``ManifestStaticFilesStorage`` raises ``ValueError`` when ``{% static %}`` names
something the manifest does not contain. That is the behaviour we want for our
own templates — a typo in an asset path should fail loudly rather than ship a
broken page — but django-jazzmin's ``admin/base.html`` renders

    data-theme-base="{% static 'vendor/bootswatch' %}"

which names a *directory*, not a file. A directory is never a manifest entry, so
every Django admin page raised ``ValueError: Missing staticfiles manifest entry
for 'vendor/bootswatch'`` and returned 500 — while the storefront, which only
references real files, was fine. The attribute is read by Jazzmin's client-side
theme switcher, which appends the theme name to it; it is a URL prefix and was
never meant to resolve on its own.

Development uses a non-hashing storage, so this only ever appeared in
production.

``manifest_strict = False`` makes an unknown name fall through to the unhashed
path instead of raising. The trade-off is deliberate: a missing asset now 404s
rather than 500ing the whole page. Collection itself is unaffected —
``collectstatic`` still post-processes and rewrites every reference inside the
CSS it collects, so a genuinely broken stylesheet reference still fails the
deploy at build time rather than silently reaching a customer.
"""

from __future__ import annotations

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ZakeyManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """Manifest storage that tolerates a third-party directory reference."""

    manifest_strict = False
