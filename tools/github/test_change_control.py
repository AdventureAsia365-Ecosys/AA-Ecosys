"""Tests for change_control.py and its use in ship_merge.merge_one (AA-1162). Offline: every gh call is scripted.

OFF (the shipped default) must keep ship_merge exactly as before: no extra GitHub read, no refusal. ON must refuse a
risky PR without an APPROVED review of its head by a human (non-bot) reviewer.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import change_control
import ship_common
import ship_merge
from ship_common import Result, ShipError
from ship_fakes import FakeRunner, pr

HEAD = "a" * 40
OLD = "9" * 40
ON = {
    "require_human_approval_for_risky": True,
    "risky_labels": ["risky", "change-control: risky"],
    "risky_paths": ["*migrations/*.sql", "*.tf", ".github/workflows/*", "*auth*",
                    "tools/github/change_control.json"],
    "ignore_paths": ["*.md"],
    "approvers": [],
    "exempt_authors": ["app/aa-ecosys-ci-bot"],
}
OFF = {**ON, "require_human_approval_for_risky": False}
NO_DELETES = Result(0, "[]\n")
DELETES_JQ = '[.[] | select(.status=="removed") | .filename]'


def js(obj) -> Result:
    return Result(0, json.dumps(obj))


def meta(labels=(), author="app/aa-agent") -> Result:
    return js({"labels": [{"name": x} for x in labels], "author": {"login": author, "is_bot": author.startswith("app/")}})


def review(login: str, state: str, commit: str = HEAD, kind: str = "User", at: str = "2026-11-21T10:00:00Z") -> dict:
    return {"user": {"login": login, "type": kind}, "state": state, "commit_id": commit, "submitted_at": at}


def runner(*, repo: str = "AA-Ecosys", n: int = 5, labels=(), files=("tools/x.py",), reviews=(),
           author: str = "app/aa-agent", merged: bool = True) -> FakeRunner:
    base = "master" if repo == "AA-Ecosys" else "main"
    views = [js(pr(n=n, head=HEAD, base=base))] * 3
    if merged:
        views.append(js(pr(n=n, state="MERGED", merge_oid="d" * 40, base=base)))
    return (FakeRunner()
            .on(("--json", "labels,author"), meta(labels, author))
            .on((DELETES_JQ,), NO_DELETES)
            .on(("[.[].filename]",), js(list(files)))
            .on((f"repos/{ship_common.slug(repo)}/pulls/{n}/reviews?per_page=100",), js(list(reviews)))
            .on(("gh", "pr", "view"), *views)
            .on((ship_common.AS_APP,), Result(0, "")))


class Quiet(unittest.TestCase):
    def setUp(self):
        self._out = contextlib.redirect_stdout(io.StringIO())
        self._out.__enter__()

    def tearDown(self):
        self._out.__exit__(None, None, None)


class ConfigTest(unittest.TestCase):
    def test_shipped_config_is_valid(self):
        cfg = change_control.load_config()
        self.assertIsInstance(cfg["require_human_approval_for_risky"], bool)
        for key in ("risky_labels", "risky_paths", "ignore_paths", "approvers", "exempt_authors"):
            self.assertIsInstance(cfg[key], list, key)
        # While ON, switching it off again is itself a risky change.
        self.assertTrue(change_control.risky_reasons(cfg, [], ["tools/github/change_control.json"], "app/aa-agent"))

    def test_missing_file_is_off_and_broken_file_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(change_control.enabled(change_control.load_config(Path(d) / "none.json")))
            bad = Path(d) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ShipError) as cm:
                change_control.load_config(bad)
            self.assertEqual(cm.exception.code, 2)
            bad.write_text('{"require_human_approval_for_risky": "yes"}', encoding="utf-8")
            with self.assertRaises(ShipError):
                change_control.load_config(bad)

    def test_enabled_only_on_true(self):
        self.assertTrue(change_control.enabled(ON))
        self.assertFalse(change_control.enabled(OFF))
        self.assertFalse(change_control.enabled({}))


class ClassifyTest(unittest.TestCase):
    def test_labels_and_paths(self):
        self.assertEqual(change_control.risky_reasons(ON, ["Risky"], [], "app/aa-agent"), ["label 'Risky'"])
        why = change_control.risky_reasons(ON, [], ["api/migrations/401_new_table.sql", "api/x.py"], "app/aa-agent")
        self.assertEqual(why, ["files api/migrations/401_new_table.sql"])
        self.assertTrue(change_control.risky_reasons(ON, [], [".github/workflows/ci.yml"], ""))
        self.assertTrue(change_control.risky_reasons(ON, [], ["accounts/aa365/main.tf"], ""))
        self.assertTrue(change_control.risky_reasons(ON, [], ["backend/app/auth/session.py"], ""))

    def test_not_risky(self):
        self.assertEqual(change_control.risky_reasons(ON, ["docs"], ["frontend/app/page.tsx"], "app/aa-agent"), [])
        # Text files never make a PR risky, even with a risky word in the name.
        self.assertEqual(change_control.risky_reasons(ON, [], ["docs/security/auth-notes.md"], ""), [])
        # The CI bot's migration copies were approved in their app PR.
        self.assertEqual(change_control.risky_reasons(ON, ["risky"], ["db/migrations/cis/401_x.sql"],
                                                      "app/aa-ecosys-ci-bot"), [])

    def test_approval_state(self):
        ok, blocked = change_control.approval_state([review("lead", "APPROVED")], HEAD, "app/aa-agent", [])
        self.assertEqual((ok, blocked), (["lead"], []))
        # Bot reviews (the agent's comment review included) never count.
        ok, _ = change_control.approval_state([review("aa-agent[bot]", "APPROVED", kind="Bot")], HEAD, "", [])
        self.assertEqual(ok, [])
        # An approval of an older head does not cover the current one.
        ok, _ = change_control.approval_state([review("lead", "APPROVED", commit=OLD)], HEAD, "", [])
        self.assertEqual(ok, [])
        # The latest decisive review wins; a later COMMENTED review does not cancel an approval.
        rs = [review("lead", "APPROVED", at="2026-11-21T10:00:00Z"),
              review("lead", "CHANGES_REQUESTED", at="2026-11-21T11:00:00Z")]
        self.assertEqual(change_control.approval_state(rs, HEAD, "", []), ([], ["lead"]))
        rs = [review("lead", "APPROVED", at="2026-11-21T10:00:00Z"),
              review("lead", "COMMENTED", at="2026-11-21T11:00:00Z")]
        self.assertEqual(change_control.approval_state(rs, HEAD, "", []), (["lead"], []))
        # The PR author cannot approve their own PR; approvers narrows who counts.
        self.assertEqual(change_control.approval_state([review("dev", "APPROVED")], HEAD, "dev", []), ([], []))
        self.assertEqual(change_control.approval_state([review("dev", "APPROVED")], HEAD, "", ["lead"]), ([], []))


class MergeGateOffTest(Quiet):
    def test_off_reads_nothing_and_merges_a_risky_pr_as_before(self):
        r = runner(labels=["risky"], files=["api/migrations/401_x.sql"])
        sha = ship_merge.merge_one(r, "AA-Ecosys", 5, change_control_cfg=OFF)
        self.assertEqual(sha, "d" * 40)
        self.assertFalse(r.called("labels,author"))
        self.assertFalse(r.called("[.[].filename]"))
        self.assertFalse([c for c in r.calls if any("/reviews" in t for t in c)])
        self.assertEqual(len(r.called(ship_common.AS_APP)), 1)

    def test_default_reads_the_shipped_config(self):
        r = runner(labels=["risky"])
        if change_control.enabled(change_control.load_config()):
            self.skipTest("change control is ON in the shipped config")
        self.assertEqual(ship_merge.merge_one(r, "AA-Ecosys", 5), "d" * 40)
        self.assertFalse(r.called("labels,author"))


class MergeGateOnTest(Quiet):
    def refused(self, r: FakeRunner, word: str, repo: str = "AA-Ecosys", n: int = 5, **kw) -> None:
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, repo, n, change_control_cfg=ON, **kw)
        self.assertEqual(cm.exception.code, 4)
        self.assertIn(word, str(cm.exception))
        self.assertFalse(r.called(ship_common.AS_APP))
        self.assertFalse(r.called(ship_common.MERGEQ))

    def test_risky_label_without_review_is_refused(self):
        self.refused(runner(labels=["risky"]), "needs an APPROVED review")

    def test_risky_file_with_only_the_agent_review_is_refused(self):
        r = runner(files=["api/migrations/401_x.sql"], reviews=[review("aa-agent[bot]", "COMMENTED", kind="Bot")])
        self.refused(r, "agent reviews do not count")

    def test_approval_of_an_older_head_is_refused(self):
        self.refused(runner(labels=["risky"], reviews=[review("lead", "APPROVED", commit=OLD)]), HEAD[:8])

    def test_changes_requested_is_refused(self):
        rs = [review("lead", "APPROVED"), review("second", "CHANGES_REQUESTED")]
        self.refused(runner(labels=["risky"], reviews=rs), "changes requested by second")

    def test_check_only_reports_the_refusal(self):
        r = runner(labels=["risky"], merged=False)
        self.refused(r, "change control", check_only=True)

    def test_queue_repo_is_refused_before_the_queue(self):
        r = runner(repo="AA-CIS-App", n=7, files=[".github/workflows/ci.yml"])
        r.on((ship_common.MERGEQ,), Result(0, ""))
        self.refused(r, "change control", repo="AA-CIS-App", n=7)

    def test_human_approval_of_the_head_merges(self):
        r = runner(labels=["risky"], reviews=[review("lead", "APPROVED")])
        self.assertEqual(ship_merge.merge_one(r, "AA-Ecosys", 5, change_control_cfg=ON), "d" * 40)
        self.assertEqual(len(r.called(ship_common.AS_APP)), 1)

    def test_not_risky_merges_without_reading_reviews(self):
        r = runner(files=["docs/guides/x.md", "frontend/app/page.tsx"])
        self.assertEqual(ship_merge.merge_one(r, "AA-Ecosys", 5, change_control_cfg=ON), "d" * 40)
        self.assertFalse([c for c in r.calls if any("/reviews" in t for t in c)])

    def test_unreadable_reviews_refuse(self):
        r = runner(labels=["risky"])
        r.rules.insert(0, (("repos/AdventureAsia365-Ecosys/AA-Ecosys/pulls/5/reviews?per_page=100",),
                           [Result(1, "", "HTTP 502")]))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-Ecosys", 5, change_control_cfg=ON)
        self.assertEqual(cm.exception.code, 2)
        self.assertFalse(r.called(ship_common.AS_APP))


if __name__ == "__main__":
    unittest.main()
