"""Staff-managed storefront content, and the line it must not cross (T-1205).

Three claims, and the third is the one that keeps the first two honest. Each is
named by the class that proves it, not here, so the traceability map points at
the assertions rather than at the file:

* every content surface the specification names is edited by staff, in the
  admin, and the storefront serves what they saved;
* the navigation is one of those surfaces, and every target it can point at is
  a route that already exists;
* everything else stays in the templates. That is a *negative* claim, so it is
  proved negatively: the fixed presentational labels still render with the
  content tables empty, which they could not do if a row supplied them, and no
  content model carries a layout or component field.

The tests below drive the admin over HTTP rather than calling ``.save()``:
"staff-manageable" is a claim about the screen a staff member actually uses.
"""

from __future__ import annotations

import json

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth.models import Group
from django.urls import Resolver404, resolve, reverse

from apps.content.models import (
    FAQ,
    Banner,
    ContactMessage,
    HomeSection,
    NavigationGroup,
    NavigationItem,
    NewsletterSubscription,
    Partner,
    StaticPage,
)
from apps.core.models import SiteSetting
from apps.reviews.models import Review
from storefront import context as ctx

pytestmark = pytest.mark.django_db

PASSWORD = "StrongPass!234"


@pytest.fixture
def content_manager(db):
    """A staff member holding exactly the Content Manager role."""
    from django.core.management import call_command

    from apps.accounts.models import User

    call_command("setup_roles", verbosity=0)
    user = User.objects.create_user(
        email="content@zakey.test", password=PASSWORD, is_staff=True
    )
    user.groups.add(Group.objects.get(name="Content Manager"))
    return user


@pytest.fixture
def content_client(client, content_manager):
    client.force_login(content_manager)
    return client


def form_payload(instance, **overrides) -> dict:
    """The editable fields of ``instance`` as an admin change-form POST."""
    model_admin = site._registry[type(instance)]
    payload: dict[str, object] = {}
    for field in instance._meta.fields:
        if not field.editable or field.auto_created:
            continue
        if field.name in model_admin.get_readonly_fields(None, instance):
            continue
        value = getattr(instance, field.attname)
        if value is None:
            value = ""
        elif isinstance(value, dict | list):
            value = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            value = "on" if value else ""
        payload[field.name] = value
    payload.update(overrides)
    return {key: value for key, value in payload.items() if value != ""}


def change_url(instance) -> str:
    meta = instance._meta
    return reverse(
        f"admin:{meta.app_label}_{meta.model_name}_change", args=[instance.pk]
    )


def add_url(model) -> str:
    meta = model._meta
    return reverse(f"admin:{meta.app_label}_{meta.model_name}_add")


# ---------------------------------------------------------------------------
# FR-096 — every named content surface is staff-managed
# ---------------------------------------------------------------------------


#: The surfaces FR-096 names, mapped to the model that stores each. Announcement
#: bar, hero and contact details are authored copy and share ``HomeSection``;
#: the payload-level edits are asserted separately below.
NAMED_SURFACES = [
    ("site settings", SiteSetting),
    ("announcement bar", HomeSection),
    ("hero", HomeSection),
    ("home sections", HomeSection),
    ("banners", Banner),
    ("partners", Partner),
    ("testimonials", Review),
    ("FAQs", FAQ),
    ("contact details", HomeSection),
    ("static pages", StaticPage),
    ("SEO metadata", StaticPage),
]


class TestEveryNamedSurfaceHasAStaffAdmin:
    """FR-096: each named surface is a record a content role may change."""

    @pytest.mark.parametrize(
        "surface,model", NAMED_SURFACES, ids=[name for name, _ in NAMED_SURFACES]
    )
    def test_the_surface_is_registered_and_writable_by_the_content_role(
        self, content_manager, surface, model
    ):
        meta = model._meta

        assert model in site._registry, f"{surface} has no admin at all"
        assert content_manager.has_perm(
            f"{meta.app_label}.change_{meta.model_name}"
        ), f"the Content Manager cannot change {surface}"

    def test_the_approved_navigation_carries_no_social_links_to_manage(
        self, storefront
    ):
        """Completing the enumeration: there is no social-links surface.

        FR-096 lists social links, and the approved design has none — the
        fixture's ``socialActions`` is empty and no template renders one. If a
        social link is ever added to the markup, this fails and the surface has
        to acquire a managing model rather than becoming a hard-coded exception.
        """
        body = storefront.get(reverse("storefront:home")).content.decode()

        for marker in ("facebook", "instagram", "twitter", "wa.me", "class=\"socials\""):
            assert marker not in body.lower(), (
                f"the storefront grew an unmanaged social link ({marker})"
            )


class TestAuthoredCopyIsStaffManageable:
    """FR-096: the announcement bar, the hero and the contact details.

    These three are authored copy rather than models of their own, so the proof
    has to go through the payload: edit the row on the admin screen, then read
    what the storefront would serve.
    """

    @pytest.mark.parametrize(
        "key,pointer,new_value",
        [
            ("announcement", ("message",), "شحن مجاني على كل الطلبات هذا الأسبوع"),
            ("home", ("hero", "description"), "نص بطل حرّره فريق المحتوى."),
            ("contact", ("email",), "hello@zakey.example"),
        ],
    )
    def test_a_content_manager_edits_it_and_the_storefront_serves_the_change(
        self, content_client, seeded_catalogue, key, pointer, new_value
    ):
        section = HomeSection.objects.get(key=key)
        payload = json.loads(json.dumps(section.data))
        target = payload
        for step in pointer[:-1]:
            target = target[step]
        assert target.get(pointer[-1]) != new_value, "precondition: value differs"
        target[pointer[-1]] = new_value

        response = content_client.post(
            change_url(section),
            form_payload(section, data=json.dumps(payload, ensure_ascii=False)),
            follow=True,
        )

        assert response.status_code == 200
        section.refresh_from_db()
        served = ctx.page_copy()[key]
        for step in pointer[:-1]:
            served = served[step]
        assert served[pointer[-1]] == new_value, (
            "the admin accepted the edit but the storefront still serves the old copy"
        )

    def test_the_edited_hero_copy_reaches_the_rendered_page(
        self, storefront, seeded_catalogue
    ):
        """Guard the guard: the copy comes from the row, not from the template.

        The ``<h1>`` itself stays a literal — it carries inline ``<em>`` markup,
        and moving markup into the database would cross the layout boundary — so
        the assertion is on the hero's editable copy around it.
        """
        section = HomeSection.objects.get(key="home")
        payload = json.loads(json.dumps(section.data))
        payload["hero"]["description"] = "وصف بطل مختلف تمامًا."
        section.data = payload
        section.save()

        body = storefront.get(reverse("storefront:home")).content.decode()

        assert "وصف بطل مختلف تمامًا." in body


class TestContentRecordsAreCreatedAndEditedByStaff:
    """FR-096: banners, partners, FAQs, static pages and their SEO metadata."""

    @pytest.mark.parametrize(
        "model,payload,lookup",
        [
            (
                Banner,
                {"title": "بانر موسم الصيف", "position": "0", "is_active": "on"},
                {"title": "بانر موسم الصيف"},
            ),
            (
                Partner,
                {"name": "شريك جديد", "position": "0", "is_active": "on"},
                {"name": "شريك جديد"},
            ),
            (
                FAQ,
                {
                    "question": "هل يوجد ضمان؟",
                    "answer": "نعم، ضمان سنتين على كل الأقفال.",
                    "page": "contact",
                    "position": "0",
                    "is_active": "on",
                },
                {"question": "هل يوجد ضمان؟"},
            ),
            (
                StaticPage,
                {
                    "slug": "warranty",
                    "title": "سياسة الضمان",
                    "body": "تفاصيل الضمان.",
                    "is_published": "on",
                },
                {"slug": "warranty"},
            ),
        ],
        ids=["banner", "partner", "faq", "static page"],
    )
    def test_a_content_manager_can_create_the_record_through_the_admin(
        self, content_client, model, payload, lookup
    ):
        response = content_client.post(add_url(model), payload, follow=True)

        assert response.status_code == 200
        assert model.objects.filter(**lookup).exists(), (
            f"the admin accepted the form but stored no {model.__name__}"
        )

    def test_seo_metadata_is_editable_on_a_static_page(self, content_client):
        page = StaticPage.objects.create(slug="terms", title="الشروط")

        content_client.post(
            change_url(page),
            form_payload(
                page,
                seo_title="شروط استخدام ZAKEY",
                seo_description="الشروط والأحكام الكاملة لمتجر زاكي.",
            ),
            follow=True,
        )

        page.refresh_from_db()
        assert page.seo_title == "شروط استخدام ZAKEY"
        assert page.seo_description == "الشروط والأحكام الكاملة لمتجر زاكي."

    def test_a_new_partner_reaches_the_storefront(self, content_client):
        content_client.post(
            add_url(Partner),
            {"name": "شريك التوزيع", "position": "1", "is_active": "on"},
            follow=True,
        )

        assert any(p["name"] == "شريك التوزيع" for p in ctx.partners())


# ---------------------------------------------------------------------------
# FR-097 — navigation is managed, and points only at existing routes
# ---------------------------------------------------------------------------


class TestNavigationIsStaffManageable:
    """FR-097: staff own the navigation; the route contract is untouched."""

    def test_a_content_manager_can_add_an_item_and_the_storefront_serves_it(
        self, content_client
    ):
        content_client.post(
            add_url(NavigationItem),
            {
                "label": "العروض",
                "href": "/shop/",
                "route_name": "",
                "icon": "",
                "group": NavigationGroup.PRIMARY,
                "position": "9",
                "is_active": "on",
            },
            follow=True,
        )

        labels = [item["label"] for item in ctx.navigation()["primary"]]
        assert "العروض" in labels

    def test_deactivating_an_item_withdraws_it_from_the_storefront(
        self, content_client, seeded_catalogue
    ):
        item = NavigationItem.objects.filter(
            group=NavigationGroup.PRIMARY, is_active=True
        ).first()
        assert item is not None, "precondition: the seed installs a primary menu"

        content_client.post(
            change_url(item), form_payload(item, is_active=""), follow=True
        )

        item.refresh_from_db()
        assert item.is_active is False
        assert item.label not in [i["label"] for i in ctx.navigation()["primary"]]

    def test_reordering_changes_the_order_the_storefront_renders(
        self, content_client, seeded_catalogue
    ):
        first, second = list(
            NavigationItem.objects.filter(group=NavigationGroup.PRIMARY).order_by(
                "position", "id"
            )[:2]
        )

        content_client.post(
            change_url(second), form_payload(second, position="0"), follow=True
        )
        content_client.post(
            change_url(first), form_payload(first, position="1"), follow=True
        )

        rendered = [item["label"] for item in ctx.navigation()["primary"]]
        assert rendered.index(second.label) < rendered.index(first.label)

    def test_every_navigation_target_is_an_existing_storefront_route(
        self, seeded_catalogue
    ):
        """The route contract half: the menu points at routes that already exist.

        A database-driven menu that could invent routes would have replaced the
        contract rather than preserved it.
        """
        unresolved = []
        for group in ctx.navigation().values():
            for item in group:
                try:
                    match = resolve(item["href"])
                except Resolver404:
                    unresolved.append(item["href"])
                    continue
                if match.namespace != "storefront":
                    unresolved.append(f"{item['href']} → {match.namespace}")

        assert unresolved == [], f"navigation targets outside the route contract: {unresolved}"

    def test_the_menu_is_not_empty(self, seeded_catalogue):
        """Guard the guard: an empty menu would satisfy the sweep vacuously."""
        groups = ctx.navigation()
        assert len(groups["primary"]) >= 4
        assert groups["utility"]


# ---------------------------------------------------------------------------
# FR-099 — presentational labels stay in the templates
# ---------------------------------------------------------------------------


#: Chrome that carries no business meaning: section titles, calls to action and
#: accessibility affordances. Making any of these editable would buy nothing and
#: cost a query, so they stay where they are.
FIXED_LABELS = (
    "تخطي إلى المحتوى",
    "كل المنتجات",
    "الشركة",
    "مركز المساعدة",
    "تسوق الآن",
    "القائمة",
)

#: Field names that would mean the database had started deciding *how* a page is
#: built rather than *what* it says.
LAYOUT_FIELD_NAMES = {
    "template",
    "template_name",
    "component",
    "layout",
    "css_class",
    "classes",
    "columns",
    "column_count",
    "width",
    "block",
    "style",
    "variant",
    "wrapper",
}

#: The content app's approved model list. A new model here means new
#: database-driven copy, which FR-099 says needs a stated business reason.
CONTENT_MODELS = {
    Banner,
    ContactMessage,
    FAQ,
    HomeSection,
    NavigationItem,
    NewsletterSubscription,
    Partner,
    StaticPage,
}


class TestPresentationalLabelsStayInTheTemplates:
    """FR-099: purely presentational labels are never database-driven."""

    def test_the_fixed_labels_render_with_an_empty_content_database(self, client, db):
        """The proof. No content rows exist, and the chrome still reads correctly.

        A label served from a row could not survive this; it would render blank.
        """
        assert not HomeSection.objects.exists()
        assert not NavigationItem.objects.exists()

        body = client.get(reverse("storefront:about")).content.decode()

        missing = [label for label in FIXED_LABELS if label not in body]
        assert missing == [], (
            f"these presentational labels vanished with an empty database, "
            f"so something is serving them from a row: {missing}"
        )

    @pytest.mark.parametrize(
        "model", sorted(CONTENT_MODELS, key=lambda m: m.__name__), ids=lambda m: m.__name__
    )
    def test_no_content_model_stores_a_layout_or_component_boundary(self, model):
        offending = sorted(
            field.name
            for field in model._meta.get_fields()
            if getattr(field, "name", "") in LAYOUT_FIELD_NAMES
        )

        assert offending == [], (
            f"{model.__name__} lets the database move a component or layout "
            f"boundary: {offending}"
        )

    def test_the_content_app_holds_exactly_the_approved_models(self):
        """A new content model is new database-driven copy; it needs a reason."""
        from django.apps import apps

        registered = {
            model for model in apps.get_app_config("content").get_models()
        }

        assert registered == CONTENT_MODELS, (
            "the content app's model list drifted from the approved set: "
            f"added={sorted(m.__name__ for m in registered - CONTENT_MODELS)}, "
            f"removed={sorted(m.__name__ for m in CONTENT_MODELS - registered)}"
        )

    def test_home_sections_carry_copy_only(self, seeded_catalogue):
        """The one JSON payload on the site stores words, never structure."""
        structural = []
        for section in HomeSection.objects.all():
            for key in section.data:
                if key.lower() in LAYOUT_FIELD_NAMES:
                    structural.append(f"{section.key}.{key}")

        assert structural == [], (
            f"authored copy started carrying layout decisions: {structural}"
        )
