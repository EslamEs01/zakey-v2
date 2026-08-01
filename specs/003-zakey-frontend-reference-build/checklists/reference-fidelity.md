# Reference-Fidelity Requirements Checklist

**Purpose**: Test whether requirements preserve the inspected reference rather than a generic
storefront interpretation
**Created**: 2026-08-01
**Evidence**: [reference-inventory.md](../reference-inventory.md)

## Inspection Gate

- [x] REF001 The reference URL was opened in a real browser.
- [x] REF002 Home and every discovered SPA screen state were inspected through visible controls.
- [x] REF003 The ten core states were captured at 1440px, 1024px, 768px and 390px.
- [x] REF004 Mobile menu, filters, product tabs, checkout payment, account wishlist and typed search
  were probed and recorded.
- [x] REF005 Screenshot and measurement evidence is preserved inside Specification 003.

## Requirement Fidelity

- [x] REF006 The exact inspected Home order overrides the shorter supporting list.
- [x] REF007 Desktop gutters, 12-column behavior, grid transformations and card ratios are recorded.
- [x] REF008 Announcement, header, hero, navigation, shop, product, cart, checkout, account and
  footer structures are described.
- [x] REF009 Typography hierarchy, palette, radii, shadows and image ratios are documented.
- [x] REF010 Responsive transformations are specified at all four required widths.
- [x] REF011 Reference-only tooling chrome and broken imagery are identified as exclusions.
- [x] REF012 Mobile overflow, clipped controls and inaccessible tabs are identified as defects to
  correct, not patterns to reproduce.
- [x] REF013 Arabic RTL and Egyptian localisation differences are bounded and justified.
- [x] REF014 Missing reference routes must extend the same design language and shared components.
- [x] REF015 Implementation screenshots must be paired with reference evidence for two review passes.

## Validation Result

All 15 reference-fidelity requirement checks pass. The reference gate authorizes planning, not
implementation; implementation remains gated by plan, tasks and Spec Kit analysis.
