#!/usr/bin/env python3
"""Check the AA Academy course files under docs/learn/ (AA-1104, GUIDE-13; format: docs/learn/README.md).

A course never copies its sources. A lesson names each source section by reference and pins a hash of that section,
so a source change shows up as a failed check instead of a lesson that silently drifts.

What it checks (errors fail the docs lint):

  * shape: docs/learn/paths/*.yaml, docs/learn/modules/<ID>-<slug>/module.yaml, quiz.yaml and
    docs/learn/allowlist.yaml validate against docs/learn/schema/*.schema.json;
  * identity: module, lesson, quiz item and path IDs are unique; a module folder starts with its ID; a lesson ID is
    <module>-NN; every lesson file exists, starts with an H1 equal to its title, and a translation <name>.vi.md
    (optional) has an H1 too;
  * references: every lesson source and quiz source resolves to a section that exists:
      doc:<catalog id>[#anchor]   a published catalog page (bare <catalog id> means the same)
      adr:<NNNN[a]>[#anchor]      a root ADR
      skill:<name>#anchor         skill/<name>/SKILL.md, only through the allowlist
      steering:<name>#anchor      .kiro/steering/<name>.md, only through the allowlist
      context:<repo>#anchor       <repo>/CONTEXT.md of an app or Infra repo, only through the allowlist
    An anchor is the GitHub heading slug. A page the docs reader serves to the owner only (SEC-*, ARCH-02/03/04) or does
    not publish at all (journals, security, templates) can never be cited;
  * pins: every source carries `sha`, the first 16 hex characters of the SHA-256 of the cited section (heading line to
    the next heading of the same or a higher level, trailing spaces and blank edge lines dropped; a reference with no
    anchor hashes the whole page body). A root source whose section changed fails until the module owner reviews the
    lesson and re-pins (`--pin`);
  * tiers (decision D13): a `partner` module cites only the catalog pages listed in the allowlist's `partner_pages`
    and allowlist sections of tier `partner`; a path holds modules of its own tier; skill, steering and CONTEXT.md
    sections are cited only when the allowlist names them (default deny);
  * quiz: every item cites one of its module's lesson sources with an anchor; answers index existing choices;
  * prerequisites name a module or a planned module of a path, and form no cycle;
  * public safety: no account or resource ID in lesson text, quiz text or titles (the docs reader guard).

External sources (context:...) live in other repos. They are checked where that repo's CONTEXT.md is present
(--ext-root DIR holding <repo>/CONTEXT.md, or the workspace layout apps/<repo>, infra/<repo>); a missing file is a
notice, and a missing anchor or a changed hash there is a warning (--strict-external makes them errors). The Docs
sync workflow checks them out and marks a stale lesson in the learn manifest.

Usage:
  python tools/docs/check_learn.py
  python tools/docs/check_learn.py --ext-root /path/to/workspace
  python tools/docs/check_learn.py --pin            # write the current hashes into module.yaml after a review
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from build_docs_reader import access_for, classify, guard_hits
from docslib import REPO_ROOT, Finding, emit, list_markdown, translation_lang

LEARN_DIR = "docs/learn"
SCHEMA_DIR = "docs/learn/schema"
ALLOWLIST = "docs/learn/allowlist.yaml"
SHA_LEN = 16
# Repos whose CONTEXT.md a `context:` reference may name, with their folder in the workspace layout.
EXTERNAL_REPOS = {
    "AA-CIS-App": "apps/AA-CIS-App",
    "AA-Booking": "apps/AA-Booking",
    "AA-TripPlanner-Web": "apps/AA-TripPlanner-Web",
    "AA-Partner": "apps/AA-Partner",
    "AA-CIS-Infra": "infra/AA-CIS-Infra",
}
ALLOWLIST_KINDS = ("skill", "steering", "context")
REF_RE = re.compile(r"^(?:(doc|adr|skill|steering|context):)?([A-Za-z0-9][A-Za-z0-9._-]*)(?:#([^\s#]+))?$")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
H1 = re.compile(r"^#\s+(.+?)\s*$")
# One `key: value` line of a block-style list item: `- key: value` opens the item, `  key: value` continues it.
ITEM_KEY = re.compile(r"^(\s*)(-\s+)?([A-Za-z_][A-Za-z0-9_]*):\s*(.*?)\s*$")


class _Loader(yaml.SafeLoader):
    """safe_load without the timestamp rule: `last_reviewed: 2026-11-14` stays the string the schema expects, like
    the unquoted dates in catalog front-matter."""


_Loader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _yaml_load(text: str):
    return yaml.load(text, Loader=_Loader)  # noqa: S506 - a SafeLoader subclass


# ── references and sections ─────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Ref:
    raw: str
    kind: str
    name: str
    anchor: str | None

    @property
    def external(self) -> bool:
        return self.kind == "context"

    @property
    def key(self) -> str:
        """The object key of the cited section inside the learn bundle (letters, digits, '.', '_', '-')."""
        anchor = self.anchor or "_page"
        return f"sections/{self.kind}/{_safe(self.name)}/{_safe(anchor)}.md"


def _safe(part: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", part)


def parse_ref(raw: str) -> Ref | None:
    m = REF_RE.match(str(raw).strip())
    if not m:
        return None
    return Ref(str(raw).strip(), m.group(1) or "doc", m.group(2), m.group(3))


def github_slug(text: str) -> str:
    """The anchor GitHub gives a heading: inline markup dropped, lower case, punctuation removed, spaces to '-'."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)   # links and images keep their text
    text = re.sub(r"<[^>]+>", "", text)                       # inline HTML
    text = text.replace("`", "").strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def headings(body: str) -> list[tuple[int, int, str]]:
    """(line index, level, unique slug) of every ATX heading outside fenced code, slugs de-duplicated like GitHub."""
    found: list[tuple[int, int, str]] = []
    seen: dict[str, int] = {}
    fence: str | None = None
    for i, line in enumerate(body.splitlines()):
        m = FENCE.match(line)
        if m:
            fence = m.group(1) if fence is None else (None if m.group(1) == fence else fence)
            continue
        if fence is not None:
            continue
        h = HEADING.match(line)
        if not h:
            continue
        slug = github_slug(h.group(2))
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        found.append((i, len(h.group(1)), slug if n == 0 else f"{slug}-{n}"))
    return found


def section(body: str, anchor: str | None) -> str | None:
    """The text of the section `anchor` names (None when no heading has that slug); the whole body without an anchor."""
    if not anchor:
        return body
    lines = body.splitlines()
    hs = headings(body)
    for n, (start, level, slug) in enumerate(hs):
        if slug != anchor:
            continue
        end = next((i for i, lvl, _ in hs[n + 1:] if lvl <= level), len(lines))
        return "\n".join(lines[start:end])
    return None


def section_sha(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:SHA_LEN]


def strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:])
    return text


@dataclass
class Resolved:
    ref: Ref
    path: str | None = None          # repo-relative path (external: "<repo>/CONTEXT.md")
    access: str = "staff"
    text: str | None = None          # the cited section
    problem: str | None = None       # why it does not resolve
    unavailable: bool = False        # external file not present here (not an error)

    @property
    def sha(self) -> str | None:
        return section_sha(self.text) if self.text is not None else None


class Sources:
    """Resolves references against this checkout (and external CONTEXT.md files where present)."""

    def __init__(self, root: Path = REPO_ROOT, ext_roots: list[Path] | None = None):
        self.root = root
        self.ext_roots = list(ext_roots or []) + [root / "_ext", root]
        self._docs: dict[str, tuple[str, str, str]] | None = None   # catalog id -> (path, access, body)

    def docs_index(self) -> dict[str, tuple[str, str, str]]:
        if self._docs is None:
            self._docs = {}
            for relpath in list_markdown(["docs"], self.root):
                if translation_lang(relpath) is not None:
                    continue
                try:
                    text = (self.root / relpath).read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                found = classify(relpath, text)
                if found is None:
                    continue
                meta, body = found
                page_id = str(meta["id"])
                self._docs.setdefault(page_id, (relpath, access_for(page_id), body))
        return self._docs

    def _external_file(self, repo: str) -> Path | None:
        for base in self.ext_roots:
            for candidate in (base / repo / "CONTEXT.md", base / EXTERNAL_REPOS[repo] / "CONTEXT.md"):
                if candidate.is_file():
                    return candidate
        return None

    def resolve(self, ref: Ref) -> Resolved:
        r = Resolved(ref)
        if ref.kind == "doc":
            hit = self.docs_index().get(ref.name)
            if hit is None:
                r.problem = f"no published catalog page has id {ref.name}"
                return r
            r.path, r.access, body = hit
        elif ref.kind == "adr":
            files = sorted((self.root / "docs/adr").glob(f"{ref.name}-*.md")) if re.fullmatch(r"\d{4}[a-z]?", ref.name) else []
            if not files:
                r.problem = f"no root ADR docs/adr/{ref.name}-*.md"
                return r
            r.path = files[0].relative_to(self.root).as_posix()
            body = files[0].read_text(encoding="utf-8")
        elif ref.kind == "skill":
            r.path = f"skill/{ref.name}/SKILL.md"
            p = self.root / r.path
            if not p.is_file():
                r.problem = f"{r.path} does not exist"
                return r
            body = strip_front_matter(p.read_text(encoding="utf-8"))
        elif ref.kind == "steering":
            r.path = f".kiro/steering/{ref.name}.md"
            p = self.root / r.path
            if not p.is_file():
                r.problem = f"{r.path} does not exist"
                return r
            body = strip_front_matter(p.read_text(encoding="utf-8"))
        else:   # context
            if ref.name not in EXTERNAL_REPOS:
                r.problem = f"unknown repo {ref.name} (one of {', '.join(EXTERNAL_REPOS)})"
                return r
            r.path = f"{ref.name}/CONTEXT.md"
            p = self._external_file(ref.name)
            if p is None:
                r.unavailable = True
                r.problem = f"{r.path} is not checked out here"
                return r
            body = strip_front_matter(p.read_text(encoding="utf-8"))
        r.text = section(body, ref.anchor)
        if r.text is None:
            r.problem = f"{r.path} has no heading with the anchor #{ref.anchor}"
        return r


# ── loading the course files ────────────────────────────────────────────────────────────────────────

@dataclass
class Course:
    paths: list[tuple[str, dict]] = field(default_factory=list)       # (relpath, data)
    modules: list[tuple[str, dict]] = field(default_factory=list)     # (module dir relpath, data)
    quizzes: dict[str, tuple[str, dict]] = field(default_factory=dict)  # module id -> (relpath, data)
    allowlist: dict = field(default_factory=dict)
    findings: list[tuple[str, Finding]] = field(default_factory=list)  # (level, finding)

    def error(self, path: str, msg: str, title: str = "Learn") -> None:
        self.findings.append(("error", Finding(path, 1, title, msg)))

    def warning(self, path: str, msg: str, title: str = "Learn") -> None:
        self.findings.append(("warning", Finding(path, 1, title, msg)))

    def notice(self, path: str, msg: str, title: str = "Learn") -> None:
        self.findings.append(("notice", Finding(path, 1, title, msg)))

    @property
    def errors(self) -> list[Finding]:
        return [f for level, f in self.findings if level == "error"]


def _schema(root: Path, name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads((root / SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8")))


def _load_yaml(course: Course, root: Path, relpath: str, validator: Draft202012Validator) -> dict | None:
    try:
        data = _yaml_load((root / relpath).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        course.error(relpath, f"cannot read: {exc}")
        return None
    if not isinstance(data, dict):
        course.error(relpath, "must be a YAML mapping")
        return None
    bad = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    for err in bad:
        where = ".".join(str(p) for p in err.path) or "(root)"
        course.error(relpath, f"{where}: {err.message}", "Learn schema")
    return None if bad else data


def load(root: Path = REPO_ROOT) -> Course:
    course = Course()
    base = root / LEARN_DIR
    if not base.is_dir():
        return course
    if (root / ALLOWLIST).is_file():
        course.allowlist = _load_yaml(course, root, ALLOWLIST, _schema(root, "allowlist")) or {}
    path_schema, module_schema, quiz_schema = (_schema(root, n) for n in ("path", "module", "quiz"))
    for p in sorted((base / "paths").glob("*.yaml")):
        rel = p.relative_to(root).as_posix()
        data = _load_yaml(course, root, rel, path_schema)
        if data is not None:
            course.paths.append((rel, data))
    for d in sorted(x for x in (base / "modules").glob("*") if x.is_dir()):
        rel = d.relative_to(root).as_posix()
        if not (d / "module.yaml").is_file():
            course.error(rel, "a module folder needs module.yaml")
            continue
        data = _load_yaml(course, root, f"{rel}/module.yaml", module_schema)
        if data is None:
            continue
        course.modules.append((rel, data))
        quiz = data.get("quiz")
        if quiz:
            qrel = f"{rel}/{quiz}"
            if not (root / qrel).is_file():
                course.error(f"{rel}/module.yaml", f"quiz file {quiz} does not exist")
            else:
                qdata = _load_yaml(course, root, qrel, quiz_schema)
                if qdata is not None:
                    course.quizzes[data["id"]] = (qrel, qdata)
    return course


# ── the checks ──────────────────────────────────────────────────────────────────────────────────────

def _allowed_sections(course: Course) -> dict[str, str]:
    """ref -> tier of every allowlist section."""
    return {str(s["ref"]): s["tier"] for s in course.allowlist.get("sections", [])}


def check(course: Course, root: Path, sources: Sources, strict_external: bool = False) -> dict[str, Resolved]:
    """Run every check, add findings to `course`, return the resolved sources by ref."""
    resolved: dict[str, Resolved] = {}

    def res(raw: str) -> Resolved | None:
        if raw not in resolved:
            ref = parse_ref(raw)
            if ref is None:
                return None
            resolved[raw] = sources.resolve(ref)
        return resolved[raw]

    def external_problem(where: str, msg: str) -> None:
        (course.error if strict_external else course.warning)(where, msg, "Learn external source")

    allowed = _allowed_sections(course)
    partner_pages = set(course.allowlist.get("partner_pages", []))
    _check_allowlist(course, sources, res, external_problem)

    module_ids: dict[str, str] = {}
    lesson_ids: dict[str, str] = {}
    for rel, m in course.modules:
        where = f"{rel}/module.yaml"
        mid = m["id"]
        if mid in module_ids:
            course.error(where, f"duplicate module id {mid} (also {module_ids[mid]})")
        module_ids[mid] = where
        if not Path(rel).name.startswith(f"{mid}-"):
            course.error(where, f"the folder name must start with the module id: {mid}-<slug>")
        for text in [m["title"], *m.get("objectives", [])]:
            for label in guard_hits(text):
                course.error(where, f"{label} in a title or objective")
        lesson_sources: set[str] = set()
        for n, lesson in enumerate(m["lessons"], 1):
            lid = lesson["id"]
            if lid in lesson_ids:
                course.error(where, f"duplicate lesson id {lid} (also {lesson_ids[lid]})")
            lesson_ids[lid] = where
            if not re.fullmatch(rf"{re.escape(mid)}-\d{{2}}", lid):
                course.error(where, f"lesson id {lid} must be {mid}-NN")
            _check_lesson_file(course, root, rel, lesson)
            for src in lesson["sources"]:
                raw = str(src["ref"])
                lesson_sources.add(raw)
                _check_source(course, where, m, lid, src, res(raw), allowed, partner_pages, external_problem)
        _check_quiz(course, m, lesson_sources)
    _check_prerequisites(course, module_ids)
    _check_paths(course, module_ids)
    return resolved


def _check_allowlist(course: Course, sources: Sources, res, external_problem) -> None:
    seen: set[str] = set()
    for s in course.allowlist.get("sections", []):
        raw = str(s["ref"])
        ref = parse_ref(raw)
        if ref is None or ref.kind not in ALLOWLIST_KINDS or not ref.anchor:
            course.error(ALLOWLIST, f"{raw}: an allowlist entry is skill:/steering:/context:<name>#<anchor>")
            continue
        if raw in seen:
            course.error(ALLOWLIST, f"{raw} is listed twice")
        seen.add(raw)
        r = res(raw)
        if r.unavailable:
            course.notice(ALLOWLIST, f"{raw}: {r.problem}; checked by the Docs sync build", "Learn external source")
        elif r.problem and ref.external:
            external_problem(ALLOWLIST, f"{raw}: {r.problem}")
        elif r.problem:
            course.error(ALLOWLIST, f"{raw}: {r.problem}")
        elif r.text is not None:
            for label in guard_hits(r.text):
                course.error(ALLOWLIST, f"{raw}: {label} in the section; it cannot be published")
    index = sources.docs_index()
    for page_id in course.allowlist.get("partner_pages", []):
        hit = index.get(page_id)
        if hit is None:
            course.error(ALLOWLIST, f"partner page {page_id} is not a published catalog page")
        elif hit[1] != "staff":
            course.error(ALLOWLIST, f"partner page {page_id} is owner only in the docs reader")


def _check_lesson_file(course: Course, root: Path, module_rel: str, lesson: dict) -> None:
    rel = f"{module_rel}/{lesson['file']}"
    p = root / rel
    if not p.is_file():
        course.error(f"{module_rel}/module.yaml", f"lesson file {lesson['file']} does not exist")
        return
    text = p.read_text(encoding="utf-8")
    if text.startswith("---"):
        course.error(rel, "a lesson file has no front-matter: its metadata lives in module.yaml")
    first = next((line for line in text.splitlines() if line.strip()), "")
    m = H1.match(first)
    if not m:
        course.error(rel, "a lesson starts with an H1")
    elif m.group(1).strip() != lesson["title"]:
        course.error(rel, f"the H1 {m.group(1).strip()!r} differs from the title in module.yaml {lesson['title']!r}")
    for label in guard_hits(text):
        course.error(rel, f"{label} in the lesson text")
    vi = p.with_name(p.name[:-3] + ".vi.md")
    if vi.is_file():
        vtext = vi.read_text(encoding="utf-8")
        if not H1.match(next((line for line in vtext.splitlines() if line.strip()), "")):
            course.error(vi.relative_to(root).as_posix(), "a lesson translation starts with an H1")
        for label in guard_hits(vtext):
            course.error(vi.relative_to(root).as_posix(), f"{label} in the lesson text")


def _check_source(course, where, module, lid, src, r, allowed, partner_pages, external_problem) -> None:
    raw = str(src["ref"])
    ref = parse_ref(raw)
    if ref is None or r is None:
        course.error(where, f"{lid}: {raw!r} is not a reference (doc:, adr:, skill:, steering:, context:)")
        return
    partner = module["tier"] == "partner"
    if ref.kind in ALLOWLIST_KINDS:
        if raw not in allowed:
            course.error(where, f"{lid}: {raw} is not in {ALLOWLIST} (skill, steering and CONTEXT.md sections are "
                                "published only through it)")
            return
        if partner and allowed[raw] != "partner":
            course.error(where, f"{lid}: {raw} is a staff section; a partner module cites partner sections only")
    elif partner and (ref.kind != "doc" or ref.name not in partner_pages):
        course.error(where, f"{lid}: {raw}: a partner module cites only the allowlist's partner_pages")
    if r.unavailable:
        course.notice(where, f"{lid}: {raw}: {r.problem}; checked by the Docs sync build", "Learn external source")
        return
    if r.problem:
        (external_problem if ref.external else lambda w, msg: course.error(w, msg))(where, f"{lid}: {raw}: {r.problem}")
        return
    if r.access != "staff":
        course.error(where, f"{lid}: {raw} is an owner-only page in the docs reader; a lesson cannot cite it")
    pinned = src.get("sha")
    if not pinned:
        course.error(where, f"{lid}: {raw} has no sha pin; run tools/docs/check_learn.py --pin after reading it")
    elif pinned != r.sha:
        msg = (f"{lid}: {raw} changed since the lesson was written (pinned {pinned}, now {r.sha}); review the lesson "
               "and its quiz items, then run tools/docs/check_learn.py --pin")
        (external_problem if ref.external else lambda w, m_: course.error(w, m_, "Learn source changed"))(where, msg)


def _check_quiz(course: Course, module: dict, lesson_sources: set[str]) -> None:
    mid = module["id"]
    hit = course.quizzes.get(mid)
    if hit is None:
        if module.get("quiz"):
            return   # already reported (missing or invalid file)
        course.error(f"{LEARN_DIR}/modules", f"module {mid} has no quiz; every module ends with one")
        return
    rel, quiz = hit
    if quiz["module"] != mid:
        course.error(rel, f"module: {quiz['module']} differs from the module id {mid}")
    seen: set[str] = set()
    for item in quiz["items"]:
        iid = item["id"]
        if iid in seen:
            course.error(rel, f"duplicate quiz item id {iid}")
        seen.add(iid)
        if not iid.startswith(f"{mid}-Q"):
            course.error(rel, f"quiz item id {iid} must start with {mid}-Q")
        src = str(item["source"])
        ref = parse_ref(src)
        if ref is None or not ref.anchor:
            course.error(rel, f"{iid}: source {src!r} needs an anchor (the section the item tests)")
        elif src not in lesson_sources:
            course.error(rel, f"{iid}: source {src} is not a source of one of the module's lessons")
        n = len(item["choices"])
        if any(a >= n for a in item["answer"]):
            course.error(rel, f"{iid}: an answer index is out of range (0 to {n - 1})")
        if item["kind"] == "single" and len(item["answer"]) != 1:
            course.error(rel, f"{iid}: a single-answer item has exactly one answer")
        for text in [item["prompt"], *item["choices"], item.get("explain", "")]:
            for label in guard_hits(text):
                course.error(rel, f"{iid}: {label} in the item text")
    if not 5 <= len(quiz["items"]) <= 10:
        course.warning(rel, f"{len(quiz['items'])} items; a module quiz has 5 to 10 retrieval items (GUIDE-13 §4.1)")


def _check_prerequisites(course: Course, module_ids: dict[str, str]) -> None:
    planned = {pid for _, p in course.paths for pid in p.get("planned", [])}
    graph = {m["id"]: list(m.get("prerequisites", [])) for _, m in course.modules}
    for rel, m in course.modules:
        for pre in m.get("prerequisites", []):
            if pre not in module_ids and pre not in planned:
                course.error(f"{rel}/module.yaml", f"prerequisite {pre} is neither a module nor planned in a path")
    state: dict[str, int] = {}

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 2:
            return
        if state.get(node) == 1:
            course.error(f"{LEARN_DIR}/modules", "prerequisite cycle: " + " -> ".join(trail + [node]))
            return
        state[node] = 1
        for nxt in graph.get(node, []):
            visit(nxt, trail + [node])
        state[node] = 2

    for node in graph:
        visit(node, [])


def _check_paths(course: Course, module_ids: dict[str, str]) -> None:
    tiers = {m["id"]: m["tier"] for _, m in course.modules}
    seen: dict[str, str] = {}
    for rel, p in course.paths:
        pid = p["id"]
        if pid in seen:
            course.error(rel, f"duplicate path id {pid} (also {seen[pid]})")
        seen[pid] = rel
        if Path(rel).stem != pid:
            course.error(rel, f"the file name must be {pid}.yaml")
        for entry in p["modules"]:
            mid = entry["id"]
            if mid not in module_ids:
                course.error(rel, f"module {mid} does not exist (a module not written yet goes under planned)")
            elif tiers[mid] != p["tier"]:
                course.error(rel, f"module {mid} is tier {tiers[mid]}; a {p['tier']} path holds {p['tier']} modules")
            if mid in p.get("planned", []):
                course.error(rel, f"module {mid} is both listed and planned")


# ── pinning ─────────────────────────────────────────────────────────────────────────────────────────

def _scalar(text: str) -> str | None:
    """The string a one-line YAML scalar loads to (quotes removed); None for anything else (flow maps, lists)."""
    try:
        value = _yaml_load(text) if text else None
    except yaml.YAMLError:
        return None
    return value if isinstance(value, str) else None


def _sha_text(sha: str) -> str:
    """The sha as YAML text, quoted when it is all digits: a bare 0000... loads as an int here and other YAML readers
    (1.2 rules) read any all-digit hash as a number."""
    return f'"{sha}"' if sha.isdigit() or _scalar(sha) != sha else sha


def _pin_lines(lines: list[str], wanted: dict[str, str]) -> tuple[list[str], set[str]]:
    """Set `sha` in every block-style list item that has a `ref` key found in `wanted` (ref -> sha), whatever the key
    order and quoting; return the new lines and the refs that were pinned."""
    out = list(lines)
    done: set[str] = set()
    i = 0
    while i < len(out):
        m = ITEM_KEY.match(out[i])
        if not (m and m.group(2)):
            i += 1
            continue
        key_indent = len(m.group(1)) + len(m.group(2))
        keys: dict[str, int] = {m.group(3): i}
        j = i + 1
        while j < len(out):
            if not out[j].strip() or out[j].lstrip().startswith("#"):
                j += 1
                continue
            c = ITEM_KEY.match(out[j])
            if not c or c.group(2) or len(c.group(1)) != key_indent:
                break
            keys[c.group(3)] = j
            j += 1
        if "ref" in keys:
            ref = _scalar(ITEM_KEY.match(out[keys["ref"]]).group(4))
            sha = wanted.get(ref) if ref is not None else None
            if sha is not None:
                done.add(ref)
                if "sha" in keys:
                    k = keys["sha"]
                    s = ITEM_KEY.match(out[k])
                    if _scalar(s.group(4)) != sha:
                        out[k] = f"{s.group(1)}{s.group(2) or ''}sha: {_sha_text(sha)}"
                else:
                    out.insert(keys["ref"] + 1, f"{' ' * key_indent}sha: {_sha_text(sha)}")
                    j += 1
        i = j
    return out, done


def pin(root: Path, course: Course, resolved: dict[str, Resolved]) -> tuple[int, list[tuple[str, str, str]]]:
    """Write the current hash of every resolvable source into its module.yaml.

    Returns the number of module files changed and the sources it could not rewrite (module.yaml, ref, sha), such as
    a flow-style `{ref: ..., sha: ...}` entry; the caller prints those so the owner can set them by hand.
    """
    changed = 0
    missed: list[tuple[str, str, str]] = []
    for rel, data in course.modules:
        wanted: dict[str, str] = {}
        for lesson in data["lessons"]:
            for src in lesson["sources"]:
                r = resolved.get(str(src["ref"]))
                if r is not None and r.sha is not None and src.get("sha") != r.sha:
                    wanted[str(src["ref"])] = r.sha
        if not wanted:
            continue
        path = root / rel / "module.yaml"
        text = path.read_text(encoding="utf-8")
        lines, done = _pin_lines(text.splitlines(), wanted)
        missed += [(f"{rel}/module.yaml", ref, sha) for ref, sha in wanted.items() if ref not in done]
        if done:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            changed += 1
    return changed, missed


def run(root: Path = REPO_ROOT, ext_roots: list[Path] | None = None, strict_external: bool = False
        ) -> tuple[Course, dict[str, Resolved]]:
    course = load(root)
    resolved = check(course, root, Sources(root, ext_roots), strict_external)
    return course, resolved


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--ext-root", type=Path, action="append", default=[],
                    help="folder holding <repo>/CONTEXT.md or the workspace layout (apps/<repo>, infra/<repo>)")
    ap.add_argument("--strict-external", action="store_true", help="external problems are errors, not warnings")
    ap.add_argument("--pin", action="store_true", help="write the current section hashes into module.yaml")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    course, resolved = run(root, args.ext_root, args.strict_external)
    if args.pin:
        n, missed = pin(root, course, resolved)
        print(f"learn: {n} module files re-pinned")
        for where, ref, sha in missed:
            print(f"learn: cannot rewrite the pin of {ref} in {where} (not a block-style list item); set sha: {sha}")
        course, resolved = run(root, args.ext_root, args.strict_external)
    for level in ("error", "warning", "notice"):
        emit([f for lvl, f in course.findings if lvl == level], level)
    lessons = sum(len(m["lessons"]) for _, m in course.modules)
    items = sum(len(q["items"]) for _, q in course.quizzes.values())
    print(f"learn: {len(course.paths)} paths, {len(course.modules)} modules, {lessons} lessons, {items} quiz items, "
          f"{len(course.allowlist.get('sections', []))} allowlisted sections, {len(course.errors)} errors")
    return 1 if course.errors else 0


if __name__ == "__main__":
    sys.exit(main())
