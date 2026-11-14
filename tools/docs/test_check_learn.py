"""Tests for check_learn.py (AA-1104). A temporary root holds the real schemas, one invented ADR and one module.

Run: python3 -m unittest discover -s tools/docs -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import check_learn as cl
from docslib import REPO_ROOT

ADR = """# 0001. Invented decision

## Context

Some context.

## Decision

We decide one thing.

### Detail

A detail under the decision.

## Consequences

Some consequences.
"""

LESSON = "# Reading the decision\n\nThe lesson text points at the decision section.\n"

QUIZ = """module: F1
items:
{items}
"""

QUIZ_ITEM = """  - id: F1-Q{n}
    kind: single
    prompt: Which section holds the decision?
    choices: [Context, Decision]
    answer: [1]
    source: {source}
"""


def module_yaml(sources: str, last_reviewed: str = "2026-11-14") -> str:
    return f"""id: F1
title: Invented module
tier: staff
status: draft
version: 1.0.0
owner: nghiep
last_reviewed: {last_reviewed}
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


class LearnCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        shutil.copytree(REPO_ROOT / cl.SCHEMA_DIR, self.root / cl.SCHEMA_DIR)
        (self.root / "docs/adr").mkdir(parents=True)
        (self.root / "docs/adr/0001-invented.md").write_text(ADR, encoding="utf-8")
        self.mod = self.root / cl.LEARN_DIR / "modules/F1-invented"
        (self.mod / "lessons").mkdir(parents=True)
        (self.mod / "lessons/01-reading.md").write_text(LESSON, encoding="utf-8")
        self.write_quiz("adr:0001#decision")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_module(self, sources: str, **kw) -> None:
        (self.mod / "module.yaml").write_text(module_yaml(sources, **kw), encoding="utf-8")

    def write_quiz(self, source: str) -> None:
        items = "".join(QUIZ_ITEM.format(n=n, source=source) for n in range(1, 6))
        (self.mod / "quiz.yaml").write_text(QUIZ.format(items=items), encoding="utf-8")

    def run_check(self) -> cl.Course:
        course, _ = cl.run(self.root)
        return course

    def run_main(self, *args: str) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cl.main(["--root", str(self.root), *args])
        return code, buf.getvalue()

    def messages(self, course: cl.Course) -> list[str]:
        return [f.message for f in course.errors]

    def decision_sha(self) -> str:
        return cl.section_sha(cl.section(ADR, "decision"))


class LoadTest(LearnCase):
    def test_unquoted_date_passes_the_schema(self):
        self.write_module(f"      - ref: adr:0001#decision\n        sha: {self.decision_sha()}")
        course = self.run_check()
        self.assertEqual(self.messages(course), [])
        self.assertEqual(course.modules[0][1]["last_reviewed"], "2026-11-14")

    def test_quoted_date_passes_too(self):
        self.write_module(f"      - ref: adr:0001#decision\n        sha: {self.decision_sha()}",
                          last_reviewed='"2026-11-14"')
        self.assertEqual(self.messages(self.run_check()), [])


class DriftTest(LearnCase):
    def test_source_change_turns_the_check_red(self):
        self.write_module(f"      - ref: adr:0001#decision\n        sha: {self.decision_sha()}")
        self.assertEqual(self.messages(self.run_check()), [])
        (self.root / "docs/adr/0001-invented.md").write_text(ADR.replace("one thing", "another thing"), encoding="utf-8")
        msgs = self.messages(self.run_check())
        self.assertEqual(len(msgs), 1)
        self.assertIn("changed since the lesson was written", msgs[0])

    def test_change_outside_the_section_keeps_it_green(self):
        self.write_module(f"      - ref: adr:0001#decision\n        sha: {self.decision_sha()}")
        (self.root / "docs/adr/0001-invented.md").write_text(ADR.replace("Some consequences.", "Other."),
                                                             encoding="utf-8")
        self.assertEqual(self.messages(self.run_check()), [])

    def test_missing_anchor_is_an_error(self):
        self.write_module("      - ref: adr:0001#no-such-heading\n        sha: 0123456789abcdef")
        self.write_quiz("adr:0001#no-such-heading")
        self.assertTrue(any("no heading with the anchor" in m for m in self.messages(self.run_check())))


class VideoTest(LearnCase):
    def with_video(self, video: str) -> list[str]:
        sources = f"      - ref: adr:0001#decision\n        sha: {self.decision_sha()}"
        text = module_yaml(sources).replace("    sources:\n", video + "    sources:\n", 1)
        (self.mod / "module.yaml").write_text(text, encoding="utf-8")
        return self.messages(self.run_check())

    def test_video_under_the_module_folder_passes(self):
        self.assertEqual(self.with_video("    video:\n      key: learn-media/F1/01-reading.mp4\n"
                                         "      captions: [en, vi]\n"), [])

    def test_video_outside_learn_media_breaks_the_schema(self):
        msgs = self.with_video("    video:\n      key: docs-reader/F1/01-reading.mp4\n      captions: [en]\n")
        self.assertTrue(msgs, "a key outside learn-media/ is refused")

    def test_video_of_another_module_is_an_error(self):
        msgs = self.with_video("    video:\n      key: learn-media/F2/01-reading.mp4\n      captions: [en]\n")
        self.assertTrue(any("must sit under learn-media/F1/" in m for m in msgs), msgs)

    def test_video_named_after_another_lesson_is_an_error(self):
        msgs = self.with_video("    video:\n      key: learn-media/F1/02-reading.mp4\n      captions: [en]\n")
        self.assertTrue(any("must start with the lesson number 01-" in m for m in msgs), msgs)

    def test_captions_need_english(self):
        msgs = self.with_video("    video:\n      key: learn-media/F1/01-reading.mp4\n      captions: [vi]\n")
        self.assertTrue(msgs, "captions without en are refused")

    def test_caption_keys_sit_next_to_the_video(self):
        self.assertEqual(cl.video_caption_keys({"key": "learn-media/F1/01-a.webm", "captions": ["en"]}),
                         [("en", "learn-media/F1/01-a.en.vtt")])


class PinTest(LearnCase):
    def assert_pins_to_green(self, sources: str) -> str:
        self.write_module(sources)
        self.assertTrue(any("no sha pin" in m or "changed since" in m for m in self.messages(self.run_check())))
        code, out = self.run_main("--pin")
        self.assertEqual(code, 0, out)
        self.assertIn("1 module files re-pinned", out)
        text = (self.mod / "module.yaml").read_text(encoding="utf-8")
        self.assertIn(self.decision_sha(), text)
        self.assertEqual(self.messages(self.run_check()), [])
        return text

    def test_pins_a_plain_ref(self):
        self.assert_pins_to_green("      - ref: adr:0001#decision")

    def test_pins_a_double_quoted_ref(self):
        self.assert_pins_to_green('      - ref: "adr:0001#decision"')

    def test_pins_a_single_quoted_ref(self):
        self.assert_pins_to_green("      - ref: 'adr:0001#decision'")

    def test_replaces_a_stale_sha_written_before_the_ref(self):
        text = self.assert_pins_to_green("      - sha: 0123456789abcdef\n        ref: adr:0001#decision")
        self.assertNotIn("0123456789abcdef", text)
        self.assertEqual(text.count("sha:"), 1)

    def test_replaces_a_stale_sha_after_a_quoted_ref(self):
        text = self.assert_pins_to_green('      - ref: "adr:0001#decision"\n        sha: "0123456789abcdef"')
        self.assertEqual(text.count("sha:"), 1)

    def test_flow_style_entry_is_reported_with_its_hash(self):
        self.write_module("      - {ref: 'adr:0001#decision'}")
        code, out = self.run_main("--pin")
        self.assertEqual(code, 1)
        self.assertIn("cannot rewrite the pin of adr:0001#decision", out)
        self.assertIn(f"set sha: {self.decision_sha()}", out)

    def test_all_digit_sha_is_quoted(self):
        self.assertEqual(cl._sha_text("0123456789012345"), '"0123456789012345"')
        self.assertEqual(cl._sha_text("0000000000000000"), '"0000000000000000"')
        self.assertEqual(cl._sha_text("0123456789abcdef"), "0123456789abcdef")


if __name__ == "__main__":
    unittest.main()
