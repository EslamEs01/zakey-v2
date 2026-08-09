# T-1901 — visual inspection record (closing)

Every one of the seven outstanding comparisons was **opened and looked at**:
expected, actual and diff, 21 images. Claude's own image channel is disabled in
this session, so each set was rendered through the Codex CLI's image input,
which genuinely decodes the PNG — verified before use by asking it to describe an
image blind, and confirming it returned the correct page, language and controls.

Pixel counts and band analysis were **not** used to decide anything. They appear
below only as measurements attached to judgements already made by eye — the
`contact` case in `visual-approval-ledger.md` §1 is the standing proof of why
that distinction matters.

Two defects were found by looking. Both were fixed in the product, and fixing one
of them made three comparisons pass against their **original, untouched**
baselines.

---

## Outcome

```
npx playwright test ./tests/visual
96 passed (0 failed)
```

| # | comparison | classification | resolution |
|---|---|---|---|
| 1 | checkout @ 1024 | **genuine product regression** | fixed in the product; baseline untouched |
| 2 | checkout @ 768 | **genuine product regression** | fixed in the product; baseline untouched |
| 3 | checkout @ 390 | **genuine product regression** | fixed in the product; baseline untouched |
| 4 | account @ 1440 | correct intentional production change | approved individually, re-baselined |
| 5 | account @ 1024 | correct intentional production change | approved individually, re-baselined |
| 6 | account @ 768 | correct intentional production change | approved individually, re-baselined |
| 7 | account @ 390 | correct intentional production change | approved individually, re-baselined |

No blanket `--update-snapshots` was ever run. The four approved baselines were
replaced one file at a time with the exact bytes that had been reviewed, so the
image that was approved is the image that became the baseline.

---

## 1–3. checkout @ 1024 / 768 / 390 — genuine product regression, fixed

| field | value |
|---|---|
| node | `tests/visual/visual-regression.spec.js:36:3 › checkout` |
| projects | `chrome-1024`, `chrome-768`, `chrome-390` (`chrome-1440` always passed) |
| route | `/checkout/` |
| language / direction | `ar-EG` / RTL |
| auth / page state | signed-out, **empty basket** (`data-qa-state` empty) |
| expected | `tests/visual/visual-regression.spec.js-snapshots/checkout-chrome-<w>-linux.png` |
| actual | `…/playwright-results/visual-visual-regression-checkout-chrome-<w>/checkout-actual.png` |
| diff | same directory, `checkout-diff.png` |
| pixel result | identical dimensions; 39,130 px @1024 (0.0285), 37,262 @768 (0.0312), 33,497 @390 (0.0443) |
| **classification** | **genuine product regression** |

### What the images showed

Not a content change at all. Every word, control, icon and value was identical;
the entire empty-basket card — border, cart icon, both text rows, both buttons —
was displaced **downward by ~76px**, and nothing else moved. The header and
footer were unchanged, and the page height was identical in both images.

The diff showed each moved element twice, 76px apart: card border at y≈179–599
vs y≈255–675, heading at y≈376 vs y≈452, buttons at y≈487 vs y≈563.

### Cause

`.checkout-stepper-wrap` carries `padding-block: 42px 34px` — **exactly 76px**.

The stepper inside it is correctly suppressed on an empty basket: its three
buttons point at step panels via `aria-controls`, and those panels only exist
when there is something to check out, so rendering it left three dangling
references (a critical `aria-valid-attr-value` violation). But only the *stepper*
was removed — the padded wrapper still rendered, leaving 76px of blank space and
pushing the card down by precisely that amount.

### Fix

`templates/pages/checkout.html` now applies the `checkout-stepper-wrap` class
only when there is a stepper to wrap. The `sr-only` heading stays either way,
because `checkout-main` is labelled by it.

All three comparisons now pass **against the original baselines**, which were
never modified — the proof that this was a defect and not a design change.

---

## 4–7. account @ 1440 / 1024 / 768 / 390 — intentional change, approved

| field | value |
|---|---|
| node | `tests/visual/visual-regression.spec.js:36:3 › account` |
| projects | `chrome-1440`, `chrome-1024`, `chrome-768`, `chrome-390` |
| route | `/account/` |
| language / direction | `ar-EG` / RTL |
| auth / page state | **signed-out** (guest); no personal data rendered |
| expected | `…-snapshots/account-chrome-<w>-linux.png` |
| actual | `…/visual-visual-regression-account-chrome-<w>/account-actual.png` |
| diff | same directory, `account-diff.png` |
| pixel result (pre-approval) | height +586 @1440, +998 @1024, +630 @768, +928 @390 |
| **classification** | **correct intentional production change** |

### What the images showed

The baseline is the **prototype's** account page: a gold badge reading
`نسخة العرض: تسجيل الدخول` ("Demo version: sign in"), an email-only card with a
`name@example.com` placeholder and a note stating that no real authentication or
accounts exist, beside a benefits card.

The actual page is the real one: sign-in with a password, full registration with
a newsletter opt-in, and password reset — required by FR-050, FR-053 and FR-054,
which the approved storefront had no surface for. A demo badge and a "there is no
real authentication here" notice would both be false on a live shop.

### A genuine regression found on the way, and fixed

The first inspection reported the auth forms as **uncarded bare blocks**, with
the footer pushed ~450px down. That was accurate: `.account-auth`,
`.account-auth-grid` and `.account-auth-card` appeared **zero times** in the
stylesheet — source *and* build. The surface had shipped with class names that
were never styled.

Two fixes, both toward the established design rather than away from it:

* the forms now carry `surface-card`, the storefront's canonical card, so they
  cannot drift from every other card on the site; `.account-auth-*` adds layout
  only (grid, gap, padding, a single-column fallback below 720px);
* the **benefits card was restored** — markup and Arabic copy verbatim from the
  approved storefront. Rewiring the page to real authentication had deleted it,
  which lost approved content and left the grid with an empty column. The auth
  forms were the intended change; deleting that card was not.

### Verified before approval, per viewport

Cards render with a white surface, border, rounded corners and consistent
padding · Arabic correctly shaped and joined, ligatures intact, nothing garbled,
reversed, clipped or overlapping · RTL correct, no mirrored punctuation, no
reordered Latin runs · shared header, hero and footer typography, spacing,
colour and icons unchanged · nothing clipped, overflowing or cut off at any edge,
including 390 · signed-out, with **no** customer name, address, order or payment
data · the free-shipping threshold string agrees between both images · every
field visibly labelled, no broken or unlabelled control, no error state · **no**
template syntax, placeholder, Lorem, TODO, `undefined`, `NaN` or fake success
message in the actual render.

### A third defect the review caught

The first attempt at these fixes used Django's `{# … #}` comment across several
lines. That syntax is **single-line only**, so both comments rendered as visible
text on `/account/` and `/checkout/`. `material-states.spec.js` caught it
immediately (`visible {# on /account/`); both are now `{% comment %}` blocks.
The repository's own `test_no_multiline_hash_comments` guards the same mistake.

---

## Method note

Codex was run with `-c 'mcp_servers={}'` and told explicitly not to use tools.
Given the chance it goes looking for the file on disk instead of describing the
image already attached, and on this machine that meant contending for the same
MCP server this session uses.

One trap worth recording: Playwright writes every viewport's capture to the same
`<route>-actual.png` basename inside a per-viewport directory. Copying them into
one folder silently overwrites, and an early review compared a 1024 baseline
against a 768 render — it confidently reported a header/footer "regression" that
was only a breakpoint difference. Images are now copied under viewport-qualified
names, and every set is dimension-checked before being read.
