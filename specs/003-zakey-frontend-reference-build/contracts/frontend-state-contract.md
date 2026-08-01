# Frontend State Contract

## Durable prototype namespace

Only `storage-adapter.js` may call `localStorage`. It owns one versioned JSON envelope at the exact
key `zakey:prototype:v1` with `{version, cart, wishlist, account}`. It validates every read, catches
unavailable/quota errors, emits recoverable status and falls back to fixture defaults. Its public
`reset()` method removes only this exact key. Components, tests and documentation must use the
adapter-backed reset control/API and never call browser storage directly.

## URL state

Search, category, collection, filter, sort, page and explicit QA-state values use query parameters.
Unknown values are ignored or normalized; pagination clamps to an available page. URL state is
shareable and works with server-rendered GET fallbacks.

## Event interface

Modules coordinate through `CustomEvent` names prefixed `zakey:`:

- `zakey:cart-change` and `zakey:wishlist-change`
- `zakey:catalogue-change`
- `zakey:prototype-status`
- `zakey:account-state-change`

Event details contain normalized IDs/counts/status only. Components render from store snapshots
rather than mutating another component's markup directly.

## Material state matrix

Every state below is captured at 1440, 1024, 768 and 390:

- shared: default, mobile menu open, search open, focus-visible, reduced-motion
- catalogue: populated, mobile filter open, active filters, no search results, no filtered results,
  loading, recoverable error
- product: available/default, alternate gallery, selected tab, open FAQ, unavailable, wishlist saved
- wishlist: populated, empty
- cart: populated, empty, coupon rejected, coupon accepted, coupon loading/recoverable error
- checkout: Shipping default, validation error, Payment, Review, loading/unavailable submission
- account: signed-out, signed-in Orders, signed-in Wishlist empty, another selected account tab
- newsletter/contact: validation error, loading, intentional unsent, recoverable error
- errors: 404 and 5xx recovery states

Default/hover/active/selected/disabled are exercised through component-focused evidence when they
do not create a distinct full-page state.

## Accessibility behavior

Dialogs/drawers move focus to their heading/first control, contain focus, close with Escape and
restore the trigger. Tabs use arrow/home/end navigation; accordions expose button/region state.
Dynamic counts, filters, cart/wishlist and form results announce through a polite live region.
Loading disables duplicate actions without removing the accessible name.

## Prohibited states

No authenticated session, saved customer, created order, paid/successful transaction, provider
response, inventory reservation, email/SMS result or server-side persistence may be represented.
