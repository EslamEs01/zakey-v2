from django.urls import path

from . import views


app_name = "storefront"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("collections/<slug:slug>/", views.collection, name="collection"),
    path("search/", views.search, name="search"),
    path("products/<slug:slug>/", views.product_detail, name="product"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("account/", views.account, name="account"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("errors/404/", views.not_found_preview, name="error-404"),
    path("errors/500/", views.server_error_preview, name="error-500"),
]
