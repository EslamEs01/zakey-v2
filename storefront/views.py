"""Storefront views — database-backed (T-1601 – T-1603, FR-130, FR-131).

Every page below reads the database. The retired ``fixture_provider`` is not
imported anywhere in this module: there is no request path left that can serve a
JSON fixture as commerce truth.

Context keys are unchanged from the approved prototype so the templates render
identically (frontend-contract.md §3); only their source moved.
"""

from __future__ import annotations

from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts import forms as accounts_forms
from apps.accounts import services as accounts_services
from apps.cart import services as cart_services
from apps.core import ratelimit
from apps.catalog import selectors
from apps.content.models import FAQ, ContactMessage, NewsletterSubscription
from apps.orders import services as orders_services
from apps.orders.models import Order
from apps.promotions import services as promotions_services
from apps.reviews.models import Review, ReviewStatus
from apps.shipping import services as shipping_services

from . import carts
from . import checkout_forms
from . import context as ctx
from . import forms


def _client_ip(request: HttpRequest) -> str:
    """The client address used to scope login rate limiting (FR-058).

    ``REMOTE_ADDR`` only. ``X-Forwarded-For`` is attacker-controlled unless a
    trusted proxy is known to overwrite it, and trusting it here would let one
    host spread its attempts across unlimited fake addresses — defeating the
    per-IP half of the lockout.
    """
    return request.META.get("REMOTE_ADDR", "")


def _first_error(form) -> str:
    """The first field error, for a flash message."""
    for errors in form.errors.values():
        if errors:
            return errors[0]
    return "تعذّر تنفيذ الطلب."


def _render(request: HttpRequest, template: str, page: str, **extra: object) -> HttpResponse:
    """Render ``template`` with the shared storefront context.

    ``?qa=`` selects a *presentation* state (loading, error, empty…) used by the
    approved QA matrix. It never selects data, so it cannot be used to make the
    page show something the database does not contain.
    """
    data = ctx.page_context(page, request.GET.get("qa", "default"))
    # Header badges are on every page, so they are resolved once here rather
    # than being fetched by a script after paint.
    data.update(carts.badge_counts(request))
    data.update(extra)
    return render(request, template, data)


# ---------------------------------------------------------------------------
# Batch 1 — home, about, contact
# ---------------------------------------------------------------------------


def home(request: HttpRequest) -> HttpResponse:
    """Home: two curated collections and the reviews flagged for this page."""
    best_sellers = selectors.get_catalogue({}, "best-sellers")["products"][:4]
    featured = selectors.get_catalogue({}, "featured")["products"][:4]
    home_reviews = [
        selectors._review_record(review)
        for review in Review.objects.filter(
            status=ReviewStatus.APPROVED, placement__contains=["home"]
        ).select_related("product")[:3]
    ]
    return _render(
        request,
        "pages/home.html",
        "home",
        best_sellers=best_sellers,
        featured=featured,
        home_reviews=home_reviews,
        partners=ctx.partners(),
    )


def about(request: HttpRequest) -> HttpResponse:
    return _render(
        request,
        "pages/about.html",
        "about",
        team_members=ctx.team_members(),
    )


def contact(request: HttpRequest) -> HttpResponse:
    return _render(
        request,
        "pages/contact.html",
        "contact",
        # Built through ctx.faqs, which resolves the English columns; reading
        # faq.question directly here served Arabic on the English page.
        contact_faqs=ctx.faqs("contact"),
    )


# ---------------------------------------------------------------------------
# Batch 2 — catalogue (shop, collection, search)
# ---------------------------------------------------------------------------


def shop(request: HttpRequest) -> HttpResponse:
    return _render(
        request, "pages/shop.html", "shop", catalogue=selectors.get_catalogue(request.GET)
    )


def collection(request: HttpRequest, slug: str) -> HttpResponse:
    catalogue = selectors.get_catalogue(request.GET, slug)
    if catalogue["criteria"].collection is None:
        return not_found(request)
    return _render(request, "pages/shop.html", "collection", catalogue=catalogue)


def search(request: HttpRequest) -> HttpResponse:
    return _render(
        request, "pages/shop.html", "search", catalogue=selectors.get_catalogue(request.GET)
    )


# ---------------------------------------------------------------------------
# Batch 3 — product detail
# ---------------------------------------------------------------------------


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    detail = selectors.get_product_detail(slug)
    if detail is None:
        return not_found(request)
    return _render(request, "pages/product_detail.html", "product", **detail)


# ---------------------------------------------------------------------------
# Batch 4 — cart (T-1604, FR-132, FR-134)
# ---------------------------------------------------------------------------


def cart(request: HttpRequest) -> HttpResponse:
    """The cart, rendered from the database with server-computed totals.

    The page used to be an empty shell that JavaScript filled from
    ``localStorage``; every figure in the summary was produced in the browser.
    Now the lines and every money figure come from ``price_cart``.
    """
    return _render(request, "pages/cart.html", "cart", **carts.cart_context(request))


def _cart_redirect(request: HttpRequest) -> HttpResponse:
    """Post/Redirect/Get back to wherever the mutation was made from.

    ``next`` is validated against this host, so the cart buttons cannot be
    turned into an open redirect (threat T-10).
    """
    target = request.POST.get("next") or reverse("storefront:cart")
    if not url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        target = reverse("storefront:cart")
    return redirect(target)


@require_POST
def cart_add(request: HttpRequest) -> HttpResponse:
    form = forms.AddToCartForm(request.POST)
    if not form.is_valid():
        messages.error(request, _first_error(form))
        return _cart_redirect(request)

    basket = carts.get_cart(request, create=True)
    try:
        cart_services.add_to_cart(
            basket, form.cleaned_data["variant"], form.cleaned_data["quantity"]
        )
    except ValidationError as error:
        messages.error(request, error.messages[0])
        return _cart_redirect(request)

    messages.success(request, "تمت الإضافة إلى السلة.")
    # "Buy now" is the same add, then straight to checkout. Expressed as its own
    # field rather than a second `next` value so the intent is explicit and does
    # not depend on which duplicate field the parser happens to return.
    if request.POST.get("buy_now"):
        return redirect("storefront:checkout")
    return _cart_redirect(request)


@require_POST
def cart_update(request: HttpRequest) -> HttpResponse:
    form = forms.UpdateCartLineForm(request.POST)
    if form.is_valid():
        basket = carts.get_cart(request, create=True)
        try:
            cart_services.update_quantity(
                basket, form.cleaned_data["variant"], form.cleaned_data["quantity"]
            )
        except ValidationError as error:
            messages.error(request, error.messages[0])
    else:
        messages.error(request, _first_error(form))
    return _cart_redirect(request)


@require_POST
def cart_remove(request: HttpRequest) -> HttpResponse:
    form = forms.RemoveCartLineForm(request.POST)
    if form.is_valid():
        basket = carts.get_cart(request, create=True)
        cart_services.remove_from_cart(basket, form.cleaned_data["variant"])
        messages.success(request, "تمت إزالة المنتج من السلة.")
    else:
        messages.error(request, _first_error(form))
    return _cart_redirect(request)


@require_POST
def cart_coupon(request: HttpRequest) -> HttpResponse:
    """Apply or clear a coupon.

    The browser sends a *code*, never a discount. Eligibility and the amount are
    decided by ``promotions.services`` against the real basket (FR-082).
    """
    # Coupon probing is how an attacker discovers valid codes, so the attempt is
    # counted before the code is even looked at (T-1707, threat T-14). The
    # refusal reuses the invalid-code message on purpose: a distinct "too many
    # attempts" would itself confirm that the earlier guesses were evaluated.
    if not ratelimit.allow("coupon", _client_ip(request)):
        messages.error(request, promotions_services.REJECTED_MESSAGE)
        return _cart_redirect(request)

    form = forms.CouponForm(request.POST)
    basket = carts.get_cart(request, create=True)
    if not form.is_valid():
        messages.error(request, promotions_services.REJECTED_MESSAGE)
        return _cart_redirect(request)

    code = form.cleaned_data["coupon"]
    if not code:
        basket.coupon = None
        basket.save(update_fields=["coupon", "updated_at"])
        messages.success(request, "تم إلغاء كود الخصم.")
        return _cart_redirect(request)

    coupon = promotions_services.find_coupon(code)
    if coupon is None:
        messages.error(request, promotions_services.REJECTED_MESSAGE)
        return _cart_redirect(request)

    totals = cart_services.price_cart(basket)
    profile = getattr(request.user, "customer_profile", None)
    try:
        promotions_services.validate_coupon(
            coupon, totals.subtotal, customer=profile, cart=basket
        )
    except ValidationError as error:
        messages.error(request, error.messages[0])
        return _cart_redirect(request)

    basket.coupon = coupon
    basket.save(update_fields=["coupon", "updated_at"])
    messages.success(request, "تم تطبيق كود الخصم.")
    return _cart_redirect(request)


@require_POST
def wishlist_toggle(request: HttpRequest) -> HttpResponse:
    form = forms.WishlistToggleForm(request.POST)
    if form.is_valid():
        saved = cart_services.toggle_wishlist(
            carts.get_wishlist(request, create=True), form.cleaned_data["product"]
        )
        messages.success(
            request, "تمت الإضافة إلى المفضلة." if saved else "تمت الإزالة من المفضلة."
        )
    else:
        messages.error(request, _first_error(form))
    target = request.POST.get("next") or reverse("storefront:wishlist")
    if not url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        target = reverse("storefront:wishlist")
    return redirect(target)


@require_POST
def set_language(request: HttpRequest) -> HttpResponse:
    """Switch the interface language and return to the page it was used on (FR-136).

    Deliberately not ``django.views.i18n.set_language`` and deliberately not
    ``i18n_patterns``. Both are the usual answer, and both would move every
    public URL under a ``/ar/`` or ``/en/`` prefix — the thirteen frozen
    storefront URLs are half of the route contract (FR-131), so the language has
    to live in a cookie instead of the path.

    The redirect target is validated against this host for the same reason every
    other ``next`` in this module is: a switcher is a perfectly ordinary open
    redirect if it forwards to whatever it is handed.
    """
    requested = (request.POST.get("language") or "").strip()
    supported = {code for code, _ in settings.LANGUAGES}
    if requested not in supported:
        requested = settings.LANGUAGE_CODE

    target = request.POST.get("next") or reverse("storefront:home")
    if not url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        target = reverse("storefront:home")

    translation.activate(requested)
    response = redirect(target)
    # The cookie is the whole mechanism. Django removed session-backed language
    # selection in 4.0, and LocaleMiddleware reads only the cookie and the
    # Accept-Language header — writing a session key here would look like it
    # worked and change nothing.
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


@require_POST
def newsletter(request: HttpRequest) -> HttpResponse:
    """Persist a newsletter sign-up (T-1206, FR-098).

    Re-subscribing is not an error and is not a duplicate: the address is the
    unique key, so the second attempt updates the existing row and the visitor
    sees the same confirmation either way. That also means the response cannot
    be used to test whether an address is already on the list.
    """
    form = forms.NewsletterForm(request.POST)
    if form.is_valid():
        # Same shape as contact: absorbed silently (T-1707). Newsletter forms
        # are used to mail-bomb a third party, so the ceiling is per IP.
        if not ratelimit.allow("newsletter", _client_ip(request)):
            messages.success(request, "تم تسجيل بريدك في النشرة.")
            return redirect("storefront:home")
        NewsletterSubscription.objects.update_or_create(
            email=form.cleaned_data["email"],
            defaults={"source": request.POST.get("source", "storefront")[:60]},
        )
        messages.success(request, "تم تسجيل بريدك في النشرة.")
    else:
        messages.error(request, _first_error(form))
    target = request.POST.get("next") or reverse("storefront:home")
    if not url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        target = reverse("storefront:home")
    return redirect(target)


@require_POST
def contact_send(request: HttpRequest) -> HttpResponse:
    """Persist a contact message (T-1206, FR-098).

    The prototype's handler validated in the browser, waited 350 ms and then
    reported success while stating the message had not been sent anywhere. It
    is a real row now, and staff see it in the admin.
    """
    form = forms.ContactForm(request.POST)
    if form.is_valid():
        # Counted per IP (T-1707). The visitor always sees the same
        # confirmation, so a flood is absorbed silently rather than answered
        # with a message telling the sender their volume is being measured.
        if not ratelimit.allow("contact", _client_ip(request)):
            messages.success(request, "تم استلام رسالتك، وسنعود إليك قريبًا.")
            return redirect("storefront:contact")
        ContactMessage.objects.create(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data["phone"],
            subject=form.cleaned_data["subject"],
            message=form.cleaned_data["message"],
        )
        messages.success(request, "تم استلام رسالتك، وسنعود إليك قريبًا.")
        return redirect("storefront:contact")

    return _render(
        request, "pages/contact.html", "contact", contact_form=form, contact_faqs=ctx.faqs("contact")
    )


def _checkout_context(request, *, form=None, step="shipping") -> dict:
    data = carts.cart_context(request)
    data.update(
        checkout_step=step,
        checkout_form=form,
        governorates=ctx.governorates(),
        service_eligibility=ctx.service_eligibility(),
        shipping_options=ctx.shipping_options(),
        installation_offered=ctx.installation_offered(),
        payment_options=ctx.payment_options(),
        # One key per submission attempt. Replaying the same rendered page —
        # a double-click, a refresh, a flaky connection — carries the same key
        # and resolves to the same order (FR-064, INV-002).
        idempotency_key=uuid4().hex,
    )
    return data


def checkout(request: HttpRequest) -> HttpResponse:
    """Checkout. GET renders the form; POST creates a real order (T-1605)."""
    step = request.GET.get("step", "shipping")
    if step not in {"shipping", "payment", "review"}:
        step = "shipping"
    return _render(
        request, "pages/checkout.html", "checkout", **_checkout_context(request, step=step)
    )


@require_POST
def checkout_submit(request: HttpRequest) -> HttpResponse:
    """Validate the whole submission and create the order (FR-060 – FR-064).

    Everything monetary is recomputed inside ``create_order`` from locked rows,
    so a request that carries its own totals gets the server's answer regardless.
    """
    basket = carts.get_cart(request)
    if basket is None or basket.is_empty:
        messages.error(request, "سلتك فارغة.")
        return redirect("storefront:cart")

    form = checkout_forms.CheckoutForm(request.POST)
    if not form.is_valid():
        # Re-render in place with the field errors attached, exactly as the
        # browser used to show them — but now they are the server's verdict.
        return _render(
            request,
            "pages/checkout.html",
            "checkout",
            **_checkout_context(request, form=form, step="shipping"),
        )

    governorate = form.cleaned_data["governorate"]
    area = form.cleaned_data.get("area")
    totals = cart_services.price_cart(basket, coupon=basket.coupon)
    discounted = totals.subtotal - totals.discount_total

    try:
        quote = shipping_services.quote_shipping(
            form.cleaned_data["shippingMethod"], governorate, area, discounted
        )
    except ValidationError as error:
        form.add_error("shippingMethod", error.messages[0])
        return _render(
            request,
            "pages/checkout.html",
            "checkout",
            **_checkout_context(request, form=form, step="shipping"),
        )

    installation_quote = None
    if form.installation_requested:
        installation_quote = shipping_services.quote_installation(governorate, basket)
        if installation_quote is None:
            form.add_error("installation", "خدمة التركيب غير متاحة لهذا الطلب.")
            return _render(
                request,
                "pages/checkout.html",
                "checkout",
                **_checkout_context(request, form=form, step="shipping"),
            )

    idempotency_key = (request.POST.get("idempotency_key") or "").strip() or uuid4().hex
    try:
        order = orders_services.create_order(
            cart=basket,
            email=form.cleaned_data["email"],
            phone=form.cleaned_data["mobile"],
            address_data=form.address_data(),
            idempotency_key=idempotency_key,
            shipping_quote=quote.as_tuple(),
            installation_quote=installation_quote,
            customer=getattr(request.user, "customer_profile", None),
            terms_accepted=form.cleaned_data["acknowledgement"],
            actor=request.user if request.user.is_authenticated else None,
        )
    except ValidationError as error:
        messages.error(request, error.messages[0])
        return _render(
            request,
            "pages/checkout.html",
            "checkout",
            **_checkout_context(request, form=form, step="review"),
        )

    # Remember the order for the confirmation page so a guest (who has no
    # account to look it up in) can still see what they just bought.
    request.session.setdefault("zakey_orders", [])
    if order.number not in request.session["zakey_orders"]:
        request.session["zakey_orders"] = [*request.session["zakey_orders"], order.number]
        request.session.modified = True
    return redirect("storefront:order-confirmation", number=order.number)


def order_confirmation(request: HttpRequest, number: str) -> HttpResponse:
    """The order the customer just placed.

    Visible to the customer who owns it, or to the guest whose session recorded
    placing it. Anyone else gets a 404 — an order number must not be a lookup
    key for other people's purchases (FR-056, INV-010).
    """
    from apps.orders.models import Order

    order = get_object_or_404(
        Order.objects.prefetch_related("lines").select_related("address"), number=number
    )
    profile = getattr(request.user, "customer_profile", None)
    owns = profile is not None and order.customer_id == profile.pk
    placed_here = order.number in request.session.get("zakey_orders", [])
    if not (owns or placed_here):
        raise Http404("لا يوجد طلب بهذا الرقم.")

    return _render(
        request, "pages/order_confirmation.html", "order-confirmation", order=order
    )


def wishlist(request: HttpRequest) -> HttpResponse:
    """The wishlist, rendered from persisted rows rather than ``localStorage``."""
    return _render(
        request, "pages/wishlist.html", "wishlist", **carts.wishlist_context(request)
    )


ACCOUNT_TABS = {"orders", "wishlist", "addresses", "payment", "settings"}


def account(request: HttpRequest) -> HttpResponse:
    """Account page (T-1606).

    The signed-in/signed-out split is decided by the *session*, not by a query
    parameter. The prototype's ``?state=signed-in`` switch is gone: it let any
    visitor render the account of a fabricated customer, and it was the last
    place where "who you are" was a URL parameter.
    """
    tab = request.GET.get("tab", "orders")
    if tab not in ACCOUNT_TABS:
        tab = "orders"

    data = {
        "account_mode": "signed-in" if request.user.is_authenticated else "signed-out",
        "account_tab": tab,
        "service_areas": ctx.service_eligibility()["areas"],
        "governorates": ctx.governorates(),
        "login_form": accounts_forms.LoginForm(),
        "registration_form": accounts_forms.RegistrationForm(),
    }
    profile = getattr(request.user, "customer_profile", None)
    if profile is not None:
        data.update(carts.wishlist_context(request))
        data["profile"] = profile
        data["orders"] = (
            Order.objects.filter(customer=profile)
            .prefetch_related("lines")
            .order_by("-placed_at", "-id")
        )
        data["addresses"] = profile.addresses.select_related("governorate", "area")
    return _render(request, "pages/account.html", "account", **data)


@require_POST
def account_login(request: HttpRequest) -> HttpResponse:
    """Sign in, then adopt whatever the visitor put in their basket first.

    The session key is captured *before* ``login()`` because Django cycles it to
    prevent session fixation; afterwards the anonymous cart is unreachable.
    """
    form = accounts_forms.LoginForm(request.POST, client_ip=_client_ip(request))
    if not form.is_valid():
        messages.error(request, _first_error(form))
        return redirect("storefront:account")

    previous_session_key = request.session.session_key or ""
    auth_login(request, form.get_user())
    carts.merge_on_login(request, previous_session_key)
    messages.success(request, "تم تسجيل الدخول.")
    return redirect("storefront:account")


@require_POST
def account_register(request: HttpRequest) -> HttpResponse:
    form = accounts_forms.RegistrationForm(request.POST)
    if not form.is_valid():
        messages.error(request, _first_error(form))
        return redirect("storefront:account")

    previous_session_key = request.session.session_key or ""
    result = accounts_services.register(form)
    auth_login(request, result.user, backend="django.contrib.auth.backends.ModelBackend")
    carts.merge_on_login(request, previous_session_key)
    messages.success(request, "تم إنشاء حسابك. تحقق من بريدك لتأكيد العنوان.")
    return redirect("storefront:account")


@require_POST
def account_logout(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    messages.success(request, "تم تسجيل الخروج.")
    return redirect("storefront:home")


@require_POST
def address_create(request: HttpRequest) -> HttpResponse:
    profile = getattr(request.user, "customer_profile", None)
    if profile is None:
        raise Http404("لا يوجد حساب.")

    form = forms.AddressForm(request.POST)
    if form.is_valid():
        form.save(profile)
        messages.success(request, "تمت إضافة العنوان.")
    else:
        messages.error(request, _first_error(form))
    return redirect(f"{reverse('storefront:account')}?tab=addresses")


@require_POST
def address_delete(request: HttpRequest) -> HttpResponse:
    """Delete one of *your own* addresses.

    The row is fetched through the owner-scoped helper, so another customer's
    id answers 404 rather than deleting their address (FR-056, INV-010).
    """
    from apps.accounts.models import Address
    from apps.core.ownership import get_owned_object

    address = get_owned_object(
        Address, request.POST.get("address"), request.user, request.session.session_key or ""
    )
    address.delete()
    messages.success(request, "تم حذف العنوان.")
    return redirect(f"{reverse('storefront:account')}?tab=addresses")


@require_POST
def profile_update(request: HttpRequest) -> HttpResponse:
    profile = getattr(request.user, "customer_profile", None)
    if profile is None:
        raise Http404("لا يوجد حساب.")

    form = forms.ProfileForm(request.POST)
    if form.is_valid():
        profile.full_name = form.cleaned_data["full_name"]
        profile.phone = form.cleaned_data["phone"]
        # `is_staff` / `is_superuser` are not fields on this form and never will
        # be: no storefront submission may grant itself privileges (FR-057).
        profile.save(update_fields=["full_name", "phone", "updated_at"])
        messages.success(request, "تم تحديث بياناتك.")
    else:
        messages.error(request, _first_error(form))
    return redirect(f"{reverse('storefront:account')}?tab=settings")


# ---------------------------------------------------------------------------
# Email confirmation and password reset (T-0404, FR-053, FR-054)
# ---------------------------------------------------------------------------

#: One message for every outcome of a reset request. Saying "no account with
#: that address" would turn this form into an account-existence oracle (FR-054).
RESET_REQUESTED_MESSAGE = (
    "إن كان هذا البريد مسجلًا لدينا فستصلك رسالة بخطوات إعادة تعيين كلمة المرور."
)


def confirm_email(request: HttpRequest, token: str) -> HttpResponse:
    """Consume an email-confirmation token (FR-053).

    Single-use by construction: the token is salted with the verified flag, so
    the same link cannot be replayed once it has done its job.
    """
    try:
        accounts_services.confirm_email(token)
    except accounts_services.InvalidToken as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "تم تأكيد بريدك الإلكتروني.")
    return redirect("storefront:account")


@require_POST
def password_reset_request(request: HttpRequest) -> HttpResponse:
    """Ask for a reset link.

    Always reports the same thing, whether or not the address exists, and never
    reveals whether the daily send cap was hit.
    """
    form = accounts_forms.PasswordResetRequestForm(request.POST)
    if form.is_valid():
        accounts_services.request_password_reset(form.cleaned_data["email"])
    messages.success(request, RESET_REQUESTED_MESSAGE)
    return redirect("storefront:account")


def password_reset_confirm(request: HttpRequest, token: str) -> HttpResponse:
    """Set a new password from a reset token (FR-054).

    The token is validated on GET as well as POST, so an expired or replayed
    link never renders a form that cannot work.
    """
    try:
        user = accounts_services.user_from_password_reset_token(token)
    except accounts_services.InvalidToken as error:
        messages.error(request, str(error))
        return redirect("storefront:account")

    if request.method == "POST":
        form = accounts_forms.SetNewPasswordForm(request.POST, user=user)
        if form.is_valid():
            accounts_services.reset_password(token, form)
            messages.success(request, "تم تحديث كلمة المرور. يمكنك تسجيل الدخول الآن.")
            return redirect("storefront:account")
        messages.error(request, _first_error(form))
    else:
        form = accounts_forms.SetNewPasswordForm(user=user)

    return _render(
        request,
        "pages/account.html",
        "account",
        account_mode="signed-out",
        account_tab="orders",
        login_form=accounts_forms.LoginForm(),
        registration_form=accounts_forms.RegistrationForm(),
        reset_form=form,
        reset_token=token,
        governorates=ctx.governorates(),
        service_areas=ctx.service_eligibility()["areas"],
    )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


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
