from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import healthz
from storefront import views


urlpatterns = [
    # Staff console. Jazzmin themes this and only this (FR-100).
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    # The public storefront keeps its route contract unchanged (FR-131).
    path("", include("storefront.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.not_found
handler500 = views.server_error
