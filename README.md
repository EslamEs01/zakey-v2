# ZAKEY v2 Frontend Reference Build

Arabic-first RTL storefront prototype for ZAKEY smart door locks. The implementation
uses Django Templates, semantic HTML, locally compiled Tailwind CSS and native
JavaScript. Catalogue, account, cart, checkout and payment data are demonstration
fixtures only; no order, payment or customer data is submitted.

## Public preview

GitHub Pages (available after the first successful deployment):
<https://eslames01.github.io/zakey-v2/>

One-time repository setup: open **Settings → Pages → Build and deployment** and
select **GitHub Actions** as the source. The workflow then publishes the preview
from pushes to `main` or `003-zakey-frontend-reference-build`.

The Pages workflow exports the presentation shell as static HTML. The Django project
remains the authoritative local preview for server-rendered GET filters and all QA
states.

## Run locally

```bash
uv sync
npm ci
npm run build
npx playwright install chrome
uv run python manage.py runserver 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/>.

## Validate

```bash
uv run python manage.py test
npm run qa
```

Specification and QA documentation are under
`specs/003-zakey-frontend-reference-build/`.
The screenshot counts in that documentation refer to the complete local QA run;
large reproducible screenshot and rendered-HTML binaries are intentionally excluded
from Git, while their manifests, measurements and findings are published.
