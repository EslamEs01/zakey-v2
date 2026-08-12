"""Per-row English copy alongside the Arabic source (FR-136).

The templates are translated through gettext, but a catalogue is not: a product
name, a category description and an FAQ answer are *data*, entered by staff in
the admin, and they change without a developer or a ``.po`` file. So every piece
of staff-authored copy the storefront renders gets an ``_en`` sibling column.

Two decisions worth stating, because both are load-bearing:

**Arabic is the required field; English is optional.** ``name`` stays
``blank=False``, ``name_en`` is ``blank=True``. A shop that never fills in an
English name is a working Arabic shop, not a broken bilingual one — and
:func:`translated` falls back per *field*, not per record, so a product with an
English name but no English description reads correctly in both.

**Columns, not a translations table.** A separate ``ProductTranslation`` model
is the more general design and the wrong one here: there are exactly two
languages, fixed at the design level, and the storefront reads these fields in
list views where a join per row is what turns a catalogue page into an N+1. A
nullable column costs nothing when empty.
"""

from __future__ import annotations

from django.db import models
from django.utils import translation


def active_language() -> str:
    """The active language reduced to its base tag (``ar-eg`` → ``ar``)."""
    return (translation.get_language() or "ar").split("-")[0].lower()


def translated(instance, field: str, language: str | None = None) -> str:
    """The value of ``field`` in the active language, falling back to Arabic.

    An empty English column means "not translated yet", not "translated to
    nothing", so it falls back rather than rendering a blank on the page.
    """
    if (language or active_language()) == "ar":
        return getattr(instance, field, "") or ""
    return (getattr(instance, f"{field}_en", "") or getattr(instance, field, "") or "")


class TranslatableModel(models.Model):
    """Mixin for models carrying ``<field>_en`` companions.

    ``translatable_fields`` names the Arabic fields that have one. It is used by
    :meth:`tr`, by the admin to build the English fieldset, and by the tests
    that assert the two stay in step.
    """

    translatable_fields: tuple[str, ...] = ()

    class Meta:
        abstract = True

    def tr(self, field: str) -> str:
        """Resolve one translatable field for the active language."""
        return translated(self, field)

    @property
    def translation_complete(self) -> bool:
        """Does every translatable field have English copy?

        Surfaced in the admin so staff can see at a glance which rows still
        read Arabic to an English visitor.
        """
        return all(
            (getattr(self, f"{name}_en", "") or "").strip()
            for name in self.translatable_fields
        )


def english_field(source: models.Field, verbose_name: str) -> models.Field:
    """Build the ``_en`` counterpart of a model field.

    Mirrors length and type, drops every constraint that belongs to the source
    column: an English name is never unique, never indexed and never required.
    """
    kwargs = {
        "verbose_name": verbose_name,
        "blank": True,
        "default": "",
    }
    if isinstance(source, models.TextField):
        return models.TextField(**kwargs)
    kwargs["max_length"] = source.max_length
    return models.CharField(**kwargs)
