"""Unit tests for build_docs_reader.py (AA-898): the publication rule, redaction and the guard.

Run: python -m unittest discover -s tools/docs -p 'test_*.py'  (needs PyYAML, tools/docs/requirements.txt)
Fixture IDs are fake (zeros and invented hex), never a real account.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_docs_reader as b  # noqa: E402

FAKE_ACCOUNT = "000000000000"


def _page(page_id: str, title: str = "A page", status: str = "active", extra: str = "", body: str = "Body.\n") -> str:
    return (
        "---\n"
        f"id: {page_id}\n"
        f"title: {title}\n"
        "type: how-to\n"
        f"status: {status}\n"
        "owner: nghiep\n"
        "audience: [owner, engineer]\n"
        "last_reviewed: 2026-10-28\n"
        f"{extra}"
        "---\n\n"
        f"# {title}\n\n{body}"
    )


class TreeCase(unittest.TestCase):
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

    def build(self) -> dict:
        return b.build(self.out, root=self.root, sha="abc123", ref="master")

    def paths(self, manifest: dict) -> set[str]:
        return {p["path"] for p in manifest["pages"]}


class PublicationRule(TreeCase):
    def test_catalog_page_published_with_front_matter_stripped(self):
        self.write("docs/ops/runbook.md", _page("OPS-01", "Run it"))
        m = self.build()
        self.assertEqual(self.paths(m), {"docs/ops/runbook.md"})
        entry = m["pages"][0]
        self.assertEqual(entry["key"], "pages/AA-Ecosys/docs/ops/runbook.md")
        self.assertEqual(entry["access"], "staff")
        self.assertEqual(entry["audience"], ["owner", "engineer"])
        self.assertEqual(entry["last_reviewed"], "2026-10-28")
        body = (self.out / entry["key"]).read_text(encoding="utf-8")
        self.assertTrue(body.startswith("# Run it"))
        self.assertNotIn("last_reviewed", body)
        self.assertEqual(m["source"], {"repo": "AA-Ecosys", "sha": "abc123", "ref": "master"})
        self.assertEqual(m["format"], 1)

    def test_never_prefixes_are_not_published_even_with_front_matter(self):
        for rel in ("docs/security/baseline.md", "docs/audits/2026-x/README.md", "docs/sessions/s.md",
                    "docs/templates/how-to.md", "docs/implementation-notes/AA-1.md", "docs/backlog/README.md",
                    "docs/research/r.md", "docs/calib/c.md", "docs/backups/dump.md", "docs/archive/old.md",
                    "docs/linear-export/AA-1.md"):
            self.write(rel, _page("OPS-09"))
        self.write("docs/guide.md", _page("GUIDE-03"))
        m = self.build()
        self.assertEqual(self.paths(m), {"docs/guide.md"})
        self.assertEqual(m["counts"]["skipped"], 11)
        self.assertNotIn("security", json.dumps(m), "skipped pages are counted, never named")

    def test_page_without_catalog_front_matter_is_skipped(self):
        self.write("docs/notes.md", "# Just notes\n")
        self.write("docs/half.md", "---\ntitle: No id\n---\n# Half\n")
        self.write("docs/broken.md", "---\nid: OPS-01\n")
        self.assertEqual(self.paths(self.build()), set())

    def test_archived_is_skipped(self):
        self.write("docs/old.md", _page("OPS-02", status="archived"))
        self.assertEqual(self.paths(self.build()), set())

    def test_adr_published_from_h1_and_status_line(self):
        self.write("docs/adr/0003a-per-owner-job-tables.md",
                   "# ADR 0003a: Per-owner job tables\n\n- **Status:** Accepted (01/10/2026, S200)\n\nText.\n")
        self.write("docs/adr/README.md", "# ADR index\n")
        m = self.build()
        self.assertEqual(self.paths(m), {"docs/adr/0003a-per-owner-job-tables.md"})
        e = m["pages"][0]
        self.assertEqual((e["id"], e["type"], e["status"]), ("ADR-0003A", "adr", "accepted"))
        self.assertEqual(e["title"], "ADR 0003a: Per-owner job tables")

    def test_owner_only_tier(self):
        self.write("docs/legal/register.md", _page("SEC-04"))
        self.write("docs/ops/runbooks/secret-rotation.md", _page("SEC-02-rotation"))
        self.write("docs/generated/inventory.md", _page("ARCH-03"))
        self.write("docs/generated/iam-roles.md", _page("ARCH-04-tables"))
        self.write("docs/ecosystem-architecture.md", _page("ARCH-01"))
        m = self.build()
        access = {p["path"]: p["access"] for p in m["pages"]}
        self.assertEqual(access["docs/legal/register.md"], "owner")
        self.assertEqual(access["docs/ops/runbooks/secret-rotation.md"], "owner")
        self.assertEqual(access["docs/generated/inventory.md"], "owner")
        self.assertEqual(access["docs/generated/iam-roles.md"], "owner")
        self.assertEqual(access["docs/ecosystem-architecture.md"], "staff")
        self.assertEqual(m["counts"]["owner_only"], 4)

    def test_output_folder_is_replaced(self):
        self.write("docs/a.md", _page("OPS-01"))
        self.build()
        (self.root / "docs/a.md").unlink()
        self.write("docs/b.md", _page("OPS-02"))
        self.build()
        self.assertFalse((self.out / "pages/AA-Ecosys/docs/a.md").exists(), "a removed page must not linger")
        self.assertTrue((self.out / "pages/AA-Ecosys/docs/b.md").exists())

    def test_translation_entry_and_english_entry_are_linked(self):
        self.write("docs/guides/ceo.md", _page("GUIDE-04", "CEO guide"))
        self.write("docs/guides/ceo.vi.md", _page("GUIDE-04", "Huong dan CEO",
                                                  extra="lang: vi\ntranslation_of: docs/guides/ceo.md\n"))
        self.write("docs/legal/register.md", _page("SEC-04", "Register"))
        self.write("docs/legal/register.vi.md", _page("SEC-04", "So dang ky",
                                                      extra="lang: vi\ntranslation_of: docs/legal/register.md\n"))
        m = self.build()
        by = {p["path"]: p for p in m["pages"]}
        en, vi = by["docs/guides/ceo.md"], by["docs/guides/ceo.vi.md"]
        self.assertEqual((en["lang"], en["translation_of"]), ("en", None))
        self.assertEqual(en["translations"], [{"lang": "vi", "path": "docs/guides/ceo.vi.md",
                                               "key": "pages/AA-Ecosys/docs/guides/ceo.vi.md",
                                               "title": "Huong dan CEO"}])
        self.assertEqual((vi["lang"], vi["translation_of"], vi["translations"]), ("vi", "docs/guides/ceo.md", []))
        self.assertEqual(vi["id"], "GUIDE-04")
        self.assertEqual(by["docs/legal/register.vi.md"]["access"], "owner", "a translation keeps the owner tier")
        self.assertEqual(m["counts"]["translations"], 2)
        self.assertTrue((self.out / vi["key"]).exists())

    def test_translation_without_published_english_page_is_skipped(self):
        self.write("docs/old.md", _page("OPS-02", status="archived"))
        self.write("docs/old.vi.md", _page("OPS-02", extra="lang: vi\ntranslation_of: docs/old.md\n"))
        self.write("docs/lonely.vi.md", _page("OPS-03", extra="lang: vi\ntranslation_of: docs/lonely.md\n"))
        self.write("docs/a.md", _page("OPS-04"))
        self.write("docs/a.vi.md", _page("OPS-05", extra="lang: vi\ntranslation_of: docs/a.md\n"))
        m = self.build()
        self.assertEqual(self.paths(m), {"docs/a.md"})
        self.assertEqual(m["pages"][0]["translations"], [])
        self.assertEqual(m["counts"]["skipped"], 4)

    def test_adr_and_plain_pages_are_english(self):
        self.write("docs/adr/0001-x.md", "# ADR 0001: X\n\n- **Status:** Accepted\n")
        self.write("docs/b.md", _page("OPS-01"))
        m = self.build()
        self.assertEqual({(p["lang"], p["translation_of"]) for p in m["pages"]}, {("en", None)})


class Redaction(TreeCase):
    def test_redacts_ids_in_body_title_and_description(self):
        body = (
            f"Account {FAKE_ACCOUNT}, bucket aa-cis-bronze-{FAKE_ACCOUNT}, "
            f"ARN arn:aws:iam::{FAKE_ACCOUNT}:role/x, sg-0abc1234, vpc-0123456789abcdef0, "
            "pool us-west-1_AbCdEfGhI, host abcdefghij.execute-api.us-west-1.amazonaws.com, "
            "key AKIAABCDEFGHIJKLMNOP.\n"
        )
        self.write("docs/x.md", _page("OPS-01", title=f"Account {FAKE_ACCOUNT}",
                                      extra=f"description: Lives in {FAKE_ACCOUNT}\n", body=body))
        m = self.build()
        e = m["pages"][0]
        text = (self.out / e["key"]).read_text(encoding="utf-8")
        for leaked in (FAKE_ACCOUNT, "sg-0abc1234", "vpc-0123456789abcdef0", "us-west-1_AbCdEfGhI",
                       "abcdefghij.execute-api", "AKIAABCDEFGHIJKLMNOP"):
            self.assertNotIn(leaked, text)
        for marker in ("[redacted-account-id]", "[redacted-vpc-id]", "[redacted-user-pool-id]",
                       "[redacted-apigw-id].execute-api", "[redacted-access-key]"):
            self.assertIn(marker, text)
        self.assertIn("aa-cis-bronze-[redacted-account-id]", text)
        self.assertIn("arn:aws:iam::[redacted-account-id]:role/x", text)
        self.assertNotIn(FAKE_ACCOUNT, json.dumps(m))
        self.assertGreaterEqual(e["redactions"], 9)

    def test_other_digit_runs_are_kept(self):
        self.write("docs/x.md", _page("OPS-01", body="Year 2026, phone 0901234567, big 1234567890123.\n"))
        text = (self.out / self.build()["pages"][0]["key"]).read_text(encoding="utf-8")
        self.assertIn("0901234567", text)
        self.assertIn("1234567890123", text, "13 digits is not an account ID")

    def test_guard_stops_the_build(self):
        original = b.REDACTIONS
        try:
            b.REDACTIONS = []   # a redaction that silently stopped working
            self.write("docs/x.md", _page("OPS-01", body=f"Account {FAKE_ACCOUNT}\n"))
            with self.assertRaises(SystemExit):
                self.build()
            self.assertFalse((self.out / "manifest.json").exists(), "nothing is written when the guard fails")
        finally:
            b.REDACTIONS = original

    def test_markers_do_not_trip_the_guard(self):
        self.assertEqual(b.guard_hits("[redacted-account-id] [redacted-vpc-id] [redacted-apigw-id].execute-api."),
                         [])


# A 1x1 PNG, base64 (rule 9 fixtures). Its payload contains a 12-digit run on purpose: digits inside an inline PNG are
# not text and must never trip the account-ID guard.
PNG_URI = ("data:image/png;base64,iVBORw0KGgo000000000000AAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwAD"
           "hgGAWjR9awAAAABJRU5ErkJggg==")


def _svg(inner: str = "", head: str = '<?xml version="1.0" encoding="UTF-8"?>\n') -> str:
    return (f'{head}<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="10" height="10"><g id="a"><text>Diagram</text>'
            f'<image xlink:href="{PNG_URI}" width="1" height="1"/>{inner}</g></svg>\n')


class SvgAssets(TreeCase):
    def test_svg_published_byte_for_byte_and_listed(self):
        svg = _svg('<use href="#a"/>')
        self.write("docs/architecture/diagrams/x.svg", svg)
        self.write("docs/x.md", _page("OPS-01", body="![Diagram](architecture/diagrams/x.svg)\n"))
        m = self.build()
        self.assertEqual(m["counts"]["assets"], 1)
        (asset,) = m["assets"]
        self.assertEqual(asset["key"], "assets/AA-Ecosys/docs/architecture/diagrams/x.svg")
        self.assertEqual(asset["type"], "image/svg+xml")
        self.assertEqual(asset["access"], "staff")
        self.assertEqual((self.out / asset["key"]).read_text(encoding="utf-8"), svg, "never redacted or rewritten")
        self.assertEqual(asset["bytes"], len(svg.encode("utf-8")))

    def test_never_folders_and_other_files_are_not_assets(self):
        self.write("docs/audits/x/a.svg", _svg())
        self.write("docs/security/b.svg", _svg())
        self.write("docs/x.png", "not an svg")
        self.write("docs/x.md", _page("OPS-01"))
        m = self.build()
        self.assertEqual(m["assets"], [])

    def test_oversize_svg_is_skipped(self):
        self.write("docs/big.svg", _svg("<!--" + "x" * (b.MAX_ASSET_BYTES + 1) + "-->"))
        self.write("docs/x.md", _page("OPS-01"))
        self.assertEqual(self.build()["assets"], [])

    def test_unsafe_svgs_fail_the_build(self):
        bad = {
            "script": _svg("<script>alert(1)</script>"),
            "foreign": _svg("<foreignObject><div>x</div></foreignObject>"),
            "handler": _svg('<rect onload="x()"/>'),
            "js-url": _svg('<a href="javascript:x()"><text>x</text></a>'),
            "remote-image": _svg('<image href="https://example.com/x.png"/>'),
            "file-image": _svg('<image xlink:href="/home/someone/icon.png"/>'),
            "css-url": _svg('<style>g{fill:url(https://example.com/x)}</style>'),
            "import": _svg("<style>@import 'x.css';</style>"),
            "entity": _svg(head='<?xml version="1.0"?>\n<!DOCTYPE svg [<!ENTITY x "y">]>\n'),
            "animate": _svg('<animate attributeName="href" to="javascript:x()"/>'),
            "account": _svg(f"<text>role in {FAKE_ACCOUNT}</text>"),
            "not-svg": "<html><body>x</body></html>",
        }
        for name, text in bad.items():
            with self.subTest(name):
                problems = b.svg_problems(text)
                self.assertTrue(problems, f"{name} should be refused")
        self.write("docs/x.md", _page("OPS-01"))
        self.write("docs/bad.svg", bad["script"])
        with self.assertRaises(SystemExit):
            self.build()
        self.assertFalse((self.out / "manifest.json").exists(), "nothing is written when an SVG is refused")

    def test_prefix_and_char_reference_bypasses_are_refused(self):
        """The parsed check (svg_tree_problems) catches what the raw-text regexes miss."""
        xhtml = 'xmlns:h="http://www.w3.org/1999/xhtml"'
        bad = {
            "svg-prefixed script": _svg('<s:script xmlns:s="http://www.w3.org/2000/svg">x()</s:script>'),
            "xhtml script": _svg(f'<h:script {xhtml}>x()</h:script>'),
            "xhtml iframe": _svg(f'<h:iframe {xhtml} src="https://example.com/"/>'),
            "prefixed set": _svg('<s:set xmlns:s="http://www.w3.org/2000/svg" attributeName="href" to="#a"/>'),
            "prefixed xlink use": _svg('<use xmlns:x="http://www.w3.org/1999/xlink" x:href="https://e.example/a#p"/>'),
            "char-ref url()": _svg('<rect style="fill:u&#114;l(https://example.com/x)"/>'),
            "char-ref @import": _svg("<style>&#64;import 'x.css';</style>"),
            "css escape": _svg("<style>g{fill:u\\72l(https://example.com/x)}</style>"),
            "xml-stylesheet": _svg('<?xml-stylesheet type="text/css" href="#a"?>'),
            "xml:base": _svg('<g xml:base="https://example.com/"/>'),
            "char-ref account": _svg(f"<text>{FAKE_ACCOUNT[:5]}&#{ord(FAKE_ACCOUNT[5])};{FAKE_ACCOUNT[6:]}</text>"),
        }
        for name, text in bad.items():
            with self.subTest(name):
                self.assertTrue(b.svg_problems(text), f"{name} should be refused")

    def test_digits_inside_inline_png_are_not_an_account_id(self):
        self.assertEqual(b.svg_problems(_svg('<use href="#a"/>')), [])

    def test_committed_diagrams_pass(self):
        """The real architecture diagrams (AA-697) are publishable as committed."""
        here = Path(__file__).resolve().parents[2] / "docs" / "architecture" / "diagrams"
        svgs = sorted(here.glob("*.svg"))
        self.assertTrue(svgs, "the diagram SVGs are committed")
        for svg in svgs:
            with self.subTest(svg.name):
                self.assertEqual(b.svg_problems(svg.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
