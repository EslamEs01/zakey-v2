# Traceability: Requirements → Architecture → Contract → Verification → Phase

**Feature**: `001-premium-storefront-experience`
**Date**: 2026-07-31
**Constitution**: v1.1.0

**Last corrected**: 2026-08-01 (DEV-1 resolution: two-column product grid at 390px)

**Coverage: 121 FR + 46 NFR + 51 SC + 7 user stories + 13 reference defects + 18 principles +
6 deviations. Unmapped items: 0.**

Legend — Contract: `C-CATALOG` (catalog provider) · `C-SESSION` (session state) · `C-CHECKOUT`
(checkout/enquiry) · `C-VIEWMODEL` (template view models) · `C-HTTP` (HTTP/errors/PE).
Phase: P0–P12 from plan §14.

---

## 1. Functional Requirements (FR-001 … FR-121)

### Navigation, destinations, information architecture

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-001 | `templates/layout/`, `LayoutVM` | C-VIEWMODEL | view + template tests; visual QA cross-page | P1 |
| FR-002 | `announcement_bar.html`, `LayoutVM.announcement` | C-VIEWMODEL | template test both states (present/absent) | P1 |
| FR-003 | `header.html`, `LayoutVM` counts | C-VIEWMODEL, C-SESSION | template test; e2e count accuracy | P1, P6 |
| FR-004 | `mobile_nav.html` | C-HTTP (PE matrix) | responsive e2e at 768/390 | P1 |
| FR-005 | `nav.js` focus trap | C-HTTP | axe open-state; manual keyboard | P1, P10 |
| FR-006 | Header search entry, `search_action_url` | C-VIEWMODEL | e2e from multiple pages | P4 |
| FR-007 | `breadcrumbs.html`, `CrumbVM` | C-VIEWMODEL | template test; a11y landmark test | P4 |
| FR-008 | `NavItemVM.is_current` | C-VIEWMODEL | template test; axe | P1 |
| FR-009 | Semantic nav markup | — | manual keyboard pass | P10 |
| FR-010 | Named-route reversal only | C-HTTP | broken-link audit; control audit | P0, P11 |
| FR-011 | Homepage rail from `featured_products_slider` | C-CATALOG | template test; visual QA | P4 |
| FR-012 | `footer_groups` built from the route table | C-VIEWMODEL | broken-link audit | P1, P9 |
| FR-091 | URL conf, semantic paths (R-006) | C-HTTP | route test; share/reload e2e | P0 |
| FR-092 | Query-string state | C-HTTP | URL round-trip e2e | P4 |

### Product discovery

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-013 | `list_products`, pagination | C-CATALOG | contract test: all 21 reachable | P4 |
| FR-014 | Category routes/views | C-CATALOG | view test ×3 categories | P4 |
| FR-015 | Collection routes/views | C-CATALOG | view test ×6 collections | P4 |
| FR-016 | `ProductQuery` 3 facets | C-CATALOG | contract test facet precision | P4 |
| FR-017 | `SortOption` has no price/rating member | C-CATALOG | type-level; UI audit | P4 |
| FR-018 | OR-within / AND-across | C-CATALOG | contract test combinations | P4 |
| FR-019 | `AppliedFilterVM.remove_url` | C-VIEWMODEL | e2e single-filter removal | P4 |
| FR-020 | `clear_all_url` | C-VIEWMODEL | e2e clear-all | P4 |
| FR-021 | Query-string encoding | C-HTTP | round-trip e2e | P4 |
| FR-022 | `SortOption` enum | C-CATALOG | UI audit | P4 |
| FR-023 | `PaginationVM` | C-VIEWMODEL | view test; edge disabled | P4 |
| FR-024 | No-results empty state | C-VIEWMODEL | e2e zero-match | P4 |
| FR-025 | Filter drawer at narrow widths | C-HTTP | responsive e2e; axe open-state | P4, P10 |
| FR-026 | Search across name/model/brand/taxonomy | C-CATALOG | contract test per model code | P4 |
| FR-027 | Empty-query handling | C-HTTP | view test | P4 |
| FR-028 | Single `product_card.html` | C-VIEWMODEL | cross-page visual comparison | P4 |
| FR-121 | Product-grid responsive matrix (spec §8.1: 4/4/2/2, CG-1…CG-7) | C-VIEWMODEL | `product-grid-columns` audit at all four widths; overflow audit; target-size audit; US2.8; both critique passes at all four widths | P4, P12 |

### Product presentation and product truth

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-029 | `Product.display_name` | C-CATALOG | loader test vs governed data | P2 |
| FR-030 | `ProductImage` roles; hero asset | C-CATALOG | asset-manifest test | P3 |
| FR-031 | `ProductDetailVM` | C-VIEWMODEL | template test | P5 |
| FR-032 | `GalleryVM`, `gallery.js` | C-VIEWMODEL | e2e pointer/keyboard/touch | P5 |
| FR-033 | `GalleryVM.has_multiple` | C-VIEWMODEL | template test single-image | P5 |
| FR-034 | `price_display` / `price_on_request` | C-CATALOG, C-VIEWMODEL | view-model invariant test | P2, P5 |
| FR-035 | `specifications` omits unpopulated | C-CATALOG | loader + template test | P2, P5 |
| FR-036 | `availability_text` enquiry-based | C-VIEWMODEL | content audit | P5 |
| FR-037 | `get_related` excludes self | C-CATALOG | contract test | P5 |
| FR-038 | `BadgeVM` verified attributes only | C-VIEWMODEL | content audit | P4 |
| FR-039 | Detail information hierarchy | C-VIEWMODEL | visual QA | P5 |
| FR-040 | `attribution_note` | C-VIEWMODEL | content audit | P5 |
| FR-041 | `ImageVM.is_placeholder` | C-VIEWMODEL | template test | P3 |
| FR-111 | Non-optional `supplier_brand`/`_relationship` | C-CATALOG, C-VIEWMODEL | loader + view-model test | P2 |
| FR-112 | Verbatim carry-through from registers | C-CATALOG | loader diff vs governed data | P2 |
| FR-113 | Synthetic prices only in tests | — | content audit; fixture scan | P11 |

### Wishlist

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-042 | `WishlistService.toggle` | C-SESSION | service + e2e | P6 |
| FR-043 | `LayoutVM.wishlist_count` | C-SESSION | e2e across navigation | P6 |
| FR-044 | Wishlist page, move-to-cart, enquiry route | C-SESSION | e2e | P6 |
| FR-045 | Session-backed persistence | C-SESSION | SC-036 persistence e2e | P6 |
| FR-046 | Copy rules, `message_key` | C-SESSION | content audit | P6 |
| FR-047 | Silent stale drop on read | C-SESSION | service test | P6 |

### Enquiry and quote request

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-048 | Enquiry entry points (product/cart/review) | C-CHECKOUT | e2e each source | P8 |
| FR-049 | Line display + removal pre-submit | C-CHECKOUT | e2e | P8 |
| FR-050 | `Totals.computable` gate | C-CATALOG | service test | P8 |
| FR-051 | No payment field anywhere | C-CHECKOUT | form-field audit (project-wide) | P7, P11 |
| FR-052 | Commit-then-confirm; wording | C-CHECKOUT | fault injection; content audit | P8 |
| FR-053 | No control for deferred behaviour | C-HTTP | control audit | P11 |

### Forms

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-054 | `FieldVM.label` non-optional | C-VIEWMODEL | template + axe | P7 |
| FR-055 | Django forms server-side | C-CHECKOUT | form tests | P7 |
| FR-056 | `field_errors` + `form_errors` | C-CHECKOUT | form + template test | P7 |
| FR-057 | `first_invalid_field`, value retention | C-CHECKOUT | e2e invalid submit | P7 |
| FR-058 | Busy state + idempotency token | C-HTTP | e2e double-submit | P7 |
| FR-059 | Success only after success | C-CHECKOUT | fault injection | P8 |
| FR-060 | Honest failure + retry | C-HTTP | fault injection | P8 |
| FR-061 | Keyboard-complete forms | — | manual keyboard | P10 |
| FR-062 | 390px form layout | — | responsive e2e | P7 |
| FR-063 | No unverified destination/promise | — | content audit | P9 |

### Informational content

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-064 | `content/` Tier-G copy (R-018) | — | content audit | P9 |
| FR-065 | Verified legacy reuse | — | provenance note review | P9 |
| FR-066 | Untraceable claims removed | — | content audit | P9 |
| FR-067 | About page retailer framing | — | content audit | P9 |
| FR-068 | Contact form; no unverified details (R-019) | C-CHECKOUT | content audit | P9 |
| FR-069 | FAQ disclosure component | C-VIEWMODEL | axe; manual keyboard | P9 |
| FR-070 | Privacy/Terms render or are removed with links | C-VIEWMODEL | broken-link audit | P9 |

### Content source and architecture

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-071 | One `CatalogProvider` port | C-CATALOG | boundary audit | P2 |
| FR-072 | No hardcoded records in templates | C-VIEWMODEL | template-attribute audit | P2 |
| FR-073 | Adapter swap by setting | C-CATALOG | Feature 002 rehearsal test | P2 |
| FR-074 | Port is storage-agnostic | C-CATALOG | contract suite | P2 |
| FR-075 | One partial per component family | — | code review; visual comparison | P1 |
| FR-076 | `tokens.css` single authority | — | source-colour audit | P1 |
| FR-077 | `{% url %}` only | C-HTTP | source audit; broken-link | P0 |
| FR-078 | i18n keys, direction-aware primitives | — | code review | P1 |

### Cross-cutting states

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-079 | `loading_skeleton.html` at final dimensions | C-VIEWMODEL | CLS measurement | P10 |
| FR-080 | `empty_state.html` | C-VIEWMODEL | e2e each empty surface | P4, P6 |
| FR-081 | `error_state.html` | C-HTTP | e2e error paths | P0 |
| FR-082 | `checkout_blocked_reason` etc. | C-VIEWMODEL | template + axe | P6 |
| FR-083 | `aria-live` announcements | C-HTTP | axe; manual screen-reader spot check | P10 |
| FR-084 | Custom 404 | C-HTTP | view test | P0 |
| FR-085 | Custom 500 | C-HTTP | view test | P0 |
| FR-086 | Unknown slug → 404 | C-CATALOG, C-HTTP | view test | P4 |
| FR-087 | Autoescape; escaping audit | C-HTTP | escaping audit; XSS probe | P4 |
| FR-088 | Page clamp | C-CATALOG | contract test | P4 |
| FR-089 | Progressive enhancement | C-HTTP | no-JS e2e journey | P14 → P11 |
| FR-090 | Renders with bar absent/present, cart empty/full | C-VIEWMODEL | template matrix test | P1, P6 |

### Cart

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-093 | `CartService.add` | C-SESSION | service + e2e | P6 |
| FR-094 | Session persistence | C-SESSION | SC-035 persistence e2e | P6 |
| FR-095 | `CartLineVM` | C-VIEWMODEL | template test | P6 |
| FR-096 | `update` / `remove` | C-SESSION | service + e2e | P6 |
| FR-097 | Header cart count | C-SESSION | e2e | P6 |
| FR-098 | `Totals.computable` false ⇒ no total | C-CATALOG | service + template test | P6 |
| FR-099 | `resolve_lines` sole totalling routine | C-CATALOG | code audit; contract test | P2 |
| FR-100 | Empty cart; disabled checkout with reason | C-VIEWMODEL | e2e | P6 |
| FR-101 | Silent stale-line drop | C-SESSION | service test | P6 |
| FR-102 | Cart copy rules | C-SESSION | content audit | P6 |

### Checkout and order review

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-103 | Step flow, back preserves values | C-CHECKOUT | e2e | P7 |
| FR-104 | Server-side gate on review | C-CHECKOUT | view test direct-navigation | P7 |
| FR-105 | No payment step/selector/field | C-CHECKOUT | route + form audit | P7 |
| FR-106 | `OrderReviewVM` | C-VIEWMODEL | template test | P7 |
| FR-107 | `disclosure` non-optional | C-VIEWMODEL | template test | P7 |
| FR-108 | `actions` exactly 3 | C-CHECKOUT | control audit | P7 |
| FR-109 | No order record or order number | C-CHECKOUT | stored-state inspection | P8 |
| FR-110 | `cart_digest` stale guard | C-CHECKOUT | e2e two-tab | P7 |

### Colour identity and design tokens

| FR | Architecture component | Contract | Verification | Phase |
| --- | --- | --- | --- | --- |
| FR-114 | 18 values in `tokens.css` | — | token-count test; rendered-colour audit | P1 |
| FR-115 | Namespace reset; verified gradients only | — | source + rendered audits | P1 |
| FR-116 | One token authority; zero literals | — | source-colour audit | P1 |
| FR-117 | Same tokens across all surfaces | — | page-vs-home drift audit | P12 |
| FR-118 | Gold role restriction | — | contrast audit | P1, P10 |
| FR-119 | Last-resort shade procedure | — | plan review if invoked | P10 |
| FR-120 | Placeholder uses `muted` | — | contrast audit; rendered audit | P1, P10 |

---

## 2. Non-Functional Requirements (NFR-001 … NFR-046)

| NFR | Architecture component | Verification | Phase |
| --- | --- | --- | --- |
| NFR-001 | Plan §13 fidelity method | Two visual critique passes | P12 |
| NFR-002 | One design system, `tokens.css` | Cross-page comparison | P12 |
| NFR-003 | 18 colour + non-colour tokens | Token-value test vs constitution | P1 |
| NFR-004 | 4px/8px rhythm from tokens | Visual QA; spacing audit | P1 |
| NFR-005 | No dark mode / excess effects | Visual QA; rendered-colour audit | P12 |
| NFR-006 | Component reuse | Cross-page comparison | P12 |
| NFR-007 | Four-width design | Responsive e2e | P10 |
| NFR-008 | Deliberate layout per width (spec §8) | Visual QA | P12 |
| NFR-009 | `scrollWidth ≤ viewport` | Responsive-overflow audit | P10 |
| NFR-010 | No clipping/collision/dead zone | Visual QA | P12 |
| NFR-011 | Square-normalised media | Asset manifest; visual QA | P3 |
| NFR-012 | Dedicated responsive behaviours | Responsive e2e | P10 |
| NFR-013 | 200% zoom | Manual + e2e | P10 |
| NFR-014 | A-1…A-20 | axe + manual | P10 |
| NFR-015 | axe zero incl. open states | axe suites | P10 |
| NFR-016 | Manual keyboard full journey | Manual pass | P10 |
| NFR-017 | Gold restriction | Contrast audit | P10 |
| NFR-018 | 24×24 / 44×44 targets | Target-size audit | P10 |
| NFR-019 | Focus trap, Escape, restore | axe open-state; manual | P10 |
| NFR-020 | `prefers-reduced-motion` | e2e with media emulation | P10 |
| NFR-021 | Derived alt text (R-017) | Template + axe | P3 |
| NFR-022 | `lang` / `dir` | Template test | P1 |
| NFR-023 | Unique titles | View test | P4 |
| NFR-024 | `aria-live` without focus steal | axe; manual | P10 |
| NFR-025 | PB-1…PB-4, PB-18 | Page-weight audit | P10 |
| NFR-026 | PB-5…PB-7 | Asset-budget report | P10 |
| NFR-027 | PB-8…PB-10, PB-19 | Web-vitals audit | P10 |
| NFR-028 | Zero console errors | Console audit | P10 |
| NFR-029 | Zero broken links | Broken-link audit | P10 |
| NFR-030 | Intrinsic dimensions always | Template test; CLS | P3 |
| NFR-031 | Lazy below fold; eager hero | DOM audit | P3 |
| NFR-032 | Local fonts/icons; no third-party | Network-trace audit | P1 |
| NFR-033 | Production build succeeds | Build command | P10 |
| NFR-034 | One adapter | Boundary audit | P2 |
| NFR-035 | Six focused JS modules | Code review; per-page budget | P7 |
| NFR-036 | No legacy frontend copied | Code review | P0 |
| NFR-037 | No Figma runtime code | Code review | P1 |
| NFR-038 | Legacy repo unmodified | Status + HEAD check | all |
| NFR-039 | CSRF + session-key cycling | View test | P0, P6 |
| NFR-040 | Server-side validation | Form tests | P7 |
| NFR-041 | No payment credential | Form-field audit | P7 |
| NFR-042 | Log hygiene | Code review | P0 |
| NFR-043 | Checkout data purpose-bound | Code review; model test | P7 |
| NFR-044 | Palette documented pre-implementation | Plan §4 (done) | P1 |
| NFR-045 | One token authority, zero literals | Source-colour audit | P1 |
| NFR-046 | Cross-page palette at 4 widths, both passes | Rendered-colour audit; visual QA | P12 |

---

## 3. Success Criteria (SC-001 … SC-050)

| SC | Verification mechanism | Phase |
| --- | --- | --- |
| SC-001 | Render all 21 surfaces at 4 widths | P12 |
| SC-002 | Contract test: all 21 products reachable by browsing | P4 |
| SC-003 | Control audit + manual inspection | P11 |
| SC-004 | Broken-link audit | P10 |
| SC-005 | Component-reuse code review | P11 |
| SC-006 | Cross-page component comparison, pass 2 | P12 |
| SC-007 | RF-1…RF-12 comparison, inspected screenshots | P12 |
| SC-008 | Responsive-overflow audit | P10 |
| SC-009 | Visual QA at all widths | P12 |
| SC-010 | axe zero violations | P10 |
| SC-011 | Manual keyboard journey | P10 |
| SC-012 | Focus-indicator contrast audit | P10 |
| SC-013 | Target-size audit | P10 |
| SC-014 | Contrast audit (gold-as-text) | P10 |
| SC-015 | Facet-precision contract test, 15 values | P4 |
| SC-016 | URL round-trip e2e | P4 |
| SC-017 | Search e2e per model code | P4 |
| SC-018 | No-results e2e | P4 |
| SC-019 | Content-integrity audit | P11 |
| SC-020 | Internal-terminology audit | P11 |
| SC-021 | Loader diff vs governed registers | P2 |
| SC-022 | Form-field audit (payment) | P7 |
| SC-023 | Fault injection | P8 |
| SC-024 | Form + checkout validation tests | P7 |
| SC-025 | Console-error audit | P10 |
| SC-026 | Page-weight + asset-budget reports | P10 |
| SC-027 | Web-vitals audit | P10 |
| SC-028 | DOM audit (dimensions, lazy) | P3 |
| SC-029 | Network-trace audit | P10 |
| SC-030 | Production build | P10 |
| SC-031 | Boundary + template-attribute audits | P2 |
| SC-032 | Legacy status + HEAD check | all |
| SC-033 | Control audit vs spec §19 | P11 |
| SC-034 | This document | — |
| SC-035 | Cart persistence e2e (5 navigations + reload) | P6 |
| SC-036 | Wishlist persistence e2e | P6 |
| SC-037 | Review-gating view test | P7 |
| SC-038 | Control + visible-copy audit | P11 |
| SC-039 | Payment-surface audit | P7 |
| SC-040 | Totals derivation test | P6 |
| SC-041 | Attribution audit across all 21 | P5 |
| SC-042 | Synthetic-price scan of content, fixtures, screenshots | P11 |
| SC-043 | Destination share/reload e2e | P4 |
| SC-044 | Stored-state inspection after full journey | P8 |
| SC-045 | Plan §4 palette table (documented pre-implementation) | P1 |
| SC-046 | Source-colour audit | P1 |
| SC-047 | Rendered-colour audit | P12 |
| SC-048 | Page-vs-homepage drift audit at 4 widths | P12 |
| SC-049 | Colour comparison recorded in both critique passes | P12 |
| SC-050 | Contrast audit (all pairings; gold; `#9CA3AF`) | P10 |
| SC-051 | Product-grid column audit at 390px + overflow + target-size audits; inspected in both critique passes | P4, P12 |

---

## 4. User Stories

| Story | Priority | Architecture | Independent-test mechanism | Phase |
| --- | --- | --- | --- | --- |
| US1 Understand ZAKEY and enter the range | P1 | Home view, hero, category/featured/value/series sections, footer | Playwright home journey at 4 widths; link sweep | P4 |
| US2 Browse and narrow the range | P1 | Listing, `ProductQuery`, filter panel, sort, pagination | Facet/sort/paginate/clear e2e incl. 390px drawer | P4 |
| US3 Inspect one product | P1 | Detail view, gallery, specs, attribution, related | Per-product e2e; attribute audit vs registers | P5 |
| US4 Collect products across the visit | P1 | `CartService`, `WishlistService`, counts, drawer | Persistence e2e (5 navigations + reload) | P6 |
| US5 Search for a specific model | P2 | Search view, provider search | Model-code search e2e; no-results; empty query | P4 |
| US6 Supply details, reach truthful review | P2 | Checkout steps, validation, `OrderReviewVM`, enquiry | Full checkout e2e incl. invalid, back-nav, stale cart | P7, P8 |
| US7 Read public information | P3 | About, Contact, FAQ, footer | Reachability + content audit at 4 widths | P9 |

---

## 5. Reference Defects (RD-1 … RD-13) — correction and proof

| RD | Defect | Correction in plan | Proof |
| --- | --- | --- | --- |
| RD-1 | Gold as text on light | Eyebrow keeps placement/size/weight/tracking; colour → `ink`/`navy` (§4) | Contrast audit; SC-014 |
| RD-2 | Fabricated product identities | Names come from the governed registers only | Loader diff; SC-021 |
| RD-3 | Fabricated prices | `price is None` ⇒ price-on-request; loader fails closed on a price | Content audit; SC-019 |
| RD-4 | Fabricated ratings/reviews | No rating field, no review surface; `gray-200` star colour not ratified | Content audit; rendered-colour audit |
| RD-5 | Fabricated awards/press | No such section or badge exists | Content audit |
| RD-6 | Fabricated scale claims | No counters or trust metrics | Content audit |
| RD-7 | Fabricated specs/guarantees | Only 5 allowlisted spec fields; no warranty/delivery/tax | Loader allowlist; content audit |
| RD-8 | Fabricated people | No leadership or testimonial section | Content audit |
| RD-9 | Card-data collection | No payment field exists anywhere | Form-field audit; SC-022 |
| RD-10 | Unsuitable hero image | Hero uses a verified ZAKEY smart-lock asset | Asset manifest; visual QA |
| RD-11 | Popularity merchandising | One featured rail; no popularity sort member | UI audit; SC-019 |
| RD-12 | Unverified announcement | Bar renders only with verified content | Template matrix test |
| RD-13 | `#9CA3AF` placeholder fails contrast | Placeholder uses `muted` `#6B7280` | Contrast audit; FR-120; SC-050 |

---

## 6. Constitutional Principles (I … XVIII)

| Principle | Where satisfied in the plan | Verification |
| --- | --- | --- |
| I Reference-led fidelity | §13 method; RD-1…RD-13; DEV-1…DEV-6 | Two critique passes; SC-007 |
| II Brand system | §4 tokens; 18 values; namespace reset | Source + rendered colour audits |
| III Technical foundation | §1 stack; zero new dependencies | Network-trace audit; build |
| IV Clean-room architecture | §2, §3, §5; one adapter; focused modules | Boundary audit; code review |
| V Content and asset integrity | R-001/017/018/019; fail-closed loader; manifest | Content-integrity audit |
| VI Functional completeness | §6 routes; C-HTTP; one totalling routine | Control audit; fault injection |
| VII Responsive design | Spec §8; §13 widths | Overflow audit; visual QA |
| VIII Accessibility | §9; DEV-3/4/5 exceed the reference | axe + manual |
| IX Performance | §10 budgets preserved | Weight, vitals, asset reports |
| X Security | §11 threat table | View/form tests; audits |
| XI Specification-first | This document; §15 boundary | Traceability review |
| XII Test-first acceptance | §12; quickstart §12 sequence | Recorded commands and results |
| XIII Visual QA | §13 two passes, inspected screenshots | Recorded observations |
| XIV Code quality | P11 guard skills; reviewed migrations | ruff, prettier, guards |
| XV Git safety | Branch only; no Git ops in planning | Status + HEAD check |
| XVI Claude governance | Opus lead; 2 bounded read-only agents | This artifact set |
| XVII LeanCtx discipline | Targeted inspection; evidence in artifacts | Artifact completeness |
| XVIII Definition of Done | P11–P12 reach all fifteen conditions | Acceptance checklist |

---

## 7. Deviations (DEV-1 … DEV-6)

Full ledger in `plan.md` §13. Summary mapping:

| DEV | Kind | Affected requirements | Verification | **Decision status** | Implementation |
| --- | --- | --- | --- | --- | --- |
| DEV-1 | Spec-vs-reference conflict, product-grid matrix (1024px **and** 390px) | spec §8 + §8.1, FR-121, SC-051, US2.8, NFR-008, RF-3 | grid-column audit at 4 widths, overflow audit, target-size audit, both critique passes | **CLOSED — specification corrected** (4/4/2/2) | Pending |
| DEV-2 | Accepted improvement — pinned mobile action bars | spec §8, A-11, NFR-018 | responsive e2e (no overlap/obscuring), target-size audit, manual keyboard, both critique passes | **CLOSED — accepted improvement** | Pending |
| DEV-3 | **Rejected reference defect** — no focus indicators | A-4, NFR-017, SC-012 | focus-contrast audit, axe, manual keyboard | **CLOSED — rejected reference defect** | Corrective implementation pending |
| DEV-4 | **Rejected reference defect** — no reduced motion | A-15, NFR-020 | reduced-motion emulation run + inspected screenshot | **CLOSED — rejected reference defect** | Corrective implementation pending |
| DEV-5 | **Rejected reference defect** — zero ARIA | A-6, A-12, A-14, NFR-024, SC-010, SC-011 | axe (all pages + open states), manual keyboard/SR check | **CLOSED — rejected reference defect** | Corrective implementation pending |
| DEV-6 | Accepted improvement — responsive section padding <768px | spec §8, RF-2 | RF-2 rhythm comparison at 4 widths, both critique passes | **CLOSED — accepted improvement** | Pending |

**Every deviation decision is CLOSED. Zero are ambiguous. Zero are deferred to task generation.**
Implementation is pending for all six only because implementation has not started — decision status
and implementation status are reported as two separate facts.

---

## 8. Coverage summary

| Dimension | Total | Mapped | Unmapped |
| --- | --- | --- | --- |
| Functional requirements | 121 | 121 | **0** |
| Non-functional requirements | 46 | 46 | **0** |
| Success criteria | 51 | 51 | **0** |
| User stories | 7 | 7 | **0** |
| Reference defects | 13 | 13 | **0** |
| Constitutional principles | 18 | 18 | **0** |
| Deviations | 6 | 6 | **0** |
| **Total** | **262** | **262** | **0** |
