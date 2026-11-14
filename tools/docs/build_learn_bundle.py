#!/usr/bin/env python3
"""Build the AA Academy learn bundle: learn manifest + lesson bodies + cited sections + quizzes (AA-1104, GUIDE-13).

The Docs sync workflow (.github/workflows/docs-sync.yml) runs this script next to build_docs_reader.py on a clean
checkout of master and uploads the output under the docs reader prefix, at learn/. It is a separate output folder and
a separate upload step: a broken course never stops the docs pages from publishing.

What it does:

  1. Runs every check of tools/docs/check_learn.py. Any error fails the build (exit 1, nothing written), except a
     changed source section ("Learn source changed"): on master that is drift to review, not a reason to withhold the
     course. The lesson is marked stale and every quiz item that cites the changed section is suspended until the
     module owner reviews the lesson and re-pins it (GUIDE-13 research §6.4). External sources (app CONTEXT.md files,
     checked out under _ext/<repo>) never fail the build either: a missing file, a missing anchor or a changed hash
     marks the lesson stale.
  2. Writes each lesson body (and its .vi.md translation) and the text of each cited section, redacted with the docs
     reader's patterns; the same guard as the reader runs on the result, and any hit fails the build.
  3. Writes each module's quiz to its own file. Quiz files hold the answers: the learning API reads them server side
     and never sends them to a browser before a submission. The manifest holds no answer.
  4. Writes learn/manifest.json last, so it never lists an object the upload has not sent yet.

Output layout (OUT_DIR, default _site/learn; uploaded to <docs reader prefix>/learn/):

  manifest.json                                format 1, below
  lessons/<module folder>/<NN-slug>.md         lesson body (no front-matter), and <NN-slug>.vi.md when it exists
  sections/<kind>/<name>/<anchor>.md           the redacted text of one cited section (Ref.key in check_learn.py)
  quizzes/<module id>.json                     {"module", "version", "items": [{id, kind, prompt, choices, answer,
                                                source, explain, suspended}]} - server side only

manifest.json:
  {"format": 1, "generated_at", "source": {"repo", "sha", "ref"},
   "counts": {"paths", "modules", "lessons", "quiz_items", "sections", "stale_lessons", "suspended_items"},
   "paths": [{"id", "title", "tier", "audience", "owner", "modules": [{"id", "required"}], "planned", "final_quiz"}],
   "modules": [{"id", "title", "tier", "status", "version", "owner", "last_reviewed", "review_every_days",
                "languages", "objectives", "prerequisites", "lab", "stale",
                "lessons": [{"id", "title", "type", "minutes", "objective", "key", "translations": [{"lang", "key"}],
                             "stale", "sources": [{"ref", "key", "pinned", "current", "stale"}],
                             "video"}],
                "quiz": {"key", "items", "suspended"}}],
   "sections": [{"ref", "kind", "name", "anchor", "path", "key", "sha", "tier", "redactions", "available"}]}

  tier        staff or partner. A module and a path carry their own; a section is partner when an agency module may
              read it (a catalog page in the allowlist's partner_pages, or an allowlist section of tier partner).
  stale       a cited section changed since the lesson was pinned, or an external section could not be read. The
              learning API opens a content review item for the module owner and hides suspended quiz items.
  key         object key relative to learn/; null when the section could not be read (stale).
  video       additive field of format 1 (AA-1105, decision D8): null, or {"key", "captions": [{"lang", "key"}]}. The
              keys are object keys in the bronze bucket under learn-media/ (not under learn/): the learning API
              presigns them after its access check. The bundle never uploads a video; tools/uat builds and uploads
              them, so a key may not exist yet (the API answers 404 for it).

Usage:
  python tools/docs/build_learn_bundle.py --out _site/learn --ext-root _ext --sha "$GITHUB_SHA" --ref master
  python tools/docs/build_learn_bundle.py --check     # build in a temp folder and print the counts only
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
from pathlib import Path

import check_learn as cl
from build_docs_reader import REPO_NAME, _git_sha, guard_hits, redact
from docslib import REPO_ROOT, emit

FORMAT = 1
DRIFT_TITLES = {"Learn source changed", "Learn external source"}


class BuildError(Exception):
    """The course cannot be published; the message lists why."""


def _module_folder(rel: str) -> str:
    return Path(rel).name


def _section_tier(ref: cl.Ref, allowed: dict[str, str], partner_pages: set[str]) -> str:
    if ref.kind in cl.ALLOWLIST_KINDS:
        return allowed.get(ref.raw, "staff")
    return "partner" if ref.kind == "doc" and ref.name in partner_pages else "staff"


def _guarded(text: str, where: str, problems: list[str]) -> tuple[str, int]:
    body, n = redact(text)
    for label in guard_hits(body):
        problems.append(f"{where}: {label} still present after redaction")
    return body, n


def build(out: Path, root: Path = REPO_ROOT, ext_roots: list[Path] | None = None, sha: str = "",
          ref: str = "") -> dict:
    """Write the learn bundle to `out` (emptied first) and return the manifest; raise BuildError when it cannot."""
    course, resolved = cl.run(root, ext_roots, strict_external=False)
    blocking = [f for level, f in course.findings if level == "error" and f.title not in DRIFT_TITLES]
    if blocking:
        emit(blocking, "error")
        raise BuildError(f"{len(blocking)} course errors (tools/docs/check_learn.py)")

    allowed = cl._allowed_sections(course)
    partner_pages = set(course.allowlist.get("partner_pages", []))
    problems: list[str] = []
    files: dict[str, str] = {}

    sections: dict[str, dict] = {}
    for raw, r in sorted(resolved.items()):
        entry = {"ref": raw, "kind": r.ref.kind, "name": r.ref.name, "anchor": r.ref.anchor, "path": r.path,
                 "key": None, "sha": r.sha, "tier": _section_tier(r.ref, allowed, partner_pages), "redactions": 0,
                 "available": r.text is not None}
        if r.text is not None:
            body, n = _guarded(r.text, raw, problems)
            entry["key"] = r.ref.key
            entry["redactions"] = n
            files[r.ref.key] = body + "\n"
        sections[raw] = entry

    modules = []
    stale_lessons = suspended_items = 0
    for rel, m in course.modules:
        folder = _module_folder(rel)
        lessons = []
        stale_refs: set[str] = set()
        for lesson in m["lessons"]:
            key = f"lessons/{folder}/{Path(lesson['file']).name}"
            src_path = root / rel / lesson["file"]
            files[key], _ = _guarded(src_path.read_text(encoding="utf-8"), key, problems)
            translations = []
            vi = src_path.with_name(src_path.name[:-3] + ".vi.md")
            if vi.is_file():
                vkey = key[:-3] + ".vi.md"
                files[vkey], _ = _guarded(vi.read_text(encoding="utf-8"), vkey, problems)
                translations.append({"lang": "vi", "key": vkey})
            sources = []
            for src in lesson["sources"]:
                raw = str(src["ref"])
                s = sections[raw]
                pinned = src.get("sha")
                is_stale = (not s["available"]) or pinned != s["sha"]
                if is_stale:
                    stale_refs.add(raw)
                sources.append({"ref": raw, "key": s["key"], "pinned": pinned, "current": s["sha"],
                                "stale": is_stale})
            lesson_stale = any(x["stale"] for x in sources)
            stale_lessons += lesson_stale
            video = None
            if lesson.get("video"):
                video = {"key": lesson["video"]["key"],
                         "captions": [{"lang": lang, "key": ckey}
                                      for lang, ckey in cl.video_caption_keys(lesson["video"])]}
            lessons.append({"id": lesson["id"], "title": lesson["title"], "type": lesson["type"],
                            "minutes": lesson["minutes"], "objective": lesson["objective"], "key": key,
                            "translations": translations, "stale": lesson_stale, "sources": sources,
                            "video": video})
        quiz_entry = None
        hit = course.quizzes.get(m["id"])
        if hit is not None:
            _, quiz = hit
            items = []
            for item in quiz["items"]:
                suspended = str(item["source"]) in stale_refs
                suspended_items += suspended
                items.append({**item, "explain": item.get("explain", ""), "suspended": suspended})
            qkey = f"quizzes/{m['id']}.json"
            files[qkey] = json.dumps({"module": m["id"], "version": m["version"], "items": items}, indent=1,
                                     ensure_ascii=False) + "\n"
            for label in guard_hits(files[qkey]):
                problems.append(f"{qkey}: {label} in the quiz")
            quiz_entry = {"key": qkey, "items": len(items), "suspended": sum(1 for i in items if i["suspended"])}
        modules.append({
            "id": m["id"], "title": m["title"], "tier": m["tier"], "status": m["status"], "version": m["version"],
            "owner": m["owner"], "last_reviewed": m["last_reviewed"], "review_every_days": m.get("review_every_days"),
            "languages": m.get("languages", ["en"]), "objectives": m["objectives"],
            "prerequisites": m.get("prerequisites", []), "lab": m.get("lab"),
            "stale": any(x["stale"] for x in lessons), "lessons": lessons, "quiz": quiz_entry,
        })

    paths = [{"id": p["id"], "title": p["title"], "tier": p["tier"], "audience": p["audience"], "owner": p["owner"],
              "modules": p["modules"], "planned": p.get("planned", []), "final_quiz": p.get("final_quiz", False)}
             for _, p in course.paths]
    manifest = {
        "format": FORMAT,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": {"repo": REPO_NAME, "sha": sha or _git_sha(root), "ref": ref or None},
        "counts": {"paths": len(paths), "modules": len(modules), "lessons": sum(len(x["lessons"]) for x in modules),
                   "quiz_items": sum((x["quiz"] or {}).get("items", 0) for x in modules), "sections": len(sections),
                   "stale_lessons": stale_lessons, "suspended_items": suspended_items},
        "paths": paths,
        "modules": modules,
        "sections": list(sections.values()),
    }
    text = json.dumps(manifest, indent=1, ensure_ascii=False) + "\n"
    for label in guard_hits(text):
        problems.append(f"manifest.json: {label}")
    if problems:
        for p in problems:
            print(f"::error title=Learn bundle guard::{p}")
        raise BuildError(f"{len(problems)} guard hits")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for key, body in sorted(files.items()):
        target = out / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    (out / "manifest.json").write_text(text, encoding="utf-8")
    # Only drift is left among the errors here: report it as a warning, the stale marks carry it to the reader.
    emit([f for lvl, f in course.findings if lvl in ("error", "warning")], "warning")
    emit([f for lvl, f in course.findings if lvl == "notice"], "notice")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", default="_site/learn", help="output folder (emptied first)")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--ext-root", type=Path, action="append", default=[],
                    help="folder holding <repo>/CONTEXT.md of the app and Infra repos (Docs sync: _ext)")
    ap.add_argument("--sha", default="", help="commit the bundle is built from (default: git HEAD)")
    ap.add_argument("--ref", default="", help="branch name recorded in the manifest")
    ap.add_argument("--check", action="store_true", help="build into a temp folder and print the counts only")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.check:
            with tempfile.TemporaryDirectory() as tmp:
                manifest = build(Path(tmp) / "learn", root, args.ext_root, args.sha, args.ref)
        else:
            manifest = build(Path(args.out), root, args.ext_root, args.sha, args.ref)
    except BuildError as exc:
        print(f"::error title=Learn bundle::{exc}; the learn bundle is not built (the docs pages are not affected)")
        return 1
    c = manifest["counts"]
    print(f"learn bundle: {c['paths']} paths, {c['modules']} modules, {c['lessons']} lessons, {c['quiz_items']} quiz "
          f"items, {c['sections']} sections, {c['stale_lessons']} stale lessons, {c['suspended_items']} suspended "
          f"items, source {manifest['source']['sha'][:12] or 'unknown'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
