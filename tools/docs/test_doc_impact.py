"""Unit tests for the docs impact check (AA-1132 A4): tools/docs/doc_impact.py and docs/catalogue/doc-map.yaml.

Run: python -m unittest tools/docs/test_doc_impact.py  (needs PyYAML)
Fixtures use invented repos, files and pages; `gh` is a scripted stand-in on PATH, nothing reaches GitHub.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import doc_impact as d  # noqa: E402

# One test runs git in a temporary repo: drop git's repo-local variables for this whole test process, like
# tools/github/ship_fakes.py (`git rev-parse --local-env-vars`; tools/github/test_git_env_isolation.py).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)


MAP = """version: 1
repos: [AA-Ecosys, Repo-River, Repo-Stone]
entries:
  - id: river-boats
    repo: Repo-River
    code: ["boats/**", "docks/*.tf"]
    pages: ["docs/harbour.md", "Repo-River:CONTEXT.md"]
    source: hand
    why: "the boats"
  - id: river-oars
    repo: Repo-River
    code: ["oars.py"]
    pages: ["docs/oars.md"]
    source: audit-s283
  - id: stone-paths
    repo: Repo-Stone
    code: ["paths/**/route.ts"]
    pages: ["docs/harbour.md"]
    source: hand
"""


def entries(text: str = MAP):
    return d.parse_map(text)


class GlobTest(unittest.TestCase):
    def test_globs(self):
        cases = [
            ("boats/**", "boats/a/b.py", True), ("boats/**", "boats.py", False),
            ("docks/*.tf", "docks/main.tf", True), ("docks/*.tf", "docks/x/main.tf", False),
            ("paths/**/route.ts", "paths/route.ts", True), ("paths/**/route.ts", "paths/a/b/route.ts", True),
            ("api/migrations/*_llm_*.sql", "api/migrations/412_llm_route_tide.sql", True),
            ("api/migrations/*_llm_*.sql", "api/migrations/412_tide.sql", False),
            ("a?.md", "ab.md", True), ("a?.md", "a/.md", False), (".github/x.yml", ".github/x.yml", True),
        ]
        for glob, path, expected in cases:
            with self.subTest(glob=glob, path=path):
                self.assertEqual(bool(d.glob_regex(glob).match(path)), expected)


class MapTest(unittest.TestCase):
    def test_valid_map(self):
        self.assertEqual([e.id for e in entries()], ["river-boats", "river-oars", "stone-paths"])

    def test_shape_problems(self):
        bad = [
            (MAP.replace("id: river-oars", "id: river-boats"), "duplicate id"),
            (MAP.replace("repo: Repo-Stone", "repo: Repo-Sky"), "not in repos"),
            (MAP.replace("source: audit-s283", "source: guess"), "source must be"),
            (MAP.replace('"docs/oars.md"', '"Repo-Sky:x.md"'), "unknown repo"),
            (MAP.replace('"docs/oars.md"', '"AA-Ecosys:docs/oars.md"'), "plain path"),
            (MAP.replace('["oars.py"]', '["../oars.py"]'), "relative to the repo root"),
            (MAP.replace('["oars.py"]', "[]"), "non-empty list of globs"),
            (MAP.replace("id: stone-paths", "id: Stone Paths"), "kebab-case"),
            (MAP.replace("version: 1", "version: 2"), "version"),
            (MAP + "# reach " + "9876" * 3 + "\n", "account ID"),
            (MAP + "# ask owl@example.invalid\n", "e-mail"),
        ]
        for text, needle in bad:
            with self.subTest(needle=needle):
                with self.assertRaises(d.MapError) as ctx:
                    d.parse_map(text)
                self.assertIn(needle, str(ctx.exception))

    def test_root_pages_must_exist_when_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs/harbour.md").write_text("# H\n", encoding="utf-8")
            with self.assertRaises(d.MapError) as ctx:
                d.parse_map(MAP, root)
            self.assertIn("docs/oars.md", str(ctx.exception))
            (root / "docs/oars.md").write_text("# O\n", encoding="utf-8")
            self.assertEqual(len(d.parse_map(MAP, root)), 3)   # app-repo pages are not checked here

    def test_committed_map_is_valid(self):
        loaded = d.load_map(check_pages=True)
        self.assertGreater(len(loaded), 20)
        self.assertEqual(len({e.id for e in loaded}), len(loaded))


class ImpactTest(unittest.TestCase):
    def test_hits_only_for_the_repo_and_matching_files(self):
        hits = d.impact(entries(), "Repo-River", ["boats/hull.py", "docks/main.tf", "README.md"])
        self.assertEqual([(h.entry.id, h.files, h.open) for h in hits],
                         [("river-boats", ["boats/hull.py", "docks/main.tf"], True)])
        self.assertEqual(d.impact(entries(), "Repo-Sky", ["boats/hull.py"]), [])

    def test_a_page_of_the_same_repo_touches_the_entry(self):
        hits = d.impact(entries(), "Repo-River", ["boats/hull.py", "CONTEXT.md"])
        self.assertEqual(hits[0].touched, ["Repo-River:CONTEXT.md"])
        self.assertFalse(hits[0].open)

    def test_root_pages_count_in_a_root_change_only(self):
        root_map = MAP.replace("repo: Repo-Stone", "repo: AA-Ecosys")
        hits = d.impact(entries(root_map), "AA-Ecosys", ["paths/a/route.ts", "docs/harbour.md"])
        self.assertEqual(hits[0].touched, ["docs/harbour.md"])
        hits = d.impact(entries(), "Repo-Stone", ["paths/a/route.ts", "docs/harbour.md"])
        self.assertTrue(hits[0].open)      # a file named docs/harbour.md in Repo-Stone is not the root page

    def test_leading_dot_slash_is_ignored(self):
        self.assertEqual(len(d.impact(entries(), "Repo-River", ["./oars.py"])), 1)

    def test_acknowledgement_forms(self):
        self.assertEqual(d.acknowledgement("x\nDocs-impact: none: renamed a variable only\n"),
                         "none: renamed a variable only")
        self.assertEqual(d.acknowledgement("docs-impact: `updated-here`"), "updated-here")
        link = "https://github.com/Org-x/AA-Ecosys/pull/12"
        self.assertEqual(d.acknowledgement(f"Docs-Impact: {link}"), link)
        for body in ("Docs-impact: later", "Docs-impact: none:", "nothing", ""):
            self.assertIsNone(d.acknowledgement(body))


class ReportTest(unittest.TestCase):
    def test_comment_lists_open_entries_with_links(self):
        hits = d.impact(entries(), "Repo-River", ["boats/a.py", "boats/b.py", "boats/c.py", "boats/d.py", "oars.py"])
        text = d.comment_body(hits, "Repo-River", None)
        self.assertTrue(text.startswith(d.MARKER))
        self.assertIn("`river-boats` (the boats)", text)
        self.assertIn("(+1)", text)
        self.assertIn(f"[docs/harbour.md](https://github.com/{d.ORG}/AA-Ecosys/blob/master/docs/harbour.md)", text)
        self.assertIn(f"[Repo-River:CONTEXT.md](https://github.com/{d.ORG}/Repo-River/blob/main/CONTEXT.md)", text)
        self.assertIn("never blocks a merge", text)
        self.assertNotIn("Acknowledged", text)

    def test_comment_when_nothing_is_open(self):
        hits = d.impact(entries(), "Repo-River", ["oars.py", "docs/oars.md"])
        self.assertIn("No docs impact left", d.comment_body([], "Repo-River", None))
        self.assertIn("No docs impact left", d.comment_body([h for h in hits if not h.open], "Repo-River", None))

    def test_annotations_are_notices_once_acknowledged(self):
        hits = d.impact(entries(), "Repo-River", ["oars.py"])
        self.assertTrue(d.annotations(hits, None)[0].startswith("::warning "))
        self.assertTrue(d.annotations(hits, "none: test only")[0].startswith("::notice "))


class MainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.map = self.dir / "doc-map.yaml"
        self.map.write_text(MAP, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def run_main(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = d.main(list(argv))
        return code, out.getvalue()

    def test_check_never_fails_unless_strict(self):
        code, out = self.run_main("check", "--map", str(self.map), "--repo", "Repo-River", "--files", "oars.py",
                                  "--github")
        self.assertEqual(code, 0)
        self.assertIn("::warning title=Docs impact (river-oars)::", out)
        code, _ = self.run_main("check", "--map", str(self.map), "--repo", "Repo-River", "--files", "oars.py",
                                "--strict")
        self.assertEqual(code, 1)

    def test_broken_map_warns_and_passes(self):
        self.map.write_text("version: 7\n", encoding="utf-8")
        code, out = self.run_main("check", "--map", str(self.map), "--repo", "Repo-River", "--files", "oars.py")
        self.assertEqual(code, 0)
        self.assertIn("::warning", out)
        code, out = self.run_main("validate", "--map", str(self.map))
        self.assertEqual(code, 1)

    def test_files_from_comment_out_and_json(self):
        listing = self.dir / "files.txt"
        listing.write_text("boats/a.py\n\n", encoding="utf-8")
        comment = self.dir / "comment.md"
        body = self.dir / "body.md"
        body.write_text("Docs-impact: none: test\n", encoding="utf-8")
        code, out = self.run_main("check", "--map", str(self.map), "--repo", "Repo-River", "--files-from",
                                  str(listing), "--comment-out", str(comment), "--pr-body-file", str(body), "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]["id"], "river-boats")
        self.assertIn("Acknowledged in the PR body: `Docs-impact: none: test`", comment.read_text(encoding="utf-8"))


    def _git(self, repo: Path, *args: str) -> str:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                              env=env).stdout.strip()

    def test_base_reads_another_checkout_up_to_head_ref(self):
        """Session close: the root worktree diffs an app checkout from its first main commit to origin/main."""
        repo = self.dir / "river"
        repo.mkdir()
        self._git(repo, "init", "-q", "-b", "main")
        (repo / "readme.txt").write_text("a\n", encoding="utf-8")
        self._git(repo, "add", ".")
        self._git(repo, "commit", "-q", "-m", "start")
        base = self._git(repo, "rev-parse", "HEAD")
        self._git(repo, "checkout", "-q", "-b", "merged")
        (repo / "oars.py").write_text("x = 1\n", encoding="utf-8")
        self._git(repo, "add", ".")
        self._git(repo, "commit", "-q", "-m", "oars")
        self._git(repo, "checkout", "-q", "main")  # the checkout itself still sits on the old head
        code, out = self.run_main("check", "--map", str(self.map), "--repo", "Repo-River", "--base", base,
                                  "--repo-dir", str(repo), "--head", "merged")
        self.assertEqual(code, 0)
        self.assertIn("OPEN    river-oars", out)
        code, out = self.run_main("check", "--map", str(self.map), "--repo", "Repo-River", "--base", base,
                                  "--repo-dir", str(repo))
        self.assertIn("no mapped code changed", out)

    def test_unknown_base_warns_instead_of_crashing(self):
        repo = self.dir / "empty"
        repo.mkdir()
        self._git(repo, "init", "-q", "-b", "main")
        code, out = self.run_main("check", "--map", str(self.map), "--repo", "Repo-River", "--base", "0" * 40,
                                  "--repo-dir", str(repo))
        self.assertEqual(code, 0)
        self.assertIn("::warning title=Docs impact::git diff", out)


FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
log = os.environ["FAKE_GH_LOG"]
args = sys.argv[1:]
stdin = sys.stdin.read() if "--input" in args else ""
with open(log, "a") as fh:
    fh.write(json.dumps({"args": args, "stdin": stdin}) + "\\n")
if os.environ.get("FAKE_GH_FAIL") and "-X" in args:
    sys.stderr.write("HTTP 403: Resource not accessible by integration\\n")
    sys.exit(1)
path = next(a for a in args if a.startswith("repos/"))
if path.endswith("/files"):
    print(os.environ.get("FAKE_GH_FILES", ""))
elif path.endswith("/comments") and "-X" not in args:
    print(os.environ.get("FAKE_GH_EXISTING", ""))
"""


class GithubPrTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        gh = self.dir / "bin" / "gh"
        gh.parent.mkdir()
        gh.write_text(FAKE_GH, encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
        self.log = self.dir / "gh.log"
        self.summary = self.dir / "summary.md"
        self.env = {"PATH": f"{gh.parent}{os.pathsep}{os.environ['PATH']}", "FAKE_GH_LOG": str(self.log),
                    "REPO": "Org-x/Repo-River", "PR": "7", "PR_BODY": "", "GITHUB_STEP_SUMMARY": str(self.summary)}

    def tearDown(self):
        self._tmp.cleanup()

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def run_pr(self, **env) -> tuple[int, str]:
        out = io.StringIO()
        with mock.patch.dict(os.environ, {**self.env, **env}, clear=False), contextlib.redirect_stdout(out):
            code = d.github_pr(entries(), None)
        return code, out.getvalue()

    def test_open_entry_creates_the_comment(self):
        code, out = self.run_pr(FAKE_GH_FILES="boats/a.py\nREADME.md")
        self.assertEqual(code, 0)
        posts = [c for c in self.calls() if "POST" in c["args"]]
        self.assertEqual(len(posts), 1)
        self.assertIn("repos/Org-x/Repo-River/issues/7/comments", posts[0]["args"])
        self.assertTrue(json.loads(posts[0]["stdin"])["body"].startswith(d.MARKER))
        self.assertIn("::warning title=Docs impact (river-boats)", out)
        self.assertIn("Docs impact (warning only)", self.summary.read_text(encoding="utf-8"))

    def test_existing_comment_is_updated_even_when_resolved(self):
        code, _ = self.run_pr(FAKE_GH_FILES="README.md", FAKE_GH_EXISTING="555")
        self.assertEqual(code, 0)
        patches = [c for c in self.calls() if "PATCH" in c["args"]]
        self.assertEqual(len(patches), 1)
        self.assertIn("repos/Org-x/Repo-River/issues/comments/555", patches[0]["args"])
        self.assertIn("No docs impact left", json.loads(patches[0]["stdin"])["body"])

    def test_nothing_mapped_posts_nothing(self):
        self.run_pr(FAKE_GH_FILES="README.md")
        self.assertFalse([c for c in self.calls() if "-X" in c["args"]])

    def test_a_refused_comment_is_a_warning_not_a_failure(self):
        code, out = self.run_pr(FAKE_GH_FILES="oars.py", FAKE_GH_FAIL="1")
        self.assertEqual(code, 0)
        self.assertIn("could not post the PR comment", out)

    def test_not_a_pr_and_broken_map_pass(self):
        out = io.StringIO()
        with mock.patch.dict(os.environ, {**self.env, "PR": ""}), contextlib.redirect_stdout(out):
            self.assertEqual(d.github_pr(entries(), None), 0)
        with contextlib.redirect_stdout(out):
            self.assertEqual(d.github_pr(None, "bad map"), 0)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
