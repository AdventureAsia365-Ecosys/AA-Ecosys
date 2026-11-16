#!/usr/bin/env python3
"""Kit transform: the one change a kit source may get on its way into the project template.

The new-project kit keeps one home per fact: a template, playbook page, skill or hook lives once in its source repo,
and the template repo copies it. A source may hold lines that only make sense in its own repo (pointers to the
source project's overlay) and, in their place, generic lines that only make sense in the copy. Both are marked; the
markers are HTML or # comments, so the source renders and runs as if they were not there.

  Leave out of the copy (the source keeps them):
    Markdown block:   a line `<!-- kit:skip -->` ... a line `<!-- /kit:skip -->` (marker lines go too)
    hash block:       a line `# kit:skip` ... a line `# /kit:skip`
    one line:         a line that ends with `<!-- kit:drop -->` (a table row may end with `<!-- kit:drop --> |`)
                      or with `# kit:drop`
  Put only into the copy (hidden in the source):
    Markdown block:   a line `<!-- kit:only` ... a line `kit:only -->` (the lines between are copied as they are)
    Markdown line:    a line `<!-- kit:only <text> -->` becomes `<text>`
    hash line:        a line `# kit:only <text>` becomes `<text>` (YAML front matter, Python, shell, text)

Nothing else changes: every other byte is copied as is. When a removed part sat between two blank lines, one of them
goes too, so the copy keeps single blank lines. Blocks must be balanced and never nested.

The template repo carries a byte copy of this file and checks every copied file against
transform(<source>) == <copy>, so a hand edit of a copy turns its CI red.

Usage: python3 kit_transform.py <source file>   (prints the transformed text)
"""

from __future__ import annotations

import re
import sys

_SKIP_OPEN = re.compile(r"^\s*(?:<!--\s*kit:skip\s*-->|#\s*kit:skip)\s*$")
_SKIP_CLOSE = re.compile(r"^\s*(?:<!--\s*/kit:skip\s*-->|#\s*/kit:skip)\s*$")
_DROP = re.compile(r"(?:<!--\s*kit:drop\s*-->\s*\|?|#\s*kit:drop)\s*$")
_ONLY_OPEN = re.compile(r"^\s*<!--\s*kit:only\s*$")
_ONLY_CLOSE = re.compile(r"^\s*kit:only\s*-->\s*$")
_ONLY_LINE_MD = re.compile(r"^<!--\s*kit:only (.*?)\s*-->\s*$")
_ONLY_LINE_HASH = re.compile(r"^#\s*kit:only (.*)$")


class MarkerError(ValueError):
    """Unbalanced or nested kit markers."""


def transform(text: str, name: str = "<text>") -> str:
    """The copy of `text`: kit:skip / kit:drop parts left out, kit:only parts put in."""
    lines = text.split("\n")
    out: list[str] = []
    state = ""  # "", "skip" or "only"
    opened_at = 0
    removed = False  # something was left out since the last kept line

    def keep(line: str) -> None:
        nonlocal removed
        if removed and line.strip() == "" and out and out[-1].strip() == "":
            return  # the blank line after a removed part, when the line before it is blank too
        removed = False
        out.append(line)

    for i, line in enumerate(lines, start=1):
        if _SKIP_OPEN.match(line) or _ONLY_OPEN.match(line):
            if state:
                raise MarkerError(f"{name}:{i}: a kit block opened inside the kit:{state} block of line {opened_at}")
            state, opened_at, removed = ("skip" if _SKIP_OPEN.match(line) else "only"), i, True
            continue
        if _SKIP_CLOSE.match(line) or _ONLY_CLOSE.match(line):
            want = "skip" if _SKIP_CLOSE.match(line) else "only"
            if state != want:
                raise MarkerError(f"{name}:{i}: kit:{want} block closed without being open")
            state, removed = "", True
            continue
        if state == "skip":
            continue
        if state == "only":
            keep(line)
            continue
        m = _ONLY_LINE_MD.match(line) or _ONLY_LINE_HASH.match(line)
        if m:
            keep(m.group(1))
            continue
        if _DROP.search(line):
            removed = True
            continue
        keep(line)
    if state:
        raise MarkerError(f"{name}:{opened_at}: kit:{state} block is never closed")
    return "\n".join(out)


def transform_bytes(data: bytes, name: str = "<bytes>") -> bytes:
    """Text files go through transform(); a file that is not UTF-8 text is copied unchanged."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    if "kit:" not in text:
        return data
    return transform(text, name).encode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], "rb") as fh:
        sys.stdout.buffer.write(transform_bytes(fh.read(), sys.argv[1]))
