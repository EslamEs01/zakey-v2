"""Dashboard wiring for the admin index (T-1308, FR-101, FR-102).

The default ``AdminSite`` class is swapped rather than a new site instantiated,
so every existing ``@admin.register(...)`` keeps working untouched. Registering
a second site would mean re-registering thirty model admins and would leave two
divergent admins to maintain.

The widgets are computed in :meth:`ZakeyAdminSite.index` only — deliberately not
in ``each_context``, which runs on *every* admin page. Eleven aggregate queries
belong on the dashboard, not on every changelist and every change form.

The attention bar follows the same rule the hard way. Work waiting on a staff
member is useless if it is only visible on a page they had to think to visit, so
it has to appear everywhere — but building it in ``each_context`` cost eight
COUNTs on a cold cache and pushed the catalogue and stock changelists past their
documented 25-query budget (T-1310). Raising that budget would have hidden a
real N+1 behind a fixed overhead, so instead the counts are served from
``zakey-alerts/`` as JSON and fetched by the page. Rendering an admin page costs
zero extra queries; the bar fills itself a moment later.
"""

from __future__ import annotations

from django.contrib import admin


class ZakeyAdminSite(admin.AdminSite):
    def get_urls(self):
        from django.urls import path

        # Prepended, not appended: the stock catch-all
        # ``<app_label>/`` route would otherwise swallow this path.
        return [
            path(
                "zakey-alerts/",
                self.admin_view(alerts_json),
                name="zakey_alerts",
            ),
            path(
                "set-language/",
                self.admin_view(set_admin_language),
                name="set_admin_language",
            ),
        ] + super().get_urls()

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


def set_admin_language(request):
    """Switch the staff console's language (FR-136).

    Separate from the storefront's switcher only because the redirect target is
    different — staff must land back on the admin page they were on, and that
    URL must be validated against this host like any other ``next``.

    Django ships its own Arabic and English admin catalogues, and Jazzmin's base
    template already derives ``dir`` from ``LANGUAGE_BIDI``, so setting the
    cookie is the whole of the change: labels, dates, and the entire layout
    mirror with it.
    """
    from django.conf import settings
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.utils import translation
    from django.utils.http import url_has_allowed_host_and_scheme
    from django.views.decorators.http import require_POST

    @require_POST
    def _handle(request):
        requested = (request.POST.get("language") or "").strip()
        if requested not in {code for code, _ in settings.LANGUAGES}:
            requested = settings.LANGUAGE_CODE

        target = request.POST.get("next") or reverse("admin:index")
        if not url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            target = reverse("admin:index")

        translation.activate(requested)
        response = redirect(target)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            requested,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
        return response

    return _handle(request)


def alerts_json(request):
    """The attention queue, filtered to what this staff member may see.

    Wrapped in ``admin_view`` at registration, so an anonymous or non-staff
    request is redirected to the login page rather than answered. That matters:
    these counts describe order volume and outstanding money, which is not
    public information about the business.
    """
    from django.http import JsonResponse

    from apps.core.alerts import attention_alerts

    try:
        alerts = attention_alerts(request.user)
    except Exception:  # pragma: no cover - defensive
        # The bar is an aid, never a gate. A failure here must not surface as a
        # broken admin page; the bar simply stays empty.
        alerts = []

    payload = [
        {
            "key": a.key,
            "label": a.label,
            "count": a.count,
            "url": a.url,
            "level": a.level,
            "icon": a.icon,
        }
        for a in alerts
    ]
    response = JsonResponse({"alerts": payload})
    # Per-user data behind auth: never let a shared cache hold it.
    response["Cache-Control"] = "private, no-store"
    return response


def install() -> None:
    """Adopt the dashboard on the default admin site."""
    admin.site.__class__ = ZakeyAdminSite
    admin.site.index_template = "admin/zakey_index.html"
