# Specification Quality Checklist: ZAKEY v2 Premium Egyptian Storefront

**Purpose**: Validate specification completeness and quality before planning
**Created**: 2026-08-01
**Revalidated**: 2026-08-01 — full re-run after the COR-001…COR-012 correction pass
**Feature**: [spec.md](../spec.md)
**Constitution**: v2.0.1

No item is marked complete without evidence. Evidence is a section reference, a measured fact, or a
command result — never an assertion. **Every item below was re-evaluated from the corrected live
artifacts. The previous `70/70` result was not carried forward**; seventeen items were found
insufficiently evidenced before this pass and are re-evidenced here.

## Content Quality

- [x] CHK001 No implementation details beyond Constitution-ratified constraints — *spec.md names no framework, library, ORM, template engine, or file layout. §16 budgets are outcome-based; §17.3 entities describe meaning, not schema. §17.1.1 states an order of operations, not code.*
- [x] CHK002 Focused on user value and business outcomes — *§1.2 states outcomes in customer terms; all 8 user stories are journeys, not components.*
- [x] CHK003 Written for non-technical stakeholders — *requirements are observable behaviours; §5 scenarios are Given/When/Then in plain language; §17.1.2 examples are arithmetic tables.*
- [x] CHK004 All mandatory template sections completed — *§§1–24 present, plus new §12.1, §14.1, §17.1.1, §17.1.2, §17.2.1 and the §9.1–§9.5 responsive breakdown.*
- [x] CHK005 No unresolved template placeholders or tokens — *verified mechanically across all six artifacts: zero bracketed all-caps placeholders, zero deferred-item markers, zero argument tokens.*
- [x] CHK006 No unresolved-clarification markers — *verified mechanically: zero occurrences.*

## Requirement Completeness

- [x] CHK007 Requirements are testable and unambiguous — **re-evidenced.** *Previously this passed while "taxable base" was undefined and "AI-style" was subjective. Both are now observable: BR-017 defines the taxable base as an equation; BR-018 fixes the single rounding point; §14.1 VI-1…VI-10 convert every visual-integrity term into a measurement with a stated failure condition. Forbidden vague phrases re-verified absent (6 checked, 0 occurrences); "responsive"/"stacked as needed"/"mobile-friendly" are explicitly barred as row values by §9.*
- [x] CHK008 Success criteria are measurable — *all 29 SC entries carry a count, percentage, threshold, or zero-tolerance condition. SC-023 names exact totals 1,436.40 / 1,710.00 / 1,604.86; SC-025 names 197.09.*
- [x] CHK009 Success criteria are technology-agnostic — *SC-001–SC-029 reference user-observable outcomes only.*
- [x] CHK010 All acceptance scenarios defined — **re-evidenced.** *Previously 38 scenarios, with no coverage of the calculation contract, city/area, feature/access-method filters, sorting, card category, product identifiers, or account profile. Now **60** scenarios (counted mechanically), each story carrying a stated Independent Test. The 22 scenarios added by this pass are listed in the §24 added-requirement mapping.*
- [x] CHK011 Edge cases identified — *15 edge cases EC-01–EC-15, each with required behaviour.*
- [x] CHK012 Scope clearly bounded — *§22 lists 11 excluded/deferred capabilities with owners; §1.3 states where the feature stops; the COR-007 scope ceiling is honoured — no loyalty, CRM, or fulfilment requirement was added.*
- [x] CHK013 Dependencies and assumptions identified — *§19 (10 assumptions), §20 (8 dependencies with blocked-if consequences).*
- [x] CHK014 Requirement and success-criteria identifiers are unique — *verified mechanically after correction: FR-001–FR-163 (163, no duplicates, no gaps); BR-001–BR-019 (19); SC-001–SC-029 (29); NFR-001–NFR-010 (10). No established identifier was renumbered; all new IDs were appended.*
- [x] CHK015 No contradictory requirements — *the priced-vs-quote-only tension is resolved by BR-010 and recorded as OQ-02. BR-006 explicitly resolves the discount-vs-threshold interaction that was previously undefined, and Example C is its regression case.*

## Visual Grounding

- [x] CHK016 Fresh browser grounding performed — *Chromium 148.0.7778.97, 2026-08-01, HTTP 200; 35 verified full-page captures retained at 1440/1024/768/390 (43 taken; 8 deleted after content-hash and DOM-heading checks proved their labelled identity wrong). No PNG was altered or regenerated in this correction pass.*
- [x] CHK017 No ungrounded visual claim — *`reference-fidelity-matrix.md` marks every page DIRECT or ADAPTATION; the §9.1–§9.5 responsive rows each carry an explicit D/A class; zero rows claim DIRECT for a width lacking its own evidence.*
- [x] CHK018 Every page mapped to inspected evidence — *matrix §1 covers all 9 in-scope page groups; §2 covers all 32 shared components.*
- [x] CHK019 Coverage gaps declared, not hidden — *`MANIFEST.md` "Coverage gaps"; matrix §3 marks ⬜ for About and Contact at 768/390 and My Account at 390; RP-07 blocks implementation of those pages until captured. Catalog is grounded at all four widths via the `catalog-via-view-*` captures.*
- [x] CHK020 Reference defects recorded with a permitted correction basis — *17 defects RD-01–RD-17, each mapped to one of the six permitted grounds; matrix §4 maps each to a requirement.*
- [x] CHK021 Deviations documented with justification — *15 deviations D-01–D-15 with reference behaviour, ZAKEY behaviour, category, and basis. All 15 preserved unchanged by this pass.*
- [x] CHK022 No Figma runtime code copied — *only rendered geometry, computed styles, and text were measured; no source extracted or reused.*
- [x] CHK023 Ratified tokens confirmed against the live reference — *all 7 core/support tokens observed with occurrence counts (inventory §1).*

## Content Integrity

- [x] CHK024 No invented content — *§11 and `content-asset-provenance.md` §4 enumerate every prohibited claim; FR-111 forbids publication. The §17.1.2 worked examples are explicitly labelled specification calculation examples, not product prices, and are barred from production by their own note plus BR-009 and FR-111.*
- [x] CHK025 Every material fact has recorded provenance — *provenance register §2 (VERIFIED), §3 (USER-AUTHORIZED), §4 (UNVERIFIED with required behaviour). Filter facets added by COR-003 draw only on the already-verified `unlock_methods` and approved specification fields.*
- [x] CHK026 Unverified content is hidden, not fabricated — *FR-026, FR-028, FR-060, FR-062, FR-063, FR-150, FR-155, FR-156 require omission; SC-002 asserts 100% traceability.*
- [x] CHK027 Development fixtures cannot reach production — *FR-112; provenance §5; the 2,190–7,490 EGP range and the §17.1.2 example figures are confined to isolated fixtures and specification prose respectively.*
- [x] CHK028 No development vocabulary in production UI — *FR-113; SC-021 asserts zero occurrences.*
- [x] CHK029 Price claims honest — *21/21 approved products verified `retail_price: null`, `commerce_mode: quote_only`; BR-010 makes quote-only the default; FR-153 prevents any sort from presenting a quote-only product as priced; SC-018 and SC-028 assert both.*

## Every Page Has Complete State Coverage

- [x] CHK030 Success behaviour defined per page — **re-evidenced.** *§10 success column now covers 13 surface groups, adding Search results, 404, 5xx and Product gallery, which were previously absent.*
- [x] CHK031 Empty behaviour defined — **re-evidenced.** *§10 empty column; FR-044, FR-045, FR-075, FR-106; Wishlist empty and populated now appear explicitly in §9.4, and Search-results empty in §10.*
- [x] CHK032 Loading behaviour defined where applicable — **re-evidenced.** *§10 loading column now includes Search results and the Product gallery's reserved-ratio placeholder.*
- [x] CHK033 Validation behaviour defined — **re-evidenced.** *FR-065, FR-073, FR-084, FR-094, FR-103, FR-110, FR-117, FR-126, plus FR-145 (city/area) and FR-157 (profile). Checkout validation is now its own responsive row in §9.4.*
- [x] CHK034 Error and recovery behaviour defined — **re-evidenced.** *§10 error column; FR-137–FR-142; EC-05, EC-07; 404 and 5xx now carry both a §10 row and a §9.5 responsive row.*
- [x] CHK035 Disabled behaviour defined with a stated reason — **re-evidenced.** *§8 "If unavailable" column now covers every control type including the eight added by this pass; FR-011 forbids unexplained disabled controls.*

## Controls and Functional Completeness

- [x] CHK036 Every visible control has defined intent — *§8 inventory covers every control type with trigger, behaviour, and unavailable presentation.*
- [x] CHK037 No dead controls, no `href="#"`, no fake success — *FR-011, FR-092, FR-142; SC-005, SC-006. RD-08 and RD-16 explicitly corrected.*
- [x] CHK038 Unavailable capabilities are honestly presented — *FR-089; §13 status table; BR-015; FR-147 extends this to delivery/installation eligibility.*

## Monetary and Egyptian Market Rules

- [x] CHK039 Monetary rules consistent across surfaces — **re-evidenced.** *Previously BR-008 asserted an identity without defining its terms. Now §17.1.1 fixes the 8-step order of operations, BR-019 forbids independent recomputation, and US4-12 tests it. SC-007 and SC-023 assert reproduction to the cent on all four surfaces.*
- [x] CHK040 VAT rule unambiguous — **re-evidenced.** *BR-005 now points at BR-017's explicit taxable-base equation instead of an undefined "taxable base". BR-017 also states the taxable-vs-non-taxable shipping case. SC-008 and Examples A/B/C verify it.*
- [x] CHK041 Free-shipping rule unambiguous — **re-evidenced.** *BR-006 now names the assessment input (the BR-003 merchandise subtotal, pre-discount), states the threshold is inclusive, and settles the discount interaction. Example B tests the exact boundary; Example C tests eligibility retention. SC-024 asserts both.*
- [x] CHK042 Decimal-safe money required — **re-evidenced.** *BR-007 prohibits binary floating point at every layer; BR-018 fixes rounding to exactly one point (VAT, half-up, 2 dp) and forbids intermediate and repeat rounding. Example C (197.0878 → 197.09) is the regression case; SC-025 asserts it.*
- [x] CHK043 Currency centralized — *BR-001 single `ج.م` formatter; SC-010 asserts zero independent formatting.*
- [x] CHK044 All 27 governorates required — **re-evidenced.** *Previously FR-083 asserted "all 27" without naming them. §12.1 now records the canonical register with exact Arabic labels; all 27 verified present by mechanical string check; SC-026 asserts rendering.*
- [x] CHK045 Egyptian phone behaviour defined — **re-evidenced.** *FR-084 server-side validation with field-linked Arabic error; US5-2 and US5-10 test rejection and input preservation; SC-012.*
- [x] CHK046 Address and delivery rules defined — **re-evidenced.** *Previously the city/area field was missing entirely. FR-145 adds it; §12.1 defines locality handling for Greater Cairo, Alexandria, Mansoura and every other governorate; FR-147 bars dishonest inference; US5-6…US5-9 test them.*
- [x] CHK047 Payment states truthful — *§13; FR-089, FR-090, FR-092; BR-013–BR-015; SC-019.*
- [x] CHK048 Installments derive from the authoritative price — *FR-088, BR-011.*

## Catalogue Filters and Sorting

- [x] CHK049 Required filters all present — *category (FR-034), use-case (FR-035), availability (FR-036), price (FR-037), **verified-feature (FR-148)**, **access-method (FR-149)**. Facet-absence behaviour FR-150. US3-6, US3-7 test them; SC-027 asserts zero invented options.*
- [x] CHK050 Sorting contract testable — *FR-151 fixes the exact permitted sort set and bars "newest"/"popular"/"best rated"/"best selling"; FR-152 requires deterministic stable tie-breaking; FR-153 governs quote-only products in mixed sets; FR-154 requires URL persistence. US3-8…US3-11, SC-028.*

## Localization and RTL

- [x] CHK051 RTL requirements concrete — *FR-097 (`lang="ar"`, `dir="rtl"`), FR-101 (bidirectional ordering), FR-131 (RTL reading and focus order), FR-156 (Latin identifiers in Arabic text); SC-013.*
- [x] CHK052 Arabic-first copy required — *FR-102 makes machine-literal phrasing a defect; §19.8 names the reviewer requirement; §12.1 labels are Arabic.*
- [x] CHK053 Typography rule recorded — *FR-098 Cairo primary, Poppins Latin-only; recorded as ratified deviation D-02.*

## Responsive

- [x] CHK054 Every page has responsive behaviour at all four widths — **re-evidenced.** *Previously 14 rows covering pages only. §9 now carries **36** rows across five sub-tables covering the shell, overlays, all 9 Home sections including Smart Home Solutions, catalogue and its zero-result state, gallery, product card, cart empty/populated, wishlist empty/populated, all four checkout states, all three account states, About, Contact, Search results, 404 and 5xx.*
- [x] CHK055 Responsive stated as observable outcomes — **re-evidenced.** *Every row states column counts, gaps, container widths, sticky/stacking behaviour or tap-target sizes. §9 explicitly bars "responsive", "stacked as needed" and "mobile-friendly" as row values.*
- [x] CHK056 Zero-overflow requirement present — **re-evidenced.** *SC-003, FR-048; every §9 row is explicitly subject to SC-003; corrects measured reference defect RD-05.*
- [x] CHK057 Responsive evidence classified per row — **re-evidenced.** *Each §9 row carries D or A. Adaptation rows cite their composition basis in `reference-fidelity-matrix.md`; no row claims DIRECT without its own evidence.*

## Home Section Contracts

- [x] CHK058 All twelve sections contracted — *§17.2.1 carries 12 rows in the exact required order, each with purpose, required data, visible-content rules, interaction, empty/unavailable behaviour, responsive reference, verification requirement and acceptance IDs.*
- [x] CHK059 Unverified sections hidden — *Best Sellers, Customer Reviews and Brand Partners are marked "omitted entirely"; FR-021, FR-026, FR-028, EC-08, EC-09; no section is filled with generic content (FR-163).*

## Visual Integrity

- [x] CHK060 Binding visual constraints are testable — *FR-160–FR-163 and §14.1 VI-1…VI-10 convert light-only theme, navy-band semantics, AI-style imagery, empty area, gradients, glassmorphism, filler sections, animation and reduced motion into measurements with explicit failure conditions.*
- [x] CHK061 Acceptance tied to review — *§14.1 binds each criterion to the grounding evidence, §17.2.1 purposes, the ratified tokens and the §9 rows, checked in both required critique passes; SC-029.*

## Accessibility

- [x] CHK062 Accessibility requirements measurable — *FR-119–FR-132 with explicit ratios (≥4.5:1, ≥3:1) and sizes (≥24×24, ≥44×44).*
- [x] CHK063 Both automated and manual verification required — *FR-129 axe + manual keyboard pass; SC-004, SC-014.*
- [x] CHK064 Focus management specified — *FR-124 trap, Escape, focus return; SC-015; corrects RD-04; §9.1 carries it for the mobile panel, filter drawer and dialogs.*
- [x] CHK065 Accessible names required for icon controls — *FR-122; corrects the measured RD-02 defect where 4/4 icon controls had none.*
- [x] CHK066 Gold-on-light contrast constraint carried — *FR-123 forbids `#C9A227` as normal-size text on `#FFFFFF`/`#F8F9FB`.*

## Security and Privacy

- [x] CHK067 Server-side validation required — *FR-117; client validation explicitly assistance only; extended to FR-145 and FR-157.*
- [x] CHK068 CSRF, escaping, redirect safety required — *FR-116, FR-118, FR-133.*
- [x] CHK069 No raw card data anywhere — *FR-090, BR-013.*
- [x] CHK070 Secrets configuration-driven — **re-evidenced.** *FR-134, BR-014; BR-016 and FR-147 extend configuration-driven behaviour to delivery and installation eligibility.*
- [x] CHK071 Personal data protected in URLs, errors, and logs — **re-evidenced.** *FR-135, FR-136, FR-140, plus the new FR-159 cross-customer isolation requirement and its US7-8 scenario, which had no coverage before this pass.*

## Feature Readiness

- [x] CHK072 All functional requirements have acceptance criteria — **re-evidenced.** *§24 maps every FR block to at least one SC, including the eight new blocks; zero unmapped.*
- [x] CHK073 User scenarios cover primary flows — **re-evidenced.** *Discovery, enquiry, filtering and sorting, purchase with the full calculation contract, Egyptian address including city/area, payment, account including profile and saved details, contact. All 8 stories remain independently testable; no story was added — coverage was achieved by extending existing stories, as instructed.*
- [x] CHK074 Exclusions prevent scope expansion — *§22 with owning future specifications; Constitution VI.2 forbids rendering controls for excluded capabilities; the COR-007 scope ceiling is respected.*
- [x] CHK075 Traceability complete — **re-evidenced.** *§24: 163 FR + 19 BR + 10 NFR all mapped; 29 SC all reachable; the added-requirement→scenario table binds every requirement introduced in this pass.*
- [x] CHK076 Ready for planning — *no blocking ambiguity; two open questions carry specified defaults (OQ-01, OQ-02); RP-07 and RP-08 are declared preconditions, not blockers.*

## Definition of Done (Constitution Principle XVIII — REQUIRED on any acceptance checklist)

These twenty conditions are not samples and MUST NOT be deleted from an acceptance checklist. At
the **specification** stage they remain **open** — they are verified at acceptance, after
implementation. They are deliberately left unchecked.

- [ ] DOD01 All in-scope requirements are implemented
- [ ] DOD02 Every requirement is traceable to an acceptance criterion — *reachable: §24 mapping complete*
- [ ] DOD03 All required tests pass
- [ ] DOD04 All required manual checks are completed
- [ ] DOD05 All required visual checks are completed
- [ ] DOD06 All captured screenshots have been inspected, and the observations are recorded
- [ ] DOD07 Responsive behavior is verified at all four approved widths, with zero unintended horizontal overflow — *reachable: §9.1–§9.5 + SC-003*
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
- [ ] DOD20 Two documented visual critique and correction passes have been completed — *reachable: §14 review method + §14.1 criteria*

## Result

**76 of 76 specification-quality items pass**, each with directly cited evidence from the corrected
artifacts. The item set grew from 70 to 76 because this pass added checks that did not previously
exist — catalogue filters (CHK049), sorting (CHK050), Home section contracts (CHK058, CHK059), and
visual integrity (CHK060, CHK061) — and renumbered the sequence to stay contiguous.

**Seventeen items were re-evidenced rather than carried forward** — CHK007, CHK010, CHK030–CHK035,
CHK039–CHK042, CHK044–CHK046, CHK054–CHK057, CHK070–CHK073, CHK075 — because their prior evidence
was insufficient before this correction. None was left checked on the strength of the old result.

The twenty Definition-of-Done conditions remain **open**, which is correct at the specification
stage.

## Notes

- **OQ-01** corner radius (reference 16px vs ratified 12px) — a governance amendment question, not a
  specification defect; ratified 12px applies until amended.
- **OQ-02** no verified retail price exists — quote-only is the specified default (BR-010). The
  §17.1.2 worked examples exercise the priced path without asserting any product price.
- **RP-07** About and Contact must be captured at 768 and 390, and My Account at 390, before those
  pages are implemented. Not a planning blocker.
- Eight captures were deleted rather than retained under labels their content did not support; see
  `MANIFEST.md` "Integrity policy applied to this set". **No PNG was altered, regenerated or removed
  in this correction pass.**
