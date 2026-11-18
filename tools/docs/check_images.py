#!/usr/bin/env python3
"""Image links on docs pages (AA-1064): every image a page shows can be published to the CIS docs reader.

For every Markdown image ``![alt](src)`` on a tracked docs/**/*.md page outside the never-published folders
(build_docs_reader.py rule 2; fenced code and inline code spans are skipped), the image must:

  - have alt text (docs/STYLE.md, "Diagrams and images");
  - be a file in this repo: no remote or data: image (the reader never loads one, and a remote image leaks the
    viewer's IP address), no path that climbs above the repo root;
  - exist, be an SVG, PNG or WebP, and sit under docs/ outside the never-published folders (journals, audits, security,
    templates, archive), with a path the reader can serve (letters, digits, '.', '_', '-' only);
  - pass the bundle builder's own check: a PNG / WebP at most 300 KB, with its signature and no account or resource ID
    in its metadata (rule 10); an SVG at most 1 MB and safe to show (rule 9).

The checks are the builder's functions, so the lint and the published bundle cannot drift apart. Needs PyYAML (the
builder imports it): tools/docs/requirements.txt. Add `docs-lint: ignore` to a line to skip it.

New audit images (AA-1132 A9, --new-audit-images --base REF): audit folders are never published, so no page check
reaches their screenshots, and 3,000+ PNG evidence files had grown to ~39 MB of git history. An image file ADDED under
docs/audits/ since REF (`git diff --diff-filter=A REF HEAD`) must be a WebP or a PNG (a JPEG / GIF / BMP / TIFF:
convert it to WebP) and at most MAX_RASTER_BYTES (300 KB, the reader's screenshot cap). Files already in git are never
re-checked. SVG diagrams are text and are not checked here.

Usage:
  python tools/docs/check_images.py                 # every page in scope
  python tools/docs/check_images.py docs/guides/x.md ...
  python tools/docs/check_images.py --new-audit-images --base origin/master
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import build_docs_reader as b
from docslib import IGNORE_MARKER, REPO_ROOT, Finding, emit, list_markdown

TITLE = "Docs image"
AUDIT_PREFIX = "docs/audits/"
AUDIT_ALLOWED = (".webp", ".png")
AUDIT_REFUSED = (".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".avif")


def check_page(root: Path, relpath: str) -> list[Finding]:
    try:
        text = (root / relpath).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = text.splitlines()
    findings: list[Finding] = []

    def add(line: int, message: str) -> None:
        findings.append(Finding(relpath, line, TITLE, message))

    for n, alt, src in b.image_links(text):
        if IGNORE_MARKER in lines[n - 1]:
            continue
        if not alt:
            add(n, f"image '{src}' has no alt text; describe what it shows: ![what it shows]({src})")
        if b.is_external_image(src):
            add(n, f"remote or inline image '{src[:80]}': the docs reader never loads one; commit the file next to "
                   "the page and link it with a relative path")
            continue
        target = b.resolve_image(src, relpath)
        if target is None:
            add(n, f"image '{src}' does not point at a file in this repo")
            continue
        suffix = Path(target).suffix.lower()
        if suffix not in b.ASSET_SUFFIXES:
            add(n, f"image '{target}' is {suffix or 'without an extension'}; use SVG for diagrams, PNG or WebP for "
                   "screenshots")
            continue
        path = root / target
        if not path.is_file():
            add(n, f"image '{target}' does not exist")
            continue
        if not target.startswith("docs/") or b.is_never(target):
            add(n, f"image '{target}' is outside docs/ or in a folder that is never published; move it next to the "
                   "page (for example an images/ folder beside it)")
            continue
        if not b.ASSET_PATH.match(target):
            add(n, f"image '{target}': use letters, digits, '.', '_' and '-' only in the path (kebab-case names)")
            continue
        data = path.read_bytes()
        if suffix in b.RASTER_SUFFIXES:
            problems = b.raster_problems(data, suffix)
        elif len(data) > b.MAX_ASSET_BYTES:
            problems = [f"{len(data)} bytes, over the {b.MAX_ASSET_BYTES} byte SVG limit"]
        else:
            try:
                problems = b.svg_problems(data.decode("utf-8"))
            except UnicodeDecodeError:
                problems = ["not UTF-8"]
        for problem in problems:
            add(n, f"image '{target}': {problem}")
    return findings


def added_files(root: Path, base: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "--no-renames", "--diff-filter=A", base, "HEAD",
                          "--", AUDIT_PREFIX], check=True, capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def check_audit_images(root: Path, files: list[str]) -> list[Finding]:
    """A9: the new image files under docs/audits/: WebP or PNG, at most MAX_RASTER_BYTES."""
    findings: list[Finding] = []
    cap = b.MAX_RASTER_BYTES
    for relpath in files:
        if not relpath.startswith(AUDIT_PREFIX):
            continue
        suffix = Path(relpath).suffix.lower()
        if suffix in AUDIT_REFUSED:
            findings.append(Finding(relpath, 1, TITLE, f"new audit image is {suffix}: convert it to WebP "
                                                       f"(cwebp -q 80, or Pillow) and keep it under {cap // 1024} KB"))
            continue
        if suffix not in AUDIT_ALLOWED:
            continue
        path = root / relpath
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > cap:
            hint = "convert it to WebP" if suffix == ".png" else "lower the quality or crop it"
            findings.append(Finding(relpath, 1, TITLE, f"new audit image is {size // 1024} KB, over the {cap // 1024} KB "
                                                       f"cap: {hint} (git history keeps every byte forever)"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="repo-relative pages (default: every docs page in scope)")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--new-audit-images", action="store_true",
                        help="check the image files added under docs/audits/ since --base instead of the pages")
    parser.add_argument("--base", help="git ref the change is compared with (--new-audit-images)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.new_audit_images:
        if not args.base:
            parser.error("--new-audit-images needs --base")
        try:
            added = args.files or added_files(root, args.base)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"::error title={TITLE}::git diff against {args.base} failed: {exc}")
            return 1
        findings = check_audit_images(root, added)
        emit(findings, "error")
        print(f"audit images: {sum(1 for f in added if f.startswith(AUDIT_PREFIX))} new files under {AUDIT_PREFIX}, "
              f"{len(findings)} errors")
        return 1 if findings else 0
    files = args.files or list_markdown(b.SCOPE, root)
    files = [f for f in files if f.endswith(".md") and not b.is_never(f)]
    findings = [f for relpath in files for f in check_page(root, relpath)]
    emit(findings, "error")
    print(f"images: {len(files)} pages checked, {len(findings)} errors")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
