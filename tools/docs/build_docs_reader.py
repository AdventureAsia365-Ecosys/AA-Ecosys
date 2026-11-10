#!/usr/bin/env python3
"""Build the /admin/docs reader bundle: manifest.json + one Markdown file per published page (AA-898).

The CIS admin page /admin/docs (AA-CIS-App, Platform > Developer > Docs) is a READER for the docs catalog of this
repo. CI (.github/workflows/docs-sync.yml) runs this script on a clean checkout of master and uploads its output to
the S3 prefix the CIS API reads. Nothing is ever synced from a laptop, and only files tracked in git are read.

Publication rule (v1; docs/README.md "Docs reader" and docs/engineering-handbook.md section 4.3 describe it):

  1. Only tracked Markdown under docs/ is considered (git ls-files).
  2. Never published, whatever the front-matter says (NEVER_PREFIXES): journals (sessions, audits, implementation
     notes, backlog, research, calib, the git-ignored backups folder), security pages (docs/security/), templates,
     the archive and the Linear export. Security reports and audit evidence therefore never leave git.
  3. A page is published only when it is a catalog page (valid front-matter with id, title and type) or an ADR
     (docs/adr/NNNN-*.md, title from the H1, status from its Status line). Anything else is a draft or a journal.
  4. status "archived" is never published.
  5. Access tier (enforced by the CIS backend, N-3): a page whose catalog id is in the SEC family (security,
     privacy and legal pages that live outside docs/security/, e.g. docs/legal/, the secret rotation runbook) or is
     one of the generated infrastructure maps (ARCH-02 network, ARCH-03 inventory, ARCH-04 IAM roles) is "owner": the API lists and serves it only to a staff member with the owner flag (shared.admin_users.is_owner)
     on a verified Cognito session. Every other page is "staff" (every admin). The front-matter `audience` is a
     navigation filter only, never an access control (frontmatter.schema.json).
  6. Every published body is redacted: 12-digit account IDs (standalone or inside a bucket name or ARN), VPC
     resource IDs, Cognito user-pool IDs, API Gateway host IDs and AWS access key IDs are replaced by a
     [redacted-...] marker. After redaction the output is scanned again with the same patterns plus the
     resource-ids lint patterns (check_docs_text.py); any hit fails the build, so nothing is uploaded.
  7. Front-matter is stripped from the published body (the manifest carries the fields the page needs).
  8. Translations (S255, docs/STYLE.md "Language"): a page body is English; a Vietnamese version is a sibling file
     <same name>.vi.md with the same id plus `lang: vi` and `translation_of: <English path>`. It is published as its own
     entry only when its English page is published, and it always takes the English page's access tier. Every entry
     carries `lang`; an English entry lists its translations, a translation names its English page. ADRs have no
     front-matter and therefore no translation.
  9. SVG images (AA-697): a tracked docs/**/*.svg outside the never-published folders is published as an asset, byte for
     byte, so a page can show it (the architecture diagrams under docs/architecture/diagrams/). It is never redacted
     (a marker would break the inline icons); instead it must pass two checks or the build fails: (a) nothing a reader
     could run or fetch: no script, foreignObject or other active element, no event-handler attribute, no javascript:
     URL, no CSS url() or @import, no entity declarations, and every href is a fragment (#id) or an inline PNG
     (data:image/png;base64); (b) its text outside those inline PNGs passes the same guard as a page body (no account
     or resource ID). Assets are "staff" tier: an SVG must not carry owner-only content. An SVG larger than
     MAX_ASSET_BYTES is skipped.
 10. Screenshots (AA-1064, docs/STYLE.md "Diagrams and images"): a tracked PNG or WebP under docs/ is published as an
     asset only when a published page links it with ``![alt](relative.png)`` (rule 9 publishes every SVG; a screenshot
     goes out only when a page shows it, so design exports and evidence folders never leave git). It is published byte
     for byte and must pass the raster check or the build fails: at most MAX_RASTER_BYTES (300 KB), the PNG / WebP
     signature, and no account or resource ID in its text metadata (PNG tEXt / iTXt / zTXt / eXIf, WebP EXIF / XMP).
     The pixels cannot be checked: crop a screenshot before committing it. Its access tier is the most open tier of the
     pages that link it (a screenshot linked only from owner pages is owner tier). An image in a never-published folder,
     outside docs/ or with a path the reader cannot serve (letters, digits, '.', '_', '-' only) is not published.
     tools/docs/check_images.py checks the same rule on every catalog page in the docs lint.

Output layout (OUT_DIR, default _site/docs-reader):

  manifest.json                    format 1, below
  pages/<repo>/<repo-relative path> the redacted Markdown body of each published page
  assets/<repo>/<repo-relative path> each published SVG (rule 9) or screenshot (rule 10), unchanged

manifest.json:
  {"format": 1, "rule": "v1", "generated_at": ISO, "source": {"repo", "sha", "ref"},
   "counts": {"published", "owner_only", "translations", "skipped", "assets", "screenshots"},
   "pages": [{"repo", "path", "key", "id", "title", "description", "type", "status", "audience", "owner",
              "last_reviewed", "generated", "access", "bytes", "sha256", "redactions",
              "lang", "translation_of", "translations"}],
   "assets": [{"repo", "path", "key", "type", "bytes", "sha256", "access"}]}

  lang            "en" for an English page (the source), "vi" for a translation.
  translation_of  translations only: the `path` of the English entry (same repo); null on an English page.
  translations    English pages only: [{"lang", "path", "key", "title"}] of the published translations, sorted by lang;
                  [] when there is none and always [] on a translation. A reader lists entries with lang "en" and
                  offers a language toggle from `translations` / `translation_of`.

`key` is the object key relative to the S3 prefix (pages/<repo>/<path>, assets/<repo>/<path>); the API reads only keys
listed here. A reader that predates rule 9 ignores "assets"; one that predates rule 10 drops the PNG / WebP entries
(its asset shape check accepts .svg only), so either deploy order is safe.
Skipped pages are counted, never named, in the manifest.

Usage:
  python tools/docs/build_docs_reader.py                       # writes _site/docs-reader
  python tools/docs/build_docs_reader.py --out /tmp/reader --sha "$GITHUB_SHA" --ref master
  python tools/docs/build_docs_reader.py --check               # build in a temp dir, print the counts only
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from check_adr_index import ADR_FILE, find_status
from check_docs_text import RESOURCE_PATTERNS
from docslib import REPO_ROOT, SOURCE_LANG, list_markdown, source_of_translation, split_front_matter, translation_lang

FORMAT = 1
RULE = "v1"
REPO_NAME = "AA-Ecosys"
SCOPE = ["docs"]

# Rule 2: never published, whatever the page says about itself.
NEVER_PREFIXES = (
    "docs/sessions/",
    "docs/audits/",
    "docs/implementation-notes/",
    "docs/backlog/",
    "docs/research/",
    "docs/calib/",
    "docs/backups/",
    "docs/security/",
    "docs/templates/",
    "docs/archive/",
    "docs/linear-export/",
)
# Rule 5: catalog id families served to the owner only: SEC (security, privacy, legal) and the generated infrastructure
# maps ARCH-02 network, ARCH-03 inventory, ARCH-04 IAM roles (DM-6.10 keeps inventories out of public repos; here they
# are redacted and owner only).
OWNER_ONLY_ID_PREFIXES = ("SEC-", "ARCH-02", "ARCH-03", "ARCH-04")
# A page bigger than this is skipped (the reader is not a file store; the API refuses larger objects too).
MAX_PAGE_BYTES = 1_000_000
# Rule 9: an SVG bigger than this is skipped (the diagrams with inline icons are 0.2-0.4 MB).
MAX_ASSET_BYTES = 1_000_000
SVG_SUFFIXES = {".svg": "image/svg+xml"}
# Rule 10 (AA-1064): screenshots a published page links. docs/STYLE.md caps them at 300 KB; the CIS API refuses a
# larger stored object too (api/services/docs_reader.py MAX_RASTER_BYTES, same value).
RASTER_SUFFIXES = {".png": "image/png", ".webp": "image/webp"}
MAX_RASTER_BYTES = 300 * 1024
ASSET_SUFFIXES = {**SVG_SUFFIXES, **RASTER_SUFFIXES}
# The asset path shape the CIS API accepts (docs_reader._ASSET_PATH): ASCII letters, digits, '.', '_', '-' per segment.
ASSET_PATH = re.compile(r"^(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_TEXT_CHUNKS = (b"tEXt", b"iTXt", b"zTXt", b"eXIf")
WEBP_TEXT_CHUNKS = (b"EXIF", b"XMP ")
# A Markdown image: ![alt](src) or ![alt](<src with spaces> "title"). Fenced code and inline code spans are skipped.
IMAGE_LINK = re.compile(r"!\[([^\]\n]*)\]\(\s*(<[^>\n]*>|[^)\s]+)(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\s*\)")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
EXTERNAL = re.compile(r"^(?://|[a-z][a-z0-9+.-]*:)", re.I)

# Rule 6: (marker, pattern). Order matters: the ARN / bucket forms are covered by the account pattern, which runs
# last so the other patterns still see the full text.
REDACTIONS: list[tuple[str, re.Pattern[str]]] = [
    ("[redacted-access-key]", re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")),
    ("[redacted-vpc-id]",
     re.compile(r"(?<![\w-])(?:sg|subnet|vpc|vpce|rtb|igw|nat|eni|acl|eipalloc|tgw)-[0-9a-f]{8}(?:[0-9a-f]{9})?(?![\w-])")),
    ("[redacted-user-pool-id]", re.compile(r"(?<![\w-])[a-z]{2}-[a-z]+-\d_[A-Za-z0-9]{9}(?![\w-])")),
    ("[redacted-apigw-id]", re.compile(r"(?<![\w-])[a-z0-9]{10}(?=\.execute-api\.)")),
    # Any run of exactly 12 digits, also inside a bucket name (aa-cis-bronze-<account>) or an ARN.
    ("[redacted-account-id]", re.compile(r"(?<!\d)\d{12}(?!\d)")),
]
# The post-redaction guard: every redaction pattern plus the docs lint patterns.
GUARD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [(m, p) for m, p in REDACTIONS] + list(RESOURCE_PATTERNS)

H1 = re.compile(r"^#\s+(.+?)\s*#*\s*$")

# Rule 9 (a): what makes an SVG unsafe to show. The CIS API runs the same check again before it serves one
# (api/services/docs_reader.py); docs/architecture/diagrams/_common.py runs it when a diagram is rendered.
INLINE_PNG = re.compile(r"data:image/png;base64,[A-Za-z0-9+/=\s]*")
SVG_FORBIDDEN: list[tuple[str, re.Pattern[str]]] = [
    ("script element", re.compile(r"<\s*script", re.I)),
    ("foreignObject element", re.compile(r"<\s*foreignObject", re.I)),
    ("active element", re.compile(r"<\s*(?:iframe|object|embed|audio|video|animate\w*|set|handler|listener)\b", re.I)),
    ("event handler attribute", re.compile(r"\son[a-z]+\s*=", re.I)),
    ("javascript: URL", re.compile(r"javascript\s*:", re.I)),
    ("CSS @import", re.compile(r"@import", re.I)),
    ("CSS url() to a non-fragment", re.compile(r"url\(\s*['\"]?(?!#)", re.I)),
    ("entity declaration", re.compile(r"<!ENTITY|<!DOCTYPE[^>]*\[", re.I)),
]
SVG_REF = re.compile(r"\s(?:xlink:)?href\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", re.I)
SVG_START = re.compile(
    r"\s*(?:<\?xml[^>]*>\s*)?(?:<!--.*?-->\s*)*(?:<!DOCTYPE svg[^>\[]*>\s*)?(?:<!--.*?-->\s*)*<svg[\s>]", re.S)
# Rule 9 (a), parsed: the regexes above see the raw text, so a namespace prefix (<s:script>, x:href) or an XML character
# reference (u&#114;l(...)) slips past them. The parsed check allowlists what Graphviz writes instead: SVG-namespace
# elements from SVG_ELEMENTS only, attributes without a namespace (plus xlink:href / xlink:title / xml:space), no on*
# attribute, every href (any namespace) a fragment or an inline PNG, and no decoded attribute value that could fetch or
# run anything. Processing instructions other than the XML declaration are refused (xml-stylesheet).
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
SVG_ELEMENTS = frozenset({
    "svg", "g", "title", "desc", "defs", "use", "a", "image", "text", "tspan", "path", "polygon", "polyline",
    "ellipse", "circle", "rect", "line", "linearGradient", "radialGradient", "stop", "clipPath", "marker", "symbol"})
SVG_NS_ATTRS = frozenset({f"{{{XLINK_NS}}}href", f"{{{XLINK_NS}}}title", f"{{{XML_NS}}}space"})
SVG_BAD_VALUE = re.compile(r"url\(\s*['\"]?(?!#)|javascript\s*:|@import|image-set|expression\s*\(|\\", re.I)
SVG_XML_DECL = re.compile(r"\s*<\?xml\s[^>]*\?>")


@dataclass
class Page:
    path: str
    meta: dict
    body: str
    access: str
    redactions: int = 0
    lang: str = SOURCE_LANG
    translation_of: str | None = None
    translations: list[dict] = field(default_factory=list)


@dataclass
class Result:
    pages: list[Page] = field(default_factory=list)
    skipped: int = 0


def _stringify(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    if isinstance(value, list):
        return [_stringify(v) for v in value]
    if isinstance(value, dict):
        return {k: _stringify(v) for k, v in value.items()}
    return value


def is_never(relpath: str) -> bool:
    return relpath.startswith(NEVER_PREFIXES)


def access_for(page_id: str) -> str:
    return "owner" if page_id.startswith(OWNER_ONLY_ID_PREFIXES) else "staff"


def redact(text: str) -> tuple[str, int]:
    count = 0
    for marker, pattern in REDACTIONS:
        text, n = pattern.subn(marker, text)
        count += n
    return text, count


def guard_hits(text: str) -> list[str]:
    """Labels of the patterns that still match after redaction (markers themselves never match)."""
    return [label for label, pattern in GUARD_PATTERNS if pattern.search(text)]


def svg_problems(text: str) -> list[str]:
    """Rule 9: why an SVG may not be published (empty list = publishable)."""
    if not SVG_START.match(text):
        return ["not an SVG document"]
    problems = [label for label, pattern in SVG_FORBIDDEN if pattern.search(text)]
    for m in SVG_REF.finditer(text):
        ref = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        if not (ref.startswith("#") or INLINE_PNG.fullmatch(ref)):
            problems.append(f"outside reference {ref[:40]!r}")
    visible = INLINE_PNG.sub("data:image/png;base64,", text)
    problems += [f"{label} in the SVG text" for label in guard_hits(visible)]
    if not any(p.startswith("entity declaration") for p in problems):   # never parse an entity declaration
        problems += svg_tree_problems(text)
    return problems


def svg_tree_problems(text: str) -> list[str]:
    """Rule 9 (a) on the parsed document (see SVG_ELEMENTS): what the raw-text regexes cannot see."""
    import xml.etree.ElementTree as ET

    decl = SVG_XML_DECL.match(text)
    if "<?" in text[decl.end() if decl else 0:]:
        return ["processing instruction"]
    try:
        root = ET.fromstring(text)
    except ET.ParseError as err:
        return [f"not well-formed XML ({err})"]
    if root.tag != f"{{{SVG_NS}}}svg":
        return ["root element is not an SVG-namespace <svg>"]
    problems: list[str] = []
    decoded: list[str] = []
    for el in root.iter():
        ns, _, name = el.tag[1:].partition("}") if el.tag.startswith("{") else ("", "", el.tag)
        if ns != SVG_NS or name not in SVG_ELEMENTS:
            problems.append(f"element not allowed {el.tag[:60]!r}")
        decoded += [el.text or "", el.tail or ""]
        for attr, value in el.attrib.items():
            local = attr.rpartition("}")[2]
            if attr.startswith("{") and attr not in SVG_NS_ATTRS:
                problems.append(f"attribute not allowed {attr[:60]!r}")
            if local.lower().startswith("on"):
                problems.append(f"event handler attribute {local[:40]!r}")
            if local == "href":
                v = value.strip()
                if not (v.startswith("#") or INLINE_PNG.fullmatch(v)):
                    problems.append(f"outside reference {v[:40]!r}")
                continue
            if SVG_BAD_VALUE.search(value):
                problems.append(f"active attribute value {local[:40]}={value[:40]!r}")
            decoded.append(value)
    problems += [f"{label} in the decoded SVG text" for label in guard_hits(" ".join(decoded))]
    return sorted(set(problems))


# ── rule 10: image links and the raster check (shared with check_images.py) ─────────────────────────────

def image_links(text: str) -> list[tuple[int, str, str]]:
    """(line number, alt text, src) of every Markdown image outside fenced code blocks and inline code spans."""
    found: list[tuple[int, str, str]] = []
    fence: str | None = None
    for n, line in enumerate(text.splitlines(), 1):
        m = FENCE.match(line)
        if m:
            if fence is None:
                fence = m.group(1)
            elif m.group(1) == fence:
                fence = None
            continue
        if fence is not None:
            continue
        for img in IMAGE_LINK.finditer(INLINE_CODE.sub("", line)):
            src = img.group(2)
            if src.startswith("<") and src.endswith(">"):
                src = src[1:-1]
            found.append((n, img.group(1).strip(), src.strip()))
    return found


def is_external_image(src: str) -> bool:
    """A remote (http, https, protocol-relative) or other-scheme (data:, javascript:) image: the reader never loads it."""
    return bool(EXTERNAL.match(src.strip()))


def resolve_image(src: str, from_path: str) -> str | None:
    """The repo-relative path an image link on page `from_path` points at, the way the CIS reader resolves it
    (frontend/lib/docsReader.ts resolveImage): relative to the page folder, a leading '/' from the repo root, query and
    fragment dropped, percent-decoded. None for an external image, an empty or fragment-only src, or a path that climbs
    above the repo root."""
    s = src.strip()
    if not s or s.startswith("#") or is_external_image(s):
        return None
    s = s.split("#")[0].split("?")[0]
    try:
        s = urllib.parse.unquote(s, errors="strict")
    except UnicodeDecodeError:
        return None
    joined = s[1:] if s.startswith("/") else posixpath.join(posixpath.dirname(from_path), s)
    parts: list[str] = []
    for seg in joined.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(seg)
    return "/".join(parts) or None


def _png_text(data: bytes) -> tuple[str, bool]:
    """(text of the metadata chunks, well-formed) of a PNG that starts with the signature."""
    texts: list[bytes] = []
    i = len(PNG_SIGNATURE)
    while i + 8 <= len(data):
        size = int.from_bytes(data[i:i + 4], "big")
        kind = data[i + 4:i + 8]
        body = data[i + 8:i + 8 + size]
        if len(body) != size or i + 12 + size > len(data):
            return "", False
        if kind == b"zTXt":
            _, _, rest = body.partition(b"\0")
            try:
                # bounded: a small compressed chunk must not inflate without limit
                texts.append(zlib.decompressobj().decompress(rest[1:], 4 * MAX_RASTER_BYTES))
            except zlib.error:
                return "", False
        elif kind in PNG_TEXT_CHUNKS:
            texts.append(body)
        if kind == b"IEND":
            return b"\n".join(texts).decode("latin-1"), True
        i += 12 + size
    return "", False


def _webp_text(data: bytes) -> tuple[str, bool]:
    """(text of the metadata chunks, well-formed) of a RIFF/WEBP file."""
    texts: list[bytes] = []
    i = 12
    while i + 8 <= len(data):
        kind = data[i:i + 4]
        size = int.from_bytes(data[i + 4:i + 8], "little")
        body = data[i + 8:i + 8 + size]
        if len(body) != size:
            return "", False
        if kind in WEBP_TEXT_CHUNKS:
            texts.append(body)
        i += 8 + size + (size & 1)
    return b"\n".join(texts).decode("latin-1"), i == len(data)


def raster_problems(data: bytes, suffix: str) -> list[str]:
    """Rule 10: why a PNG / WebP may not be published (empty list = publishable)."""
    suffix = suffix.lower()
    if suffix not in RASTER_SUFFIXES:
        return [f"{suffix or 'no extension'} is not a screenshot type (PNG or WebP)"]
    problems: list[str] = []
    if len(data) > MAX_RASTER_BYTES:
        problems.append(f"{len(data)} bytes, over the {MAX_RASTER_BYTES // 1024} KB cap (crop it or save it as WebP)")
    if suffix == ".png":
        if not data.startswith(PNG_SIGNATURE):
            return problems + ["not a PNG file"]
        text, ok = _png_text(data)
    else:
        if not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
            return problems + ["not a WebP file"]
        text, ok = _webp_text(data)
    if not ok:
        problems.append("malformed image file")
    problems += [f"{label} in the image metadata" for label in guard_hits(text)]
    return problems


def _adr_meta(relpath: str, text: str) -> dict | None:
    name = Path(relpath).name
    if not ADR_FILE.match(name):
        return None
    title = next((m.group(1) for line in text.splitlines() if (m := H1.match(line))), None)
    if not title:
        return None
    status, _ = find_status(text)
    number = name.split("-", 1)[0]
    return {
        "id": f"ADR-{number.upper()}",
        "title": title.strip(),
        "type": "adr",
        "status": (status or "").strip("* ").split(" ", 1)[0].strip(".,;").lower() or "unknown",
        "audience": ["engineer", "cto", "agent"],
        "owner": "nghiep",
    }


def classify(relpath: str, text: str) -> tuple[dict, str] | None:
    """(meta, body) when the page is published under the rule, else None."""
    if is_never(relpath):
        return None
    try:
        raw, body_start = split_front_matter(text)
    except ValueError:
        return None
    if raw is None:
        if relpath.startswith("docs/adr/"):
            meta = _adr_meta(relpath, text)
            return (meta, text) if meta else None
        return None
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict):
        return None
    meta = _stringify(meta)
    if not all(isinstance(meta.get(k), str) and meta.get(k) for k in ("id", "title", "type")):
        return None
    if meta.get("status") == "archived":
        return None
    body = "\n".join(text.splitlines()[body_start - 1:]).lstrip("\n")
    return meta, body


def collect(root: Path = REPO_ROOT) -> Result:
    result = Result()
    for relpath in list_markdown(SCOPE, root):
        path = root / relpath
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            result.skipped += 1
            continue
        found = classify(relpath, text)
        if found is None or len(text.encode("utf-8")) > MAX_PAGE_BYTES:
            result.skipped += 1
            continue
        meta, body = found
        body, n = redact(body)
        title, nt = redact(str(meta["title"]))
        meta["title"] = title
        if isinstance(meta.get("description"), str):
            meta["description"], nd = redact(meta["description"])
            n += nd
        lang = translation_lang(relpath)
        page = Page(relpath, meta, body, access_for(str(meta["id"])), n + nt)
        if lang is not None:
            page.lang, page.translation_of = lang, source_of_translation(relpath)
        result.pages.append(page)
    return _link_translations(result)


def _link_translations(result: Result) -> Result:
    """Rule 8: keep a translation only when its English page is published with the same id; give it that page's access
    tier and list it on the English entry."""
    english = {p.path: p for p in result.pages if p.translation_of is None}
    kept: list[Page] = []
    for page in result.pages:
        if page.translation_of is None:
            kept.append(page)
            continue
        source = english.get(page.translation_of)
        if (source is None or page.meta.get("translation_of") != page.translation_of
                or str(source.meta.get("id")) != str(page.meta.get("id"))):
            result.skipped += 1
            continue
        page.access = source.access
        source.translations.append({"lang": page.lang, "path": page.path, "key": f"pages/{REPO_NAME}/{page.path}",
                                    "title": page.meta["title"]})
        kept.append(page)
    for page in kept:
        page.translations.sort(key=lambda t: t["lang"])
    result.pages = kept
    return result


@dataclass
class Asset:
    path: str
    data: bytes
    access: str = "staff"

    @property
    def key(self) -> str:
        return f"assets/{REPO_NAME}/{self.path}"

    def entry(self) -> dict:
        return {"repo": REPO_NAME, "path": self.path, "key": self.key,
                "type": ASSET_SUFFIXES[Path(self.path).suffix.lower()], "bytes": len(self.data),
                "sha256": hashlib.sha256(self.data).hexdigest(), "access": self.access}


def list_assets(root: Path = REPO_ROOT, suffixes=None) -> list[str]:
    """Tracked image files under docs/ (git ls-files); a filesystem walk outside a git checkout (unit tests).
    `suffixes` defaults to the SVG suffix (rule 9)."""
    suffixes = SVG_SUFFIXES if suffixes is None else suffixes
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", *SCOPE],
                             check=True, capture_output=True).stdout.decode("utf-8")
        files = [f for f in out.split("\0") if Path(f).suffix.lower() in suffixes]
        if files or (root / ".git").exists():
            return sorted(files)
    except (OSError, subprocess.CalledProcessError):
        pass
    found: list[str] = []
    for scope in SCOPE:
        base = root / scope
        if base.is_dir():
            found += [p.relative_to(root).as_posix() for p in base.rglob("*")
                      if p.is_file() and p.suffix.lower() in suffixes]
    return sorted(found)


def collect_raster_assets(pages: list[Page], root: Path = REPO_ROOT) -> tuple[list[Asset], list[str]]:
    """Rule 10: (screenshots the published pages link, problems that fail the build)."""
    linked: dict[str, str] = {}
    for page in pages:
        for _line, _alt, src in image_links(page.body):
            target = resolve_image(src, page.path)
            if (target is None or Path(target).suffix.lower() not in RASTER_SUFFIXES
                    or not target.startswith("docs/") or is_never(target) or not ASSET_PATH.match(target)):
                continue
            linked[target] = "staff" if page.access == "staff" or linked.get(target) == "staff" else "owner"
    tracked = set(list_assets(root, RASTER_SUFFIXES))
    assets: list[Asset] = []
    problems: list[str] = []
    for relpath in sorted(linked):
        if relpath not in tracked:
            continue   # a missing image: the page shows its alt text; check_images.py fails the docs lint on it
        try:
            data = (root / relpath).read_bytes()
        except OSError:
            continue
        found = raster_problems(data, Path(relpath).suffix)
        if found:
            problems += [f"{relpath}: {p}" for p in found]
            continue
        assets.append(Asset(relpath, data, linked[relpath]))
    return assets, problems


def collect_assets(root: Path = REPO_ROOT) -> tuple[list[Asset], list[str]]:
    """Rule 9: (publishable SVG assets, problems that fail the build)."""
    assets: list[Asset] = []
    problems: list[str] = []
    for relpath in list_assets(root):
        if is_never(relpath):
            continue
        try:
            data = (root / relpath).read_bytes()
        except OSError:
            continue
        if len(data) > MAX_ASSET_BYTES:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{relpath}: not UTF-8")
            continue
        found = svg_problems(text)
        if found:
            problems += [f"{relpath}: {p}" for p in found]
            continue
        assets.append(Asset(relpath, data))
    return assets, problems


def _entry(page: Page) -> dict:
    data = page.body.encode("utf-8")
    m = page.meta
    audience = m.get("audience") if isinstance(m.get("audience"), list) else []
    return {
        "repo": REPO_NAME,
        "path": page.path,
        "key": f"pages/{REPO_NAME}/{page.path}",
        "id": m["id"],
        "title": m["title"],
        "description": m.get("description") if isinstance(m.get("description"), str) else None,
        "type": m["type"],
        "status": m.get("status"),
        "audience": [a for a in audience if isinstance(a, str)],
        "owner": m.get("owner"),
        "last_reviewed": m.get("last_reviewed"),
        "generated": bool(m.get("generated", False)),
        "access": page.access,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "redactions": page.redactions,
        "lang": page.lang,
        "translation_of": page.translation_of,
        "translations": [dict(t) for t in page.translations],
    }


def build(out: Path, root: Path = REPO_ROOT, sha: str = "", ref: str = "") -> dict:
    """Write the bundle to `out` (emptied first) and return the manifest. Raises SystemExit on a guard hit."""
    result = collect(root)
    assets, problems = collect_assets(root)
    rasters, raster_problems_found = collect_raster_assets(result.pages, root)
    assets += rasters
    problems += raster_problems_found
    for page in result.pages:
        # Everything a reader sees: the body and the manifest's text fields (not the sha256, which is hex).
        visible = {k: v for k, v in _entry(page).items() if k not in ("sha256", "bytes", "redactions")}
        for label in guard_hits(page.body + "\n" + json.dumps(visible, ensure_ascii=False)):
            problems.append(f"{page.path}: {label} still present after redaction")
    if problems:
        for p in problems:
            print(f"::error title=Docs reader guard::{p}")
        raise SystemExit(1)

    if out.exists():
        shutil.rmtree(out)
    (out / "pages").mkdir(parents=True)
    entries = []
    for page in sorted(result.pages, key=lambda p: p.path):
        target = out / "pages" / REPO_NAME / page.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page.body, encoding="utf-8")
        entries.append(_entry(page))
    for asset in assets:
        target = out / asset.key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(asset.data)
    manifest = {
        "format": FORMAT,
        "rule": RULE,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": {"repo": REPO_NAME, "sha": sha or _git_sha(root), "ref": ref or None},
        "counts": {
            "published": len(entries),
            "owner_only": sum(1 for e in entries if e["access"] == "owner"),
            "translations": sum(1 for e in entries if e["translation_of"]),
            "skipped": result.skipped,
            "assets": len(assets),
            "screenshots": len(rasters),
        },
        "pages": entries,
        "assets": [a.entry() for a in assets],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def _git_sha(root: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", default="_site/docs-reader", help="output folder (emptied first)")
    ap.add_argument("--sha", default="", help="commit the bundle is built from (default: git HEAD)")
    ap.add_argument("--ref", default="", help="branch name recorded in the manifest")
    ap.add_argument("--check", action="store_true", help="build into a temp folder and print the counts only")
    args = ap.parse_args(argv)
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = build(Path(tmp) / "out", sha=args.sha, ref=args.ref)
    else:
        manifest = build(Path(args.out), sha=args.sha, ref=args.ref)
    c = manifest["counts"]
    redacted = sum(p["redactions"] for p in manifest["pages"])
    print(f"docs reader: {c['published']} pages published ({c['owner_only']} owner only, {c['translations']} translations), "
          f"{c['skipped']} skipped, {c['assets']} assets ({c['screenshots']} screenshots), "
          f"{redacted} values redacted, source {manifest['source']['sha'][:12] or 'unknown'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
