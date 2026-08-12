"""Extract translatable strings and compile the catalogues, without gettext.

    python manage.py sync_translations            # extract + compile
    python manage.py sync_translations --check    # fail if anything is untranslated

Django's own ``makemessages``/``compilemessages`` need the GNU gettext binaries.
This does the same two jobs in Python (see :mod:`apps.core.translations`) so a
translation can be added and shipped on a host that has no gettext installed —
which is the deployment host.

Existing translations in the ``.po`` are always preserved; only the msgid list
and the source references are regenerated.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.translations import compile_po, extract_messages, parse_po, write_po


class Command(BaseCommand):
    help = "Extract translatable strings and compile .mo catalogues (no gettext needed)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Exit non-zero if any message is missing a translation.",
        )
        parser.add_argument(
            "--locale",
            action="append",
            default=None,
            help="Limit to these language codes (repeatable). Defaults to settings.LANGUAGES.",
        )

    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR)
        locale_dir = Path(settings.LOCALE_PATHS[0])

        messages = extract_messages(root)
        self.stdout.write(f"extracted {len(messages)} messages from {root}")

        codes = options["locale"] or [code for code, _ in settings.LANGUAGES]
        # The source language needs no catalogue: an untranslated msgid already
        # renders as the Arabic it was written in.
        source_language = settings.LANGUAGE_CODE.split("-")[0]

        missing_total = 0
        for code in codes:
            if code == source_language:
                continue
            po_path = locale_dir / code / "LC_MESSAGES" / "django.po"
            mo_path = po_path.with_suffix(".mo")
            existing = parse_po(po_path.read_text(encoding="utf-8")) if po_path.is_file() else {}
            total, untranslated = write_po(po_path, code, messages, existing)
            compiled = compile_po(po_path, mo_path)
            missing_total += untranslated
            self.stdout.write(
                f"{code}: {total} messages, {untranslated} untranslated, "
                f"{compiled} compiled into {mo_path.relative_to(root)}"
            )

        if options["check"] and missing_total:
            raise CommandError(
                f"{missing_total} message(s) have no translation. "
                f"Fill them in under {locale_dir.relative_to(root)} and re-run."
            )
