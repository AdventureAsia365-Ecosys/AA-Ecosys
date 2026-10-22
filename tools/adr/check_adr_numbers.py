#!/usr/bin/env python3
"""ADR number check (AA-928). Stdlib only.

Reads the ADR folder (default docs/adr) and the "Numbering" section of its README.md:

    | Number | Status | For |
    |---|---|---|
    | 0009 | Reserved | AI platform and governance (AA-804) |

    Next free root numbers: **0011**, **0014**.

The older one-line form "Reserved: **0009** AI platform (AA-804)." is also understood (base branches before AA-928).

Static rules (the tree as it is):
  S1  one base file per number (no two `0010-*.md`), one file per amendment (no two `0006a-*.md`);
  S2  an amendment `NNNNx` has its base ADR `NNNN-*.md`;
  S3  a reserved number has no ADR file (base or amendment);
  S4  every reservation names its Linear issue (AA-n);
  S5  the "Next free root numbers" line equals the computed list: every unused, unreserved number below the
      highest used-or-reserved number, then that number + 1.

PR rules (--base <git ref>: compares the ADR files this branch adds with the base branch):
  D1  an added ADR must not reuse a number (or amendment letter) that the base already uses, unless the base file with
      that number is gone in this tree (a rename);
  D2  an added ADR with a number the base reserves passes only when its header (the lines before the first "## ")
      cites the reserving issue and this tree no longer reserves the number;
  D3  an added base ADR takes one of the base's next free numbers (computed, not read), or a number reserved for it
      (D2); no skipping ahead;
  D4  an added amendment takes the next letter after the base's last amendment of that ADR.

Usage:
  python tools/adr/check_adr_numbers.py                      # static rules on docs/adr
  python tools/adr/check_adr_numbers.py --base origin/master  # static + PR rules against a git ref
  python tools/adr/check_adr_numbers.py --propose 0011        # is 0011 free to use? (exit 1 if not)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_FILE = re.compile(r"^(?P<num>\d{4})(?P<suffix>[a-z]?)-[a-z0-9-]+\.md$")
ISSUE = re.compile(r"\bAA-\d+\b")
TABLE_ROW = re.compile(r"^\|\s*(?P<num>\d{4})\s*\|\s*(?P<status>[^|]+?)\s*\|\s*(?P<what>[^|]*?)\s*\|\s*$")
LEGACY_RESERVED = re.compile(r"^Reserved:\s*(?P<rest>.+)$")
LEGACY_ITEM = re.compile(r"\*\*(?P<num>\d{4})\*\*\s*(?P<what>[^*]*)")
NEXT_FREE = re.compile(r"^Next free root numbers?:\s*(?P<rest>.+)$", re.IGNORECASE)
NUMBER_TOKEN = re.compile(r"\b(\d{4})\b")


@dataclass
class AdrSet:
    """ADR files and the README's numbering data, from a folder or a git ref."""

    files: list[str] = field(default_factory=list)
    readme: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def parsed(self) -> list[tuple[str, int, str]]:
        out = []
        for name in self.files:
            m = ADR_FILE.match(name)
            if m:
                out.append((name, int(m.group("num")), m.group("suffix")))
        return out

    def used_numbers(self) -> set[int]:
        return {num for _, num, _ in self.parsed}

    def base_numbers(self) -> set[int]:
        return {num for _, num, suffix in self.parsed if not suffix}

    def letters(self, num: int) -> list[str]:
        return sorted(suffix for _, n, suffix in self.parsed if n == num and suffix)

    def reservations(self) -> dict[int, str]:
        return parse_reservations(self.readme)

    def next_free_line(self) -> list[int] | None:
        return parse_next_free(self.readme)


def numbering_section(readme: str) -> list[str]:
    lines = readme.splitlines()
    out: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            inside = line[3:].strip().lower() == "numbering"
            continue
        if inside:
            out.append(line)
    return out


def parse_reservations(readme: str) -> dict[int, str]:
    reserved: dict[int, str] = {}
    for line in numbering_section(readme):
        m = TABLE_ROW.match(line.strip())
        if m and m.group("status").strip().lower().startswith("reserved"):
            reserved[int(m.group("num"))] = m.group("what").strip()
    for line in readme.splitlines():
        m = LEGACY_RESERVED.match(line.strip())
        if m:
            for item in LEGACY_ITEM.finditer(m.group("rest")):
                reserved.setdefault(int(item.group("num")), item.group("what").strip(" .,;"))
    return reserved


def parse_next_free(readme: str) -> list[int] | None:
    for line in readme.splitlines():
        m = NEXT_FREE.match(line.strip())
        if m:
            return [int(n) for n in NUMBER_TOKEN.findall(m.group("rest"))]
    return None


def compute_next_free(used: set[int], reserved: set[int]) -> list[int]:
    taken = used | reserved
    if not taken:
        return [1]
    top = max(taken)
    return [n for n in range(1, top) if n not in taken] + [top + 1]


def header_of(text: str) -> str:
    out = []
    for line in text.splitlines():
        if line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out)


def load_dir(adr_dir: Path) -> AdrSet:
    files = sorted(p.name for p in adr_dir.glob("*.md") if ADR_FILE.match(p.name))
    readme_path = adr_dir / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    headers = {name: header_of((adr_dir / name).read_text(encoding="utf-8")) for name in files}
    return AdrSet(files=files, readme=readme, headers=headers)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def load_git(root: Path, ref: str, adr_rel: str) -> AdrSet:
    listing = _git(root, "ls-tree", "--name-only", f"{ref}:{adr_rel}")
    files = sorted(n for n in listing.splitlines() if ADR_FILE.match(n))
    try:
        readme = _git(root, "show", f"{ref}:{adr_rel}/README.md")
    except subprocess.CalledProcessError:
        readme = ""
    return AdrSet(files=files, readme=readme)


def fmt(num: int, suffix: str = "") -> str:
    return f"{num:04d}{suffix}"


def check_static(head: AdrSet) -> list[str]:
    errors: list[str] = []
    seen: dict[tuple[int, str], str] = {}
    for name, num, suffix in head.parsed:
        key = (num, suffix)
        if key in seen:
            errors.append(f"S1 {name}: number {fmt(num, suffix)} is already used by {seen[key]}")
        else:
            seen[key] = name
    bases = head.base_numbers()
    for name, num, suffix in head.parsed:
        if suffix and num not in bases:
            errors.append(f"S2 {name}: amendment of ADR {fmt(num)}, but no {fmt(num)}-*.md exists")
    reserved = head.reservations()
    for name, num, suffix in head.parsed:
        if num in reserved:
            errors.append(f"S3 {name}: {fmt(num)} is reserved for '{reserved[num]}'. If this is that ADR, delete the "
                          "reservation row in docs/adr/README.md in the same PR; otherwise take a next-free number")
    for num, what in sorted(reserved.items()):
        if not ISSUE.search(what):
            errors.append(f"S4 README.md: reservation {fmt(num)} ('{what}') names no Linear issue (AA-n)")
    expected = compute_next_free(head.used_numbers(), set(reserved))
    stated = head.next_free_line()
    if stated is None:
        errors.append("S5 README.md: no 'Next free root numbers:' line in the Numbering section; expected "
                      + ", ".join(fmt(n) for n in expected))
    elif stated != expected:
        errors.append("S5 README.md: 'Next free root numbers' says " + ", ".join(fmt(n) for n in stated)
                      + "; the files and reservations give " + ", ".join(fmt(n) for n in expected))
    return errors


def check_pr(base: AdrSet, head: AdrSet) -> list[str]:
    errors: list[str] = []
    base_names = set(base.files)
    head_names = set(head.files)
    base_reserved = base.reservations()
    head_reserved = head.reservations()
    base_next = compute_next_free(base.used_numbers(), set(base_reserved))
    base_by_key: dict[tuple[int, str], list[str]] = {}
    for name, num, suffix in base.parsed:
        base_by_key.setdefault((num, suffix), []).append(name)
    for name, num, suffix in head.parsed:
        if name in base_names:
            continue
        key = (num, suffix)
        still_there = [n for n in base_by_key.get(key, []) if n in head_names]
        if still_there:
            errors.append(f"D1 {name}: {fmt(num, suffix)} is already used on the base branch by {still_there[0]}")
            continue
        if key in base_by_key:
            continue  # rename of an existing ADR (the base file with this number is gone here)
        if num in base_reserved:
            issues = set(ISSUE.findall(base_reserved[num]))
            cited = set(ISSUE.findall(head.headers.get(name, "")))
            if not issues & cited:
                errors.append(f"D2 {name}: {fmt(num)} is reserved on the base branch for '{base_reserved[num]}'; only "
                              "an ADR whose header cites " + ", ".join(sorted(issues) or ["that issue"])
                              + " may use it")
            elif num in head_reserved:
                errors.append(f"D2 {name}: uses reserved {fmt(num)}; delete its reservation row in the same PR")
            continue
        if not suffix:
            if num not in base_next:
                errors.append(f"D3 {name}: {fmt(num)} is not a next-free number of the base branch (free: "
                              + ", ".join(fmt(n) for n in base_next) + ")")
        else:
            letters = base.letters(num)
            expected = chr(ord(letters[-1]) + 1) if letters else "a"
            if num not in base.base_numbers() and num not in head.base_numbers():
                continue  # S2 reports it
            if suffix != expected:
                errors.append(f"D4 {name}: the next amendment of ADR {fmt(num)} is {fmt(num, expected)}, "
                              f"not {fmt(num, suffix)}")
    return errors


def check_propose(head: AdrSet, number: str) -> list[str]:
    m = re.fullmatch(r"(\d{4})([a-z]?)", number)
    if not m:
        return [f"--propose {number}: expected NNNN or NNNNx"]
    num, suffix = int(m.group(1)), m.group(2)
    reserved = head.reservations()
    if num in reserved:
        return [f"{fmt(num)} is reserved for '{reserved[num]}'"]
    if suffix:
        if num not in head.base_numbers():
            return [f"ADR {fmt(num)} does not exist, so {number} cannot amend it"]
        letters = head.letters(num)
        expected = chr(ord(letters[-1]) + 1) if letters else "a"
        return [] if suffix == expected else [f"the next amendment of ADR {fmt(num)} is {fmt(num, expected)}"]
    if num in head.used_numbers():
        return [f"{fmt(num)} is already used"]
    free = compute_next_free(head.used_numbers(), set(reserved))
    if num not in free:
        return [f"{fmt(num)} is not next free (free: " + ", ".join(fmt(n) for n in free) + ")"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("adr_dir", nargs="?", default="docs/adr")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--base", help="git ref of the base branch (PR rules D1-D4)")
    parser.add_argument("--propose", help="check whether this number (NNNN or NNNNx) may be used now")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    head = load_dir(root / args.adr_dir)
    if args.propose:
        problems = check_propose(head, args.propose)
        print(f"adr-numbers: {args.propose} " + ("is free" if not problems else "is NOT free: " + "; ".join(problems)))
        return 1 if problems else 0
    errors = check_static(head)
    if args.base:
        errors += check_pr(load_git(root, args.base, args.adr_dir), head)
    for e in errors:
        print(f"::error title=ADR numbers::{e}")
    print(f"adr-numbers: {len(head.parsed)} ADR files, {len(head.reservations())} reserved, next free "
          + ", ".join(fmt(n) for n in compute_next_free(head.used_numbers(), set(head.reservations())))
          + f"; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
