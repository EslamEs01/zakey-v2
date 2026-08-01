# Specification Quality Checklist: ZAKEY v2 Premium Egyptian Storefront

**Purpose**: Validate specification completeness and quality before planning
**Created**: 2026-08-01
**Feature**: [spec.md](../spec.md)
**Constitution**: v2.0.1

No item is marked complete without evidence. Evidence is a section reference, a measured fact, or
a command result — never an assertion.

## Content Quality

- [x] CHK001 No implementation details beyond Constitution-ratified constraints — *spec.md names no framework, library, ORM, template engine, or file layout. §16 budgets are outcome-based; §17.3 entities describe meaning, not schema.*
- [x] CHK002 Focused on user value and business outcomes — *§1.2 states outcomes in customer terms; all 8 user stories are journeys, not components.*
- [x] CHK003 Written for non-technical stakeholders — *requirements are observable behaviours; §5 scenarios are Given/When/Then in plain language.*
- [x] CHK004 All mandatory template sections completed — *§§1–24 present; no section left as "N/A" without a reason.*
- [x] CHK005 No unresolved template placeholders or tokens — *verified mechanically against `spec.md`, the matrix, the provenance register, the inventory and the manifest: zero bracketed all-caps placeholders, zero deferred-item markers, zero argument tokens.*
- [x] CHK006 No unresolved-clarification markers — *verified mechanically: zero occurrences across all specification artifacts.*

## Requirement Completeness

- [x] CHK007 Requirements are testable and unambiguous — *each FR states an observable condition; forbidden vague phrases ("looks good", "premium enough", "works correctly", "fully responsive", "user-friendly", "similar to Figma") verified absent.*
- [x] CHK008 Success criteria are measurable — *all 22 SC entries carry a count, percentage, threshold, or zero-tolerance condition.*
- [x] CHK009 Success criteria are technology-agnostic — *SC-001–SC-022 reference user-observable outcomes only.*
- [x] CHK010 All acceptance scenarios defined — *8 user stories, 38 numbered Given/When/Then scenarios (counted mechanically), each with a stated Independent Test.*
- [x] CHK011 Edge cases identified — *15 edge cases EC-01–EC-15, each with required behaviour.*
- [x] CHK012 Scope clearly bounded — *§22 lists 11 excluded/deferred capabilities with owners; §1.3 states where the feature stops.*
- [x] CHK013 Dependencies and assumptions identified — *§19 (10 assumptions), §20 (8 dependencies with blocked-if consequences).*
- [x] CHK014 Requirement and success-criteria identifiers are unique — *verified mechanically: FR-001–FR-142 with no duplicate ID; BR-001–BR-016 unique; SC-001–SC-022 unique; NFR-001–NFR-010 unique.*
- [x] CHK015 No contradictory requirements — *the one structural tension (priced journey vs. quote-only evidence) is resolved explicitly by BR-010 and recorded as OQ-02 with a default, not left as a contradiction.*

## Visual Grounding

- [x] CHK016 Fresh browser grounding performed — *Chromium 148.0.7778.97, 2026-08-01, HTTP 200; 35 verified full-page captures retained at 1440/1024/768/390 (43 taken; 8 deleted after content-hash and DOM-heading checks proved their labelled identity wrong).*
- [x] CHK017 No ungrounded visual claim — *`reference-fidelity-matrix.md` marks every page DIRECT or ADAPTATION; **zero pages are DIRECT for a width lacking its own evidence**.*
- [x] CHK018 Every page mapped to inspected evidence — *matrix §1 covers all 9 in-scope page groups; §2 covers all 32 shared components.*
- [x] CHK019 Coverage gaps declared, not hidden — *`MANIFEST.md` "Coverage gaps"; matrix §3 marks ⬜ for About and Contact at 768/390 and My Account at 390; RP-07 blocks implementation of those pages until captured. Catalog is grounded at all four widths via the `catalog-via-view-*` captures.*
- [x] CHK020 Reference defects recorded with a permitted correction basis — *17 defects RD-01–RD-17, each mapped to one of the six permitted grounds; matrix §4 maps each to a requirement.*
- [x] CHK021 Deviations documented with justification — *15 deviations D-01–D-15 with reference behaviour, ZAKEY behaviour, category, and basis.*
- [x] CHK022 No Figma runtime code copied — *only rendered geometry, computed styles, and text were measured; no source extracted or reused (inventory §12, XIX.8).*
- [x] CHK023 Ratified tokens confirmed against the live reference — *all 7 core/support tokens observed with occurrence counts (inventory §1).*

## Content Integrity

- [x] CHK024 No invented content — *§11 and `content-asset-provenance.md` §4 enumerate every prohibited claim; FR-111 forbids publication.*
- [x] CHK025 Every material fact has recorded provenance — *provenance register §2 (VERIFIED), §3 (USER-AUTHORIZED), §4 (UNVERIFIED with required behaviour).*
- [x] CHK026 Unverified content is hidden, not fabricated — *FR-026, FR-028, FR-060, FR-062, FR-063 require omission; SC-002 asserts 100% traceability.*
- [x] CHK027 Development fixtures cannot reach production — *FR-112; provenance §5; the 2,190–7,490 EGP range is confined to isolated fixtures.*
- [x] CHK028 No development vocabulary in production UI — *FR-113; SC-021 asserts zero occurrences.*
- [x] CHK029 Price claims honest — *21/21 approved products verified `retail_price: null`, `commerce_mode: quote_only`; BR-010 makes quote-only the default; SC-018 asserts zero unpriced products show a price or cart action.*

## Every Page Has Complete State Coverage

- [x] CHK030 Success behaviour defined per page — *§10 success column for all 9 surface groups.*
- [x] CHK031 Empty behaviour defined — *§10 empty column; FR-044, FR-045, FR-075, FR-106.*
- [x] CHK032 Loading behaviour defined where applicable — *§10 loading column.*
- [x] CHK033 Validation behaviour defined — *FR-065, FR-073, FR-084, FR-094, FR-103, FR-110, FR-117, FR-126.*
- [x] CHK034 Error and recovery behaviour defined — *§10 error column; FR-137–FR-142; EC-05, EC-07.*
- [x] CHK035 Disabled behaviour defined with a stated reason — *§8 "If unavailable" column for every control; FR-011 forbids unexplained disabled controls.*

## Controls and Functional Completeness

- [x] CHK036 Every visible control has defined intent — *§8 inventory covers 33 control types with trigger, behaviour, and unavailable presentation.*
- [x] CHK037 No dead controls, no `href="#"`, no fake success — *FR-011, FR-092, FR-142; SC-005, SC-006. Reference defects RD-08 and RD-16 explicitly corrected.*
- [x] CHK038 Unavailable capabilities are honestly presented — *FR-089; §13 status table; BR-015.*

## Monetary and Egyptian Market Rules

- [x] CHK039 Monetary rules consistent across surfaces — *BR-008 identity required on cart, checkout, review, confirmation; SC-007; NFR-010 forbids stale totals.*
- [x] CHK040 VAT rule unambiguous — *BR-005: 14% of the taxable base via one shared tested routine; SC-008.*
- [x] CHK041 Free-shipping rule unambiguous — *BR-006: free at subtotal ≥ 1,500 EGP, else configured charge, with shortfall stated; SC-009.*
- [x] CHK042 Decimal-safe money required — *BR-007 prohibits binary floating point and requires centralized rounding.*
- [x] CHK043 Currency centralized — *BR-001 single `ج.م` formatter; SC-010 asserts zero independent formatting.*
- [x] CHK044 All 27 governorates required — *FR-083; SC-011.*
- [x] CHK045 Egyptian phone behaviour defined — *FR-084 server-side validation with field-linked Arabic error; SC-012.*
- [x] CHK046 Address and delivery rules defined — *FR-085 detailed address + landmark; FR-086, FR-087 configuration-driven; BR-016.*
- [x] CHK047 Payment states truthful — *§13; FR-089, FR-090, FR-092; BR-013–BR-015; SC-019.*
- [x] CHK048 Installments derive from the authoritative price — *FR-088, BR-011.*

## Localization and RTL

- [x] CHK049 RTL requirements concrete — *FR-097 (`lang="ar"`, `dir="rtl"`), FR-101 (bidirectional ordering), FR-131 (RTL reading and focus order); SC-013. Not expressed as "supports RTL".*
- [x] CHK050 Arabic-first copy required — *FR-102 makes machine-literal phrasing a defect; §19.8 assumption names the reviewer requirement.*
- [x] CHK051 Typography rule recorded — *FR-098 Cairo primary, Poppins Latin-only; recorded as ratified deviation D-02.*

## Responsive

- [x] CHK052 Every page has responsive behaviour at all four widths — *§9 covers 14 surface rows × 4 widths with concrete column counts and gaps, derived from measured reference values.*
- [x] CHK053 Responsive stated as observable outcomes — *§9 uses measured column counts, gaps and container widths; SC-003 asserts zero overflow. No page is described merely as "mobile-friendly".*
- [x] CHK054 Zero-overflow requirement present — *SC-003, FR-048; corrects measured reference defect RD-05.*
- [x] CHK055 Responsive evidence recorded per page — *matrix §3 coverage table; gaps declared where evidence is absent.*

## Accessibility

- [x] CHK056 Accessibility requirements measurable — *FR-119–FR-132 with explicit ratios (≥4.5:1, ≥3:1) and sizes (≥24×24, ≥44×44).*
- [x] CHK057 Both automated and manual verification required — *FR-129 axe + manual keyboard pass; SC-004, SC-014.*
- [x] CHK058 Focus management specified — *FR-124 trap, Escape, focus return; SC-015; corrects RD-04.*
- [x] CHK059 Accessible names required for icon controls — *FR-122; corrects the measured RD-02 defect where 4/4 icon controls had none.*
- [x] CHK060 Gold-on-light contrast constraint carried — *FR-123 forbids `#C9A227` as normal-size text on `#FFFFFF`/`#F8F9FB`.*

## Security and Privacy

- [x] CHK061 Server-side validation required — *FR-117; client validation explicitly assistance only.*
- [x] CHK062 CSRF, escaping, redirect safety required — *FR-116, FR-118, FR-133.*
- [x] CHK063 No raw card data anywhere — *FR-090, BR-013.*
- [x] CHK064 Secrets configuration-driven — *FR-134, BR-014.*
- [x] CHK065 Personal data protected in URLs, errors, and logs — *FR-135, FR-136; non-enumerating auth errors FR-140.*

## Feature Readiness

- [x] CHK066 All functional requirements have acceptance criteria — *§24 maps every FR block to at least one SC; zero unmapped.*
- [x] CHK067 User scenarios cover primary flows — *discovery, enquiry, filtering, purchase, address, payment, account, contact.*
- [x] CHK068 Exclusions prevent scope expansion — *§22 with owning future specifications; Constitution VI.2 forbids rendering controls for excluded capabilities.*
- [x] CHK069 Traceability complete — *§24: 142 FR + 16 BR + 10 NFR all mapped; 22 SC all reachable.*
- [x] CHK070 Ready for planning — *no blocking ambiguity; two open questions carry specified defaults (OQ-01, OQ-02).*

## Definition of Done (Constitution Principle XVIII — REQUIRED on any acceptance checklist)

These twenty conditions are not samples and MUST NOT be deleted from an acceptance checklist. At
the **specification** stage they are recorded as *reachable*, not *achieved* — they are verified at
acceptance, after implementation.

- [ ] DOD01 All in-scope requirements are implemented
- [ ] DOD02 Every requirement is traceable to an acceptance criterion — *reachable: §24 mapping complete*
- [ ] DOD03 All required tests pass
- [ ] DOD04 All required manual checks are completed
- [ ] DOD05 All required visual checks are completed
- [ ] DOD06 All captured screenshots have been inspected, and the observations are recorded
- [ ] DOD07 Responsive behavior is verified at all four approved widths, with zero unintended horizontal overflow — *reachable: §9 + SC-003*
- [ ] DOD08 Accessibility is verified by both automated and manual means, with no unresolved critical or serious violation — *reachable: FR-129 + SC-004*
- [ ] DOD09 Production assets build successfully, including the production Tailwind build
- [ ] DOD10 No dead controls remain, and every visible control has been exercised — *reachable: §8 + SC-005*
- [ ] DOD11 No unexpected console errors remain — *reachable: NFR-006 + SC-016*
- [ ] DOD12 Documentation is current
- [ ] DOD13 Known limitations are truthfully recorded — *reachable: §17.5, §21, MANIFEST gaps*
- [ ] DOD14 Unrelated user work remains untouched
- [ ] DOD15 The final report includes the exact commands executed and their exact results
- [ ] DOD16 Every implemented page and component cites the Principle XIX grounding evidence it was built and compared against — *reachable: `reference-fidelity-matrix.md`*
- [ ] DOD17 Arabic-first and RTL correctness is verified — *reachable: FR-097–FR-102, FR-131, SC-013*
- [ ] DOD18 Every visible business claim, asset, and price carries documented provenance — *reachable: `content-asset-provenance.md` + SC-002*
- [ ] DOD19 Every external integration is genuinely implemented and verified, or presented honestly as unavailable/integration-ready — *reachable: §13 + SC-019*
- [ ] DOD20 Two documented visual critique and correction passes have been completed — *reachable: §14 review method*

## Result

**70 of 70 specification-quality items pass.** The twenty Definition-of-Done conditions are
recorded as reachable and remain open until acceptance, which is correct at the specification
stage.

## Notes

- Two open questions carry specified defaults and do **not** block planning:
  **OQ-01** corner radius (reference 16px vs ratified 12px) — a governance amendment question, not
  a specification defect; ratified 12px applies until amended.
  **OQ-02** no verified retail price exists — quote-only is the specified default (BR-010).
- **RP-07** is a real precondition: About and Contact must be captured at 768 and 390, and My
  Account at 390, before those pages are implemented. It does not block planning.
- Eight captures were deleted rather than retained under labels their content did not support.
  That is recorded in `MANIFEST.md` under "Integrity policy applied to this set".
