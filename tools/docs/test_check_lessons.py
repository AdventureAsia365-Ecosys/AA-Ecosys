"""Tests for check_lessons.py (AA-1024 G22). Invented lesson text; a temporary repo stands in for the root.

Run: python3 -m unittest discover -s tools/docs -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_lessons as cl

# S272: a git hook (pre-push) exports GIT_DIR and friends; a git command run in a temporary repo below would then act
# on the real repo (a hook-run test once set core.bare, a fake identity and refs in an app clone). Drop git's
# repo-local variables for this whole test process (the list is `git rev-parse --local-env-vars`; test_git_env_isolation).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

GIT_ENV = {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "T",
           "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

OLD = """# Lessons

Intro line.

## Area one

- **Old principle without a guard field** — symptom → cause (S200).
"""


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for p, text in {
            "skill/aa-lessons/lessons.md": OLD,
            ".claude/hooks/aa_shell_guard.py": 'RULES = (("PKILL-1", 1), ("ZSH-1", 2))\nRULE_IDS = ("RAM-1",)\n',
            "tools/github/ship_wave.py": "# tool\n",
            "tools/workflows/lane.js": "// lane\n",
            "docs/backlog/README.md": "| GRD-3 | shell guard for a demo |\n",
            "docs/backlog/tracker/plan.json": '{"issues": [{"id": "AA-1500"}]}\n',
        }.items():
            f = self.root / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
        self.git("init", "-q", "-b", "master")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "start")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True,
                       env=dict(os.environ, **GIT_ENV))

    def add_line(self, line: str) -> None:
        p = self.root / cl.LESSONS
        p.write_text(p.read_text(encoding="utf-8") + line + "\n", encoding="utf-8")

    def run_main(self, *argv) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cl.main(list(argv), root=self.root)
        return code, out.getvalue()


class CheckLineTest(RepoCase):
    def why(self, line: str) -> str | None:
        planned = (self.root / "docs/backlog/README.md").read_text() + (
            self.root / "docs/backlog/tracker/plan.json").read_text()
        return cl.check_line(line, self.root, cl.hook_rules(self.root), planned)

    def test_good_forms(self):
        for line in (
            "- **Do X** — y → z (S271, AA-1024). Guard: tool tools/github/ship_wave.py.",
            "- **Do X** — y → z (S271). Guard: hook aa_shell_guard:PKILL-1",
            "- **Do X** — y (S271). Guard: lane tools/workflows/lane.js:46",
            "- **Do X** — y (S271). Guard: test apps/AA-Demo/tests/unit/test_x.py::test_y",
            "- **Do X** — y (S271). Guard: pending GRD-3.",
            "- **Do X** — y (S271). Guard: pending AA-1500",
            "- **Do X** — y (S270, S271). Guard: none: judgement which source the business trusts is a choice.",
            "- **Do X** — y (S271). Guard: none: external the vendor portal has no API at all.",
        ):
            self.assertIsNone(self.why(line), line)

    def test_bad_forms(self):
        cases = {
            "- **Do X** — y → z (S271). Bắt bằng: a query.": "no Guard field",
            "- **Do X** — y (S271). Guard: tool tools/github/nope.py": "does not exist",
            "- **Do X** — y (S271). Guard: hook aa_shell_guard:NOPE-9": "has no rule NOPE-9",
            "- **Do X** — y (S271). Guard: lane tools/github/ship_wave.py": "tools/workflows/",
            "- **Do X** — y (S271). Guard: test": "needs a target",
            "- **Do X** — y (S271). Guard: pending GRD-77": "not in docs/backlog",
            "- **Do X** — y (S271). Guard: pending soon": "GRD-<n> or AA-<n>",
            "- **Do X** — y (S271). Guard: none": "reason kind",
            "- **Do X** — y (S271). Guard: none: judgement": "3+ words",
            "- **Do X** — y (S262, S271). Guard: none: one-off it happened only this time": "repeat",
            "- **Do X** — y (S271). Guard: maybe later": "unknown Guard kind",
        }
        for line, want in cases.items():
            why = self.why(line)
            self.assertIsNotNone(why, line)
            self.assertIn(want, why, line)


class MainTest(RepoCase):
    def test_base_mode_checks_only_new_or_changed_lines(self):
        code, out = self.run_main("--base", "master")
        self.assertEqual(code, 0, out)  # the old line has no Guard field and is not checked
        self.add_line("- **New principle** — symptom → cause (S271). Bắt bằng: careful reading.")
        code, out = self.run_main("--base", "master")
        self.assertEqual(code, 1)
        self.assertIn("1 new or changed lesson line(s)", out)
        self.assertIn("::error file=skill/aa-lessons/lessons.md,line=8,title=Lesson needs a Guard::", out)

    def test_editing_an_old_line_needs_the_field_too(self):
        p = self.root / cl.LESSONS
        p.write_text(p.read_text().replace("(S200).", "(S200, S271 again)."), encoding="utf-8")
        code, out = self.run_main("--base", "master")
        self.assertEqual(code, 1, out)
        p.write_text(p.read_text().replace("(S200, S271 again).", "(S200, S271). Guard: pending GRD-3."),
                     encoding="utf-8")
        self.assertEqual(self.run_main("--base", "master")[0], 0)

    def test_pending_file_and_sweep(self):
        pend = self.root / "pending.md"
        pend.write_text("# S999 pending\n\n- **A** — b (S999). Guard: pending GRD-3\n- **C** — d (S999).\n")
        code, out = self.run_main("--pending", str(pend))
        self.assertEqual(code, 1)
        self.assertIn("line=4", out)
        self.add_line("- **Guarded** — x (S271). Guard: tool tools/github/ship_wave.py")
        code, out = self.run_main("--sweep")
        self.assertEqual(code, 0)
        self.assertIn("delete me (guard tool tools/github/ship_wave.py exists)", out)

    def test_real_lessons_file_parses(self):
        real = cl.REPO_ROOT / cl.LESSONS
        lines = cl.lesson_lines(real.read_text(encoding="utf-8"))
        self.assertGreater(len(lines), 50)
        self.assertTrue(all(t.startswith("- ") for _, t in lines))


if __name__ == "__main__":
    unittest.main()
