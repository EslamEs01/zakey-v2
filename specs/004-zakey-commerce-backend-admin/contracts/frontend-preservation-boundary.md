# Contract: Frontend Preservation Boundary

**Feature**: 004-zakey-commerce-backend-admin
**Status**: Binding on every task. Violating it fails review regardless of test results.

---

## 1. The rule

> The backend is designed around the frontend. The frontend is not redesigned around the backend.

The storefront delivered by Specification 003 was visually approved. This feature replaces its data source. It does not restyle, restructure, rebuild or "improve" it.

---

## 2. Protected — MUST NOT change

**Routing**: all 13 URLs; all 13 route names; `<slug>` patterns; the 9 product / 6 collection / 4 category slugs; 404 and 500 behaviour.

**Structure**: page structure; section order; heading hierarchy; template inheritance; the 4 components (`product_card`, `catalogue_filters`, `newsletter`, `icon`); header; footer.

**Visual identity**: colours; typography (Cairo, Poppins); spacing (8px system); the 12-column grid; 12px radii; shadows; imagery; iconography; light-mode-only.

**Content and language**: all Arabic copy; `dir="rtl"`; `lang="ar-EG"`; `ج.م` currency label; Arabic validation messages.

**Behaviour**: gallery; filters; search; sort; pagination; cart, wishlist, checkout and account interfaces; drawers; dialogs; tabs; accordions; animations; reduced-motion.

**Accessibility**: landmarks; heading order; focus management and restoration; focus trapping; live regions; `aria-*`; keyboard navigation (including the RTL arrow mapping at `account.js:5` and `product.js:55`); touch targets; contrast.

**Responsive**: behaviour at 1440 / 1024 / 768 / 390.

**Architecture**: Tailwind; native ES modules; no CDN; **no React, Vue, Svelte, Alpine, HTMX or any SPA framework**; no second public theme.

**JS hook surface**: the **139 `data-*` attributes** baselined in T-0104. Renaming one is a breaking change requiring a matching JS edit, an explicit note, and a visual gate.

---

## 3. Permitted integration changes — and only these

1. Replace `fixture_provider` calls with services/QuerySets **behind the same template context keys**.
2. Add `method="post"`, `{% csrf_token %}` and hidden identifiers to existing forms.
3. Convert the `method="get"` demo forms (account, contact) to POST.
4. Replace hardcoded hrefs with `{% url %}`.
5. Replace `localStorage` state through an isolated adapter.
6. Render real authentication, cart, wishlist and order state into the regions already built for them.
7. Place validation messages into the existing `.field-error` and `[data-error-summary]` regions.
8. Add non-visual attributes for accessibility, testing or JS hooks.
9. Remove business rules from JavaScript once the server owns them, keeping presentation.
10. **Add shipping and installation rows to the existing order-summary component** — see §4.

Anything not on this list requires Claude's written approval before the task starts.

---

## 4. The two approved visual deltas

The prototype total is `subtotal − discount`; shipping and installation are never added, and `shippingOptions` contain no price (`frontend-contract.md` §1.2). A real store cannot render a correct total that way.

| Delta | Task | Bound |
|---|---|---|
| Shipping cost row in the summary | T-1604 (FR-041) | New row inside the existing summary component, existing markup pattern, existing Arabic label style |
| Installation cost row in the summary | T-1605 (FR-062) | Same |

Both are **deliberately re-baselined**: Claude reviews the screenshot diff, confirms only the intended rows changed, and records the approval in the task evidence. **Silent re-baselining is a review failure.** No other visual delta is approved anywhere in this feature.

---

## 5. Forbidden — no task may authorise

Redesigning a page · restyling components · changing the brand identity · replacing the Tailwind architecture · introducing a frontend framework · rebuilding a page from scratch · deleting an existing interaction · changing responsive behaviour without evidence of a functional defect · changing copy or imagery unnecessarily · adding a second customer-facing theme · **letting Jazzmin styling reach the storefront**.

Jazzmin themes the staff admin only (FR-100). T-1301 explicitly verifies the storefront renders unchanged after Jazzmin is installed.

---

## 6. The gate

Every task touching `templates/` or `static/` runs, and must pass:

| Check | Pass condition |
|---|---|
| Visual regression | No diff vs. the T-0102b baseline at 1440/1024/768/390, except an approved §4 delta |
| Routes | All 13 names and URLs resolve identically |
| Slugs | All 19 slugs resolve |
| Console | Zero errors on every route × viewport |
| Overflow | `scrollWidth <= clientWidth` everywhere |
| RTL | `dir="rtl"` intact, no LTR leakage |
| Accessibility | No new critical or serious axe violation |
| Assets | No 404 |
| No-JS | Existing no-JS suite passes |
| HTML | `npm run check:html` clean |
| Hooks | `data-*` inventory matches the T-0104 baseline |

**Failing any check blocks the task.** The fix is to correct the change, never to update the baseline to match — except for the two §4 deltas, with recorded approval.

---

## 7. Batch reversibility

Phase 16 is six independent batches (T-1601…T-1606). Each is revertible on its own: one page group, one commit boundary, one gate run. A failing batch reverts without disturbing the others, so integration can never leave the storefront in a half-broken state.
