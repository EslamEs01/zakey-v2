"""The backend boundary contract (T-0203a, T-1608).

Two guarantees, asserted rather than reviewed:

1. **The approved stack is present.** The original frontend-phase guard asserted
   the *absence* of a database, of ``django.contrib.admin``/``auth``/``sessions``
   and of ``SessionMiddleware``. This feature deliberately inverts every one of
   those, so the guard was replaced by its mirror image: the same list, required
   instead of forbidden.

2. **No runtime module can read the approved dataset.** The prototype's
   ``storefront/fixture_provider.py`` is deleted; the dataset survives only as
   seed input, and its query logic only as a test oracle. This file is what
   stops either one quietly becoming a request-time source of truth again.
"""

from __future__ import annotations

import re
from importlib.util import find_spec
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

import storefront

#: Directories that run in production. Nothing here may read the dataset.
RUNTIME_ROOTS = ("apps", "storefront", "config")

#: The one sanctioned reader outside tests: the seed management command, which
#: is operator-invoked and never touches a request.
SEED_COMMAND = Path("apps/core/management/commands/seed_demo.py")

DATASET_NAMES = ("approved-catalogue.json", "frontend-fixtures.json")


class DatasetBoundaryTests(SimpleTestCase):
    """T-1608: the dataset is seed input, never a commerce source of truth."""

    def test_the_retired_fixture_provider_is_gone(self):
        self.assertIsNone(
            find_spec("storefront.fixture_provider"),
            "storefront.fixture_provider still exists; it served fixture data to "
            "real requests and must not be importable from a shipped app",
        )

    def test_the_storefront_ships_no_dataset(self):
        storefront_path = Path(storefront.__file__).parent
        self.assertFalse(
            (storefront_path / "fixtures").exists(),
            "the storefront app still carries a fixtures directory",
        )

    def test_the_dataset_lives_with_the_seed_command(self):
        dataset = Path(settings.BASE_DIR, "apps/core/seed_data/approved-catalogue.json")
        self.assertTrue(dataset.is_file(), f"missing seed dataset at {dataset}")

    def test_no_runtime_module_reads_the_dataset(self):
        """Grep the shipped code for the dataset filename.

        A name-based check rather than an import graph on purpose: the danger is
        a module reading the JSON by path, which no import graph would show.
        """
        offenders = []
        for root in RUNTIME_ROOTS:
            for module in Path(settings.BASE_DIR, root).rglob("*.py"):
                relative = module.relative_to(settings.BASE_DIR)
                if relative == SEED_COMMAND:
                    continue
                text = module.read_text(encoding="utf-8")
                if any(name in text for name in DATASET_NAMES):
                    offenders.append(str(relative))
        self.assertEqual(
            offenders,
            [],
            "runtime modules reference the approved dataset by name: "
            f"{offenders}. Only the seed command may read it (T-1608).",
        )

    def test_no_runtime_module_imports_the_test_oracle(self):
        """``tests.fixtures.reference_catalogue`` is the parity oracle.

        It reproduces the prototype's pricing and filtering, so a shipped module
        importing it would reintroduce exactly what T-1608 removed.
        """
        offenders = []
        # Match an actual import, not any mention: a comment explaining the
        # boundary is not a breach of it.
        pattern = re.compile(
            r"^\s*(?:from|import)\s+tests[.\s]|^\s*from\s+\S*\breference_catalogue\b",
            re.MULTILINE,
        )
        for root in RUNTIME_ROOTS:
            for module in Path(settings.BASE_DIR, root).rglob("*.py"):
                if pattern.search(module.read_text(encoding="utf-8")):
                    offenders.append(str(module.relative_to(settings.BASE_DIR)))
        self.assertEqual(offenders, [], f"runtime modules import the test oracle: {offenders}")

    def test_templates_do_not_render_a_fixture_variable(self):
        """The base template used to serialise the whole dataset into the page."""
        offenders = []
        for template in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            text = template.read_text(encoding="utf-8")
            if re.search(r"\{\{\s*fixture\.|\{%\s*for\s+\w+\s+in\s+fixture\.", text):
                offenders.append(str(template.relative_to(settings.BASE_DIR)))
        self.assertEqual(offenders, [], f"templates still read a fixture: {offenders}")


class BackendStackTests(SimpleTestCase):
    """T-0203a: the replacement for the retired ``FrontendBoundaryTests``.

    Each assertion below is the inversion of one the old guard made, so the
    intent it protected (a coherent, declared stack) is still covered while the
    absent-backend precondition it froze is gone.
    """

    def test_storefront_remains_presentation_only(self):
        """The storefront owns no domain models and no migrations."""
        self.assertIsNone(find_spec("storefront.models"))
        storefront_path = Path(storefront.__file__).parent
        self.assertFalse((storefront_path / "migrations").exists())

    def test_domain_lives_in_the_approved_apps(self):
        """The 12 approved applications are installed, and only those."""
        expected = {
            "apps.core",
            "apps.accounts",
            "apps.catalog",
            "apps.inventory",
            "apps.cart",
            "apps.shipping",
            "apps.promotions",
            "apps.orders",
            "apps.payments",
            "apps.reviews",
            "apps.content",
            "apps.audit",
        }
        installed = {app for app in settings.INSTALLED_APPS if app.startswith("apps.")}
        self.assertEqual(installed, expected)

    def test_required_backend_stack_is_enabled(self):
        """FR-003: the stack the old guard forbade is now mandatory."""
        for app in (
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
        ):
            self.assertIn(app, settings.INSTALLED_APPS)
        for middleware in (
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
        ):
            self.assertIn(middleware, settings.MIDDLEWARE)

    def test_database_is_postgresql(self):
        """FR-002/NFR-005: SQLite cannot evidence locking, so it is refused."""
        self.assertIn("postgresql", settings.DATABASES["default"]["ENGINE"])

    def test_jazzmin_is_admin_only_and_precedes_django_admin(self):
        """FR-100: Jazzmin themes the staff admin, never the storefront."""
        apps_list = list(settings.INSTALLED_APPS)
        self.assertIn("jazzmin", apps_list)
        self.assertLess(apps_list.index("jazzmin"), apps_list.index("django.contrib.admin"))

    def test_jazzmin_assets_never_load_on_the_storefront(self):
        """FR-100/FR-103: the admin theme must not leak into a public page.

        Scoped to the storefront. ``templates/admin/`` *is* the staff admin, so
        a template in there referencing admin assets is the intended behaviour,
        not a leak — scanning it would only ever produce false positives.
        """
        admin_root = Path(settings.BASE_DIR, "templates", "admin")
        offenders = []
        scanned = []
        for template in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            if admin_root in template.parents:
                continue
            scanned.append(template)
            text = template.read_text(encoding="utf-8").lower()
            if "jazzmin" in text or "admin/css" in text:
                offenders.append(str(template.relative_to(settings.BASE_DIR)))
        self.assertEqual(offenders, [], f"storefront templates reference admin assets: {offenders}")
        # Guard the guard: if that scoping ever excluded everything, the
        # assertion above would pass vacuously and protect nothing.
        self.assertGreater(len(scanned), 10)

    def test_no_storefront_template_inherits_from_the_admin(self):
        """The other direction: the storefront must not extend or include the admin."""
        admin_root = Path(settings.BASE_DIR, "templates", "admin")
        offenders = []
        for template in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            if admin_root in template.parents:
                continue
            text = template.read_text(encoding="utf-8")
            if any(
                tag in text
                for tag in ('extends "admin/', "extends 'admin/", 'include "admin/', "include 'admin/")
            ):
                offenders.append(str(template.relative_to(settings.BASE_DIR)))
        self.assertEqual(offenders, [], f"storefront templates inherit from the admin: {offenders}")
