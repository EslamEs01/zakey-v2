"""Message extraction and catalogue compilation without GNU gettext.

``makemessages`` and ``compilemessages`` shell out to ``xgettext``, ``msguniq``
and ``msgfmt``. Those are not installed on the deployment host and are not
something a handover should require someone to install before they can add a
translation — so the two things this project actually needs from them are
reimplemented here in Python:

* :func:`extract_messages` finds every translatable string in the templates and
  the Python sources, using Django's own :func:`templatize` so the msgids come
  out byte-identical to what ``xgettext`` would have produced (in particular
  ``{{ name }}`` inside ``blocktranslate`` becomes ``%(name)s``);
* :func:`write_po` and :func:`compile_po` round-trip the ``.po`` file and emit
  the binary ``.mo`` catalogue that ``gettext`` reads at runtime.

This is not a general gettext implementation. It covers singular messages with
optional context, which is everything this codebase uses; plural forms are
carried through verbatim if a translator adds them by hand but are not
generated.
"""

from __future__ import annotations

import ast
import re
import struct
from pathlib import Path

from django.utils.translation.template import templatize

#: Directories that never contain first-party source.
EXCLUDED_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", "staticfiles", "_site",
    "_pages-preview", ".pytest_cache", ".ruff_cache", "locale", ".artifacts",
    ".pgdev", "migrations", "htmlcov", "media",
}

#: The gettext aliases this codebase uses.
_GETTEXT_NAMES = {
    "gettext", "gettext_lazy", "ngettext", "ngettext_lazy",
    "pgettext", "pgettext_lazy", "npgettext", "npgettext_lazy",
    "_",
}

#: ``templatize`` masks everything that is *not* translatable with filler
#: characters so line numbers survive, which means its output is not valid
#: Python and cannot be parsed — xgettext scans it lexically, and so does this.
#: Both quote styles: templatize emits gettext calls with single quotes, but
#: leaves an inline ``_("...")`` — the form used in a filter argument — exactly
#: as the template author wrote it.
_PY_STRING = r"""(?:u?'(?:[^'\\]|\\.)*'|u?"(?:[^"\\]|\\.)*")"""
_TEMPLATE_CALL = re.compile(
    r"(?<![A-Za-z0-9_])(gettext|pgettext|ngettext|npgettext|_)\("
    r"(" + _PY_STRING + r")"
    r"(?:\s*,\s*(" + _PY_STRING + r"))?"
    r"(?:\s*,\s*(" + _PY_STRING + r"))?"
)


def _walk(root: Path, suffixes: tuple[str, ...]):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def _string_value(node) -> str | None:
    """The literal value of an AST node, or None when it is not a literal.

    A non-literal msgid — ``_(variable)`` — cannot be extracted at all, by
    gettext or by anything else, so it is skipped rather than guessed at.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _string_value(node.left)
        right = _string_value(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _extract_from_python(source: str, origin: str, messages: dict) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name not in _GETTEXT_NAMES or not node.args:
            continue
        context = None
        args = list(node.args)
        if name.startswith(("pgettext", "npgettext")):
            context = _string_value(args.pop(0))
            if context is None:
                continue
        msgid = _string_value(args[0]) if args else None
        if not msgid:
            continue
        messages.setdefault((context, msgid), []).append(origin)


def _extract_from_templatized(source: str, origin: str, messages: dict) -> None:
    for match in _TEMPLATE_CALL.finditer(source):
        name, first, second, _third = match.groups()
        try:
            first_value = ast.literal_eval(first)
        except (ValueError, SyntaxError):
            continue
        context = None
        msgid = first_value
        if name in ("pgettext", "npgettext") and second:
            try:
                context, msgid = first_value, ast.literal_eval(second)
            except (ValueError, SyntaxError):
                continue
        if not msgid:
            continue
        messages.setdefault((context, msgid), []).append(origin)


def extract_messages(root: Path) -> dict[tuple[str | None, str], list[str]]:
    """Every translatable string in the project, keyed by (context, msgid)."""
    messages: dict[tuple[str | None, str], list[str]] = {}

    for path in _walk(root, (".html", ".txt")):
        origin = str(path.relative_to(root))
        try:
            # templatize turns template i18n tags into gettext calls, applying
            # the same msgid normalisation xgettext would then have seen.
            translated = templatize(path.read_text(encoding="utf-8"), origin=origin)
        except Exception:  # pragma: no cover - a malformed template
            continue
        _extract_from_templatized(translated, origin, messages)

    for path in _walk(root, (".py",)):
        origin = str(path.relative_to(root))
        _extract_from_python(path.read_text(encoding="utf-8"), origin, messages)

    return messages


# ---------------------------------------------------------------------------
# .po round-trip
# ---------------------------------------------------------------------------

_PO_HEADER = """msgid ""
msgstr ""
"Project-Id-Version: ZAKEY v2\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Language: {language}\\n"
"Plural-Forms: {plural}\\n"
"""

PLURAL_FORMS = {
    "en": "nplurals=2; plural=(n != 1);",
    "ar": "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);",
}


def _po_quote(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\t", "\\t")
        .replace("\r", "")
    )
    if "\n" not in escaped:
        return '"' + escaped + '"'
    lines = escaped.split("\n")
    parts = ['""']
    for index, line in enumerate(lines):
        suffix = "\\n" if index < len(lines) - 1 else ""
        parts.append('"' + line + suffix + '"')
    return "\n".join(parts)


def _po_unquote(chunks: list[str]) -> str:
    joined = "".join(chunks)
    return (
        joined.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace('\\"', '"')
        .replace("\\\\", "\\")
    )


def parse_po(text: str) -> dict[tuple[str | None, str], str]:
    """Existing translations, keyed the same way as :func:`extract_messages`."""
    entries: dict[tuple[str | None, str], str] = {}
    context: str | None = None
    msgid: list[str] | None = None
    msgstr: list[str] | None = None
    current: list[str] | None = None
    ctxt: list[str] | None = None

    def flush():
        nonlocal context, msgid, msgstr, ctxt
        if msgid is not None and msgstr is not None:
            key_id = _po_unquote(msgid)
            key_ctx = _po_unquote(ctxt) if ctxt is not None else None
            if key_id:
                entries[(key_ctx, key_id)] = _po_unquote(msgstr)
        context = None
        msgid = msgstr = ctxt = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            if not line:
                flush()
                current = None
            continue
        if line.startswith("msgctxt "):
            flush()
            ctxt = [line[len("msgctxt "):].strip()[1:-1]]
            current = ctxt
        elif line.startswith("msgid "):
            if msgstr is not None:
                flush()
            msgid = [line[len("msgid "):].strip()[1:-1]]
            current = msgid
        elif line.startswith("msgstr "):
            msgstr = [line[len("msgstr "):].strip()[1:-1]]
            current = msgstr
        elif line.startswith('"') and current is not None:
            current.append(line[1:-1])
    flush()
    return entries


def write_po(
    path: Path,
    language: str,
    messages: dict[tuple[str | None, str], list[str]],
    existing: dict[tuple[str | None, str], str],
) -> tuple[int, int]:
    """Write ``path``, keeping every translation already in it.

    Returns ``(total, untranslated)``. A msgid that has disappeared from the
    source is dropped rather than kept as a commented-out obsolete entry: this
    file is regenerated, not hand-maintained, so stale entries are noise.
    """
    lines = [_PO_HEADER.format(language=language, plural=PLURAL_FORMS.get(language, PLURAL_FORMS["en"]))]
    untranslated = 0
    for (context, msgid) in sorted(messages, key=lambda k: (k[1], k[0] or "")):
        origins = messages[(context, msgid)]
        lines.append("")
        for origin in sorted(set(origins))[:8]:
            lines.append(f"#: {origin}")
        if context is not None:
            lines.append("msgctxt " + _po_quote(context))
        lines.append("msgid " + _po_quote(msgid))
        translation = existing.get((context, msgid), "")
        if not translation:
            untranslated += 1
        lines.append("msgstr " + _po_quote(translation))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(messages), untranslated


def compile_po(po_path: Path, mo_path: Path) -> int:
    """Compile a ``.po`` into the binary ``.mo`` format gettext reads.

    Only entries with a non-empty translation are emitted; an untranslated
    msgid must be *absent* from the catalogue so gettext falls back to the
    source string, which here is the correct Arabic.
    """
    entries = parse_po(po_path.read_text(encoding="utf-8"))
    catalogue: dict[str, str] = {"": f"Content-Type: text/plain; charset=UTF-8\n"}
    for (context, msgid), msgstr in entries.items():
        if not msgstr:
            continue
        key = f"{context}\x04{msgid}" if context else msgid
        catalogue[key] = msgstr

    keys = sorted(catalogue)
    ids = b""
    strs = b""
    offsets = []
    for key in keys:
        encoded_id = key.encode("utf-8")
        encoded_str = catalogue[key].encode("utf-8")
        offsets.append((len(ids), len(encoded_id), len(strs), len(encoded_str)))
        ids += encoded_id + b"\x00"
        strs += encoded_str + b"\x00"

    count = len(keys)
    key_start = 7 * 4 + 16 * count
    value_start = key_start + len(ids)
    key_offsets = []
    value_offsets = []
    for id_offset, id_length, str_offset, str_length in offsets:
        key_offsets += [id_length, id_offset + key_start]
        value_offsets += [str_length, str_offset + value_start]

    output = struct.pack(
        "Iiiiiii",
        0x950412DE,  # magic
        0,           # revision
        count,
        7 * 4,       # offset of key table
        7 * 4 + count * 8,  # offset of value table
        0,           # hash table size
        0,           # hash table offset
    )
    output += struct.pack(f"{len(key_offsets)}i", *key_offsets)
    output += struct.pack(f"{len(value_offsets)}i", *value_offsets)
    output += ids
    output += strs

    mo_path.parent.mkdir(parents=True, exist_ok=True)
    mo_path.write_bytes(output)
    return count
