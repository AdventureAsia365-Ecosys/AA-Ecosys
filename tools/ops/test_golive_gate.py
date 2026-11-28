"""AA-1117 — tools/ops/golive_gate.py: the YAML subset parser, the line rules (dead proof path or anchor, unknown owner
role, open line past due or without owner and due, the two gate date lines: go-live and pilot data), the rendered
page, the what-if dates, and the committed checklist itself (valid as of its `updated` date, page in sync). Invented
paths and titles only; no network.

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
    item = {"id": "GL-99", "kind": "date", "gate_date": "golive", "title": "Go-live date", "source": "Invented",
            "value": None, "owner": "business owner"}
    item.update(over)
    return item


def _pilot_line(**over):
    item = {"id": "GL-98", "kind": "date", "gate_date": "pilot_data", "title": "Pilot data date",
            "source": "Invented", "value": None, "owner": "business owner"}
    item.update(over)
    return item


def _doc(*items, add_missing_dates=True):
    """A checklist of the given lines; a gate date line the test did not pass is added unset (add_missing_dates)."""
    items = list(items) or [_gate()]
    if add_missing_dates:
        present = {it.get("gate_date") for it in items if it.get("kind") == "date"}
        if "golive" not in present:
            items.append(_date_line())
        if "pilot_data" not in present:
            items.append(_pilot_line())
    return {"version": 1, "updated": "2026-11-25", "items": items}


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
        self.assertTrue(any("go-live date is not set" in w for w in warnings), warnings)
        self.assertTrue(any("pilot data date is not set" in w for w in warnings), warnings)
        self.assertEqual(summary, {"lines": 1, "met": 0, "open": 1, "open_before_pilot_data": 0,
                                   "golive_date": None, "pilot_data_date": None})

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
        errors, _, _ = self._errors(_doc(_gate(), _pilot_line(), add_missing_dates=False))
        self.assertTrue(any("exactly one go-live date line" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _date_line(), add_missing_dates=False))
        self.assertTrue(any("exactly one pilot data date line" in e and "found 0" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _date_line(), _date_line(id="GL-97")))
        self.assertTrue(any("found 2" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _date_line(value="soon")))
        self.assertTrue(any("value must be an ISO date" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(value="2027-01-01"), _date_line()))
        self.assertTrue(any("value is only for a gate date line" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _date_line(due="2026-11-20")))
        self.assertTrue(any("go-live date was due 2026-11-20 and is still not set" in e for e in errors), errors)
        errors, _, _ = self._errors(_doc(_gate(), _pilot_line(owner=None, due="2026-11-20")))
        self.assertTrue(any("GL-98: the pilot data date line needs an owner role" in e for e in errors), errors)
        self.assertTrue(any("pilot data date was due 2026-11-20" in e for e in errors), errors)

    def test_gate_date_field(self):
        errors, _, _ = self._errors(_doc(_gate(gate_date="someday")))
        self.assertTrue(any("GL-01: gate_date must be one of golive, pilot_data" in e for e in errors), errors)
        line = _date_line()
        del line["gate_date"]
        errors, _, _ = self._errors(_doc(_gate(), line, _pilot_line(), add_missing_dates=False))
        self.assertTrue(any("GL-99: gate_date must be one of" in e and "required on a date line" in e
                            for e in errors), errors)
        errors, _, summary = self._errors(_doc(_gate(), _gate(id="GL-02", gate_date="pilot_data")))
        self.assertEqual(errors, [])
        self.assertEqual(summary["open_before_pilot_data"], 1)

    def test_set_pilot_data_date_bounds_pilot_lines_only(self):
        pilot_gate = _gate(id="GL-02", gate_date="pilot_data", due="2027-01-10")
        golive_gate = _gate(due="2027-01-10")
        doc = _doc(golive_gate, pilot_gate, _pilot_line(value="2026-12-20"))
        errors, _, summary = self._errors(doc)
        self.assertEqual(summary["pilot_data_date"], "2026-12-20")
        self.assertTrue(any("GL-02: due 2027-01-10 is after the pilot data date 2026-12-20" in e for e in errors),
                        errors)
        self.assertFalse(any(e.startswith("GL-01") for e in errors), errors)
        errors, _, _ = self._errors(doc, today=date(2026, 12, 20))
        self.assertTrue(any("pilot data date 2026-12-20 is reached with 1 open line(s): GL-02" in e
                            for e in errors), errors)
        pilot_gate["proof"] = ["docs/drills/result.json"]
        self.assertEqual(self._errors(_doc(golive_gate, pilot_gate, _pilot_line(value="2026-12-20")),
                                      today=date(2026, 12, 21))[0], [])

    def test_go_live_date_bounds_pilot_lines_too(self):
        doc = _doc(_gate(gate_date="pilot_data", due="2027-02-01"), _date_line(value="2027-01-20"))
        errors, _, _ = self._errors(doc)
        self.assertTrue(any("GL-01: due 2027-02-01 is after the go-live date 2027-01-20" in e for e in errors), errors)

    def test_pilot_data_date_after_go_live_fails(self):
        doc = _doc(_gate(due="2026-12-01"), _date_line(value="2027-01-20"), _pilot_line(value="2027-02-01"))
        errors, _, _ = self._errors(doc)
        self.assertTrue(any("pilot data date 2027-02-01 is after the go-live date 2027-01-20" in e for e in errors),
                        errors)
        doc = _doc(_gate(due="2026-12-01"), _date_line(value="2027-01-20"), _pilot_line(value="2027-01-20"))
        self.assertEqual(self._errors(doc)[0], [])

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
        self.assertIn("**Go-live date (GL-99):**", out)
        self.assertIn("**Pilot data date (GL-98):**", out)
        self.assertIn("| GL-01 | A \\| B | Invented ADR 9999 | go-live | met |", out)

    def test_render_counts_and_marks_pilot_lines(self):
        doc = _doc(_gate(), _gate(id="GL-02", gate_date="pilot_data"), _pilot_line(value="2026-12-20"))
        out = gg.render(doc)
        self.assertIn("**0 of 2 lines met**, 2 open (1 of them due before the pilot data date)", out)
        self.assertIn("| GL-02 | Widget drill passed | Invented ADR 9999 | pilot data | open |", out)
        self.assertIn("**Pilot data date (GL-98):** 2026-12-20.", out)

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
                "  - id: GL-02\n    kind: date\n    gate_date: golive\n    title: Go-live date\n    source: Invented\n"
                "    value: null\n    owner: business owner\n"
                "  - id: GL-03\n    kind: date\n    gate_date: pilot_data\n    title: Pilot data date\n"
                "    source: Invented\n    value: null\n    owner: business owner\n", encoding="utf-8")
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
            # what-if dates change the check, never the file or the page comparison
            before = (root / gg.CHECKLIST).read_text(encoding="utf-8")
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(gg.main(["--root", tmp, "check", "--today", "2026-11-25",
                                          "--golive", "2027-01-20", "--pilot-data", "2027-02-01"]), 1)
            self.assertIn("is after the go-live date", out.getvalue())
            self.assertNotIn("stale", out.getvalue())
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(gg.main(["--root", tmp, "check", "--today", "2026-11-25",
                                          "--golive", "2027-01-20", "--pilot-data", "2026-12-20"]), 0)
            self.assertIn("go-live date 2027-01-20, pilot data date 2026-12-20", out.getvalue())
            self.assertEqual((root / gg.CHECKLIST).read_text(encoding="utf-8"), before)


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

    def test_committed_checklist_covers_the_adr_0012_gate_and_one_line_per_gate_date(self):
        doc = gg.load_checklist()
        sources = [it.get("source", "") for it in doc["items"]]
        for n in range(1, 9):
            self.assertTrue(any(f"decision 11, gate item {n}" in s for s in sources), n)
        for key in gg.GATE_DATES:
            self.assertEqual(sum(1 for it in doc["items"] if it.get("kind") == "date" and it.get("gate_date") == key),
                             1, key)

    def test_committed_pilot_lines(self):
        """S297 plan: the key ceremony (GL-06) and the no-real-data-before-DPA line are due before the pilot data."""
        items = {it["id"]: it for it in gg.load_checklist()["items"]}
        for iid in ("GL-06", "GL-15", "GL-16"):
            self.assertEqual(items[iid].get("gate_date"), "pilot_data", iid)
        self.assertIn("docs/ops/runbooks/key-ceremony.md", items["GL-06"]["refs"])


if __name__ == "__main__":
    unittest.main()
