# ZAKEY Frontend Quickstart

Commands below are the verified local workflow.

## Install

```bash
uv sync
npm ci
```

## Build CSS/assets

```bash
npm run build
```

## Preview

```bash
uv run python manage.py runserver 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/>. The preview requires no database, provider account or external
production service.

## Test and validate

```bash
uv run python manage.py test
npm run check
npm test
```

`npm run check` runs the production asset build, native-JavaScript syntax checks, QA contract
validation and rendered HTML validation. `npm test` runs the Playwright integrity, interaction,
responsive, console/asset and axe suites using the locally installed Chrome channel.

## Prototype routes

- `/`
- `/shop/`
- `/collections/<slug>/`
- `/search/?q=<query>`
- `/products/<slug>/`
- `/cart/`
- `/checkout/`
- `/wishlist/`
- `/account/`
- `/about/`
- `/contact/`
- `/errors/404/`
- `/errors/500/`

## Reset prototype state

Use the clearly labelled “إعادة ضبط النموذج” control in the footer. Matrix tests seed the same
versioned envelope directly for deterministic states; trigger-driven journeys manipulate prototype
state through visible UI controls.

The adapter removes only the ZAKEY demonstration envelope. It does not affect accounts, orders or any server
data because none exist in this feature.
