"""Tests for build_learn_bundle.py and for the committed course under docs/learn/ (AA-1104).

A temporary root holds the real schemas, one invented ADR, one invented app CONTEXT.md and one module. The last class
checks the real sample module: it passes as committed, and a change to a section it cites turns the check red.

Run: python3 -m unittest discover -s tools/docs -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import build_learn_bundle as blb
import check_learn as cl
from docslib import REPO_ROOT

ADR = """# 0001. Invented decision

## Context

Some context.

## Decision

We decide one thing.

## Consequences

Some consequences.
"""

CONTEXT = """# Invented app - Repo Context

## Run it locally

Run the invented app.

## Layout

Some layout.
"""

LESSON = "# Reading the decision\n\nThe lesson text points at the decision section.\n"

ALLOWLIST = """version: 1
sections:
  - ref: context:AA-Booking#run-it-locally
    tier: staff
    reason: The lesson teaches the local run of the invented app.
partner_pages: []
"""


def module_yaml(sources: str) -> str:
    return f"""id: F1
title: Invented module
tier: staff
status: draft
version: 1.0.0
owner: nghiep
last_reviewed: 2026-11-14
objectives:
  - Find the decision section of an ADR.
quiz: quiz.yaml
lessons:
  - id: F1-01
    file: lessons/01-reading.md
    title: Reading the decision
    type: reading
    minutes: 5
    objective: Name the section that records a decision.
    sources:
{sources}
"""


def quiz_yaml(sources: list[str]) -> str:
    items = ""
    for n in range(1, 6):
        items += f"""  - id: F1-Q{n}
    kind: single
    prompt: Which section holds the decision?
    choices: [Context, Decision]
    answer: [1]
    source: {sources[n % len(sources)]}
"""
    return f"module: F1\nitems:\n{items}"


class BundleCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "repo"
        self.out = Path(self._tmp.name) / "out"
        self.ext = Path(self._tmp.name) / "ext"
        shutil.copytree(REPO_ROOT / cl.SCHEMA_DIR, self.root / cl.SCHEMA_DIR)
        (self.root / "docs/adr").mkdir(parents=True)
        (self.root / "docs/adr/0001-invented.md").write_text(ADR, encoding="utf-8")
        (self.ext / "AA-Booking").mkdir(parents=True)
        (self.ext / "AA-Booking/CONTEXT.md").write_text(CONTEXT, encoding="utf-8")
        (self.root / cl.ALLOWLIST).write_text(ALLOWLIST, encoding="utf-8")
        self.mod = self.root / cl.LEARN_DIR / "modules/F1-invented"
        (self.mod / "lessons").mkdir(parents=True)
        (self.mod / "lessons/01-reading.md").write_text(LESSON, encoding="utf-8")
        self.adr_sha = cl.section_sha(cl.section(ADR, "decision"))
        self.ctx_sha = cl.section_sha(cl.section(CONTEXT, "run-it-locally"))
        self.write(adr_sha=self.adr_sha, ctx_sha=self.ctx_sha)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, adr_sha: str, ctx_sha: str) -> None:
        sources = (f"      - ref: adr:0001#decision\n        sha: {adr_sha}\n"
                   f"      - ref: context:AA-Booking#run-it-locally\n        sha: {ctx_sha}")
        (self.mod / "module.yaml").write_text(module_yaml(sources), encoding="utf-8")
        (self.mod / "quiz.yaml").write_text(quiz_yaml(["adr:0001#decision", "context:AA-Booking#run-it-locally"]),
                                            encoding="utf-8")

    def build(self) -> dict:
        with contextlib.redirect_stdout(io.StringIO()):
            return blb.build(self.out, self.root, [self.ext], sha="0" * 40, ref="master")


class BuildTest(BundleCase):
    def test_writes_manifest_lessons_sections_and_quiz(self):
        m = self.build()
        self.assertEqual(m["counts"]["lessons"], 1)
        self.assertEqual(m["counts"]["stale_lessons"], 0)
        lesson = m["modules"][0]["lessons"][0]
        self.assertEqual(lesson["key"], "lessons/F1-invented/01-reading.md")
        self.assertTrue((self.out / lesson["key"]).is_file())
        for src in lesson["sources"]:
            self.assertTrue((self.out / src["key"]).is_file(), src)
        self.assertEqual((self.out / "sections/adr/0001/decision.md").read_text(encoding="utf-8").splitlines()[0],
                         "## Decision")
        quiz = json.loads((self.out / "quizzes/F1.json").read_text(encoding="utf-8"))
        self.assertEqual(quiz["items"][0]["answer"], [1])

    def test_manifest_never_holds_an_answer(self):
        text = json.dumps(self.build())
        self.assertNotIn('"answer"', text)
        self.assertNotIn('"choices"', text)

    def test_root_source_change_marks_stale_and_suspends_its_items(self):
        (self.root / "docs/adr/0001-invented.md").write_text(ADR.replace("one thing", "two things"), encoding="utf-8")
        m = self.build()
        mod = m["modules"][0]
        self.assertTrue(mod["stale"])
        stale = [s for s in mod["lessons"][0]["sources"] if s["stale"]]
        self.assertEqual([s["ref"] for s in stale], ["adr:0001#decision"])
        quiz = json.loads((self.out / "quizzes/F1.json").read_text(encoding="utf-8"))
        suspended = {i["id"] for i in quiz["items"] if i["suspended"]}
        expected = {i["id"] for i in quiz["items"] if i["source"] == "adr:0001#decision"}
        self.assertEqual(suspended, expected)
        self.assertEqual(mod["quiz"]["suspended"], len(expected))

    def test_missing_external_file_marks_stale_without_failing(self):
        shutil.rmtree(self.ext)
        m = self.build()
        src = [s for s in m["modules"][0]["lessons"][0]["sources"] if s["ref"].startswith("context:")][0]
        self.assertTrue(src["stale"])
        self.assertIsNone(src["key"])

    def test_lesson_without_video_has_a_null_video(self):
        self.assertIsNone(self.build()["modules"][0]["lessons"][0]["video"])

    def test_lesson_video_passes_into_the_manifest_with_caption_keys(self):
        text = (self.mod / "module.yaml").read_text(encoding="utf-8")
        text = text.replace("    sources:\n", "    video:\n      key: learn-media/F1/01-reading.mp4\n"
                                               "      captions: [en, vi]\n    sources:\n", 1)
        (self.mod / "module.yaml").write_text(text, encoding="utf-8")
        video = self.build()["modules"][0]["lessons"][0]["video"]
        self.assertEqual(video, {"key": "learn-media/F1/01-reading.mp4",
                                 "captions": [{"lang": "en", "key": "learn-media/F1/01-reading.en.vtt"},
                                              {"lang": "vi", "key": "learn-media/F1/01-reading.vi.vtt"}]})
        self.assertFalse((self.out / "learn-media").exists(), "the bundle never uploads a video")

    def test_course_error_fails_and_writes_nothing(self):
        (self.mod / "lessons/01-reading.md").write_text("# Another title\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(blb.BuildError):
            blb.build(self.out, self.root, [self.ext])
        self.assertFalse(self.out.exists())

    def test_id_in_an_allowlisted_section_fails(self):
        (self.ext / "AA-Booking/CONTEXT.md").write_text(CONTEXT.replace("Run the invented app.",
                                                                         "Key AKIA0000000000000000 here."),
                                                        encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(blb.BuildError):
            blb.build(self.out, self.root, [self.ext])
        self.assertFalse(self.out.exists())

    def test_main_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(blb.main(["--root", str(self.root), "--ext-root", str(self.ext), "--check"]), 0)
        (self.mod / "quiz.yaml").write_text("module: F1\nitems: []\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(blb.main(["--root", str(self.root), "--ext-root", str(self.ext), "--check"]), 1)


class CommittedCourseTest(unittest.TestCase):
    """The committed docs/learn/ passes check_learn.py, and a change to a section it cites turns the check red."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.course, self.resolved = cl.run(REPO_ROOT)
        # A copy of the course plus every root page it cites (the docs index walks the copy, not git).
        shutil.copytree(REPO_ROOT / cl.LEARN_DIR, self.root / cl.LEARN_DIR)
        index = cl.Sources(REPO_ROOT).docs_index()
        pages = {r.path for r in self.resolved.values() if r.path and not r.ref.external}
        pages |= {index[p][0] for p in self.course.allowlist.get("partner_pages", []) if p in index}
        for relpath in pages:
            if (REPO_ROOT / relpath).is_file():
                target = self.root / relpath
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / relpath, target)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def errors(self, root: Path) -> list[str]:
        course, _ = cl.run(root)
        return [f.message for f in course.errors]

    def test_committed_course_is_green(self):
        self.assertEqual([f.message for f in self.course.errors], [])
        self.assertGreaterEqual(len(self.course.modules), 1)

    def test_copy_is_green_then_red_after_a_source_change(self):
        self.assertEqual(self.errors(self.root), [])
        root_sources = [r for r in self.resolved.values() if not r.ref.external and r.text]
        self.assertTrue(root_sources, "the sample module cites at least one root section")
        r = root_sources[0]
        page = self.root / r.path
        text = page.read_text(encoding="utf-8")
        self.assertIn(r.text, text)
        page.write_text(text.replace(r.text, r.text + "\n\nOne more sentence in the cited section.", 1),
                        encoding="utf-8")
        msgs = self.errors(self.root)
        self.assertTrue(any("changed since the lesson was written" in m for m in msgs), msgs)


if __name__ == "__main__":
    unittest.main()
