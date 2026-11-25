"""AA-1117 — tools/ops/golive_gate.py: the YAML subset parser, the line rules (dead proof path or anchor, unknown owner
role, open line past due or without owner and due, the go-live date line), the rendered page, and the committed
checklist itself (valid as of its `updated` date, page in sync). Invented paths and titles only; no network.

Run: python3 -m unittest discover -s tools/ops -p 'test_golive_gate.py'
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import golive_gate as gg  # noqa: E402

TODAY = date(2026, 11, 25)


def _gate(**over):
    item = {"id": "GL-01", "kind": "gate", "title": "Widget drill passed", "source": "Invented ADR 9999",
            "proof": [], "refs": [], "owner": "tech lead", "due": "2026-12-15"}
    item.update(over)
    return item


def _date_line(**over):
    item = {"id": "GL-99", "kind": "date", "title": "Go-live date", "source": "Invented", "value": None,
            "owner": "business owner"}
    item.update(over)
    return item


def _doc(*items):
    return {"version": 1, "updated": "2026-11-25", "items": list(items) or [_gate(), _date_line()]}


class _Repo:
    """A throwaway repo root with a few invented files to link."""

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        (root / "docs/drills").mkdir(parents=True)
        (root / "docs/drills/widget.md").write_text(
            "# Widget drill\n\n## 1. Steps, and checks\n\n## Steps\n\n```\n## Not a heading\n```\n", encoding="utf-8")
        (root / "docs/drills/result.json").write_text('{"ok": true}\n', encoding="utf-8")
        return root

    def __exit__(self, *exc):
        self._tmp.cleanup()


class ParserTest(unittest.TestCase):
    def test_subset(self):
        text = (
            "# comment\n"
            "version: 1\n"
            "updated: 2026-11-25   # trailing comment\n"
            "empty:\n"
            "flow: [a, 'b c', \"d\"]\n"
            "none: []\n"
            "items:\n"
            "  - id: GL-01\n"
            "    title: \"A: quoted # not a comment\"\n"
            "    single: 'it''s'\n"
            "    flag: true\n"
            "    proof:\n"
            "      - docs/x.md#a\n"
            "      - https://example.invalid/y\n"
            "  - id: GL-02\n"
            "    nothing: null\n"
            "seq_same_indent:\n"
            "- one\n"
            "- two\n"
        )
        self.assertEqual(gg.parse_yaml(text), {
            "version": 1, "updated": "2026-11-25", "empty": None, "flow": ["a", "b c", "d"], "none": [],
            "items": [
                {"id": "GL-01", "title": "A: quoted # not a comment", "single": "it's", "flag": True,
                 "proof": ["docs/x.md#a", "https://example.invalid/y"]},
                {"id": "GL-02", "nothing": None},
            ],
            "seq_same_indent": ["one", "two"],
        })

    def test_refused_constructs_name_the_line(self):
        cases = {
            "a: b: c\n": "line 1",                  # an unquoted ': ' inside a value
            "a: 1\n\tb: 2\n": "line 2",             # tab indentation
            "a: 1\n   b: 2\n": "line 2",            # stray indentation
            "a: 1\na: 2\n": "line 2",               # duplicate key
            "a: {b: 1}\n": "line 1",                # flow mapping
            "a: |\n  text\n": "line 1",             # block scalar
            "a: [x, , y]\n": "line 1",              # empty flow item
            "a: \"open\n": "line 1",                # unterminated quote
            "---\na: 1\n": "line 1",                # document marker
            "just text\n": "line 1",
        }
        for text, where in cases.items():
            with self.subTest(text=text):
                with self.assertRaises(gg.GateError) as ctx:
                    gg.parse_yaml(text)
                self.assertIn(where, str(ctx.exception))

    def test_matches_pyyaml_on_the_committed_checklist(self):
        try:
            import yaml  # type: ignore
        except ImportError:  # the guard itself needs no PyYAML; docs-lint has it
            self.skipTest("PyYAML not installed")
        text = (gg.REPO_ROOT / gg.CHECKLIST).read_text(encoding="utf-8")
        ours = json.dumps(gg.parse_yaml(text), sort_keys=True, default=str)
        theirs = json.dumps(yaml.safe_load(text), sort_keys=True, default=str)
        self.assertEqual(ours, theirs)


class LinkTest(unittest.TestCase):
    def test_links(self):
        with _Repo() as root:
            ok = ["docs/drills/widget.md", "docs/drills", "docs/drills/widget.md#widget-drill",
                  "docs/drills/widget.md#1-steps-and-checks", "docs/drills/widget.md#steps",
                  "docs/drills/result.json#L1", "https://example.invalid/report"]
            for link in ok:
                with self.subTest(link=link):
                    self.assertIsNone(gg.check_link(link, root))
            bad = {
                "docs/drills/missing.md": "dead path",
                "docs/drills/widget.md#not-a-heading": "no heading",
                "docs/drills/widget.md#no-such": "no heading",
                "docs/drills/result.json#L99": "fewer lines",
                "docs/drills/result.json#ok": "needs a Markdown file",
                "docs/drills#steps": "needs a file",
                "/etc/hostname": "repo-relative",
                "docs/../docs/drills/widget.md": "repo-relative",
                "http://example.invalid/x": "use https",
                "": "empty link",
            }
            for link, needle in bad.items():
                with self.subTest(link=link):
                    self.assertIn(needle, gg.check_link(link, root) or "")

    def test_heading_slugs(self):
        md = "# A `code` title\n## Same\n## Same\n### [Linked](x.md) name!\n```\n# hidden\n```\n"
        self.assertEqual(gg.heading_slugs(md), {"a-code-title", "same", "same-1", "linked-name"})


class EvaluateTest(unittest.TestCase):
    def _errors(self, doc, today=TODAY):
        with _Repo() as root:
            errors, warnings, summary = gg.evaluate(doc, today, root)
        return errors, warnings, summary

    def test_open_line_with_owner_and_future_due_passes(self):
        errors, warnings, summary = self._errors(_doc())
        self.assertEqual(errors, [])
        self.assertTrue(any("not set" in w for w in warnings))
        self.assertEqual(summary, {"lines": 1, "met": 0, "open": 1, "golive_date": None})

    def test_dead_proof_and_ref_paths_fail(self):
        errors, _, _ = self._errors(_doc(_gate(proof=["docs/drills/gone.json"], refs=["docs/nowhere.md"]),
                                         _date_line()))
        self.assertEqual(len([e for e in errors if "dead path" in e]), 2)

    def test_unknown_owner_role_fails(self):
        errors, _, _ = self._errors(_doc(_gate(owner="Jane Doe"), _date_line()))
        self.assertTrue(any("unknown owner role 'Jane Doe'" in e for e in errors), errors)

    def test_past_due_without_proof_fails_and_with_proof_passes(self):
        errors, _, _ = self._errors(_doc(_gate(due="2026-11-24"), _date_line()))
        self.assertTrue(any("has passed with no proof" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(due="2026-11-24", proof=["docs/drills/result.json"]), _date_line()))
        self.assertEqual(errors, [])
        errors, _, _ = self._errors(_doc(_gate(due="2026-11-25"), _date_line()))  # due today is not late
        self.assertEqual(errors, [])

    def test_open_line_needs_owner_and_due(self):
        for over in ({"owner": None}, {"due": None}):
            with self.subTest(over=over):
                errors, _, _ = self._errors(_doc(_gate(**over), _date_line()))
                self.assertTrue(any("needs an owner role and an ISO due date" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(owner=None, due=None, proof=["docs/drills/widget.md"]), _date_line()))
        self.assertEqual(errors, [])
        errors, _, _ = self._errors(_doc(_gate(due="15/12/2026"), _date_line()))
        self.assertTrue(any("due must be an ISO date" in e for e in errors), errors)

    def test_date_line_rules(self):
        errors, _, _ = self._errors(_doc(_gate(), _date_line(owner=None)))
        self.assertTrue(any("needs an owner role" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate()))
        self.assertTrue(any("exactly one go-live date line" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _date_line(), _date_line(id="GL-98")))
        self.assertTrue(any("found 2" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _date_line(value="soon")))
        self.assertTrue(any("value must be an ISO date" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(value="2027-01-01"), _date_line()))
        self.assertTrue(any("value is only for the go-live date line" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _date_line(due="2026-11-20")))
        self.assertTrue(any("still not set" in e for e in errors), errors)

    def test_set_golive_date_bounds_open_lines(self):
        doc = _doc(_gate(due="2027-02-01"), _date_line(value="2027-01-20"))
        errors, _, summary = self._errors(doc)
        self.assertTrue(any("after the go-live date 2027-01-20" in e for e in errors), errors)
        self.assertEqual(summary["golive_date"], "2027-01-20")
        doc = _doc(_gate(due="2027-01-10"), _date_line(value="2027-01-20"))
        self.assertEqual(self._errors(doc)[0], [])
        errors, _, _ = self._errors(doc, today=date(2027, 1, 20))
        self.assertTrue(any("is reached with 1 open line(s): GL-01" in e for e in errors), errors)
        doc = _doc(_gate(due="2027-01-10", proof=["docs/drills/result.json"]), _date_line(value="2027-01-20"))
        self.assertEqual(self._errors(doc, today=date(2027, 1, 21))[0], [])

    def test_shape_errors(self):
        errors, _, _ = self._errors(_doc(_gate(prof=["x"]), _gate(), _date_line()))
        self.assertTrue(any("unknown field 'prof'" in e for e in errors), errors)
        self.assertTrue(any("GL-01: duplicate id" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(id="G1", kind="maybe", title=""), _date_line()))
        for needle in ("id must look like GL-01", "kind must be one of", "title is required"):
            self.assertTrue(any(needle in e for e in errors), (needle, errors))
        errors, _, _ = self._errors({"version": 2, "updated": "today", "items": [], "extra": 1})
        for needle in ("unknown top-level keys: extra", "version must be 1", "updated must be", "items must be"):
            self.assertTrue(any(needle in e for e in errors), (needle, errors))
        errors, _, _ = self._errors(_doc(_gate(proof="docs/drills/widget.md"), _date_line()))
        self.assertTrue(any("proof must be a list" in e for e in errors), errors)

    def test_due_soon_is_a_warning_only(self):
        errors, warnings, _ = self._errors(_doc(_gate(due="2026-12-01"), _date_line()))
        self.assertEqual(errors, [])
        self.assertTrue(any("due within 14 days" in w and "GL-01" in w for w in warnings), warnings)


class RenderTest(unittest.TestCase):
    def test_render_links_relative_to_the_page_and_escapes_pipes(self):
        doc = _doc(_gate(title="A | B", proof=["docs/drills/result.json"], refs=["https://example.invalid/x"]),
                   _date_line())
        out = gg.render(doc, page="docs/ops/go-live/README.md")
        self.assertIn("**1 of 1 lines met**, 0 open", out)
        self.assertIn("A \\| B", out)
        self.assertIn("[`result.json`](../../drills/result.json)", out)
        self.assertIn("[example.invalid](https://example.invalid/x)", out)
        self.assertIn("not set; owner: business owner", out)

    def test_splice_needs_one_pair_of_markers(self):
        page = "# Page\n\n" + gg.BEGIN + "\nold\n" + gg.END + "\n\ntail\n"
        new = gg.splice(page, "NEW")
        self.assertIn("\nNEW\n", new)
        self.assertNotIn("old", new)
        self.assertTrue(new.endswith("tail\n"))
        for bad in ("# no markers\n", gg.END + "\n" + gg.BEGIN + "\n", page + gg.BEGIN + "\n"):
            with self.assertRaises(gg.GateError):
                gg.splice(bad, "NEW")

    def test_check_fails_on_a_stale_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/ops/go-live").mkdir(parents=True)
            (root / "docs/x.md").write_text("# X\n", encoding="utf-8")
            (root / gg.CHECKLIST).write_text(
                "version: 1\nupdated: 2026-11-25\nitems:\n"
                "  - id: GL-01\n    kind: gate\n    title: Invented line\n    source: Invented\n"
                "    proof: [docs/x.md]\n"
                "  - id: GL-02\n    kind: date\n    title: Go-live date\n    source: Invented\n"
                "    value: null\n    owner: business owner\n", encoding="utf-8")
            (root / gg.PAGE).write_text(f"# Gate\n\n{gg.BEGIN}\nstale\n{gg.END}\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(gg.main(["--root", tmp, "check", "--today", "2026-11-25"]), 1)
            self.assertIn("rendered list is stale", out.getvalue())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(gg.main(["--root", tmp, "render", "--write"]), 0)
            summary = root / "summary.md"
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(gg.main(["--root", tmp, "check", "--today", "2026-11-25",
                                          "--summary", str(summary)]), 0)
            self.assertIn("go-live gate OK", out.getvalue())
            self.assertIn("## Go-live gate", summary.read_text(encoding="utf-8"))


class CommittedChecklistTest(unittest.TestCase):
    """The committed checklist was valid on its `updated` date: every link resolves, every owner is a role, every
    open line has an owner and a due date. A later past-due line is the weekly workflow's job, not this test's."""

    def test_committed_checklist_is_valid_as_of_its_update(self):
        doc = gg.load_checklist()
        errors, _, summary = gg.evaluate(doc, date.fromisoformat(doc["updated"]))
        self.assertEqual(errors, [])
        self.assertGreaterEqual(summary["lines"], 15)

    def test_committed_page_matches_the_checklist(self):
        doc = gg.load_checklist()
        page = (gg.REPO_ROOT / gg.PAGE).read_text(encoding="utf-8")
        self.assertEqual(gg.splice(page, gg.render(doc)), page,
                         "run python3 tools/ops/golive_gate.py render --write")

    def test_committed_checklist_covers_the_adr_0012_gate_and_one_date_line(self):
        doc = gg.load_checklist()
        sources = [it.get("source", "") for it in doc["items"]]
        for n in range(1, 9):
            self.assertTrue(any(f"decision 11, gate item {n}" in s for s in sources), n)
        self.assertEqual(sum(1 for it in doc["items"] if it.get("kind") == "date"), 1)


if __name__ == "__main__":
    unittest.main()
