# Backend Handoff Boundary

## Frontend feature owns now

- Semantic page/component markup and responsive design system
- Presentation-only fixture/context shapes
- Browser-local cart/wishlist/account demonstration adapters
- Three-step checkout UI and client validation
- Prototype shipping, installation, tax, coupon, payment and order-history labels
- Accessibility, tests, screenshots and visual evidence

## Deferred to a separately approved backend feature

- Domain/database models and migrations
- Admin/catalogue/inventory management
- Authentication, authorization and customer persistence
- Cart/order/checkout business services and durable transactions
- Payment, shipping, installation, email or SMS providers
- APIs, queues, caches, production infrastructure and deployment

## Replaceable seams

Future backend work may replace `fixture_provider.py` and `storage-adapter.js` behind normalized
view/state contracts. It must preserve template component inputs unless a new approved spec changes
them. Prototype order-history rows, payment labels and service eligibility are not authoritative
business rules or seed data.

## Stop gate

Completion of Specification 003 ends at user visual review. No backend requirements, models,
migrations, integration stubs, provider credentials, admin setup or production actions may be
started in this branch or feature.
