"""Unit tests for event-based docs freshness (AA-1132 A5): tools/docs/docs_freshness.py and build_docs_reader rule 15.

Run: python -m unittest tools/docs/test_docs_freshness.py  (needs PyYAML, tools/docs/requirements.txt)
Fixtures are invented pages, code and repos; git runs in temporary repositories with fixed commit dates.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_docs_reader as b  # noqa: E402
import docs_freshness as f  # noqa: E402

for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

DOC_MAP = """version: 1
repos: [AA-Ecosys, AA-Booking, AA-Partner]
entries:
  - id: lantern-root-tool
    repo: AA-Ecosys
    code: ["tools/lantern/**"]
    pages: ["docs/guides/lantern.md", "skill/lantern/SKILL.md"]
    source: hand
  - id: booking-oars
    repo: AA-Booking
    code: ["backend/oars/*.py"]
    pages: ["docs/guides/oars.md", "AA-Booking:CONTEXT.md"]
    source: hand
  - id: partner-sails
    repo: AA-Partner
    code: ["api/sails/**"]
    pages: ["docs/guides/sails.md"]
    source: hand
"""

OWNERS = """version: 1
files:
  - path: skill/*/SKILL.md
    owner: tech-lead
  - path: AA-Booking:CONTEXT.md
    owner: tech-lead
    review_every_days: 10
  - path: .claude/rules.md
    owner: tech-lead
    last_reviewed: 2026-01-01
    review_every_days: 30
    depends_on: [partner-sails]
"""


def page(page_id: str, title: str, reviewed: str = "2026-01-01", body: str = "Body.\n") -> str:
    return (f"---\nid: {page_id}\ntitle: {title}\ntype: how-to\nstatus: active\nowner: tech-lead\naudience: [staff]\n"
            f"last_reviewed: {reviewed}\n---\n\n# {title}\n\n{body}")


class GitRepo:
    def __init__(self, path: Path):
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q")
        self.day = 0

    def git(self, *args: str, date: str | None = None) -> str:
        env = dict(os.environ)
        if date:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        return subprocess.run(["git", "-C", str(self.path), "-c", "user.name=t", "-c", "user.email=t@t.invalid", *args],
                              check=True, capture_output=True, text=True, env=env).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        p = self.path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> str:
        self.day += 1
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message, date=f"2026-02-{self.day:02d}T10:00:00+00:00")
        return self.git("rev-parse", "HEAD")


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.root = GitRepo(base / "root")
        self.deps = base / "deps"
        self.booking = GitRepo(self.deps / "AA-Booking")
        self.root.write(f.doc_impact.MAP, DOC_MAP)
        self.root.write(f.OWNERS, OWNERS)
        self.root.write("docs/guides/lantern.md", page("GUIDE-81", "Lantern guide"))
        self.root.write("docs/guides/oars.md", page("GUIDE-82", "Oars guide"))
        self.root.write("docs/guides/sails.md", page("GUIDE-83", "Sails guide"))
        self.root.write("skill/lantern/SKILL.md", "# Lantern skill\n")
        self.root.write(".claude/rules.md", "# Rules\n")
        self.root.write("tools/lantern/run.py", "x = 1\n")
        self.root.commit("docs: first pages")                                       # 02-01
        self.booking.write("CONTEXT.md", "# Booking context\n")
        self.booking.write("backend/oars/row.py", "y = 1\n")
        self.booking.commit("feat: oars")                                          # 02-01

    def tearDown(self):
        self._tmp.cleanup()

    def compute(self, deps: bool = True, today: str = "2026-02-20") -> f.Freshness:
        return f.compute(self.root.path, self.deps if deps else None, "HEAD", dt.date.fromisoformat(today))


class FlagTest(Fixture):
    def test_code_change_after_the_page_flags_it(self):
        self.root.write("tools/lantern/run.py", "x = 2\n")
        sha = self.root.commit("feat: brighter lantern")                           # 02-02
        fr = self.compute()
        flag = fr.pages["docs/guides/lantern.md"]
        self.assertEqual((flag["count"], flag["changes"][0]["entry"], flag["changes"][0]["sha"]),
                         (1, "lantern-root-tool", sha))
        self.assertTrue(flag["since"].startswith("2026-02-01"))
        self.assertNotIn("docs/guides/oars.md", fr.pages)

    def test_a_later_page_change_or_the_same_commit_clears_it(self):
        self.root.write("tools/lantern/run.py", "x = 2\n")
        self.root.commit("feat: brighter lantern")                                 # 02-02
        self.root.write("docs/guides/lantern.md", page("GUIDE-81", "Lantern guide", body="Updated.\n"))
        self.root.commit("docs: lantern guide follows")                            # 02-03
        self.root.write("tools/lantern/run.py", "x = 3\n")
        self.root.write("docs/guides/lantern.md", page("GUIDE-81", "Lantern guide", body="Both.\n"))
        self.root.commit("feat: lantern and its page together")                    # 02-04
        self.assertNotIn("docs/guides/lantern.md", self.compute().pages)

    def test_app_repo_history_counts_only_when_given(self):
        self.booking.write("backend/oars/row.py", "y = 2\n")
        self.booking.commit("fix: oars")                                           # 02-02 (booking repo)
        self.booking.write("backend/other.py", "z = 1\n")
        self.booking.commit("chore: unmapped file")
        fr = self.compute()
        self.assertEqual(fr.pages["docs/guides/oars.md"]["changes"][0]["repo"], "AA-Booking")
        self.assertEqual(fr.pages["docs/guides/oars.md"]["count"], 1)
        self.assertIn("AA-Partner", fr.repos_not_checked)                          # no history: never guessed
        self.assertNotIn("docs/guides/sails.md", fr.pages)
        fr = self.compute(deps=False)
        self.assertNotIn("docs/guides/oars.md", fr.pages)
        self.assertIn("AA-Booking", fr.repos_not_checked)

    def test_agent_files_glob_calendar_and_depends_on(self):
        self.root.write("tools/lantern/run.py", "x = 2\n")
        self.root.commit("feat: brighter lantern")
        fr = self.compute(today="2026-03-01")
        by = {a["path"]: a for a in fr.agent_files}
        self.assertEqual(sorted(by), [".claude/rules.md", "AA-Booking:CONTEXT.md", "skill/lantern/SKILL.md"])
        self.assertTrue(by["skill/lantern/SKILL.md"]["needs_review"])            # listed in the lantern entry
        self.assertFalse(by["skill/lantern/SKILL.md"]["overdue"])                # 90 days from 02-01
        self.assertTrue(by["AA-Booking:CONTEXT.md"]["overdue"])                  # 10 days from its last commit
        self.assertEqual(by[".claude/rules.md"]["last_reviewed"], "2026-02-01")  # its commit is newer than the row
        self.assertIsNone(by[".claude/rules.md"]["needs_review"])                # partner history not given
        s = fr.summary()
        self.assertEqual((s["agent_files"], s["agent_files_overdue"]), (3, 1))
        text = f.render(fr, dt.date(2026, 3, 1))
        self.assertIn("`docs/guides/lantern.md`", text)
        self.assertIn("(overdue)", text)

    def test_shallow_or_missing_history_is_none(self):
        self.assertIsNone(f.git_commits(self.root.path.parent / "nowhere"))


class OwnersTest(Fixture):
    def check(self, text: str) -> None:
        ids = {e.id for e in f.doc_impact.load_map(self.root.path / f.doc_impact.MAP)}
        f.parse_owners(text, self.root.path, ids)

    def test_committed_fixture_validates(self):
        self.assertEqual(len(f.load_owners(self.root.path, check=True)), 3)

    def test_problems(self):
        bad = {
            "unknown key": "version: 1\nfiles:\n  - path: .claude/rules.md\n    owner: tech-lead\n    colour: red\n",
            "person as owner": "version: 1\nfiles:\n  - path: .claude/rules.md\n    owner: Some Person\n",
            "no match": "version: 1\nfiles:\n  - path: skill/*/NOPE.md\n    owner: tech-lead\n",
            "unknown entry": ("version: 1\nfiles:\n  - path: .claude/rules.md\n    owner: tech-lead\n"
                              "    depends_on: [no-such-entry]\n"),
            "unknown repo": "version: 1\nfiles:\n  - path: AA-Elsewhere:CONTEXT.md\n    owner: tech-lead\n",
            "bad date": ("version: 1\nfiles:\n  - path: .claude/rules.md\n    owner: tech-lead\n"
                         "    last_reviewed: soon\n"),
            "account id": "version: 1\n# " + "5678" * 3 + "\nfiles: []\n",
            "version": "version: 2\nfiles: []\n",
        }
        for name, text in bad.items():
            with self.subTest(name=name), self.assertRaises(f.OwnersError):
                self.check(text)

    def test_cli_validate(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(f.main(["validate", "--root", str(self.root.path)]), 0)
        self.assertIn("3 rows", out.getvalue())


class VerifiedTest(Fixture):
    def run_verified(self, body: str) -> str:
        base = self.root.git("rev-parse", "HEAD")
        self.root.write("docs/guides/lantern.md", page("GUIDE-81", "Lantern guide", reviewed="2026-02-10"))
        self.root.write("docs/guides/oars.md", page("GUIDE-82", "Oars guide", body="Text only.\n"))
        self.root.write(f.OWNERS, OWNERS.replace("last_reviewed: 2026-01-01", "last_reviewed: 2026-02-10"))
        body_file = self.root.path.parent / "body.md"
        body_file.write_text(body, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = f.main(["verified", "--root", str(self.root.path), "--base", base, "--pr-body-file", str(body_file)])
        self.assertEqual(code, 0)                                                  # warn only
        return out.getvalue()

    def test_raised_without_a_verified_line_warns(self):
        out = self.run_verified("Refs AA-1\n\nTidy.\n")
        self.assertIn("::warning title=Verified line::docs/guides/lantern.md", out)
        self.assertIn(f"{f.OWNERS}: .claude/rules.md", out)
        self.assertNotIn("oars.md", out)                                           # body changed, date did not

    def test_a_verified_line_clears_it(self):
        out = self.run_verified("Refs AA-1\n\nVerified: lantern guide against tools/lantern on master.\n")
        self.assertNotIn("::warning", out)


class BundleTest(Fixture):
    def test_manifest_carries_needs_review_and_the_summary(self):
        self.root.write("tools/lantern/run.py", "x = 2\n")
        self.root.commit("feat: brighter lantern")
        out = self.root.path.parent / "bundle"
        with contextlib.redirect_stdout(io.StringIO()):
            m = b.build(out, root=self.root.path, sha="abc", ref="master", deps_root=self.deps)
        entries = {p["path"]: p for p in m["pages"]}
        self.assertEqual(entries["docs/guides/lantern.md"]["needs_review"]["count"], 1)
        self.assertIsNone(entries["docs/guides/oars.md"]["needs_review"])
        self.assertEqual(m["counts"]["needs_review"], 1)
        self.assertIn("AA-Booking", m["freshness"]["repos_checked"])

    def test_without_a_doc_map_the_build_still_succeeds(self):
        (self.root.path / f.doc_impact.MAP).unlink()
        self.root.commit("chore: no map")
        out = self.root.path.parent / "bundle"
        with contextlib.redirect_stdout(io.StringIO()) as log:
            m = b.build(out, root=self.root.path, sha="abc", ref="master")
        self.assertIsNone(m["freshness"])
        self.assertIn("needs_review not computed", log.getvalue())


if __name__ == "__main__":
    unittest.main()
