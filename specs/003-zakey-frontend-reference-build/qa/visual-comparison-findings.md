# Visual Comparison Findings

**Final status**: Both browser-based passes complete; material findings fixed.

Reference captures live in reference-evidence/screenshots/. Implementation captures
live in qa/implementation-screenshots/. The comparison used matching 1440, 1024, 768
and 390 widths wherever the reference exposed that state.

## Pass one — structural fidelity

| Finding | Fix | Final result |
|---|---|---|
| Reference order and density had to remain authoritative | Home follows hero, trust strip, category, best-seller, promotion, featured, value, smart-home, review, partner, newsletter and footer rhythm | Pass |
| Mobile source filter overflowed in-flow | Preserved content/order in a focus-managed edge drawer capped to the viewport | Pass |
| Mobile cart and coupon controls clipped in the source | Reflowed line items, quantities, coupon and summary below 620px | Pass |
| Product tabs clipped at 390px | Added non-shrinking, horizontally scrollable semantic tabs | Pass |
| Desktop splits needed predictable tablet/mobile collapse | Added governed 820px and 520px transformations across commerce/account/company pages | Pass |
| Product imagery was inconsistent or broken remotely | Replaced it with six optimized local studio-style WebP smart-lock assets | Pass |

Pass-one review covered composition, section order, container width, grids, density,
header, hero, card ratios, footer and breakpoint transformations. Affected states
were recaptured; the final matrix has no horizontal overflow or broken local assets.

## Pass two — typography and polish

| Finding | Fix | Final result |
|---|---|---|
| Latin-first type could not serve Arabic | Bundled Cairo for Arabic and limited Poppins to suitable Latin labels | Pass |
| Gold text needed stronger contrast on light surfaces | Used navy for body/actions and reserved gold for accents or controlled bands | Pass |
| RTL details needed logical alignment | Used logical properties, RTL navigation/order, aligned prices and Arabic wrapping | Pass |
| Controls needed consistent keyboard/touch treatment | Added visible focus, 44px targets, Escape/focus restoration and reduced motion | Pass |
| Empty/loading/error states varied | Unified state panels, Arabic status copy, disabled/loading treatment and recovery links | Pass |
| About/Contact initially felt detached | Reused the shared navy bands, governed cards, spacing, buttons and footer grammar | Pass |

Pass two covered typography, Arabic wrapping, RTL, fine spacing, icons, borders,
shadows, imagery, form states, contrast, animation and premium consistency.

## Intentional differences

- Arabic-first RTL and Egyptian copy replace English/LTR while preserving hierarchy.
- Prices, 14% VAT, free-shipping threshold, governorates and mobile fields are localized.
- Local generated WebP assets replace broken/inconsistent remote reference images.
- The filter drawer, stronger focus treatment and mobile reflow correct source
  accessibility/overflow defects without changing component identity.
- Required pages absent from the source—Collection, Search Results, standalone
  Wishlist, signed-out Account, 404 and 5xx—extend the same design grammar.
- Checkout Payment direct source evidence is absent at 1024 and 768; those widths use
  the documented Shipping and shared responsive grammar.

No difference remains that creates a generic alternative design.
