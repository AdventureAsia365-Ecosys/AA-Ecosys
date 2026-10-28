#!/usr/bin/env python3
"""PRD front matter and reference check (AA-894 scope 4; rules in docs/product/README.md).

For every page under docs/product/ except docs/product/README.md (a PRD):
  * the front matter has `linear` (at least one AA-<n> key) and the path lists `adrs`, `contracts`, `erd`,
    `migrations` (lists, `[]` allowed);
  * the page has a `## Acceptance criteria` section with at least one item `- **AC-<n>** ...`, IDs unique.
For every docs page with front matter (journals excluded), each entry of `adrs`, `contracts`, `erd` and `migrations`
is a repo-relative path that exists. A path into another workspace repo (`apps/<repo>/...`, `infra/<repo>/...`) is
checked when that repo is checked out next to this one (the local workspace) and reported as a warning otherwise
(root CI has only this repo).

Exit 1 on any error. Root repo only (the app and Infra repos hold no PRDs); not one of the vendored files.

Usage:
  python tools/docs/check_prd_refs.py [--root PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath

import yaml

from docslib import REPO_ROOT, Finding, emit, is_journal, list_markdown, split_front_matter, translation_lang

PRD_DIR = "docs/product/"
PRD_INDEX = "docs/product/README.md"
PATH_FIELDS = ("adrs", "contracts", "erd", "migrations")
OTHER_REPO_PREFIXES = ("apps/", "infra/")
LINEAR_RE = re.compile(r"^AA-[0-9]+$")
AC_HEADING_RE = re.compile(r"^## Acceptance criteria\s*$")
AC_ITEM_RE = re.compile(r"^\s*[-*] \*\*(AC-[0-9]+)\*\*")
HEADING_RE = re.compile(r"^#{1,2} ")


def is_prd(relpath: str) -> bool:
    # A translation (<name>.vi.md, docs/STYLE.md "Language") is the same PRD in another language, not a second PRD;
    # its front matter is checked as a translation by check_frontmatter.py.
    return relpath.startswith(PRD_DIR) and relpath != PRD_INDEX and translation_lang(relpath) is None


def _line_of(lines: list[str], key: str) -> int:
    for i, line in enumerate(lines, 1):
        if line.startswith(f"{key}:"):
            return i
    return 1


def check_path(root: Path, relpath: str, field: str, entry, line: int) -> tuple[list[Finding], list[Finding]]:
    errors: list[Finding] = []
    warnings: list[Finding] = []
    title = "PRD reference"
    if not isinstance(entry, str) or not entry.strip():
        return [Finding(relpath, line, title, f"{field}: entries must be non-empty strings, got {entry!r}")], []
    p = PurePosixPath(entry)
    if p.is_absolute() or ".." in p.parts or entry.startswith("./"):
        return [Finding(relpath, line, title, f"{field}: {entry} must be a repo-relative path (no '/', './', '..')")], []
    if entry.startswith(OTHER_REPO_PREFIXES) and len(p.parts) >= 2:
        repo_dir = root / p.parts[0] / p.parts[1]
        if not repo_dir.is_dir():
            warnings.append(Finding(relpath, line, title, f"{field}: {entry} is in another repo "
                                    f"({p.parts[0]}/{p.parts[1]}), not checked out here: not checked"))
            return errors, warnings
    if not (root / entry).exists():
        errors.append(Finding(relpath, line, title, f"{field}: {entry} does not exist"))
    return errors, warnings


def acceptance_ids(body: list[str]) -> tuple[list[str] | None, list[str]]:
    """(AC ids in the '## Acceptance criteria' section or None without the section, duplicate ids)."""
    ids: list[str] | None = None
    for line in body:
        if AC_HEADING_RE.match(line):
            ids = []
            continue
        if ids is not None:
            if HEADING_RE.match(line):
                break
            m = AC_ITEM_RE.match(line)
            if m:
                ids.append(m.group(1))
    dupes = sorted({i for i in (ids or []) if (ids or []).count(i) > 1})
    return ids, dupes


def check_page(root: Path, relpath: str) -> tuple[list[Finding], list[Finding]]:
    text = (root / relpath).read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[Finding] = []
    warnings: list[Finding] = []
    prd = is_prd(relpath)
    try:
        raw, body_start = split_front_matter(text)
    except ValueError as exc:
        return ([Finding(relpath, 1, "PRD front matter", str(exc))] if prd else []), []
    if raw is None:
        return ([Finding(relpath, 1, "PRD front matter", "a PRD needs front matter (docs/product/README.md)")]
                if prd else []), []
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return ([Finding(relpath, 1, "PRD front matter", f"YAML does not parse: {exc}")] if prd else []), []
    if not isinstance(data, dict):
        return [], []
    if prd:
        linear = data.get("linear")
        if not isinstance(linear, list) or not linear:
            errors.append(Finding(relpath, _line_of(lines, "linear"), "PRD front matter",
                                  "linear: at least one Linear issue key (AA-<n>) is required"))
        else:
            bad = [k for k in linear if not isinstance(k, str) or not LINEAR_RE.match(k)]
            if bad:
                errors.append(Finding(relpath, _line_of(lines, "linear"), "PRD front matter",
                                      f"linear: not an issue key: {', '.join(map(str, bad))}"))
        for field in PATH_FIELDS:
            if field not in data:
                errors.append(Finding(relpath, 1, "PRD front matter",
                                      f"{field}: required on a PRD (use [] when there is nothing yet)"))
            elif not isinstance(data[field], list):
                errors.append(Finding(relpath, _line_of(lines, field), "PRD front matter",
                                      f"{field}: must be a list of repo-relative paths"))
        ids, dupes = acceptance_ids(lines[body_start - 1:])
        if ids is None:
            errors.append(Finding(relpath, 1, "PRD acceptance criteria", "missing section '## Acceptance criteria'"))
        elif not ids:
            errors.append(Finding(relpath, 1, "PRD acceptance criteria",
                                  "no criterion: items start with '- **AC-<n>**'"))
        if dupes:
            errors.append(Finding(relpath, 1, "PRD acceptance criteria", f"duplicate IDs: {', '.join(dupes)}"))
    for field in PATH_FIELDS:
        entries = data.get(field)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            e, w = check_path(root, relpath, field, entry, _line_of(lines, field))
            errors += e
            warnings += w
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root (default: this checkout)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors: list[Finding] = []
    warnings: list[Finding] = []
    pages = [p for p in list_markdown(["docs"], root) if not is_journal(p)]
    prds = [p for p in pages if is_prd(p)]
    for relpath in pages:
        e, w = check_page(root, relpath)
        errors += e
        warnings += w
    emit(warnings, "warning")
    emit(errors, "error")
    print(f"prd-refs: {len(prds)} PRD(s), {len(pages)} pages scanned, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
