from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from scripts import export_static_site


class StaticExportTests(TestCase):
    def test_prefix_root_paths_preserves_external_and_fragment_urls(self) -> None:
        source = 'href="/" href="/shop/" src="https://example.com/a.png" href="#faq"'

        rewritten = export_static_site.prefix_root_paths(source, "/zakey-v2/")

        self.assertIn('href="/zakey-v2/"', rewritten)
        self.assertIn('href="/zakey-v2/shop/"', rewritten)
        self.assertIn('src="https://example.com/a.png"', rewritten)
        self.assertIn('href="#faq"', rewritten)

    def test_export_contains_all_fixture_routes_and_project_path_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "site"

            page_count = export_static_site.export_site(output, "/zakey-v2/")

            self.assertGreaterEqual(page_count, 20)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "404.html").is_file())
            self.assertTrue((output / "products" / "zakey-apex-pro" / "index.html").is_file())
            self.assertTrue((output / "account" / "signed-out" / "index.html").is_file())
            home = (output / "index.html").read_text(encoding="utf-8")
            css = (output / "static" / "dist" / "css" / "app.css").read_text(encoding="utf-8")
            self.assertIn('href="/zakey-v2/static/dist/css/app.css"', home)
            self.assertIn('/zakey-v2/static/dist/assets/fonts/', css)

    def test_export_refuses_to_replace_an_unowned_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "existing"
            output.mkdir()
            protected_file = output / "keep.txt"
            protected_file.write_text("preserve", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "not owned"):
                export_static_site.export_site(output, "/zakey-v2/")

            self.assertEqual(protected_file.read_text(encoding="utf-8"), "preserve")
