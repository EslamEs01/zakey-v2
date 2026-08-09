from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402

from apps.catalog.models import Collection, Product  # noqa: E402
from apps.core.models import PublicationStatus  # noqa: E402


STATIC_SOURCE = PROJECT_ROOT / "static" / "dist"
EXPORT_SENTINEL = ".zakey-static-export"
ROOT_PATH_PATTERN = re.compile(r"(?P<quote>[\"'`])/(?P<path>(?!/)[A-Za-z])")
ROOT_ATTRIBUTE_PATTERN = re.compile(r"(?P<attribute>\b(?:href|action|src)=)(?P<quote>[\"'])/(?P=quote)")
CSS_ROOT_URL_PATTERN = re.compile(r"url\(/(?P<path>(?!/)[A-Za-z])")


@dataclass(frozen=True)
class ExportRoute:
    request_path: str
    output_path: str
    expected_status: int = 200


def normalize_base_path(value: str) -> str:
    stripped = value.strip().strip("/")
    return f"/{stripped}/" if stripped else "/"


def prefix_root_paths(content: str, base_path: str) -> str:
    if base_path == "/":
        return content
    prefix = base_path.rstrip("/")
    content = ROOT_PATH_PATTERN.sub(
        lambda match: f"{match.group('quote')}{prefix}/{match.group('path')}",
        content,
    )
    content = ROOT_ATTRIBUTE_PATTERN.sub(
        lambda match: f"{match.group('attribute')}{match.group('quote')}{base_path}{match.group('quote')}",
        content,
    )
    return CSS_ROOT_URL_PATTERN.sub(
        lambda match: f"url({prefix}/{match.group('path')}",
        content,
    )


def html_routes() -> list[ExportRoute]:
    """Every page the static preview exports, from the published catalogue.

    Slugs come from the database (T-1608) rather than the JSON fixture, so the
    preview cannot drift from what the real storefront serves.

    The account page is exported once, signed-out. A static export has no
    session, and the signed-in view is now decided by the session rather than
    by a ``?state=`` query parameter that any visitor could set.
    """
    published = {"status": PublicationStatus.PUBLISHED}
    routes = [
        ExportRoute("/", "index.html"),
        ExportRoute("/shop/", "shop/index.html"),
        ExportRoute("/search/?q=ذكي", "search/index.html"),
        ExportRoute("/cart/", "cart/index.html"),
        ExportRoute("/checkout/", "checkout/index.html"),
        ExportRoute("/wishlist/", "wishlist/index.html"),
        ExportRoute("/account/", "account/index.html"),
        ExportRoute("/about/", "about/index.html"),
        ExportRoute("/contact/", "contact/index.html"),
        ExportRoute("/errors/404/", "errors/404/index.html", 404),
        ExportRoute("/errors/500/", "errors/500/index.html", 500),
    ]
    routes.extend(
        ExportRoute(f"/collections/{slug}/", f"collections/{slug}/index.html")
        for slug in Collection.objects.filter(**published).values_list("slug", flat=True)
    )
    routes.extend(
        ExportRoute(f"/products/{slug}/", f"products/{slug}/index.html")
        for slug in Product.objects.filter(**published).values_list("slug", flat=True)
    )
    return routes


def prepare_output(output: Path) -> None:
    if output.is_symlink():
        raise ValueError("Static export output cannot be a symbolic link")
    resolved = output.resolve()
    if resolved in {PROJECT_ROOT.resolve(), Path(resolved.anchor)}:
        raise ValueError("Static export output must be a dedicated directory")
    if resolved.exists():
        sentinel = resolved / EXPORT_SENTINEL
        if not resolved.is_dir() or not sentinel.is_file():
            raise ValueError("Refusing to replace a directory not owned by the static exporter")
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)
    (resolved / EXPORT_SENTINEL).touch()


def rewrite_account_links(html: str) -> str:
    html = html.replace('href="/account/?state=signed-out"', 'href="/account/signed-out/"')
    return html.replace('href="/account/?state=signed-in"', 'href="/account/"')


def export_html(output: Path, base_path: str) -> int:
    client = Client()
    count = 0
    for route in html_routes():
        response = client.get(route.request_path)
        if response.status_code != route.expected_status:
            raise RuntimeError(
                f"Expected {route.expected_status} for {route.request_path}, got {response.status_code}"
            )
        html = rewrite_account_links(response.content.decode("utf-8"))
        destination = output / route.output_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(prefix_root_paths(html, base_path), encoding="utf-8")
        count += 1

        if route.request_path == "/errors/404/":
            (output / "404.html").write_text(prefix_root_paths(html, base_path), encoding="utf-8")
    return count


def export_static_assets(output: Path, base_path: str) -> None:
    if not STATIC_SOURCE.is_dir():
        raise FileNotFoundError("Run `npm run build` before exporting the static site")
    destination = output / "static" / "dist"
    shutil.copytree(STATIC_SOURCE, destination)
    for pattern in ("*.js", "*.css"):
        for asset in destination.rglob(pattern):
            asset.write_text(prefix_root_paths(asset.read_text(encoding="utf-8"), base_path), encoding="utf-8")


def export_site(output: Path, base_path: str) -> int:
    normalized_base = normalize_base_path(base_path)
    prepare_output(output)
    page_count = export_html(output, normalized_base)
    export_static_assets(output, normalized_base)
    (output / ".nojekyll").touch()
    return page_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the ZAKEY presentation shell for GitHub Pages")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "_site")
    parser.add_argument("--base-path", default="/zakey-v2/")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    pages = export_site(arguments.output, arguments.base_path)
    print(f"Exported {pages} static pages to {arguments.output.resolve()}")
