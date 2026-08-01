from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .fixture_provider import get_catalogue, get_product, page_context


def _render(request: HttpRequest, template: str, page: str, **extra: object) -> HttpResponse:
    context = page_context(page, request.GET.get("qa", "default"))
    context.update(extra)
    return render(request, template, context)


def home(request: HttpRequest) -> HttpResponse:
    fixture = page_context("home")["fixture"]
    best_sellers = [item for item in fixture["products"] if "collection-best" in item["collectionIds"]][:4]
    featured = [item for item in fixture["products"] if "collection-featured" in item["collectionIds"]][:4]
    home_reviews = [item for item in fixture["reviews"] if "home" in item["placement"]][:3]
    return _render(
        request,
        "pages/home.html",
        "home",
        best_sellers=best_sellers,
        featured=featured,
        home_reviews=home_reviews,
    )


def shop(request: HttpRequest) -> HttpResponse:
    return _render(request, "pages/shop.html", "shop", catalogue=get_catalogue(request.GET))


def collection(request: HttpRequest, slug: str) -> HttpResponse:
    catalogue = get_catalogue(request.GET, slug)
    if catalogue["criteria"].collection is None:
        return not_found(request)
    return _render(request, "pages/shop.html", "collection", catalogue=catalogue)


def search(request: HttpRequest) -> HttpResponse:
    return _render(request, "pages/shop.html", "search", catalogue=get_catalogue(request.GET))


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_product(slug)
    if product is None:
        return not_found(request)
    return _render(request, "pages/product_detail.html", "product", **product)


def cart(request: HttpRequest) -> HttpResponse:
    return _render(request, "pages/cart.html", "cart")


def checkout(request: HttpRequest) -> HttpResponse:
    step = request.GET.get("step", "shipping")
    if step not in {"shipping", "payment", "review"}:
        step = "shipping"
    return _render(request, "pages/checkout.html", "checkout", checkout_step=step)


def wishlist(request: HttpRequest) -> HttpResponse:
    return _render(request, "pages/wishlist.html", "wishlist")


def account(request: HttpRequest) -> HttpResponse:
    mode = request.GET.get("state", "signed-out")
    if mode not in {"signed-out", "signed-in"}:
        mode = "signed-out"
    tab = request.GET.get("tab", "orders")
    return _render(request, "pages/account.html", "account", account_mode=mode, account_tab=tab)


def about(request: HttpRequest) -> HttpResponse:
    return _render(request, "pages/about.html", "about")


def contact(request: HttpRequest) -> HttpResponse:
    return _render(request, "pages/contact.html", "contact")


def not_found(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    response = _render(request, "pages/404.html", "404")
    response.status_code = 404
    return response


def server_error(request: HttpRequest) -> HttpResponse:
    response = _render(request, "pages/500.html", "5xx")
    response.status_code = 500
    return response


def not_found_preview(request: HttpRequest) -> HttpResponse:
    response = _render(request, "pages/404.html", "404")
    response.status_code = 404
    return response


def server_error_preview(request: HttpRequest) -> HttpResponse:
    response = _render(request, "pages/500.html", "5xx")
    response.status_code = 500
    return response
