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
    # Mutating endpoints (T-1604). POST-only and CSRF-protected; they are not
    # new *pages*, so the 13-route public contract is unchanged.
    path("cart/add/", views.cart_add, name="cart-add"),
    path("cart/update/", views.cart_update, name="cart-update"),
    path("cart/remove/", views.cart_remove, name="cart-remove"),
    path("cart/coupon/", views.cart_coupon, name="cart-coupon"),
    path("wishlist/toggle/", views.wishlist_toggle, name="wishlist-toggle"),
    path("newsletter/", views.newsletter, name="newsletter"),
    path("checkout/submit/", views.checkout_submit, name="checkout-submit"),
    path("orders/<str:number>/", views.order_confirmation, name="order-confirmation"),
    path("account/login/", views.account_login, name="account-login"),
    path("account/register/", views.account_register, name="account-register"),
    path("account/logout/", views.account_logout, name="account-logout"),
    path("account/addresses/add/", views.address_create, name="address-create"),
    path("account/addresses/delete/", views.address_delete, name="address-delete"),
    path("account/profile/", views.profile_update, name="profile-update"),
    path("contact/send/", views.contact_send, name="contact-send"),
    path("account/confirm/<str:token>/", views.confirm_email, name="account-confirm"),
    path(
        "account/password-reset/",
        views.password_reset_request,
        name="password-reset-request",
    ),
    path(
        "account/password-reset/<str:token>/",
        views.password_reset_confirm,
        name="password-reset-confirm",
    ),
]
