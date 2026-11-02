"""Unit tests for plan_sync.py (S263, AA-896 lane plan-sync): merge rules, file format, guards, CLI modes.

Run: python3 -m unittest discover -s tools/linear -p 'test_*.py'   (stdlib only, no Linear key, no network)
Fixtures are invented issues; account-like numbers and ARNs are built at run time, never written literally.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plan_sync as ps  # noqa: E402

FAKE_ACCOUNT = "0" * 12
FAKE_ARN = "ar" + "n:aws:iam::" + FAKE_ACCOUNT + ":role/x"


def plan_issue(ident, **kw):
    base = {"id": ident, "title": f"Invented task {ident}", "status": "Backlog", "priority": "Medium",
            "project": "core", "milestone": "M1", "session": "S300", "size": "M",
            "next": "L1 · wire the widget", "needs": ""}
    base.update(kw)
    return base


def node(ident, *, title=None, state=("Backlog", "backlog"), priority=3, project="CIS Core — Invented",
         due=None, archived=False, trashed=False, created="2026-01-02T00:00:00.000Z"):
    return {"identifier": ident, "title": title or f"Invented task {ident}", "priority": priority, "dueDate": due,
            "archivedAt": "2026-01-03T00:00:00.000Z" if archived else None, "trashed": trashed,
            "createdAt": created, "state": {"name": state[0], "type": state[1]},
            "project": {"name": project} if project else None}


def make_plan(issues):
    return {"updated": "2026-01-01", "session": "S299", "next_session": "S300", "source": "invented",
            "projects": {"core": "Core", "data": "Data", "crm": "CRM", "portal": "Portal", "tpbk": "TP & BK"},
            "milestones": [{"id": "M1", "name": "First", "status": "active", "window": "S300",
                            "criteria": [{"text": "a thing works", "done": False}]}],
            "checks": [], "waiting": [], "log": [], "issues": issues}


class NormalizeTest(unittest.TestCase):
    def test_priority_labels(self):
        self.assertEqual([ps.normalize(node("AA-1", priority=p))["priority"] for p in range(5)],
                         ["No priority", "Urgent", "High", "Medium", "Low"])
        self.assertEqual(ps.normalize(node("AA-1", priority=None))["priority"], "No priority")

    def test_project_prefixes(self):
        cases = {"Data Platform — X": "data", "CIS Core — Y": "core", "CIS Portal — Z": "portal",
                 "TripPlanner & AA-Booking": "tpbk", "AA-Booking (AAA) — Foundation": "tpbk",
                 "Partner CRM — AA-Partner": "crm"}
        for name, key in cases.items():
            self.assertEqual(ps.project_key(name), key, name)
        self.assertIsNone(ps.project_key("Some Other Project"))
        self.assertIsNone(ps.project_key(None))
        self.assertEqual(ps.normalize(node("AA-1", project=None))["project"], "other")


class MergeTest(unittest.TestCase):
    def test_linear_fields_overwrite_hand_fields_stay(self):
        plan = make_plan([plan_issue("AA-10", status="Todo", priority="Low", next="L2 · keep me", needs="ask")])
        linear = [ps.normalize(node("AA-10", title="Renamed task", state=("In Progress", "started"), priority=2,
                                    project="Data Platform — Invented"))]
        new, diff = ps.merge(plan, linear)
        got = new["issues"][0]
        self.assertEqual((got["title"], got["status"], got["priority"], got["project"]),
                         ("Renamed task", "In Progress", "High", "data"))
        self.assertEqual((got["next"], got["needs"], got["milestone"], got["session"], got["size"]),
                         ("L2 · keep me", "ask", "M1", "S300", "M"))
        self.assertEqual({c[1] for c in diff["changed"]}, {"title", "status", "priority", "project"})
        self.assertEqual(plan["issues"][0]["status"], "Todo", "merge must not modify its input")

    def test_private_issue_keeps_its_plan_title(self):
        plan = make_plan([plan_issue("AA-11", title="AA-11 (details private)", status="Todo", private=True)])
        linear = [ps.normalize(node("AA-11", title="Secret working title", state=("In Progress", "started")))]
        new, diff = ps.merge(plan, linear)
        self.assertEqual(new["issues"][0]["title"], "AA-11 (details private)")
        self.assertEqual(new["issues"][0]["status"], "In Progress")
        self.assertNotIn("Secret working title", repr(diff))

    def test_closed_issue_removed_with_reason(self):
        plan = make_plan([plan_issue("AA-10"), plan_issue("AA-11")])
        new, diff = ps.merge(plan, [ps.normalize(node("AA-11"))], {"AA-10": "Done in Linear"})
        self.assertEqual([i["id"] for i in new["issues"]], ["AA-11"])
        self.assertEqual(diff["removed"], [("AA-10", "Done in Linear")])

    def test_unknown_reason_when_not_in_closed_map(self):
        _, diff = ps.merge(make_plan([plan_issue("AA-10")]), [])
        self.assertIn("not open in Linear", diff["removed"][0][1])

    def test_new_issue_gets_slot_defaults_sorted_by_number(self):
        plan = make_plan([plan_issue("AA-10")])
        linear = [ps.normalize(node(i)) for i in ("AA-10", "AA-120", "AA-12")]
        new, diff = ps.merge(plan, linear)
        self.assertEqual([i["id"] for i in new["issues"]], ["AA-10", "AA-12", "AA-120"])
        self.assertEqual(diff["added"], ["AA-12", "AA-120"])
        added = new["issues"][1]
        self.assertEqual((added["milestone"], added["session"], added["needs"], added["size"], added["next"]),
                         ("later", "unscheduled", "cần xếp slot", "", ""))
        self.assertEqual(list(added), [k for k in ps.KEY_ORDER if k in added])

    def test_due_linear_wins_plan_only_due_kept_with_warning(self):
        plan = make_plan([plan_issue("AA-10", due="2026-02-01"), plan_issue("AA-11", due="2026-03-01"),
                          plan_issue("AA-12")])
        linear = [ps.normalize(node("AA-10", due="2026-02-05")), ps.normalize(node("AA-11")),
                  ps.normalize(node("AA-12", due="2026-04-01"))]
        new, diff = ps.merge(plan, linear)
        self.assertEqual([i.get("due") for i in new["issues"]], ["2026-02-05", "2026-03-01", "2026-04-01"])
        self.assertTrue(any("AA-11" in w and "set it in Linear" in w for w in diff["warnings"]))
        self.assertEqual(list(new["issues"][2])[-1], "due")

    def test_archived_open_issue_kept_with_warning(self):
        new, diff = ps.merge(make_plan([plan_issue("AA-10")]), [ps.normalize(node("AA-10", archived=True))])
        self.assertEqual(len(new["issues"]), 1)
        self.assertTrue(any("archived" in w for w in diff["warnings"]))

    def test_trashed_or_closed_nodes_count_as_gone(self):
        linear = [ps.normalize(node("AA-10", trashed=True)), ps.normalize(node("AA-11", state=("Done", "completed")))]
        new, diff = ps.merge(make_plan([plan_issue("AA-10"), plan_issue("AA-11")]), linear)
        self.assertEqual(new["issues"], [])
        self.assertEqual(len(diff["removed"]), 2)

    def test_unknown_project_warns_and_maps_to_other(self):
        new, diff = ps.merge(make_plan([]), [ps.normalize(node("AA-10", project="Brand New Project"))])
        self.assertEqual(new["issues"][0]["project"], "other")
        self.assertTrue(any("Brand New Project" in w for w in diff["warnings"]))

    def test_no_changes_when_in_sync(self):
        plan = make_plan([plan_issue("AA-10")])
        new, diff = ps.merge(plan, [ps.normalize(node("AA-10"))])
        self.assertFalse(ps.has_changes(diff))
        self.assertEqual(new, plan)


class FormatTest(unittest.TestCase):
    def test_real_plan_round_trips_byte_for_byte(self):
        text = ps.PLAN.read_text(encoding="utf-8")
        self.assertEqual(ps.dumps(json.loads(text)), text)

    def test_stamp_sets_dates_and_session(self):
        out = ps.stamp(make_plan([]), "2026-01-05", "2026-01-05T01:02Z", "S301")
        self.assertEqual(list(out)[:2], ["updated", "synced_at"])
        self.assertEqual((out["updated"], out["synced_at"], out["session"], out["next_session"]),
                         ("2026-01-05", "2026-01-05T01:02Z", "S301", "S302"))
        again = ps.stamp(out, "2026-01-06", "2026-01-06T00:00Z")
        self.assertEqual((again["synced_at"], again["session"]), ("2026-01-06T00:00Z", "S301"))

    def test_js_arrays_from_index(self):
        ses, ms = ps.orders(ps.INDEX)
        self.assertIn("unscheduled", ses)
        self.assertIn("later", ms)
        self.assertIsNone(ps.js_array("var X = 1;", "SES_ORDER"))


class GuardTest(unittest.TestCase):
    def test_safety_flags_account_ids_and_arns(self):
        self.assertTrue(ps.safety_problems(f"id {FAKE_ACCOUNT} here"))
        self.assertTrue(ps.safety_problems(FAKE_ARN))
        self.assertEqual(ps.safety_problems("AA-1003 due 2026-11-03, 1234567890123 is 13 digits"), [])

    def test_arn_only_at_a_word_start(self):
        self.assertEqual(ps.safety_problems("Learn: how the invented widget works; barn: red"), [])
        self.assertTrue(ps.safety_problems(f"see ({FAKE_ARN})"))

    def test_validate_real_plan_has_no_errors(self):
        ses, ms = ps.orders(ps.INDEX)
        errors, _ = ps.validate(json.loads(ps.PLAN.read_text(encoding="utf-8")), ses, ms)
        self.assertEqual(errors, [])

    def test_validate_errors_and_warnings(self):
        plan = make_plan([plan_issue("AA-10", due="soon", priority="Big", session="Sx", milestone="Mx"),
                          plan_issue("AA-10")])
        plan["milestones"][0]["risks"] = [{"text": "x"}]
        plan["source"] = f"see {FAKE_ACCOUNT}"
        errors, warnings = ps.validate(plan, ["S300"], ["M1"])
        joined = "\n".join(errors)
        for part in ("not YYYY-MM-DD", "priority 'Big'", "listed twice", "risk keys", "public safety"):
            self.assertIn(part, joined)
        self.assertTrue(any("Sx" in w for w in warnings) and any("Mx" in w for w in warnings))

    def test_scope_allows_only_linear_owned_changes(self):
        base = make_plan([plan_issue("AA-10"), plan_issue("AA-11")])
        synced, _ = ps.merge(base, [ps.normalize(node("AA-10", state=("Todo", "unstarted"))),
                                    ps.normalize(node("AA-13", due="2026-05-01"))])
        synced = ps.stamp(synced, "2026-01-05", "2026-01-05T00:00Z")
        self.assertEqual(ps.scope_violations(base, synced), [])
        hand = json.loads(json.dumps(synced))
        hand["issues"][0]["next"] = "edited"
        hand["checks"] = [{"due": "x", "issue": "AA-10", "text": "y"}]
        hand["session"] = "S301"
        got = ps.scope_violations(base, hand)
        self.assertTrue(any("'next'" in g for g in got))
        self.assertTrue(any("'checks'" in g for g in got))
        self.assertTrue(any("'session'" in g for g in got))


class LogDraftTest(unittest.TestCase):
    def test_closed_canceled_created_since(self):
        changed = [
            dict(node("AA-20", state=("Done", "completed")), completedAt="2026-01-03T05:00:00Z"),
            dict(node("AA-21", state=("Done", "completed")), completedAt="2025-12-30T05:00:00Z"),
            dict(node("AA-22", state=("Canceled", "canceled")), canceledAt="2026-01-02T00:00:00Z"),
            dict(node("AA-23", created="2026-01-04T00:00:00Z")),
            dict(node("AA-9", state=("Done", "completed"), created="2026-01-02T00:00:00Z"),
                 completedAt="2026-01-02T09:00:00Z"),
        ]
        d = ps.log_draft(changed, "2026-01-02", "S301", "05/01/2026")
        self.assertEqual(d["closed"], ["AA-9", "AA-20"])
        self.assertEqual(d["canceled"], ["AA-22"])
        self.assertEqual(d["created"], ["AA-9", "AA-20", "AA-21", "AA-22", "AA-23"])
        self.assertEqual((d["session"], d["date"], d["reopened"], d["notes"]), ("S301", "05/01/2026", [], []))


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "plan.json"
        self.path.write_text(ps.dumps(make_plan([plan_issue("AA-10", session="S263", milestone="M1"),
                                                 plan_issue("AA-11", session="S263", milestone="M1")])),
                             encoding="utf-8")
        self.linear = [ps.normalize(node("AA-10", state=("In Progress", "started")))]
        self.changed = [dict(node("AA-11", state=("Done", "completed")), completedAt="2026-01-02T00:00:00Z")]

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *argv, linear=None):
        out = io.StringIO()
        with mock.patch.object(ps, "fetch_open", return_value=self.linear if linear is None else linear), \
                mock.patch.object(ps, "fetch_changed_since", return_value=self.changed), \
                mock.patch("linear_api.api_key", return_value="test-key"), \
                contextlib.redirect_stdout(out):
            code = ps.main(["--plan", str(self.path), *argv])
        return code, out.getvalue()

    def test_dry_run_writes_nothing(self):
        before = self.path.read_text(encoding="utf-8")
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("REMOVED  AA-11: Done in Linear", out)
        self.assertIn("dry run", out)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_check_exit_codes(self):
        self.assertEqual(self.run_main("--check")[0], 1)
        self.changed = []
        self.assertEqual(self.run_main("--check", linear=[ps.normalize(node("AA-10")),
                                                          ps.normalize(node("AA-11"))])[0], 0)

    def test_write_with_session_and_log_draft(self):
        code, out = self.run_main("--write", "--session", "S301", "--log-draft")
        self.assertEqual(code, 0, out)
        got = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual([i["id"] for i in got["issues"]], ["AA-10"])
        self.assertEqual(got["issues"][0]["status"], "In Progress")
        self.assertEqual((got["session"], got["next_session"]), ("S301", "S302"))
        self.assertIn("synced_at", got)
        self.assertIn('"closed": [\n  "AA-11"', out)

    def test_public_safety_refuses_to_write(self):
        before = self.path.read_text(encoding="utf-8")
        code, out = self.run_main("--write", linear=[ps.normalize(node("AA-10", title=f"leak {FAKE_ACCOUNT}"))])
        self.assertEqual(code, 2)
        self.assertIn("refusing", out)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_public_safety_prints_nothing_from_linear(self):
        # The workflow puts stdout in a public Actions log and the bot PR body: a leaked value must not be printed,
        # neither in a CHANGED title line nor in a WARN line with a Linear project name.
        leak_title = ps.normalize(node("AA-10", title=f"Invented title {FAKE_ACCOUNT}"))
        leak_project = ps.normalize(node("AA-12", project=f"Team {FAKE_ARN}"))
        for linear in ([leak_title], [ps.normalize(node("AA-10")), leak_project]):
            for argv in (("--check",), ("--write", "--log-draft"), ()):
                code, out = self.run_main(*argv, linear=linear)
                self.assertEqual(code, 2, out)
                self.assertNotIn(FAKE_ACCOUNT, out)
                self.assertNotIn(FAKE_ARN, out)
                self.assertNotIn("CHANGED", out)
                self.assertNotIn("WARN", out)
                self.assertIn("refusing", out)

    def test_validate_and_check_scope_offline(self):
        with mock.patch("linear_api.api_key", side_effect=AssertionError("offline modes must not read the key")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ps.main(["--plan", str(self.path), "--validate"]), 0)
                base = Path(self.tmp.name) / "base.json"
                edited = json.loads(self.path.read_text(encoding="utf-8"))
                base.write_text(ps.dumps(edited), encoding="utf-8")
                edited["issues"][0]["needs"] = "hand edit"
                self.path.write_text(ps.dumps(edited), encoding="utf-8")
                self.assertEqual(ps.main(["--plan", str(self.path), "--check-scope", str(base)]), 1)
            self.assertIn("hand-owned 'needs' changed", out.getvalue())


if __name__ == "__main__":
    unittest.main()
