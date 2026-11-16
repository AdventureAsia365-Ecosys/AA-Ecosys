#!/usr/bin/env python3
"""Kit sources stay generic (AA-1103): every root file the public project template copies, after the kit transform,
holds no AA name, ID or account number.

The new-project kit's template repo (public, no AA names: kit decision D13) copies the files listed in
tools/project-kit/kit-sources.txt from this repo byte for byte, after tools/project-kit/kit_transform.py leaves out the blocks and
lines marked kit:skip / kit:drop. A source that gains an AA term outside those markers would leak into the public
template at its next release; this check fails first, in the root repo's Docs lint.

Checks, for each `<source> <dest>` line of kit-sources.txt:
  - the source exists and its kit markers are balanced;
  - its transformed text matches no pattern of tools/project-kit/kit-denylist.txt (AA names, issue keys, people, hosts,
    account-number shapes);
  - the dest path is relative, inside the template repo, and unique.

Usage: python3 tools/project-kit/check_kit_sources.py [--root <repo root>]
       python3 tools/project-kit/check_kit_sources.py --scan <dir> [--denylist <file>]   (scan a tree, e.g. the template repo)
Test:  python3 -m unittest discover -s tools/project-kit -p 'test_*.py'
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_transform import MarkerError, transform_bytes  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCES = HERE / "kit-sources.txt"
DENYLIST = HERE / "kit-denylist.txt"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".tmp-session"}


def read_list(path: Path) -> list[tuple[int, list[str]]]:
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.split("#", 1)[0].strip() if line.lstrip().startswith("#") else line.strip()
        if line:
            rows.append((n, line.split()))
    return rows


def load_denylist(path: Path) -> list[re.Pattern]:
    pats = []
    for n, (_, words) in enumerate(read_list(path), start=1):
        pats.append(re.compile(" ".join(words)))
    return pats


def leaks(text: str, pats: list[re.Pattern]) -> list[tuple[int, str]]:
    """(line number, pattern) for every line that matches a denylist pattern. The matched text is not returned."""
    found = []
    for i, line in enumerate(text.splitlines(), start=1):
        for p in pats:
            if p.search(line):
                found.append((i, p.pattern))
                break
    return found


def check_sources(root: Path, sources: Path, denylist: Path) -> list[str]:
    pats = load_denylist(denylist)
    errors: list[str] = []
    seen: dict[str, int] = {}
    for n, words in read_list(sources):
        if len(words) != 2:
            errors.append(f"{sources.name}:{n}: expected `<source> <dest>`, got {len(words)} field(s)")
            continue
        src, dest = words
        d = PurePosixPath(dest)
        if d.is_absolute() or ".." in d.parts:
            errors.append(f"{sources.name}:{n}: dest {dest} must be a relative path inside the template repo")
        if dest in seen:
            errors.append(f"{sources.name}:{n}: dest {dest} is listed twice (line {seen[dest]})")
        seen[dest] = n
        path = root / src
        if not path.is_file():
            errors.append(f"{sources.name}:{n}: source {src} does not exist")
            continue
        try:
            data = transform_bytes(path.read_bytes(), src)
        except MarkerError as e:
            errors.append(str(e))
            continue
        for line, pat in leaks(data.decode("utf-8", "replace"), pats):
            errors.append(f"{src}:{line}: matches the kit denylist ({pat}); reword it or mark it kit:skip / kit:drop")
    return errors


def scan_tree(base: Path, denylist: Path) -> list[str]:
    pats = load_denylist(denylist)
    errors = []
    for p in sorted(base.rglob("*")):
        if not p.is_file() or SKIP_DIRS & set(p.relative_to(base).parts):
            continue
        rel = p.relative_to(base).as_posix()
        for line, pat in leaks(rel, pats):
            errors.append(f"{rel}: the path matches the kit denylist ({pat})")
        try:
            text = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        for line, pat in leaks(text, pats):
            errors.append(f"{rel}:{line}: matches the kit denylist ({pat})")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--sources", type=Path, default=SOURCES)
    ap.add_argument("--denylist", type=Path, default=DENYLIST)
    ap.add_argument("--scan", type=Path, help="scan every text file of this tree instead of the kit sources")
    a = ap.parse_args(argv)
    if a.scan:
        errors = scan_tree(a.scan, a.denylist)
        what = f"files under {a.scan}"
    else:
        errors = check_sources(a.root, a.sources, a.denylist)
        what = f"{len(read_list(a.sources))} kit sources"
    for e in errors:
        print(e)
    print(f"kit sources: {what} checked, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
