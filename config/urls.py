from django.urls import include, path

from storefront import views


urlpatterns = [
    path("", include("storefront.urls")),
]

handler404 = views.not_found
handler500 = views.server_error
