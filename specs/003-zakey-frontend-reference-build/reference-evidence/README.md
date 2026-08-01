# Reference Evidence

This directory preserves live-reference evidence captured from
<https://remote-fried-86528699.figma.site/> on 2026-08-01.

- `screenshots/`: 53 full-page PNG captures.
- `measurements/`: 53 JSON records containing viewport, document, heading, control
  and main-section geometry.

Core states use `{state}-{width}.{png,json}` at widths 1440, 1024, 768 and 390.
Additional filenames identify interaction states. These files document the source
prototype only; they are not production assets and must not be served by ZAKEY v2.

Known caveats:

- The Figma Make attribution overlay is browser tooling, not design content.
- The prototype keeps the root URL while changing SPA screen state.
- The source has several broken images and mobile overflow defects.
- `newsletter-invalid-390` is an attempted interaction capture, not evidence of a
  working invalid-newsletter state.
