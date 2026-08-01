# Interaction Matrix

**Final status**: Pass.

The QA contract contains 56 states. Each state is initialized by a direct URL,
visible action, reduced-motion media emulation, explicit QA query or centralized
prototype-storage envelope. All 56 passed the shared integrity gate at all four
required widths.

## Trigger-driven journeys

| Journey | Controls exercised | Result |
|---|---|---|
| Header navigation | Products disclosure, search open/close, mobile menu, Escape and focus restoration | Pass at 4 widths |
| Catalogue | category selection, sorting, pagination/recovery and mobile filter drawer | Pass at 4 widths |
| Product | thumbnail, arrow-key tabs, quantity, wishlist and Add to Cart | Pass at 4 widths |
| Cart | quantity, accepted coupon and removal | Pass at 4 widths |
| Checkout | valid Egyptian fields, governorate/city, standard shipping, payment, step navigation and explicit unavailable final state | Pass at 4 widths |
| Account | signed-out/signed-in prototype switch and tab selection | Pass at 4 widths |
| Error recovery | 404 Shop and 500 Home recovery links | Pass at 4 widths |

The dedicated interaction run completed 28/28 cases: seven journeys multiplied by
1440, 1024, 768 and 390. The complete state run completed 224/224.

Contact/newsletter validation, loading, intentional-unsent and recoverable-error
states are covered by the complete state matrix rather than the seven journey tests.

## Contracted material states

- shared frame: menu, search, Products disclosure, hover, focus-visible and reduced motion;
- Home: default, newsletter validation/loading/unsent/error;
- catalogue: default, active filters, mobile drawer, empty search/filter, loading/error;
- Product: default, alternate gallery, specifications, FAQ, unavailable and wishlisted;
- Cart: default, populated, empty, coupon accepted/rejected/loading/error;
- Checkout: default, shipping, validation, payment, review, loading and unavailable submission;
- Wishlist: default, populated and empty;
- Account: default, signed out, orders, empty wishlist and addresses;
- Contact: default, validation, loading, unsent and error;
- About, Collection, 404 and 5xx default states.

No visible control intentionally submits commerce data. Payment/order completion is
explicitly unavailable in the prototype, with Shop and Cart recovery actions.
