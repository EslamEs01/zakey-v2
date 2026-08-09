"""Dashboard wiring for the admin index (T-1308, FR-101, FR-102).

The default ``AdminSite`` class is swapped rather than a new site instantiated,
so every existing ``@admin.register(...)`` keeps working untouched. Registering
a second site would mean re-registering thirty model admins and would leave two
divergent admins to maintain.

The widgets are computed in :meth:`ZakeyAdminSite.index` only — deliberately not
in ``each_context``, which runs on *every* admin page. Eleven aggregate queries
belong on the dashboard, not on every changelist and every change form.
"""

from __future__ import annotations

from django.contrib import admin


class ZakeyAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        from apps.core.dashboard import dashboard_widgets

        context = dict(extra_context or {})
        try:
            # Filtered by the viewer: the dashboard must obey the same role
            # matrix as the changelists it links to (FR-111).
            context["zakey_widgets"] = dashboard_widgets(request.user)
        except Exception:  # pragma: no cover - defensive
            # A dashboard that cannot render must not lock staff out of the
            # admin entirely; the page degrades to Django's stock index.
            context["zakey_widgets"] = []
        return super().index(request, extra_context=context)


def install() -> None:
    """Adopt the dashboard on the default admin site."""
    admin.site.__class__ = ZakeyAdminSite
    admin.site.index_template = "admin/zakey_index.html"
