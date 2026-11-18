#!/usr/bin/env python3
"""The full-text search index of the /admin/docs reader (AA-1133, S283 decision c-s283-docs-search: server-side FTS5).

build_docs_reader.py calls :func:`write_index` at publish time, after the redaction guard passed, with the published
pages (redacted bodies and titles only, nothing else). The result is one SQLite file, ``search/index.sqlite`` in the
bundle, uploaded by the Docs sync workflow next to the pages; the manifest names it (``search``: key, format, bytes,
sha256, sections). The CIS API (api/services/docs_search.py) loads it read-only, checks its sha256 against the manifest,
and answers ``GET /admin/docs/search``, filtering every hit by the caller's access tier.

Index layout (format 1):

  meta(key, value)          format, source sha
  sections (FTS5)           one row per heading section of a published page:
      title    the page title                 (indexed, weight highest)
      heading  the section heading text       (indexed)
      body     the section text, Markdown marks removed, Mermaid sources skipped (indexed)
      folded   title + heading + body with "đ" / "Đ" spelled "d" / "D", only when the section has one (indexed;
               unicode61 folds every other Vietnamese mark but not the stroke, so "dem" would miss "đêm")
      repo, path, lang, access, slug          (UNINDEXED: where the hit opens and who may see it)

``slug`` is the reader's heading slug (frontend lib/docsReader.ts ``outline`` / ``Slugger``: lower case, punctuation
dropped, each space a "-", "-1" / "-2" for repeats), so a hit opens the page at that heading (``#doc-<slug>``). The text
before the first heading is a section with an empty slug (the top of the page).

Tokenizer: ``unicode61 remove_diacritics 2`` (case and accents folded), so "hoi an" finds "Hội An" and a query typed
without Vietnamese marks still matches (the folded column covers "đ"). Typo tolerance (a trigram table) is a later slice.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

FORMAT = 1
KEY = "search/index.sqlite"

_FENCE = re.compile(r"^\s*(```+|~~~+)\s*([A-Za-z0-9_+-]*)")
_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MARKS = re.compile(r"[`*_~]")
_SLUG_DROP = re.compile(r"[^\w\s-]", re.UNICODE)
_SPACE = re.compile(r"\s")
_TEXT_MARKS = re.compile(r"[`*_~>#|]|<!--.*?-->|<[^>\n]+>")
_WS = re.compile(r"\s+")
_STROKE = str.maketrans({"đ": "d", "Đ": "D"})


def heading_text(md: str) -> str:
    """Plain text of an inline Markdown heading (frontend lib/docsReader.ts headingText)."""
    text = _IMAGE.sub(r"\1", md)
    text = _LINK.sub(r"\1", text)
    return _MARKS.sub("", text).strip()


def slugify(text: str) -> str:
    """GitHub-like heading slug (frontend lib/docsReader.ts slugify): lower case, punctuation dropped (letters with
    accents and digits kept), each whitespace character a "-"."""
    return _SPACE.sub("-", _SLUG_DROP.sub("", text.strip().lower()))


class Slugger:
    """Repeated slugs get -1, -2 like GitHub (frontend lib/docsReader.ts Slugger)."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        base = slugify(text) or "section"
        n = self._seen.get(base)
        self._seen[base] = (-1 if n is None else n) + 1
        return base if n is None else f"{base}-{n + 1}"


def plain_text(md: str) -> str:
    """Searchable text of a Markdown fragment: link and image targets dropped, marks and HTML tags removed."""
    text = _IMAGE.sub(r"\1", md)
    text = _LINK.sub(r"\1", text)
    text = _TEXT_MARKS.sub(" ", text)
    return _WS.sub(" ", text).strip()


def sections(body: str, title: str) -> list[tuple[str, str, str]]:
    """(heading, slug, text) for each section of a page body; the first is the text before any heading ("" slug,
    the page title as heading). Headings inside fenced code are not headings; Mermaid sources are not indexed."""
    slugger = Slugger()
    out: list[tuple[str, str, list[str]]] = [(title, "", [])]
    fence: str | None = None
    skip_fence = False
    for line in body.split("\n"):
        f = _FENCE.match(line)
        if f:
            if fence is None:
                fence = f.group(1)[0]
                skip_fence = f.group(2).lower() == "mermaid"
                continue
            if f.group(1)[0] == fence:
                fence = None
                skip_fence = False
                continue
        if fence is not None:
            if not skip_fence:
                out[-1][2].append(line)
            continue
        m = _HEADING.match(line)
        if m:
            text = heading_text(m.group(2))
            out.append((text, slugger.slug(text), []))
            continue
        out[-1][2].append(line)
    rows = []
    for heading, slug, lines in out:
        text = plain_text("\n".join(lines))
        if slug == "" and not text:
            continue   # nothing before the first heading
        rows.append((heading, slug, text))
    return rows


def folded(*parts: str) -> str:
    """The "đ"-folded copy of a section's text, or "" when it has no "đ" / "Đ" (nothing to add to the index)."""
    text = " ".join(parts)
    return text.translate(_STROKE) if ("đ" in text or "Đ" in text) else ""


def write_index(target: Path, pages: list[dict], source_sha: str) -> int:
    """Write the index for ``pages`` ([{repo, path, lang, access, title, body}], already redacted and guard-checked) to
    ``target``; return the number of sections. Raises RuntimeError when this SQLite has no FTS5."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    conn = sqlite3.connect(str(target))
    try:
        try:
            conn.execute(
                "CREATE VIRTUAL TABLE sections USING fts5(title, heading, body, folded, repo UNINDEXED, path UNINDEXED, "
                "lang UNINDEXED, access UNINDEXED, slug UNINDEXED, tokenize = 'unicode61 remove_diacritics 2')")
        except sqlite3.OperationalError as err:
            raise RuntimeError(f"this SQLite ({sqlite3.sqlite_version}) has no FTS5: {err}") from err
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany("INSERT INTO meta (key, value) VALUES (?, ?)",
                         [("format", str(FORMAT)), ("source_sha", source_sha or "")])
        count = 0
        for page in sorted(pages, key=lambda p: (p["repo"], p["path"])):
            rows = [(page["title"], heading, text, folded(page["title"], heading, text), page["repo"], page["path"],
                     page["lang"], page["access"], slug)
                    for heading, slug, text in sections(page["body"], page["title"])]
            conn.executemany("INSERT INTO sections (title, heading, body, folded, repo, path, lang, access, slug) "
                             "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
            count += len(rows)
        conn.execute("INSERT INTO sections (sections) VALUES ('optimize')")
        conn.commit()
        conn.execute("VACUUM")
    finally:
        conn.close()
    return count
