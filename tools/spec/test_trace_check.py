"""Tests for trace_check.py (AA-1137). Run: python3 -m unittest discover -s tools/spec -p 'test_*.py'

Fixture specs are written to temporary folders with invented content. The committed spec of AA-1137 and the three
templates under skill/aa-linear-issue/templates/spec/ are passing fixtures: a change that breaks them fails here.
Fake IDs are assembled at run time, so no repo-wide resource-ID scan sees a literal one in this file.
"""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import trace_check as tc  # noqa: E402

SAMPLE = REPO / ".kiro" / "specs" / "AA-1137-spec-trace"
TEMPLATES = REPO / "skill" / "aa-linear-issue" / "templates" / "spec"
ACCOUNT = "1234" + "5678" + "9012"
SG = "sg-" + "0123456789abcdef0"

REQ = """\
---
id: spec-AA-42
issue: AA-42
title: Invented slice
status: {status}
owner_repo: AA-Example
kind: {kind}
{approved}
---

# Invented slice

## Problem

The lantern service forgets the colour of each lantern after a restart.

## Requirements

- R1.1 WHEN a lantern is lit THE SYSTEM SHALL store its colour.
  Verify: tests/unit/test_lantern.py; live: GET /lanterns/7 returns colour amber
- R1.2 IF the colour is unknown THEN THE SYSTEM SHALL
  answer with the default colour.
  Verify: test: tests/unit/test_lantern.py::test_default
"""

TASKS = """\
# Tasks

- [{s1}] T1 Store the colour - repo: AA-Example - lane: l1
  _Requirements: R1.1_
- [{s2}] T2 Default colour - repo: AA-Example
  _Requirements: R1.2_
"""

DESIGN = """\
# Design

### D1 Keep colours in the lantern table

Hard to reverse: {hard}
{approved}
"""


def git(cwd: Path, *args: str) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.invalid")
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(k, None)
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=env).stdout


class SpecFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dir = self.root / ".kiro" / "specs" / "AA-42-lanterns"
        self.dir.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, status="in-progress", kind="quick", approved="approved_at: 2026-11-19", s1=" ", s2=" ",
              req=None, tasks=None, design=None):
        (self.dir / "requirements.md").write_text(req if req is not None else REQ.format(
            status=status, kind=kind, approved=approved), encoding="utf-8")
        if tasks is not False:
            (self.dir / "tasks.md").write_text(tasks if tasks is not None else TASKS.format(s1=s1, s2=s2),
                                               encoding="utf-8")
        if design is not None:
            (self.dir / "design.md").write_text(design, encoding="utf-8")

    def errors(self, base: str | None = None) -> list[str]:
        spec = tc.load_spec(self.dir)
        found = spec.findings + (tc.check_frozen(spec, base) if base else [])
        return [f.message for f in found if f.level == "error"]


class ParseAndRulesTest(SpecFixture):
    def test_valid_quick_spec_passes_and_parses(self):
        self.write()
        spec = tc.load_spec(self.dir)
        self.assertEqual([f.message for f in spec.findings], [])
        self.assertEqual(spec.status, "in-progress")
        self.assertEqual(list(spec.requirements), ["R1.1", "R1.2"])
        r11, r12 = spec.requirements["R1.1"], spec.requirements["R1.2"]
        self.assertEqual(r11.tests, ["tests/unit/test_lantern.py"])
        self.assertEqual(r11.live, ["GET /lanterns/7 returns colour amber"])
        self.assertIn("default colour", r12.text)  # a wrapped criterion keeps its second line
        self.assertEqual(r12.tests, ["tests/unit/test_lantern.py::test_default"])
        self.assertEqual(spec.tasks["T1"].refs, ["R1.1"])
        self.assertEqual(spec.tasks["T1"].repo, "AA-Example")

    def test_task_with_unknown_or_missing_requirement(self):
        self.write(tasks="- [ ] T1 Store - repo: x\n  _Requirements: R9.9_\n- [ ] T2 Nothing named\n")
        errs = self.errors()
        self.assertTrue(any("T1 names 'R9.9'" in e for e in errs), errs)
        self.assertTrue(any("T2 names no requirement" in e for e in errs), errs)

    def test_kiro_style_refs_and_group_refs_resolve(self):
        self.write(tasks="- [ ] T1 Store\n  _Requirements: 1.1_\n- [ ] T2 All of R1\n  _Requirements: R1_\n")
        self.assertEqual(self.errors(), [])

    def test_requirement_without_verify_or_shall(self):
        req = REQ.format(status="draft", kind="quick", approved="").replace(
            "  Verify: test: tests/unit/test_lantern.py::test_default\n", "")
        req = req.replace("WHEN a lantern is lit THE SYSTEM SHALL store", "WHEN a lantern is lit it stores")
        self.write(req=req)
        errs = self.errors()
        self.assertTrue(any("R1.2 has no Verify line" in e for e in errs), errs)
        self.assertTrue(any("R1.1 is not an EARS criterion" in e for e in errs), errs)

    def test_verify_item_that_is_neither_test_nor_live(self):
        req = REQ.format(status="draft", kind="quick", approved="").replace(
            "Verify: test: tests/unit/test_lantern.py::test_default", "Verify: ask someone")
        self.write(req=req)
        errs = self.errors()
        self.assertTrue(any("'ask someone' is neither a test" in e for e in errs), errs)
        self.assertTrue(any("names no test and no live step" in e for e in errs), errs)

    def test_front_matter_rules(self):
        self.write(approved="")
        self.assertTrue(any("needs approved_at" in e for e in self.errors()))
        self.write(status="done")
        self.assertTrue(any("status 'done'" in e for e in self.errors()))
        self.write(kind="epic")
        self.assertTrue(any("kind 'epic'" in e for e in self.errors()))
        self.write(req=REQ.format(status="draft", kind="quick", approved="").replace("id: spec-AA-42", "id: x"))
        self.assertTrue(any("should be 'spec-AA-42'" in e for e in self.errors()))
        self.write(req="# no front matter\n\n- R1.1 THE SYSTEM SHALL glow.\n  Verify: tests/a.py\n")
        self.assertTrue(any("no front-matter" in e for e in self.errors()))

    def test_folder_name_must_carry_the_issue(self):
        other = self.root / ".kiro" / "specs" / "AA-43-lanterns"
        self.write()
        self.dir.rename(other)
        self.dir = other
        self.assertTrue(any("folder name 'AA-43-lanterns'" in e for e in self.errors()))

    def test_duplicate_ids(self):
        self.write(tasks="- [ ] T1 A\n  _Requirements: R1.1_\n- [ ] T1 B\n  _Requirements: R1.2_\n")
        self.assertTrue(any("T1 is defined twice" in e for e in self.errors()))

    def test_carried_and_dropped_need_a_target_or_reason(self):
        self.write(tasks="- [~] T1 Store carried later\n  _Requirements: R1.1_\n- [-] T2 Default\n")
        errs = self.errors()
        self.assertTrue(any("T1 is carried but names no issue" in e for e in errs), errs)
        self.assertTrue(any("T2 is dropped without a reason" in e for e in errs), errs)
        self.write(tasks="- [~] T1 Store carried -> AA-77 (needs the new table)\n  _Requirements: R1.1_\n"
                         "- [-] T2 Default dropped: the default is already served\n")
        self.assertEqual(self.errors(), [])

    def test_implemented_spec_has_no_open_task(self):
        self.write(status="implemented", s1="x")
        self.assertTrue(any("T2 is still open but the spec is implemented" in e for e in self.errors()))
        self.write(status="implemented", s1="x", s2="x")
        self.assertEqual(self.errors(), [])

    def test_uncovered_requirement_is_a_warning_only(self):
        self.write(tasks="- [ ] T1 Store\n  _Requirements: R1.1_\n")
        spec = tc.load_spec(self.dir)
        self.assertEqual([f.message for f in spec.findings if f.level == "error"], [])
        self.assertTrue(any("R1.2 is not named" in f.message for f in spec.findings if f.level == "warning"))

    def test_missing_files(self):
        self.write(tasks=False)
        self.assertTrue(any("no tasks.md" in e for e in self.errors()))
        (self.dir / "requirements.md").unlink()
        self.assertTrue(any("no requirements.md" in e for e in self.errors()))

    def test_bugfix_file_name_and_not_both(self):
        self.write(kind="bugfix")
        (self.dir / "requirements.md").rename(self.dir / "bugfix.md")
        self.assertEqual(self.errors(), [])
        self.write(kind="bugfix")
        self.assertTrue(any("both requirements.md and bugfix.md" in e for e in self.errors()))

    def test_feature_needs_design_and_flagged_decisions(self):
        self.write(kind="feature")
        self.assertTrue(any("needs design.md" in e for e in self.errors()))
        self.write(kind="feature", design="# Design\n\nNo decisions yet.\n")
        self.assertTrue(any("has no decision" in e for e in self.errors()))
        self.write(kind="feature", design="# Design\n\n### D1 Something\n\nText only.\n")
        self.assertTrue(any("lacks a 'Hard to reverse" in e for e in self.errors()))
        self.write(kind="feature", design=DESIGN.format(hard="yes (drops a column)", approved=""))
        self.assertTrue(any("D1 is hard to reverse and has no 'Approved:'" in e for e in self.errors()))
        self.write(kind="feature", design=DESIGN.format(hard="yes (drops a column)",
                                                        approved="Approved: 2026-11-19, session decision page"))
        self.assertEqual(self.errors(), [])
        # A draft spec may wait for the approval.
        self.write(kind="feature", status="draft", design=DESIGN.format(hard="yes", approved=""))
        self.assertEqual(self.errors(), [])

    def test_account_and_resource_ids_are_refused(self):
        self.write(req=REQ.format(status="draft", kind="quick", approved="") + f"\nThe bucket of {ACCOUNT}.\n")
        self.assertTrue(any("12-digit account ID" in e for e in self.errors()))
        self.write(tasks=TASKS.format(s1=" ", s2=" ") + f"\nOpen {SG} first.\n")
        self.assertTrue(any("VPC resource ID" in e for e in self.errors()))

    def test_lines_in_code_fences_are_ignored(self):
        req = REQ.format(status="draft", kind="quick", approved="") + "\n```text\n- R9.1 an example\n```\n"
        self.write(req=req)
        self.assertNotIn("R9.1", tc.load_spec(self.dir).requirements)

    def test_show_prints_tasks_with_their_requirements(self):
        self.write()
        out = tc.show(tc.load_spec(self.dir), ["T1", "T9"])
        self.assertIn("T1 Store the colour", out)
        self.assertIn("R1.1 WHEN a lantern is lit", out)
        self.assertIn("live: GET /lanterns/7", out)
        self.assertIn("T9: not in tasks.md", out)


class FrozenAndPrModeTest(SpecFixture):
    def setUp(self):
        super().setUp()
        git(self.root, "init", "-q", "-b", "master")

    def commit(self, msg: str) -> str:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", msg)
        return git(self.root, "rev-parse", "HEAD").strip()

    def test_implemented_spec_is_frozen_except_archiving(self):
        self.write(status="implemented", s1="x", s2="x")
        base = self.commit("implemented")
        self.assertEqual(self.errors(base), [])
        (self.dir / "tasks.md").write_text(TASKS.format(s1="x", s2="x") + "- [ ] T3 New work\n  _Requirements: "
                                                                          "R1.1_\n", encoding="utf-8")
        self.assertTrue(any(e.startswith("frozen") for e in self.errors(base)))
        self.write(status="archived", s1="x", s2="x")
        self.assertEqual(self.errors(base), [])
        self.write(status="archived", s1="x", s2="x",
                   design="# Design\n")  # a new file in a frozen spec
        self.assertTrue(any("a new file is a change" in e for e in self.errors(base)))

    def test_in_progress_spec_is_not_frozen(self):
        self.write(status="in-progress")
        base = self.commit("start")
        self.write(status="implemented", s1="x", s2="x")
        self.assertEqual(self.errors(base), [])

    def run_pr(self, text: str, base: str | None, *extra: str) -> tuple[int, str]:
        tf = self.root / "pr.md"
        tf.write_text(text, encoding="utf-8")
        argv = ["pr", "--root", str(self.root), "--text-file", str(tf), *extra]
        if base:
            argv += ["--base", base]
        out = io.StringIO()
        cwd = os.getcwd()
        try:
            os.chdir(self.root)
            with contextlib.redirect_stdout(out):
                rc = tc.main(argv)
        finally:
            os.chdir(cwd)
        return rc, out.getvalue()

    def test_pr_without_spec_passes(self):
        (self.root / "README.md").write_text("x\n", encoding="utf-8")
        shutil.rmtree(self.dir)
        base = self.commit("base")
        rc, out = self.run_pr("feat: x\n\nRefs AA-41", base)
        self.assertEqual(rc, 0)
        self.assertIn("No spec", out)

    def test_pr_naming_an_issue_with_a_broken_spec_fails(self):
        self.write(tasks="- [ ] T1 Store\n  _Requirements: R7.1_\n")
        base = self.commit("spec")
        rc, out = self.run_pr("feat: x\n\nRefs AA-42", base)
        self.assertEqual(rc, 1)
        self.assertIn("R7.1", out)
        rc, out = self.run_pr("feat: x\n\nRefs AA-420", base)  # AA-420 is another issue
        self.assertEqual(rc, 0, out)

    def test_pr_changing_a_spec_checks_it_even_without_its_issue(self):
        self.write()
        base = self.commit("spec")
        self.write(tasks="- [ ] T1 Store\n")
        self.commit("break it")
        summary = self.root / "summary.md"
        rc, out = self.run_pr("chore: unrelated", base, "--summary", str(summary))
        self.assertEqual(rc, 1)
        self.assertIn("T1 names no requirement", out)
        self.assertIn("| spec-AA-42 |", summary.read_text(encoding="utf-8"))

    def test_extra_root_holds_cross_repo_specs(self):
        shutil.rmtree(self.root / ".kiro")
        (self.root / "README.md").write_text("x\n", encoding="utf-8")
        base = self.commit("app repo")
        with tempfile.TemporaryDirectory() as other:
            d = Path(other) / ".kiro" / "specs" / "AA-42-lanterns"
            d.mkdir(parents=True)
            (d / "requirements.md").write_text(REQ.format(status="draft", kind="quick", approved=""),
                                               encoding="utf-8")
            (d / "tasks.md").write_text(TASKS.format(s1=" ", s2=" "), encoding="utf-8")
            rc, out = self.run_pr("Refs AA-42", base, "--extra-root", other)
            self.assertEqual(rc, 0, out)
            self.assertIn("spec-AA-42", out)
            (d / "tasks.md").write_text("- [ ] T1 x\n", encoding="utf-8")
            rc, _ = self.run_pr("Refs AA-42", base, "--extra-root", other)
            self.assertEqual(rc, 1)


class CommittedFixturesTest(unittest.TestCase):
    def test_the_aa1137_spec_passes(self):
        spec = tc.load_spec(SAMPLE)
        self.assertEqual([f.render() for f in spec.findings if f.level == "error"], [])
        self.assertEqual(spec.spec_id, "spec-AA-1137")
        self.assertEqual(spec.front.get("kind"), "feature")

    def test_templates_pass_once_filled(self):
        for kind in ("feature", "bugfix", "quick"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                d = Path(tmp) / f"AA-1-{kind}"
                d.mkdir()
                for f in (TEMPLATES / kind).glob("*.md"):
                    (d / f.name).write_text(f.read_text(encoding="utf-8").replace("AA-<n>", "AA-1"),
                                            encoding="utf-8")
                spec = tc.load_spec(d)
                self.assertEqual([x.render() for x in spec.findings if x.level == "error"], [])
                self.assertEqual(spec.front["kind"], kind)
                self.assertEqual(spec.status, "draft")

    def test_workflow_safety(self):
        raw = (REPO / ".github" / "workflows" / "spec-trace.yml").read_text(encoding="utf-8")
        wf = "\n".join(line.split(" # ")[0] if "uses:" not in line else line
                       for line in raw.splitlines() if not line.lstrip().startswith("#"))
        self.assertNotIn("pull_request_target", wf)
        self.assertNotIn("secrets.", wf)
        self.assertIn("merge_group:", wf)
        self.assertIn("workflow_call:", wf)
        self.assertIn("contents: read", wf)
        for line in wf.splitlines():
            if "uses:" in line and "./" not in line:
                self.assertRegex(line, r"@[0-9a-f]{40} # v\d", line)
        # the PR text reaches the script through the environment, never inline in a run block
        for line in wf.splitlines():
            if "github.event.pull_request.body" in line or "github.event.pull_request.title" in line:
                self.assertRegex(line, r"^\s+[A-Z_]+: \$\{\{ github\.event\.pull_request\.(body|title) \}\}$")


if __name__ == "__main__":
    unittest.main()
