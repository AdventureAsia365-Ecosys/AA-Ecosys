#!/usr/bin/env python3
"""Secrets register v2: the rotation block of each row, its parser and its checks (AA-1183 part 1).

The register is docs/security/secrets-register.yaml (names and metadata only, never a value). Version 2 gives every
row a `rotation` block that a reader or the weekly rotation check (AA-1183 part 2) can parse:

    rotation:
      class: scheduled            # scheduled | auto | on-incident | identifier | retired
      interval_days: 180          # scheduled: required; auto: optional (e.g. KMS 365)
      owner_role: tech-lead       # tech-lead | business-owner | aws | registrar | tenant
      method: script              # script | manual | terraform | vendor-console | aws | app | registrar
      last_rotated: "2026-11-27"  # YYYY-MM-DD or unknown (hand-written: AWS dates move on tag or host-only edits)
      next_due: "2027-05-26"      # YYYY-MM-DD or unknown; never later than last_rotated + interval_days
      expires: "2027-01-21"       # optional: the day it stops working (certificate, domain, vendor token)
      events: [key-ceremony, suspected-leak]   # optional: also rotate on these events
      copy_of: "secretsmanager:acc2 aa-cis/dev/admin-secret"   # a copy row: "<store> <name>" of its primary
      how: "free text: the runbook, script or console step"

Classes:
  scheduled    rotated by a person on a fixed interval (90, 180, 365 or 730 days); last_rotated and next_due
               are required (unknown allowed, which the weekly check reports as a finding).
  auto         renewed or rotated by AWS or the registrar (KMS, ACM, RDS server certificate, domains on
               auto-renew); nothing to do unless the renewal does not happen (watch `expires`).
  on-incident  rotated only on an event (suspected leak, abuse, a person leaving): LLM vendor keys (tech lead
               decision S295, with a vendor-side spend limit), public tokens, tenant credentials, vendor console
               logins. last_rotated is required (unknown allowed, not a finding).
  identifier   not a credential (a role ARN, a bucket, a region, an account ID kept out of a public repo).
  retired      the row's status is deleted, removed, orphan-delete or pending-removal; next_due is then the date
               by which the credential must be revoked or deleted, when it still exists.

A copy row (`copy_of`) has the class of its primary and its own last_rotated (the day this copy was last set); its
interval and next_due come from the primary, so they are not written on the copy.

Commands (PyYAML; offline, reads the repo files only):
  python3 tools/security/secrets_register.py validate             exit 1 on any error (one per line)
  python3 tools/security/secrets_register.py schedule [--as-of D] the live rows by next due date (TSV)
  python3 tools/security/secrets_register.py md --check | --write the Markdown view: the rotation schedule block, and
                                                                  the Rotation and Status cells of every register
                                                                  table row; one table row per YAML row, both ways
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "docs/security/secrets-register.yaml"
REGISTER_MD = REPO_ROOT / "docs/security/secrets-register.md"

VERSION = 2
CLASSES = ("scheduled", "auto", "on-incident", "identifier", "retired")
OWNER_ROLES = ("tech-lead", "business-owner", "aws", "registrar", "tenant")
METHODS = ("script", "manual", "terraform", "vendor-console", "aws", "app", "registrar")
EVENTS = ("key-ceremony", "go-live", "suspected-leak", "staff-change", "after-use", "offboarding", "abuse")
STATUSES_GONE = ("deleted", "removed", "orphan-delete", "pending-removal")
STATUSES = ("keep", "open-item", "pending-x1", "planned") + STATUSES_GONE
UNKNOWN = "unknown"
KEYS = ("class", "interval_days", "owner_role", "method", "last_rotated", "next_due", "expires", "events",
        "copy_of", "how")

# The Markdown view (secrets-register.md): one generated block, and the register tables under "## Register".
MD_BEGIN = "<!-- rotation-schedule:begin (python3 tools/security/secrets_register.py md --write) -->"
MD_END = "<!-- rotation-schedule:end -->"
MD_REGISTER_HEADING = "## Register"
MD_DEFAULT_STORE = "secretsmanager:acc2"   # the Secrets Manager table has no Store column


class RegisterError(Exception):
    """The register file cannot be read at all."""


@dataclass(frozen=True)
class Rotation:
    cls: str
    interval_days: Optional[int] = None
    owner_role: Optional[str] = None
    method: Optional[str] = None
    last_rotated: Optional[str] = None    # "YYYY-MM-DD" | "unknown" | None (not written)
    next_due: Optional[str] = None        # "YYYY-MM-DD" | "unknown" | None
    expires: Optional[str] = None
    events: tuple[str, ...] = ()
    copy_of: Optional[str] = None
    how: Optional[str] = None


@dataclass(frozen=True)
class Entry:
    name: str
    store: str
    status: str
    rotation: Optional[Rotation]
    raw_rotation: object = None

    @property
    def key(self) -> str:
        return f"{self.store} {self.name}"


@dataclass
class Register:
    version: object
    updated: object
    entries: list[Entry] = field(default_factory=list)

    def by_key(self) -> dict[str, Entry]:
        return {e.key: e for e in self.entries}


def _text(value) -> Optional[str]:
    """YAML gives an unquoted date as datetime.date; the register compares ISO strings."""
    if value is None:
        return None
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value)


def _date(value: Optional[str]) -> Optional[dt.date]:
    if value is None or value == UNKNOWN:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def parse_rotation(raw) -> Optional[Rotation]:
    if not isinstance(raw, dict):
        return None
    interval = raw.get("interval_days")
    events = raw.get("events") or ()
    return Rotation(
        cls=str(raw.get("class", "")),
        interval_days=interval if isinstance(interval, int) and not isinstance(interval, bool) else None,
        owner_role=_text(raw.get("owner_role")),
        method=_text(raw.get("method")),
        last_rotated=_text(raw.get("last_rotated")),
        next_due=_text(raw.get("next_due")),
        expires=_text(raw.get("expires")),
        events=tuple(str(e) for e in events) if isinstance(events, (list, tuple)) else ("<not a list>",),
        copy_of=_text(raw.get("copy_of")),
        how=_text(raw.get("how")),
    )


def load(path: Path = REGISTER) -> Register:
    try:
        import yaml  # PyYAML (tools/docs/requirements.txt)
    except ImportError:  # pragma: no cover - CI installs it
        raise RegisterError("PyYAML is required (pip install -r tools/docs/requirements.txt)") from None
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RegisterError(f"cannot read {path}: {type(exc).__name__}") from None
    if not isinstance(doc, dict) or not isinstance(doc.get("secrets"), list):
        raise RegisterError("the register has no 'secrets' list")
    reg = Register(version=doc.get("version"), updated=_text(doc.get("updated")))
    for i, row in enumerate(doc["secrets"]):
        if not isinstance(row, dict):
            raise RegisterError(f"row {i} is not a mapping")
        raw = row.get("rotation")
        reg.entries.append(Entry(name=str(row.get("name", "")), store=str(row.get("store", "")),
                                 status=str(row.get("status", "")), rotation=parse_rotation(raw), raw_rotation=raw))
    return reg


def _check_date(where: str, label: str, value: Optional[str], errors: list[str], allow_unknown: bool) -> None:
    if value is None:
        return
    if value == UNKNOWN:
        if not allow_unknown:
            errors.append(f"{where}: {label} cannot be unknown")
        return
    if _date(value) is None:
        errors.append(f"{where}: {label} {value!r} is not YYYY-MM-DD")


def validate(reg: Register) -> list[str]:
    """Every problem in the register's rotation data, one line each (empty list = valid)."""
    errors: list[str] = []
    if reg.version != VERSION:
        errors.append(f"register version is {reg.version!r}, expected {VERSION}")
    keys = reg.by_key()
    seen: set[str] = set()
    for i, e in enumerate(reg.entries):
        where = f"row {i} ({e.key})"
        if not e.name or not e.store:
            errors.append(f"row {i}: needs name and store")
        if e.key in seen:
            errors.append(f"{where}: duplicate store and name")
        seen.add(e.key)
        if e.status not in STATUSES:
            errors.append(f"{where}: unknown status {e.status!r}")
        r = e.rotation
        if r is None:
            errors.append(f"{where}: rotation must be a mapping with a class (register v2)")
            continue
        unknown_keys = sorted(set(e.raw_rotation) - set(KEYS))
        if unknown_keys:
            errors.append(f"{where}: unknown rotation keys {unknown_keys}")
        if r.cls not in CLASSES:
            errors.append(f"{where}: unknown rotation class {r.cls!r}")
            continue
        gone = e.status in STATUSES_GONE
        if gone and r.cls != "retired":
            errors.append(f"{where}: status {e.status} needs class retired")
        if r.cls == "retired" and not gone:
            errors.append(f"{where}: class retired needs a deleted/removed/orphan-delete/pending-removal status")
        if r.owner_role is not None and r.owner_role not in OWNER_ROLES:
            errors.append(f"{where}: unknown owner_role {r.owner_role!r}")
        if r.method is not None and r.method not in METHODS:
            errors.append(f"{where}: unknown method {r.method!r}")
        for ev in r.events:
            if ev not in EVENTS:
                errors.append(f"{where}: unknown event {ev!r}")
        if "interval_days" in e.raw_rotation and (r.interval_days is None or r.interval_days <= 0):
            errors.append(f"{where}: interval_days must be a positive integer")
        _check_date(where, "last_rotated", r.last_rotated, errors, allow_unknown=True)
        _check_date(where, "next_due", r.next_due, errors, allow_unknown=True)
        _check_date(where, "expires", r.expires, errors, allow_unknown=False)

        if r.copy_of is not None:
            _validate_copy(where, e, r, keys, errors)
            continue
        if r.cls in ("identifier", "retired"):
            for k in ("interval_days", "last_rotated", "owner_role", "method"):
                if r.cls == "identifier" and k in e.raw_rotation:
                    errors.append(f"{where}: an identifier has no {k}")
            if r.cls == "identifier" and r.next_due is not None:
                errors.append(f"{where}: an identifier has no next_due")
            continue
        if r.owner_role is None:
            errors.append(f"{where}: owner_role is required for class {r.cls}")
        if r.cls == "scheduled":
            if r.interval_days is None:
                errors.append(f"{where}: scheduled needs interval_days")
            if r.method is None:
                errors.append(f"{where}: scheduled needs method")
            if r.last_rotated is None:
                errors.append(f"{where}: scheduled needs last_rotated (a date or unknown)")
            if r.next_due is None:
                errors.append(f"{where}: scheduled needs next_due (a date or unknown)")
            last, due = _date(r.last_rotated), _date(r.next_due)
            if last and due and r.interval_days:
                if due > last + dt.timedelta(days=r.interval_days):
                    errors.append(f"{where}: next_due {r.next_due} is later than last_rotated + "
                                  f"{r.interval_days} days ({(last + dt.timedelta(days=r.interval_days))})")
                if due < last:
                    errors.append(f"{where}: next_due {r.next_due} is before last_rotated {r.last_rotated}")
        elif r.cls == "on-incident":
            if r.last_rotated is None:
                errors.append(f"{where}: on-incident needs last_rotated (a date or unknown)")
            if r.interval_days is not None or r.next_due is not None:
                errors.append(f"{where}: on-incident has no interval_days or next_due")
        elif r.cls == "auto" and r.next_due == UNKNOWN:
            errors.append(f"{where}: auto next_due cannot be unknown (leave it out)")
    return errors


def _validate_copy(where: str, e: Entry, r: Rotation, keys: dict[str, Entry], errors: list[str]) -> None:
    primary = keys.get(r.copy_of)
    if primary is None:
        errors.append(f"{where}: copy_of {r.copy_of!r} names no register row (\"<store> <name>\")")
        return
    if primary.key == e.key:
        errors.append(f"{where}: a row cannot be a copy of itself")
        return
    pr = primary.rotation
    if pr is None:
        return
    if pr.copy_of is not None:
        errors.append(f"{where}: copy_of {r.copy_of!r} is itself a copy; point at the primary")
    if r.cls != pr.cls and r.cls != "retired":
        errors.append(f"{where}: a copy has the class of its primary ({pr.cls}), not {r.cls}")
    for k in ("interval_days", "next_due"):
        if k in e.raw_rotation:
            errors.append(f"{where}: a copy takes {k} from its primary; remove it")
    if r.cls not in ("identifier", "retired") and r.last_rotated is None:
        errors.append(f"{where}: a copy needs its own last_rotated (a date or unknown)")


def effective(entry: Entry, reg: Register) -> Rotation:
    """The rotation of a row with a copy's interval and next due date taken from its primary."""
    r = entry.rotation
    assert r is not None
    if r.copy_of is None:
        return r
    primary = reg.by_key().get(r.copy_of)
    if primary is None or primary.rotation is None:
        return r
    p = primary.rotation
    return Rotation(cls=r.cls, interval_days=p.interval_days, owner_role=r.owner_role or p.owner_role,
                    method=r.method or p.method, last_rotated=r.last_rotated, next_due=p.next_due,
                    expires=r.expires or p.expires, events=r.events or p.events, copy_of=r.copy_of, how=r.how)


def copies_of(entry: Entry, reg: Register) -> list[Entry]:
    return [e for e in reg.entries if e.rotation and e.rotation.copy_of == entry.key]


def live(entry: Entry) -> bool:
    """A row the schedule shows: not an identifier, and not gone unless it still waits for revocation."""
    r = entry.rotation
    if r is None or r.cls == "identifier":
        return False
    if r.cls == "retired":
        return entry.status in ("orphan-delete", "pending-removal") and r.next_due is not None
    return True


def _sort_key(entry: Entry, reg: Register) -> tuple:
    r = effective(entry, reg)
    due = _date(r.next_due) or _date(r.expires)
    if due is not None:
        return (0, due.isoformat(), entry.store, entry.name)
    if (r.next_due == UNKNOWN) or (r.cls == "scheduled" and r.last_rotated == UNKNOWN):
        return (1, "", entry.store, entry.name)
    return (2, "", entry.store, entry.name)


def schedule(reg: Register) -> list[Entry]:
    return sorted((e for e in reg.entries if live(e)), key=lambda e: _sort_key(e, reg))


def label(entry: Entry, reg: Register) -> str:
    """The short Rotation cell of a register table row in the Markdown view."""
    r = entry.rotation
    if r is None:
        return "—"
    if r.copy_of is not None and r.cls not in ("retired", "identifier"):
        return f"copy of `{r.copy_of.split(' ', 1)[1]}`"
    if r.cls == "scheduled":
        return f"scheduled {r.interval_days} d"
    if r.cls == "auto":
        return "auto (AWS)" if r.owner_role == "aws" else "auto"
    return {"on-incident": "on incident", "identifier": "identifier", "retired": "retired"}[r.cls]


def _cell(text: Optional[str]) -> str:
    return (text or "—").replace("|", "\\|")


def render_schedule(reg: Register) -> str:
    rows = schedule(reg)
    counts = {c: sum(1 for e in reg.entries if e.rotation and e.rotation.cls == c) for c in CLASSES}
    lines = [
        MD_BEGIN,
        "",
        f"Rows by class: scheduled {counts['scheduled']}, auto {counts['auto']}, on incident "
        f"{counts['on-incident']}, identifier {counts['identifier']}, retired {counts['retired']}. "
        "The table lists every row that is not an identifier or gone, soonest first; a copy row takes the "
        "interval and next due date of its primary.",
        "",
        "| Name | Store | Class | Every | Owner role | Last rotated | Next due | Expires | Also on | Method |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in rows:
        r = effective(e, reg)
        cls = label(e, reg) if r.copy_of else r.cls.replace("-", " ")
        every = f"{r.interval_days} d" if r.interval_days else "—"
        lines.append(
            f"| `{_cell(e.name)}` | `{_cell(e.store)}` | {_cell(cls)} | {every} | {_cell(r.owner_role)} | "
            f"{_cell(r.last_rotated)} | {_cell(r.next_due)} | {_cell(r.expires)} | {_cell(', '.join(r.events))} | "
            f"{_cell(r.method)} |")
    lines += ["", MD_END]
    return "\n".join(lines)


_ROW = re.compile(r"^\|(.+)\|\s*$")


def _split(line: str) -> list[str]:
    m = _ROW.match(line)
    if not m:
        return []
    return [c.strip() for c in re.split(r"(?<!\\)\|", m.group(1))]


def _name(cell: str) -> str:
    return cell.replace("`", "").strip()


def md_rows(md: str) -> list[tuple[int, str, str, int, Optional[int]]]:
    """(line index, store, name, Rotation column, Status column or None) of each table row under '## Register'."""
    out: list[tuple[int, str, str, int, Optional[int]]] = []
    lines = md.splitlines()
    in_register = False
    header: list[str] = []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            in_register = line.strip() == MD_REGISTER_HEADING
            header = []
            continue
        if not in_register:
            continue
        cells = _split(line)
        if not cells:
            header = []
            continue
        if not header:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if "Rotation" not in header:
            continue
        store = _name(cells[header.index("Store")]) if "Store" in header else MD_DEFAULT_STORE
        status_col = header.index("Status") if "Status" in header else None
        out.append((i, store, _name(cells[0]), header.index("Rotation"), status_col))
    return out


def render_md(md: str, reg: Register) -> tuple[str, list[str]]:
    """The Markdown with the schedule block and every Rotation cell rendered; problems that need a hand edit."""
    problems: list[str] = []
    if md.count(MD_BEGIN) != 1 or md.count(MD_END) != 1 or md.index(MD_BEGIN) > md.index(MD_END):
        return md, ["the rotation schedule markers are missing or unbalanced"]
    head, rest = md.split(MD_BEGIN, 1)
    _, tail = rest.split(MD_END, 1)
    md = head + render_schedule(reg) + tail
    keys = reg.by_key()
    lines = md.splitlines()
    found: set[str] = set()
    for i, store, name, col, status_col in md_rows(md):
        key = f"{store} {name}"
        entry = keys.get(key)
        if entry is None:
            problems.append(f"secrets-register.md line {i + 1}: {key} has no row in the YAML")
            continue
        if key in found:
            problems.append(f"secrets-register.md line {i + 1}: a second table row for {key}")
        found.add(key)
        cells = _split(lines[i])
        cells[col] = label(entry, reg)
        if status_col is not None:
            cells[status_col] = f"**{entry.status}**"
        lines[i] = "| " + " | ".join(cells) + " |"
    for key in keys:
        if key not in found:
            problems.append(f"secrets-register.md: no table row for {key}")
    return "\n".join(lines) + ("\n" if md.endswith("\n") else ""), problems


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--register", type=Path, default=REGISTER)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sp = sub.add_parser("schedule")
    sp.add_argument("--as-of", type=dt.date.fromisoformat, default=None)
    mp = sub.add_parser("md")
    mp.add_argument("--md", type=Path, default=REGISTER_MD)
    g = mp.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    try:
        reg = load(args.register)
    except RegisterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = validate(reg)
    if args.cmd == "validate" or errors:
        for err in errors:
            print(err)
        print(f"{len(reg.entries)} rows, {len(errors)} errors")
        return 1 if errors else 0
    if args.cmd == "schedule":
        as_of = args.as_of
        for e in schedule(reg):
            r = effective(e, reg)
            due = _date(r.next_due)
            days = (due - as_of).days if (due and as_of) else ""
            print("\t".join([e.store, e.name, r.cls, str(r.interval_days or ""), r.last_rotated or "",
                             r.next_due or "", r.expires or "", str(days)]))
        return 0
    md = args.md.read_text(encoding="utf-8")
    new, problems = render_md(md, reg)
    for p in problems:
        print(p)
    if args.write:
        if new != md:
            args.md.write_text(new, encoding="utf-8")
        return 1 if problems else 0
    if new != md:
        print("secrets-register.md is out of date: run python3 tools/security/secrets_register.py md --write")
        return 1
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
