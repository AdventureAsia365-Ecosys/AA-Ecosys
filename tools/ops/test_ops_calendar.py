"""AA-1184 — tools/ops/ops_calendar.py: the line rules, the state of each kind on a given day, the register lines, the
compliance evidence detail (a deliberately past-due line turns it red and its size stays under the 8 KiB limit), the
.ics feed (deterministic, folded, CRLF) and the committed calendar itself (valid, page and feed in sync). Invented
titles, paths and registers only; no network.

Run: python3 -m unittest discover -s tools/ops -p 'test_ops_calendar.py'
"""
from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ops_calendar as oc  # noqa: E402

TODAY = date(2026, 12, 10)
REAL_ROOT = Path(__file__).resolve().parents[2]


def _deadline(**over):
    item = {"id": "OC-101", "kind": "deadline", "title": "Renew the widget licence", "owner": "tech lead",
            "source": "Invented decision 9999", "date": "2026-12-20", "warn_days": 5, "reminder": "session"}
    item.update(over)
    return item


def _recurring(**over):
    item = {"id": "OC-102", "kind": "recurring", "title": "Weekly widget review", "owner": "agent",
            "source": "Invented", "cadence": "weekly", "anchor": "2026-12-07", "evidence": "docs/audits/*widget*",
            "warn_days": 2, "reminder": "auto"}
    item.update(over)
    return item


def _trigger(**over):
    item = {"id": "OC-103", "kind": "trigger", "title": "File the gadget dossier", "owner": "business owner",
            "source": "Invented", "trigger": "first real gadget data", "within_days": 30, "warn_days": 7,
            "reminder": "none"}
    item.update(over)
    return item


def _automated(**over):
    item = {"id": "OC-104", "kind": "automated", "title": "Nightly widget probe", "owner": "agent",
            "source": "Invented", "cadence": "nightly", "reminder": "auto"}
    item.update(over)
    return item


def _doc(*items):
    return {"version": 1, "updated": "2026-12-01", "items": list(items) or [_deadline()]}


class _Repo:
    """A throwaway repo root with invented audit folders and registers."""

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        for name in ("2026-11-23-S900-widget-review", "2026-12-01-S901-widget-review"):
            (root / "docs/audits" / name).mkdir(parents=True)
            (root / "docs/audits" / name / "README.md").write_text("# Widget review\n", encoding="utf-8")
        (root / "docs/security").mkdir(parents=True)
        (root / "docs/security/vuln-exceptions.toml").write_text(
            '[[exception]]\nrepo = "AppA"\nid = "CVE-0000-0001"\nexpires = 2026-12-12\n\n'
            '[[exception]]\nrepo = "AppB"\nid = "CVE-0000-0002"\nexpires = 2027-03-01\n', encoding="utf-8")
        (root / "docs/ops/go-live").mkdir(parents=True)
        (root / "docs/ops/go-live/checklist.yaml").write_text(
            "version: 1\nupdated: 2026-12-01\nitems:\n"
            "  - id: GL-01\n    kind: gate\n    title: Widget gate\n    source: Invented\n    proof: []\n"
            "    owner: tech lead\n    due: 2026-12-08\n"
            "  - id: GL-02\n    kind: gate\n    title: Met gate\n    source: Invented\n    proof: [docs/x.md]\n"
            "    owner: tech lead\n    due: 2026-11-01\n", encoding="utf-8")
        return root

    def __exit__(self, *exc):
        self._tmp.cleanup()


class ValidateTest(unittest.TestCase):
    def test_a_good_calendar_validates(self):
        with _Repo() as root:
            doc = _doc(_deadline(), _recurring(), _trigger(), _automated())
            self.assertEqual(oc.validate(doc, root), [])

    def test_rules(self):
        cases = [
            (_deadline(id="OC-1"), "id must look like"),
            (_deadline(owner="Jane Doe"), "owner must be one of"),
            (_deadline(reminder="email"), "reminder must be one of"),
            (_deadline(warn_days=None), "warn_days is required"),
            (_deadline(date=None), "needs a date, a window_from or a dates_from"),
            (_deadline(date="20/12/2026"), "date must be an ISO date"),
            (_deadline(window_from="2026-12-30"), "window_from is after the date"),
            (_deadline(title="x" * 101), "longer than 100"),
            (_deadline(title="Close the widget issue AA-123"), "names an issue id"),
            (_deadline(note="ping ops@example.com"), "an e-mail address"),
            (_deadline(title="Account 123456789012 cleanup"), "an account ID"),
            (_deadline(title="Widget | gadget"), "may not contain '|'"),
            (_deadline(cadence="weekly"), "does not apply to a deadline line"),
            (_deadline(dates_from="widget-register", date=None), "dates_from must be one of"),
            (_deadline(dates_from="vuln-exceptions"), "takes its dates from the register"),
            (_deadline(evidence="docs/missing.md"), "dead path"),
            (_recurring(cadence="fortnightly"), "cadence must be"),
            (_recurring(anchor=None), "needs an anchor"),
            (_recurring(evidence="../outside/*"), "repo-relative glob"),
            (_recurring(evidence="check:Bad-Id"), "check id must look like"),
            (_recurring(warn_days=None), "warn_days is required"),
            (_trigger(within_days=None), "needs within_days"),
            (_trigger(trigger=""), "needs the trigger event"),
            (_automated(cadence=None), "needs its cadence"),
            (_automated(evidence="docs/x/*"), "evidence is a check"),
            (dict(_deadline(), colour="red"), "unknown field 'colour'"),
        ]
        with _Repo() as root:
            for item, needle in cases:
                errors = oc.validate(_doc(item), root)
                self.assertTrue(any(needle in e for e in errors), (item, needle, errors))

    def test_duplicate_ids_and_top_level(self):
        with _Repo() as root:
            errors = oc.validate({"version": 2, "updated": "x", "items": [_deadline(), _deadline()]}, root)
        self.assertTrue(any("duplicate id" in e for e in errors))
        self.assertTrue(any("version must be 1" in e for e in errors))
        self.assertTrue(any("updated must be" in e for e in errors))

    def test_reminder_only_and_check_lines_need_no_warn_days(self):
        with _Repo() as root:
            doc = _doc(_recurring(evidence="none", warn_days=None),
                       _recurring(id="OC-105", evidence="check:widget_review_recent", warn_days=None))
            self.assertEqual(oc.validate(doc, root), [])


class StateTest(unittest.TestCase):
    def state(self, item, today=TODAY, root=None):
        with _Repo() as r:
            return oc.evaluate_line(item, today, root or r)

    def test_deadline_states(self):
        self.assertEqual(self.state(_deadline(date="2026-12-09")).state, "overdue")
        self.assertEqual(self.state(_deadline(date="2026-12-10")).state, "due_soon")   # due today is not overdue
        self.assertEqual(self.state(_deadline(date="2026-12-15")).state, "due_soon")   # inside warn_days 5
        self.assertEqual(self.state(_deadline(date="2026-12-16")).state, "ok")
        done = self.state(_deadline(date="2026-12-01", done="2026-11-30"))
        self.assertEqual((done.state, done.last), ("done", date(2026, 11, 30)))

    def test_window_lines(self):
        self.assertEqual(self.state(_deadline(date=None, window_from="2026-12-01", warn_days=None)).state, "open")
        later = self.state(_deadline(date=None, window_from="2026-12-20", warn_days=None))
        self.assertEqual((later.state, later.extra), ("ok", "opens 2026-12-20"))
        before = self.state(_deadline(window_from="2026-12-12", date="2026-12-14"))
        self.assertEqual(before.state, "ok")   # a window not yet open is not due soon

    def test_recurring_takes_the_newest_evidence_date(self):
        ln = self.state(_recurring())
        self.assertEqual((ln.last, ln.due, ln.state), (date(2026, 12, 1), date(2026, 12, 8), "overdue"))
        ln = self.state(_recurring(cadence="monthly"))
        self.assertEqual((ln.due, ln.state), (date(2027, 1, 1), "ok"))

    def test_recurring_without_evidence_is_due_on_its_anchor(self):
        ln = self.state(_recurring(evidence="docs/audits/*gadget*", anchor="2026-12-11"))
        self.assertEqual((ln.last, ln.due, ln.state), (None, date(2026, 12, 11), "due_soon"))

    def test_reminder_only_and_check_lines_are_never_overdue(self):
        ln = self.state(_recurring(evidence="none", anchor="2026-11-02"))
        self.assertEqual((ln.state, ln.due), ("scheduled", date(2026, 12, 14)))   # next weekly slot on or after today
        ln = self.state(_recurring(evidence="check:widget_review_recent"))
        self.assertEqual((ln.state, ln.check, ln.due), ("watched", "widget_review_recent", None))

    def test_trigger_states(self):
        self.assertEqual(self.state(_trigger()).state, "waiting")
        ln = self.state(_trigger(trigger_date="2026-11-01"))
        self.assertEqual((ln.due, ln.state), (date(2026, 12, 1), "overdue"))
        self.assertEqual(self.state(_trigger(trigger_date="2026-11-01", done="2026-11-20")).state, "done")

    def test_automated_is_listed_never_due(self):
        ln = self.state(_automated(evidence="check:widget_heartbeat"))
        self.assertEqual((ln.state, ln.check), ("automated", "widget_heartbeat"))

    def test_register_lines_read_their_dates(self):
        ln = self.state(_deadline(date=None, dates_from="vuln-exceptions", warn_days=5))
        self.assertEqual((ln.due, ln.state), (date(2026, 12, 12), "due_soon"))
        self.assertEqual(ln.extra, "0 past due, 1 within 5 days, of 2 dated rows")
        gl = self.state(_deadline(date=None, dates_from="go-live-checklist", warn_days=5))
        self.assertEqual((gl.due, gl.state), (date(2026, 12, 8), "overdue"))   # the met gate line is ignored

    def test_month_arithmetic_clamps_to_the_month_end(self):
        self.assertEqual(oc.add_months(date(2027, 1, 31), 1), date(2027, 2, 28))
        self.assertEqual(oc.step(date(2026, 11, 30), "quarterly"), date(2027, 2, 28))
        self.assertEqual(oc.step(date(2026, 12, 1), "every 10 days"), date(2026, 12, 11))
        self.assertEqual(oc.next_slot(date(2026, 1, 31), "monthly", date(2026, 3, 1)), date(2026, 3, 31))


class EvidenceDetailTest(unittest.TestCase):
    def test_a_deliberately_past_due_line_turns_the_check_red_and_removing_it_turns_it_green(self):
        with _Repo() as root:
            green = _doc(_deadline(date="2026-12-20"))
            status, summary, detail = oc.evidence_detail(green, TODAY, root)
            self.assertEqual((status, detail["overdue"]), ("pass", 0))
            red = _doc(_deadline(date="2026-12-20"), _deadline(id="OC-199", title="Past-due test line",
                                                               date="2026-12-09"))
            status, summary, detail = oc.evidence_detail(red, TODAY, root)
            self.assertEqual((status, detail["overdue"]), ("fail", 1))
            self.assertIn("OC-199", summary)
            status, _, _ = oc.evidence_detail(green, TODAY, root)
            self.assertEqual(status, "pass")

    def test_the_drill_flag_injects_one_past_due_line(self):
        with _Repo() as root:
            status, summary, detail = oc.evidence_detail(_doc(_deadline()), TODAY, root, drill=True)
        self.assertEqual((status, detail["drill"]), ("fail", True))
        row = oc.parse_row(detail["rows"][-1])
        self.assertEqual((row["id"], row["state"], row["due"]), ("OC-999", "overdue", "2026-12-09"))

    def test_an_invalid_calendar_is_an_error_not_a_pass(self):
        with _Repo() as root:
            status, _, detail = oc.evidence_detail(_doc(_deadline(owner="someone")), TODAY, root)
        self.assertEqual((status, detail), ("error", {"errors": 1}))

    def test_rows_round_trip_and_notes_only_on_attention_lines(self):
        with _Repo() as root:
            doc = _doc(_deadline(date="2026-12-09", note="Overdue note"), _deadline(id="OC-105", note="Calm note"),
                       _recurring(id="OC-106", evidence="check:widget_review_recent"))
            _, _, detail = oc.evidence_detail(doc, TODAY, root)
        rows = [oc.parse_row(r) for r in detail["rows"]]
        self.assertEqual(rows[0], {"id": "OC-101", "kind": "D", "state": "overdue", "due": "2026-12-09", "last": None,
                                   "owner": "TL", "title": "Renew the widget licence", "check": None, "extra": None,
                                   "note": "Overdue note"})
        self.assertIsNone(rows[1]["note"])
        self.assertEqual((rows[2]["kind"], rows[2]["owner"], rows[2]["check"]), ("R", "AG", "widget_review_recent"))

    def test_a_large_calendar_still_fits_the_detail_limit(self):
        items = [_deadline(id=f"OC-{n:03d}", title=f"Invented duty number {n} " + "w" * 70, date="2027-06-01")
                 for n in range(100, 230)]
        with _Repo() as root:
            _, _, detail = oc.evidence_detail(_doc(*items, _deadline(id="OC-999", date="2026-12-01")), TODAY, root)
        self.assertLessEqual(len(json.dumps(detail).encode()), 8192)
        self.assertTrue(detail.get("truncated"))
        self.assertEqual([oc.parse_row(r)["id"] for r in detail["rows"]], ["OC-999"])   # attention lines kept


class IcsTest(unittest.TestCase):
    def test_feed_is_deterministic_folded_and_crlf(self):
        doc = _doc(_deadline(note="A long note " * 12), _recurring(cadence="quarterly"),
                   _trigger(trigger_date="2026-11-01"), _trigger(id="OC-107"), _automated(),
                   _deadline(id="OC-108", date=None, window_from="2027-01-04", warn_days=None))
        feed = oc.ics(doc)
        self.assertEqual(feed, oc.ics(doc))
        self.assertTrue(feed.startswith("BEGIN:VCALENDAR\r\n") and feed.endswith("END:VCALENDAR\r\n"))
        lines = feed.split("\r\n")[:-1]
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in lines))
        self.assertNotIn("\n", feed.replace("\r\n", ""))
        unfolded = feed.replace("\r\n ", "")
        self.assertIn("DTSTART;VALUE=DATE:20261220", unfolded)
        self.assertIn("RRULE:FREQ=MONTHLY;INTERVAL=3", unfolded)
        self.assertIn("DTSTART;VALUE=DATE:20261201", unfolded)          # trigger date + 30 days
        self.assertEqual(unfolded.count("BEGIN:VEVENT"), 4)              # waiting trigger and automated line omitted
        self.assertIn("SUMMARY:opens: OC-108", unfolded)
        self.assertIn("DTSTAMP:20261201T000000Z", unfolded)              # the calendar's updated date, never now

    def test_register_lines_stay_out_of_the_feed_so_a_register_edit_never_makes_it_stale(self):
        def refuse(*_a, **_k):
            raise AssertionError("ics() must not read a register")

        doc = _doc(_deadline(), *(_deadline(id=f"OC-1{n}0", date=None, dates_from=src)
                                  for n, src in enumerate(oc.DATES_FROM, start=1)))
        saved, oc.register_dates = oc.register_dates, refuse
        try:
            feed = oc.ics(doc).replace("\r\n ", "")
        finally:
            oc.register_dates = saved
        self.assertEqual(feed.count("BEGIN:VEVENT"), 1)                   # only the dated line
        self.assertNotIn("OC-110", feed)


class CommittedCalendarTest(unittest.TestCase):
    """The real docs/ops/calendar.yaml validates, its page table and .ics feed are in sync, and its detail fits."""

    def test_valid_and_in_sync(self):
        doc = oc.load(REAL_ROOT)
        self.assertEqual(oc.validate(doc, REAL_ROOT), [])
        page = (REAL_ROOT / oc.PAGE).read_text(encoding="utf-8")
        self.assertEqual(oc.splice(page, oc.render(doc)), page, "run: python3 tools/ops/ops_calendar.py render --write")
        self.assertEqual((REAL_ROOT / oc.ICS).read_bytes(), oc.ics(doc).encode("utf-8"),
                         "run: python3 tools/ops/ops_calendar.py ics --write")

    def test_a_duty_a_compliance_check_grades_is_watched_never_graded_by_a_glob(self):
        """One limit per duty: a recurring line for a duty that a compliance check already grades against an
        admin-editable age setting reads that check (evidence check:<id>) and has no warn_days of its own; a repo glob
        would give the duty a second limit and a second evidence source."""
        graded = {"last_access_review": re.compile(r"access review", re.I),
                  "last_restore_drill": re.compile(r"restore drill", re.I),
                  "monthly_review_recent": re.compile(r"security posture review", re.I)}
        collector = (REAL_ROOT / "tools/compliance/collect.py").read_text(encoding="utf-8")
        for check_id in ("last_access_review", "last_restore_drill"):
            self.assertIn(f'("{check_id}", lambda', collector, f"{check_id} is no longer a collector check")
        doc = oc.load(REAL_ROOT)
        seen = set()
        for it in doc["items"]:
            if it.get("kind") != "recurring":
                continue
            for check_id, rx in graded.items():
                if rx.search(it["title"]):
                    seen.add(check_id)
                    self.assertEqual(it.get("evidence"), f"check:{check_id}", it["id"])
                    self.assertNotIn("warn_days", it, f"{it['id']}: the check's setting decides overdue")
        self.assertEqual(seen, set(graded))

    def test_detail_of_the_real_calendar_fits_without_truncation(self):
        doc = oc.load(REAL_ROOT)
        _, _, detail = oc.evidence_detail(doc, date.fromisoformat(doc["updated"]), REAL_ROOT)
        self.assertLessEqual(len(json.dumps(detail).encode()), oc.DETAIL_BUDGET)
        self.assertNotIn("truncated", detail)

    def test_check_command_pull_request_mode_never_fails_on_overdue_alone(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = oc.main(["check", "--warn-overdue", "--today", "2030-01-01"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("overdue", out.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(oc.main(["check", "--today", "2030-01-01"]), 1)


if __name__ == "__main__":
    unittest.main()
