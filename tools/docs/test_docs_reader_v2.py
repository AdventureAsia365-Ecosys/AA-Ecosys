"""Unit tests for the docs reader v2 fields and the search index (AA-1133): build_docs_reader.py rules 11-12 and
docs_search_index.py.

Run: python -m unittest tools/docs/test_docs_reader_v2.py  (needs PyYAML, tools/docs/requirements.txt)
Fixtures use invented pages and places only.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_docs_reader as b  # noqa: E402
import docs_search_index as si  # noqa: E402

# One test runs git in a temporary repo: drop git's repo-local variables for this whole test process, like
# tools/github/ship_fakes.py (`git rev-parse --local-env-vars`; tools/github/test_git_env_isolation.py).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)


def _page(page_id: str, title: str = "A page", extra: str = "", body: str = "Body.\n", owner: str = "nghiep") -> str:
    return (
        "---\n"
        f"id: {page_id}\n"
        f"title: {title}\n"
        "type: how-to\n"
        "status: active\n"
        f"owner: {owner}\n"
        "audience: [staff]\n"
        "last_reviewed: 2026-11-01\n"
        f"{extra}"
        "---\n\n"
        f"# {title}\n\n{body}"
    )


class Tree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "repo"
        self.out = Path(self._tmp.name) / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def build(self, **kw) -> dict:
        return b.build(self.out, root=self.root, sha="abc123", ref="master", **kw)

    def entry(self, manifest: dict, path: str) -> dict:
        return next(p for p in manifest["pages"] if p["path"] == path)


class NavTest(Tree):
    def test_nav_derived_from_folder(self):
        self.write("docs/ops/runbooks/x.md", _page("OPS-90"))
        self.write("docs/legal/y.md", _page("LEG-90"))
        self.write("docs/guides/z.md", _page("GUIDE-90"))
        self.write("docs/architecture/erd/e.md", _page("ARCH-90"))
        self.write("docs/architecture/w.md", _page("ARCH-91"))
        self.write("docs/onboarding.md", _page("CAT-90"))
        self.write("docs/misc/q.md", _page("REF-90"))
        m = self.build()
        got = {p["path"]: (p["nav"], p["nav_derived"]) for p in m["pages"]}
        self.assertEqual(got["docs/ops/runbooks/x.md"], ("operations", True))
        self.assertEqual(got["docs/legal/y.md"], ("legal-security", True))
        self.assertEqual(got["docs/guides/z.md"], ("guides", True))
        self.assertEqual(got["docs/architecture/erd/e.md"], ("reference", True))
        self.assertEqual(got["docs/architecture/w.md"], ("architecture", True))
        self.assertEqual(got["docs/onboarding.md"], ("start", True))
        self.assertEqual(got["docs/misc/q.md"], ("reference", True))
        self.assertEqual(m["counts"]["nav_derived"], 7)

    def test_front_matter_nav_wins_and_bad_values_fall_back(self):
        self.write("docs/ops/a.md", _page("OPS-91", extra="nav: start\nnav_order: 3\n"))
        self.write("docs/ops/b.md", _page("OPS-92", extra="nav: nowhere\nnav_order: 5000\n"))
        m = self.build()
        a, bb = self.entry(m, "docs/ops/a.md"), self.entry(m, "docs/ops/b.md")
        self.assertEqual((a["nav"], a["nav_derived"], a["nav_order"]), ("start", False, 3))
        self.assertEqual((bb["nav"], bb["nav_derived"], bb["nav_order"]), ("operations", True, None))

    def test_every_default_group_is_a_schema_value(self):
        schema = json.loads((Path(__file__).resolve().parents[2] / "docs/templates/frontmatter.schema.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(tuple(schema["properties"]["nav"]["enum"]), b.NAV_GROUPS)
        self.assertTrue({g for _p, g in b.NAV_DEFAULTS} <= set(b.NAV_GROUPS))


class MetaTest(Tree):
    def test_owner_slug_is_the_role(self):
        self.write("docs/x.md", _page("CAT-91"))
        self.write("docs/y.md", _page("CAT-92", owner="business-owner"))
        m = self.build()
        self.assertEqual(self.entry(m, "docs/x.md")["owner"], "tech-lead")
        self.assertEqual(self.entry(m, "docs/y.md")["owner"], "business-owner")

    def test_adr_status_loses_trailing_stars(self):
        self.write("docs/adr/0099-invented.md", "# ADR 0099: An invented choice\n\n- **Status:** **Accepted** (amended)\n")
        m = self.build()
        e = self.entry(m, "docs/adr/0099-invented.md")
        self.assertEqual(e["status"], "accepted")
        self.assertEqual(e["owner"], "tech-lead")

    def test_known_issue_is_passed_redacted_and_trimmed(self):
        fake = "0" * 12
        self.write("docs/guides/k.md", _page("GUIDE-91", extra=f"known_issue: 'Steps   for account {fake} are old.'\n"))
        self.write("docs/guides/n.md", _page("GUIDE-92"))
        m = self.build()
        note = self.entry(m, "docs/guides/k.md")["known_issue"]
        self.assertNotIn(fake, note)
        self.assertTrue(note.startswith("Steps for account [redacted"))
        self.assertIsNone(self.entry(m, "docs/guides/n.md")["known_issue"])

    def test_github_source_only_when_public(self):
        self.write("docs/x.md", _page("CAT-93"))
        self.assertIsNone(self.build()["source"]["github"])
        self.assertIsNone(self.build(github_repo="Org-x/Repo-y", visibility="private")["source"]["github"])
        self.assertIsNone(self.build(github_repo="not a repo", visibility="public")["source"]["github"])
        self.assertEqual(self.build(github_repo="Org-x/Repo-y", visibility="public")["source"]["github"], "Org-x/Repo-y")

    def test_last_changed_is_null_outside_git(self):
        self.write("docs/x.md", _page("CAT-94"))
        self.assertIsNone(self.entry(self.build(), "docs/x.md")["last_changed"])

    def test_last_changed_is_each_files_own_commit(self):
        self.write("docs/x.md", _page("CAT-95"))
        self.write("docs/y.md", _page("CAT-96"))

        def git(*args: str) -> str:
            return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True,
                                  text=True).stdout.strip()

        git("init", "-q")
        git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "add", ".")
        git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "one")
        first = git("rev-parse", "HEAD")
        self.write("docs/y.md", _page("CAT-96", body="Changed.\n"))
        git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-am", "two")
        second = git("rev-parse", "HEAD")
        m = self.build()
        self.assertEqual(self.entry(m, "docs/x.md")["last_changed"]["sha"], first)
        self.assertEqual(self.entry(m, "docs/y.md")["last_changed"]["sha"], second)
        self.assertRegex(self.entry(m, "docs/y.md")["last_changed"]["date"], r"^\d{4}-\d{2}-\d{2}T")


class SlugTest(unittest.TestCase):
    """Same cases as the reader (frontend lib/docsReader.test.mjs slugify / Slugger / headingText)."""

    def test_slugify(self):
        self.assertEqual(si.slugify("Hello, World!"), "hello-world")
        self.assertEqual(si.slugify("6.3 Rollout and rollback"), "63-rollout-and-rollback")
        self.assertEqual(si.slugify("Đà Lạt trip"), "đà-lạt-trip")
        self.assertEqual(si.slugify("a  b"), "a--b")
        self.assertEqual(si.slugify("snake_case-x"), "snake_case-x")

    def test_repeats_get_suffixes(self):
        s = si.Slugger()
        self.assertEqual([s.slug("Steps"), s.slug("Steps"), s.slug("Steps"), s.slug("!!")], ["steps", "steps-1", "steps-2",
                                                                                            "section"])

    def test_heading_text(self):
        self.assertEqual(si.heading_text("Use `x` and [the guide](a.md) **now**"), "Use x and the guide now")


class SectionsTest(unittest.TestCase):
    def test_sections_skip_fenced_headings_and_mermaid(self):
        body = ("Intro line.\n\n## First step\n\nRun it.\n\n```bash\n# not a heading\necho hi\n```\n\n"
                "```mermaid\ngraph TD; Secretnode-->B\n```\n\n### Check\n\nLooks [good](x.md).\n\n## First step\n")
        rows = si.sections(body, "Invented page")
        self.assertEqual([(h, s) for h, s, _t in rows],
                         [("Invented page", ""), ("First step", "first-step"), ("Check", "check"),
                          ("First step", "first-step-1")])
        self.assertIn("echo hi", rows[1][2])
        self.assertIn("not a heading", rows[1][2])
        self.assertNotIn("Secretnode", " ".join(t for _h, _s, t in rows))
        self.assertEqual(rows[2][2], "Looks good.")

    def test_page_without_intro_has_no_empty_top_section(self):
        rows = si.sections("## Only\n\nText.\n", "T")
        self.assertEqual([s for _h, s, _t in rows], ["only"])


class SearchIndexTest(Tree):
    def test_index_in_bundle_with_access_and_hash(self):
        self.write("docs/guides/a.md", _page("GUIDE-93", title="Lantern market guide",
                                             body="## Opening hours\n\nThe lantern stalls open at dusk.\n"))
        self.write("docs/legal/s.md", _page("SEC-93", title="Private lantern notes",
                                            body="## Owner part\n\nLantern ledger for owners.\n"))
        m = self.build()
        idx = self.out / "search" / "index.sqlite"
        self.assertTrue(idx.exists())
        self.assertEqual(m["search"]["key"], "search/index.sqlite")
        self.assertEqual(m["search"]["bytes"], idx.stat().st_size)
        import hashlib
        self.assertEqual(m["search"]["sha256"], hashlib.sha256(idx.read_bytes()).hexdigest())
        conn = sqlite3.connect(f"file:{idx}?mode=ro", uri=True)
        rows = conn.execute("SELECT path, access, slug FROM sections WHERE sections MATCH ? ORDER BY bm25(sections)",
                            ('"lantern"*',)).fetchall()
        conn.close()
        self.assertIn(("docs/guides/a.md", "staff", "opening-hours"), rows)
        self.assertIn(("docs/legal/s.md", "owner", "owner-part"), rows)

    def test_accents_fold(self):
        self.write("docs/guides/v.md", _page("GUIDE-94", title="Phố cổ guide", body="## Chợ đêm\n\nĐèn lồng.\n"))
        self.build()
        conn = sqlite3.connect(f"file:{self.out / 'search' / 'index.sqlite'}?mode=ro", uri=True)
        hits = [conn.execute("SELECT slug FROM sections WHERE sections MATCH ?", (q,)).fetchall()
                for q in ('"cho"* "dem"*', '"chợ"* "đêm"*', '"den"* "long"*')]
        conn.close()
        self.assertEqual(hits, [[("chợ-đêm",)]] * 3)
        self.assertEqual(si.folded("a", "b"), "")
        self.assertEqual(si.folded("Đèn", "đêm"), "Dèn dêm")


if __name__ == "__main__":
    unittest.main()
