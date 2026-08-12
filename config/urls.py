import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from apps.core.views import healthz
from storefront import views


urlpatterns = [
    # Staff console. Jazzmin themes this and only this (FR-100).
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    # The public storefront keeps its route contract unchanged (FR-131).
    path("", include("storefront.urls")),
]

# Uploaded media.
#
# Nginx is meant to serve /media/ (deploy/zakey-nginx.conf carries the alias),
# and where it does, ZAKEY_SERVE_MEDIA should be set False so Django never sees
# these requests. But that nginx file is an *example* that has to be installed
# by hand, and when it is not, every image a staff member uploads through the
# admin 404s while the page around it renders perfectly — which reads as a
# broken upload rather than a missing web-server rule.
#
# So the fallback defaults to ON: a correct page served slightly less
# efficiently beats a catalogue of broken images.
#
# `django.conf.urls.static.static()` is deliberately NOT used here. It returns
# an empty list whenever DEBUG is False, so wiring the fallback through it would
# have looked right and served nothing in the one environment that needs it.
# `serve` is pointed at MEDIA_ROOT only, and it refuses any path that escapes
# that directory.
if settings.DEBUG or getattr(settings, "ZAKEY_SERVE_MEDIA", False):
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]

handler404 = views.not_found
handler500 = views.server_error
