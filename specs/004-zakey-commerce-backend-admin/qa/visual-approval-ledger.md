# Visual regression ledger — Phase 19

Re-discovered from a fresh run, not carried over from an earlier report.

```
npx playwright test ./tests/visual --reporter=list
85 passed  11 failed        (before remediation)
```

After fixing the contact regression below:

```
npx playwright test ./tests/visual --grep contact --reporter=list
20 passed  0 failed         (against the UNMODIFIED baseline)
```

**No snapshot has been updated. No `--update-snapshots` command has been run.**

---

## 0. Fresh re-verification (final-completion session)

The comparison set was **re-discovered from scratch in a new session**, not
carried over. Port 8000 was occupied by an unrelated project, so the suite was
run against a private port; nothing else was varied.

```
npm run reset:dev
ZAKEY_E2E_BASE_URL=http://127.0.0.1:8012 \
ZAKEY_E2E_SERVER_COMMAND='uv run python manage.py runserver 127.0.0.1:8012 --noreload' \
npx playwright test ./tests/visual --reporter=list

7 failed
  [chrome-1440] account   [chrome-1024] account   [chrome-768] account   [chrome-390] account
  [chrome-1024] checkout  [chrome-768] checkout   [chrome-390] checkout
89 passed (9.5m)
```

Identical to the set recorded in §2 below: `account` × 4 and `checkout` × 3.
The contact regression stays fixed and the `search` @ 390 fix still holds.
**No snapshot was updated in this session either** — `git status --short
tests/visual/` is empty and all 52 tracked snapshots keep their pre-session
timestamps.

### These seven are the *only* thing failing the QA gate (T-1906)

A complete `npm run qa` was run afterwards:

```
505 passed, 7 failed  ·  exit 1
  [chrome-1440] account   [chrome-1024] account   [chrome-768] account   [chrome-390] account
  [chrome-1024] checkout  [chrome-768] checkout   [chrome-390] checkout
```

Every other stage passed — build, `check:js`, `check:matrix`, e2e, accessibility,
no-JS, `check:html`, `check:evidence` and `test:pages`. So **T-1906 needs nothing
of its own**: approving or fixing these seven comparisons turns the gate green.

### The 21 images that must be opened

| # | route | vp | file |
|---|---|---|---|
| 1 | account | 1440 | `tests/visual/visual-regression.spec.js-snapshots/account-chrome-1440-linux.png` (expected) |
| 2 | account | 1440 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-1440/account-actual.png` |
| 3 | account | 1440 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-1440/account-diff.png` |
| 4 | account | 1024 | `tests/visual/visual-regression.spec.js-snapshots/account-chrome-1024-linux.png` (expected) |
| 5 | account | 1024 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-1024/account-actual.png` |
| 6 | account | 1024 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-1024/account-diff.png` |
| 7 | account | 768 | `tests/visual/visual-regression.spec.js-snapshots/account-chrome-768-linux.png` (expected) |
| 8 | account | 768 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-768/account-actual.png` |
| 9 | account | 768 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-768/account-diff.png` |
| 10 | account | 390 | `tests/visual/visual-regression.spec.js-snapshots/account-chrome-390-linux.png` (expected) |
| 11 | account | 390 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-390/account-actual.png` |
| 12 | account | 390 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-account-chrome-390/account-diff.png` |
| 13 | checkout | 1024 | `tests/visual/visual-regression.spec.js-snapshots/checkout-chrome-1024-linux.png` (expected) |
| 14 | checkout | 1024 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-checkout-chrome-1024/checkout-actual.png` |
| 15 | checkout | 1024 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-checkout-chrome-1024/checkout-diff.png` |
| 16 | checkout | 768 | `tests/visual/visual-regression.spec.js-snapshots/checkout-chrome-768-linux.png` (expected) |
| 17 | checkout | 768 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-checkout-chrome-768/checkout-actual.png` |
| 18 | checkout | 768 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-checkout-chrome-768/checkout-diff.png` |
| 19 | checkout | 390 | `tests/visual/visual-regression.spec.js-snapshots/checkout-chrome-390-linux.png` (expected) |
| 20 | checkout | 390 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-checkout-chrome-390/checkout-actual.png` |
| 21 | checkout | 390 | `specs/003-zakey-frontend-reference-build/qa/playwright-results/visual-visual-regression-checkout-chrome-390/checkout-diff.png` |

All 21 files were confirmed present on disk. **Image viewing is unavailable in
this session**: the `Read` tool reports *"No such tool available: Read. Read is
disabled for this session, in subagents as well as here"*, and no other
image-capable tool exists. Approval therefore remains impossible here, for the
same reason as before — and the `contact` case in §1 is the standing proof that
pixel counts and band analysis are not a substitute for looking.

---

## 1. Resolved: `contact` × 4 viewports — GENUINE PRODUCT REGRESSION

| field | value |
|---|---|
| test node | `tests/visual/visual-regression.spec.js:36:3 › contact` |
| viewports | 1440, 1024, 768, 390 |
| route | `/contact/` |
| language / direction | ar-EG / RTL |
| state | signed-out, default |
| baseline | `tests/visual/baseline-004/contact-<w>.png` |
| actual | `…/playwright-results/visual-visual-regression-contact-chrome-<w>/contact-actual.png` |
| diff | same directory, `contact-diff.png` |
| pixel result | 112 354–1 223 502 px (ratio 0.07–0.46) |
| **classification** | **genuine product regression** |

### Diagnosis

The page was **shorter** than the baseline — −88 px (1440), −95 px (1024),
−103 px (390) — and every differing row was below y≈1253. A page losing height
below the fold means content disappeared, not that content was added.

`templates/pages/contact.html` still filtered the FAQ accordion with

```django
{% for faq in contact_faqs %}{% if faq.id in contact.faqIds %}
```

`contact.faqIds` is a **fixture-era** key. Once the catalogue moved to the
database, `ctx.faqs("contact")` began returning FAQs already filtered by
`FAQ.page`, and `contact.faqIds` ceased to exist — so the condition was
permanently false and the accordion rendered **zero** rows.

Measured before the fix:

```
database FAQ <details> rendered: 0
FAQ rows in DB for page='contact': 2
```

Two collapsed `<details>` ≈ 94 px, which matches the observed height loss.

### Fix

The redundant guard was removed (the queryset is already page-scoped). After
the fix: `database FAQ <details> rendered: 2`, and all four contact comparisons
**pass against the untouched baseline** — which is the proof that the baseline
was correct all along and that this was never an intentional delta.

---

## 2. Outstanding: `account` × 4 and `checkout` × 3 — NOT APPROVED

| route | viewports | height change | first differing row |
|---|---|---|---|
| account | 1440, 1024, 768, 390 | +514, +514, +146, +140 px | y≈305–321 |
| checkout | 1024, 768, 390 (1440 passes) | unchanged | y≈271–280 |

### What is mechanically established

**account** — the header and hero are pixel-identical above y≈305. The signed-out
page now renders three auth cards (login, register, forgot-password) where the
baseline had two. The set-new-password form is correctly **absent** without a
token. The delta is attributable to the password-reset UI required by FR-054 /
T-0404, which the approved storefront had no surface for.

**checkout** — page height is unchanged and the differences sit in a single
region y≈271–609. 1440 passes, so this is not a global style change.

### Why neither is approved here

`T-1901` accepts *"only the two approved deltas (shipping row, installation
row) … each with a recorded approval."* Neither of these is one of those two.

More decisively: approval requires confirming there is no unrelated regression
in typography, spacing, alignment, colour, icons or usability. **The `Read`
tool is disabled in this session, including for subagents, so the baseline,
actual and diff PNGs cannot be opened.** Pixel counts and band analysis are not
visual review, and the contact case above is exactly why that distinction
matters — the band analysis pointed at the right region, but only reading the
*code* revealed that the change was a regression rather than an intentional
delta.

Approving these would mean asserting something I did not verify.

### Discharged mechanically (not a substitute for approval)

`tests/visual/material-states.spec.js` — 44 assertions across 4 viewports,
all passing, covering: RTL/lang correctness, absence of visible template
syntax/placeholder/Lorem/TODO/undefined, zero horizontal overflow, zero controls
overhanging the viewport, every field labelled and focusable, invalid input
producing a visible `aria-describedby`-linked error with `aria-invalid`,
signed-out account showing no fabricated customer, signed-in showing the
session's own identity, checkout rendering no steppers on an empty basket, and
contact never reporting success without persistence.

### To close T-1901

1. Open `<route>-expected.png`, `<route>-actual.png` and `<route>-diff.png` for
   each of the 7 remaining comparisons.
2. Confirm the only visible change on `account` is the added forgot-password
   card, and on `checkout` the shipping and installation rows.
3. Confirm no unrelated typography, spacing, colour or alignment change.
4. Re-baseline **individually**, per approved image — never a blanket
   `--update-snapshots`.
5. Re-run `npx playwright test ./tests/visual` and require 96 passed / 0 failed.

---

## 3. Previously reported, now confirmed fixed

`search` @ 390 — the server-rendered heading regression fixed in an earlier
batch. It passes against the unmodified baseline in this run.
