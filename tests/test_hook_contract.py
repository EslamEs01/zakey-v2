"""The 139-hook behavioural contract (T-0104 → T-1609, frontend-contract §5).

§5 does not freeze the hook list: it says renaming one "is a breaking change
requiring a matching JS edit and a visual-regression pass", and T-1609's literal
acceptance is **zero unintended renames**. So the gate is change control, not
immutability — every departure from the T-0104 baseline must be declared here,
with the production behaviour that replaced it.

An undeclared disappearance fails. A prototype hook creeping back into a runtime
template fails. A hook whose control no longer does anything fails.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

BASE_DIR = Path(settings.BASE_DIR)
BASELINE = BASE_DIR / "specs/004-zakey-commerce-backend-admin/qa/data-hooks-baseline.json"

#: Baseline hooks deliberately retired because the server-backed implementation
#: removed the behaviour they addressed. Each entry records WHY, so a future
#: reader can tell a decision from an accident.
RETIRED: dict[str, str] = {
    "data-catalogue-product-library": (
        "The hidden per-product template library existed so catalogue.js could "
        "re-render the grid client-side. The server filters, sorts and paginates "
        "now (T-1602/T-1607); the library and its consumer were deleted together."
    ),
    "data-catalogue-product-template": (
        "Per-product <template> clone source for the same client-side re-render. "
        "Removed with its only consumer."
    ),
    "data-cart-loading": (
        "'Loading the local cart…' spinner. The cart is server-rendered, so there "
        "is no asynchronous load to wait for and the control would never show."
    ),
    "data-wishlist-loading": "Same as data-cart-loading, for the wishlist.",
    "data-checkout-loading": "Same as data-cart-loading, for checkout.",
    "data-account-demo-form": (
        "The prototype's demonstration account form. Replaced by real "
        "registration and login forms (data-register-form / data-login-form) "
        "backed by a session."
    ),
    "data-account-unavailable": (
        "Buttons that announced a feature was unavailable in the prototype "
        "(tracking, adding an address, adding a payment method). Addresses are "
        "now real (data-account-address); the others were removed rather than "
        "left as dead controls."
    ),
    "data-prototype-form": (
        "The newsletter form that validated in the browser and reported success "
        "while saving nothing. Replaced by data-newsletter-form, which posts to "
        "a real endpoint (T-1206)."
    ),
}

#: Baseline hooks that survive under a new name, with the replacement. Empty:
#: every surviving control kept its original hook (several were restored during
#: T-1609 review after the commerce rewrite had renamed them).
RENAMED: dict[str, str] = {}

#: Runtime template roots. A prototype hook reappearing here is a regression.
TEMPLATE_ROOT = BASE_DIR / "templates"
JS_ROOT = BASE_DIR / "static/src/js"


def _current_inventory() -> dict[str, list[str]]:
    raw = subprocess.run(
        [sys.executable, str(BASE_DIR / "scripts/list-data-hooks.py")],
        capture_output=True, text=True, cwd=BASE_DIR, check=True,
    ).stdout
    payload = json.loads(raw)
    for key in ("hooks", "attributes", "data_hooks"):
        if isinstance(payload.get(key), dict):
            return payload[key]
    return {k: v for k, v in payload.items() if isinstance(v, list)}


def _baseline_inventory() -> dict[str, list[str]]:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    for key in ("hooks", "attributes", "data_hooks"):
        if isinstance(payload.get(key), dict):
            return payload[key]
    return {k: v for k, v in payload.items() if isinstance(v, list)}


class HookContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.baseline = _baseline_inventory()
        cls.current = _current_inventory()

    def test_baseline_is_the_recorded_139(self):
        self.assertEqual(len(self.baseline), 139, "the T-0104 baseline changed size")

    def test_every_baseline_hook_is_accounted_for(self):
        """Present, renamed-with-a-mapping, or explicitly retired. Nothing else."""
        unexplained = []
        for hook in sorted(self.baseline):
            if hook in self.current:
                continue
            if hook in RETIRED or hook in RENAMED:
                continue
            unexplained.append(hook)
        self.assertEqual(
            unexplained,
            [],
            "baseline hooks vanished without a recorded reason — this is the "
            f"'unintended rename' T-1609 forbids: {unexplained}",
        )

    def test_retired_hooks_are_really_gone_from_runtime(self):
        """A retired hook must not linger in a template or a shipped script."""
        offenders = []
        for hook in RETIRED:
            for root in (TEMPLATE_ROOT, JS_ROOT):
                for path in root.rglob("*"):
                    if path.suffix not in {".html", ".js"} or not path.is_file():
                        continue
                    if hook in path.read_text(encoding="utf-8"):
                        offenders.append(f"{hook} -> {path.relative_to(BASE_DIR)}")
        self.assertEqual(
            offenders, [], f"retired prototype hooks are back in runtime code: {offenders}"
        )

    def test_no_shipped_script_consumes_a_missing_hook(self):
        """A script querying a hook that no template renders is a dead control."""
        rendered = set(self.current)
        dead = []
        pattern = re.compile(r"data-([a-z0-9-]+)")
        for path in JS_ROOT.rglob("*.js"):
            text = path.read_text(encoding="utf-8")
            # dataset.fooBar -> data-foo-bar; only selector strings are checked.
            for match in re.finditer(r"""\[data-([a-z0-9-]+)[\]=]""", text):
                hook = f"data-{match.group(1)}"
                if hook not in rendered:
                    dead.append(f"{path.relative_to(BASE_DIR)}: {hook}")
        self.assertEqual(
            dead, [], f"scripts query hooks no template renders (dead controls): {dead}"
        )

    def test_renamed_hooks_declare_their_replacement(self):
        missing = [
            f"{old} -> {new}"
            for old, new in RENAMED.items()
            if new not in self.current
        ]
        self.assertEqual(missing, [], f"declared replacements are absent: {missing}")

    def test_unique_hooks_are_not_duplicated_within_a_template(self):
        """Hooks that identify one control must not appear twice in one file."""
        unique_hooks = {
            "data-checkout-form",
            "data-cart-lines",
            "data-checkout-lines",
            "data-error-summary",
            "data-account-panels",
            "data-newsletter-form",
        }
        offenders = []
        for template in TEMPLATE_ROOT.rglob("*.html"):
            text = template.read_text(encoding="utf-8")
            for hook in unique_hooks:
                # Whole-attribute match: a plain substring count treats
                # `data-error-summary-list` as a second `data-error-summary`.
                occurrences = len(re.findall(rf"{re.escape(hook)}(?![a-z0-9-])", text))
                if occurrences > 1:
                    offenders.append(f"{template.relative_to(BASE_DIR)}: {hook}")
        self.assertEqual(offenders, [], f"duplicated unique hooks: {offenders}")
