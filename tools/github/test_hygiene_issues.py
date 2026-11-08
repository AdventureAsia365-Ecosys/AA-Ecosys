"""Tests for hygiene_issues.py (AA-1024, S273). Offline: gh is a stub. Run: python3 -m unittest discover -s tools/github"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hygiene_issues as hi  # noqa: E402

GB = 10**9
REPO = "demo-org/root"


def row(repo, bytes_=1 * GB, stale_bytes=0, wl5=(), cache_error=None):
    return {"repo": repo, "bytes": bytes_, "entries": 10, "by_ref": {"default": bytes_},
            "top": [{"family": "setup-uv-*", "entries": 3, "bytes": bytes_}], "stale": 2 if stale_bytes else 0,
            "stale_bytes": stale_bytes, "wl5": list(wl5), "cache_error": cache_error}


def report(rows, unreadable=(), unknown_public=(), org_error=None):
    return {"rows": rows, "unreadable": list(unreadable), "warn_gb": 8.0,
            "org": {"public": [], "unknown_public": list(unknown_public), "error": org_error}}


CLEAN = report([row("AA-Ecosys"), row("AA-CIS-App")])


class FakeGh:
    def __init__(self, issues=(), fail=()):
        self.issues, self.fail, self.calls = list(issues), fail, []

    def __call__(self, cmd, input=None, **kw):
        self.calls.append((cmd, input))
        verb = cmd[1:3]
        if tuple(verb) in self.fail:
            return subprocess.CompletedProcess(cmd, 1, "", "HTTP 500")
        if verb == ["issue", "list"]:
            return subprocess.CompletedProcess(cmd, 0, json.dumps(self.issues), "")
        if verb == ["issue", "create"]:
            return subprocess.CompletedProcess(cmd, 0, f"https://github.com/{REPO}/issues/99\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def verbs(self):
        return [" ".join(c[1:3]) for c, _ in self.calls if c[1:3] != ["issue", "list"]]


class HygieneFindings(unittest.TestCase):
    def test_all_clear_is_absent(self):
        f = hi.hygiene_findings(CLEAN)
        self.assertEqual({k: v.status for k, v in f.items()},
                         {"cache-over-threshold": "absent", "stale-caches": "absent", "external-downloads": "absent",
                          "unknown-public-repo": "absent", "needs-permission": "absent"})

    def test_present_findings(self):
        rep = report([row("AA-CIS-App", 9 * GB, stale_bytes=GB, wl5=["ci.yml:build:WL5 step 'x' downloads y"])],
                     unknown_public=["scratch-demo"])
        f = hi.hygiene_findings(rep)
        self.assertEqual(f["cache-over-threshold"].status, "present")
        self.assertIn("**AA-CIS-App**: 9.00 GB", f["cache-over-threshold"].lines[0])
        self.assertEqual(f["stale-caches"].status, "present")
        self.assertEqual(f["external-downloads"].status, "present")
        self.assertEqual(f["unknown-public-repo"].lines, [f"**scratch-demo** (https://github.com/{hi.ORG}/scratch-demo)"])

    def test_stale_below_the_floor_is_absent(self):
        f = hi.hygiene_findings(report([row("AA-CIS-App", stale_bytes=GB // 10)]))
        self.assertEqual(f["stale-caches"].status, "absent")

    def test_unreadable_repo_makes_absent_unknown_but_not_present(self):
        f = hi.hygiene_findings(report([row("AA-Ecosys")], unreadable=["AA-Partner"], org_error="HTTP 502"))
        self.assertEqual(f["cache-over-threshold"].status, "unknown")
        self.assertEqual(f["external-downloads"].status, "unknown")
        self.assertEqual(f["unknown-public-repo"].status, "unknown")
        f = hi.hygiene_findings(report([row("AA-Ecosys", 9 * GB)], unreadable=["AA-Partner"]))
        self.assertEqual(f["cache-over-threshold"].status, "present")
        self.assertIn("Not measured this run: AA-Partner.", f["cache-over-threshold"].note)

    def test_cache_403_is_needs_permission_and_cache_types_unknown(self):
        rows = [row("AA-Ecosys"), row("AA-CIS-App", 0, cache_error="needs Actions: read")]
        f = hi.hygiene_findings(report(rows), token_source="github-token")
        self.assertEqual(f["needs-permission"].status, "present")
        self.assertIn("AA_CI_BOT_APP_ID", f["needs-permission"].fix)
        self.assertIn("Actions: Read-only", f["needs-permission"].fix)
        # the write-capable App key goes into the master-only environment, never a repo-level secret
        self.assertIn("environment `ci-hygiene`", f["needs-permission"].fix)
        self.assertIn("never at repo level", f["needs-permission"].fix)
        self.assertEqual(f["cache-over-threshold"].status, "unknown")
        self.assertEqual(f["external-downloads"].status, "absent")   # workflows were still scanned
        f = hi.hygiene_findings(report(rows), token_source="app")
        self.assertNotIn("AA_CI_BOT_APP_ID", f["needs-permission"].fix)

    def test_no_rows_at_all_is_unknown(self):
        f = hi.hygiene_findings(report([], unreadable=["AA-Ecosys"]))
        self.assertEqual(f["needs-permission"].status, "unknown")


class ReadFailures(unittest.TestCase):
    """The run colour comes from the report: a finding (check exit 1) must not hide a failed read."""

    def test_clean_report_has_none(self):
        self.assertEqual(hi.read_failures(CLEAN, "hygiene"), [])

    def test_red_plus_unreadable_repo_is_a_failure(self):
        r = report([row("AA-CIS-App", 9 * GB)], unreadable=["AA-Booking"])
        self.assertEqual(hi.read_failures(r, "hygiene"), ["AA-Booking: unreadable"])

    def test_org_error_or_missing_org_is_a_failure(self):
        self.assertEqual(hi.read_failures(report([row("AA-Ecosys")], org_error="HTTP 502"), "hygiene"),
                         ["org repository list: HTTP 502"])
        no_org = {"rows": [row("AA-Ecosys")], "unreadable": []}
        self.assertEqual(hi.read_failures(no_org, "hygiene"), ["org repository list: not read"])

    def test_cache_403_is_not_a_read_failure(self):   # it has its own "needs permission" issue
        self.assertEqual(hi.read_failures(report([row("AA-Booking", cache_error="403")]), "hygiene"), [])

    def test_pins_outdated_plus_unknown_upstream_is_a_failure(self):
        failures = hi.read_failures(Pins.REPORT, "pins")
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0].startswith("pin scanner: upstream release unreadable"))
        self.assertEqual(hi.read_failures({"pins": [], "unreadable": ["AA-Partner"]}, "pins"), ["AA-Partner: unreadable"])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            bad, ok = Path(d, "bad.json"), Path(d, "ok.json")
            bad.write_text(json.dumps(report([row("AA-CIS-App", 9 * GB)], unreadable=["AA-Booking"])))
            ok.write_text(json.dumps(CLEAN))
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                self.assertEqual(hi.main(["read-failures", "--kind", "hygiene", "--report", str(bad)]), 3)
                self.assertEqual(hi.main(["read-failures", "--kind", "hygiene", "--report", str(ok)]), 0)
            self.assertEqual(out.getvalue(), "AA-Booking: unreadable\n")
            Path(d, "list.json").write_text("[]")
            with mock.patch("sys.stderr", io.StringIO()):
                self.assertEqual(hi.main(["read-failures", "--kind", "pins", "--report", str(Path(d, "list.json"))]), 2)


class Workflow(unittest.TestCase):
    """Guards on .github/workflows/ci-hygiene.yml (text checks: the unit job installs no YAML parser)."""

    TEXT = (Path(__file__).resolve().parents[2] / ".github/workflows/ci-hygiene.yml").read_text(encoding="utf-8")

    def _jobs(self) -> dict[str, str]:
        body = self.TEXT.split("\njobs:\n", 1)[1]
        parts = re.split(r"(?m)^  ([a-z][a-z0-9_-]*):\n", body)
        return dict(zip(parts[1::2], parts[2::2]))

    def test_app_key_only_inside_the_master_only_environment(self):
        head = self.TEXT.split("\njobs:\n", 1)[0]
        self.assertNotIn("secrets.", head)          # workflow-level env cannot read environment secrets
        readers = {name for name, text in self._jobs().items() if "secrets.AA_CI_BOT_PRIVATE_KEY" in text}
        self.assertEqual(readers, {"hygiene"})
        self.assertRegex(self._jobs()["hygiene"], rf"(?m)^    environment: {re.escape(hi.ENVIRONMENT)}$")

    def test_red_comes_from_the_report(self):
        hygiene = self._jobs()["hygiene"]
        self.assertIn("hygiene_issues.py read-failures", hygiene)
        self.assertIn("if: steps.measure.outputs.degraded == 'true'", hygiene)
        self.assertNotIn("outputs.rc ==", hygiene)


class Plan(unittest.TestCase):
    def _present(self):
        return hi.hygiene_findings(report([row("AA-CIS-App", 9 * GB)]))

    def test_create_then_keep_then_update_then_close(self):
        f = self._present()
        acts = {a.key: a for a in hi.plan(f, [], "ci-hygiene", run_url="https://run/1")}
        create = acts["cache-over-threshold"]
        self.assertEqual(create.kind, "create")
        self.assertTrue(create.title.endswith("[ci-hygiene:cache-over-threshold]"))
        self.assertIn("_Last change: https://run/1_", create.body)
        self.assertNotIn("stale-caches", acts)    # absent and no issue: nothing to do
        issue = {"number": 5, "title": create.title, "body": create.body}
        same = {a.key: a for a in hi.plan(f, [issue], "ci-hygiene", run_url="https://run/2")}
        self.assertEqual(same["cache-over-threshold"].kind, "keep")   # the run link alone is no change
        bigger = hi.hygiene_findings(report([row("AA-CIS-App", 9.5 * GB)]))
        upd = {a.key: a for a in hi.plan(bigger, [issue], "ci-hygiene")}
        self.assertEqual((upd["cache-over-threshold"].kind, upd["cache-over-threshold"].number), ("update", 5))
        clear = {a.key: a for a in hi.plan(hi.hygiene_findings(CLEAN), [issue], "ci-hygiene", run_url="https://run/3")}
        self.assertEqual(clear["cache-over-threshold"].kind, "close")
        self.assertIn("Cleared", clear["cache-over-threshold"].comment)

    def test_unknown_leaves_the_issue_open(self):
        issue = {"number": 5, "title": "x [ci-hygiene:cache-over-threshold]", "body": ""}
        f = hi.hygiene_findings(report([row("AA-Ecosys")], unreadable=["AA-CIS-App"]))
        acts = {a.key: a for a in hi.plan(f, [issue], "ci-hygiene")}
        self.assertEqual(acts["cache-over-threshold"].kind, "leave")

    def test_duplicates_closed_oldest_kept(self):
        f = self._present()
        t = hi.title_for(f["cache-over-threshold"], "ci-hygiene")
        issues = [{"number": 9, "title": t, "body": ""}, {"number": 4, "title": t, "body": ""}]
        acts = hi.plan(f, issues, "ci-hygiene")
        self.assertIn(("duplicate", 9), [(a.kind, a.number) for a in acts])
        self.assertIn(("update", 4), [(a.kind, a.number) for a in acts])

    def test_issue_without_marker_is_ignored(self):
        acts = hi.plan(hi.hygiene_findings(CLEAN), [{"number": 1, "title": "Hand-written note", "body": ""}],
                       "ci-hygiene")
        self.assertEqual([a for a in acts if a.number == 1], [])

    def test_pin_vanished_closes_only_when_report_complete(self):
        issue = {"number": 7, "title": "Pinned tool update: demotool 1 -> 2 [ci-pin:demotool]", "body": ""}
        self.assertEqual(hi.plan({}, [issue], "ci-pin", complete=True)[0].kind, "close")
        self.assertEqual(hi.plan({}, [issue], "ci-pin", complete=False)[0].kind, "leave")


class Pins(unittest.TestCase):
    REPORT = {"unreadable": [], "pins": [
        {"key": "demotool", "upstream": "demo-org/demotool", "prefix": "v", "versions": ["1.2.0", "1.2.5"],
         "where": ["AA-CIS-App:.github/actions/release-bin/pins.txt:2"], "latest": "1.3.0",
         "latest_url": "https://github.com/demo-org/demotool/releases/tag/v1.3.0", "status": "outdated", "error": None},
        {"key": "lychee", "upstream": "lycheeverse/lychee", "prefix": "lychee-v", "versions": ["0.24.2"], "where": [],
         "latest": "0.24.2", "latest_url": "u", "status": "current", "error": None},
        {"key": "Demo_Model", "upstream": "demo-org/spacy-models", "prefix": "m-", "versions": ["3.8.0"], "where": [],
         "latest": "3.9.0", "latest_url": "u", "status": "outdated", "error": None},
        {"key": "plugin", "upstream": None, "prefix": "", "versions": ["1.0"], "where": [], "latest": None,
         "latest_url": None, "status": "manual", "error": None},
        {"key": "scanner", "upstream": "demo-org/scanner", "prefix": "v", "versions": ["8.0.0"], "where": [],
         "latest": None, "latest_url": None, "status": "unknown", "error": "HTTP 404"},
    ]}

    def test_pin_findings(self):
        f, complete = hi.pin_findings(self.REPORT)
        self.assertTrue(complete)
        self.assertEqual({k: v.status for k, v in f.items()},
                         {"demotool": "present", "lychee": "absent", "demo_model": "present", "scanner": "unknown"})
        self.assertEqual(f["demotool"].title, "Pinned tool update: demotool 1.2.0, 1.2.5 -> 1.3.0")
        self.assertIn("disagree", f["demotool"].fix)
        self.assertIn("major.minor", f["demo_model"].fix)
        self.assertIn("No auto-merge", f["demotool"].fix)


class Sync(unittest.TestCase):
    def _run(self, rep, fake, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "r.json")
            path.write_text(json.dumps(rep), encoding="utf-8")
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                rc = hi.main(["sync", "--kind", extra[0], "--report", str(path), "--repo", REPO, *extra[1:]], run=fake)
        return rc, out.getvalue()

    def test_plan_only_writes_nothing(self):
        fake = FakeGh()
        rc, text = self._run(report([row("AA-CIS-App", 9 * GB)]), fake, "hygiene")
        self.assertEqual(rc, 0)
        self.assertEqual(fake.verbs(), [])
        self.assertIn("plan only", text)
        self.assertIn("| cache-over-threshold | present | create (new finding) |", text)

    def test_apply_creates_with_label_and_closes_cleared(self):
        old = {"number": 3, "title": "Stale [ci-hygiene:stale-caches]", "body": "x"}
        fake = FakeGh(issues=[old])
        rc, _ = self._run(report([row("AA-CIS-App", 9 * GB)]), fake, "hygiene", "--apply", "--run-url", "https://r/1")
        self.assertEqual(rc, 0)
        self.assertEqual(fake.verbs(), ["label create", "issue create", "issue close"])
        create = next((c, i) for c, i in fake.calls if c[1:3] == ["issue", "create"])
        self.assertIn("--label", create[0])
        self.assertIn("ci-hygiene", create[0])
        self.assertIn("9.00 GB", create[1])
        close = next(c for c, _ in fake.calls if c[1:3] == ["issue", "close"])
        self.assertEqual(close[3], "3")
        self.assertIn("completed", close)

    def test_failed_write_exit_1_and_unreadable_report_exit_2(self):
        rc, _ = self._run(report([row("AA-CIS-App", 9 * GB)]), FakeGh(fail=(("issue", "create"),)), "hygiene",
                          "--apply")
        self.assertEqual(rc, 1)
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(hi.main(["sync", "--kind", "pins", "--report", "/nonexistent/r.json"], run=FakeGh()), 2)

    def test_pins_kind_uses_its_own_label_and_marker(self):
        fake = FakeGh()
        rc, text = self._run(Pins.REPORT, fake, "pins", "--apply")
        self.assertEqual(rc, 0)
        listed = next(c for c, _ in fake.calls if c[1:3] == ["issue", "list"])
        self.assertIn("ci-pin-update", listed)
        titles = [c[c.index("--title") + 1] for c, _ in fake.calls if c[1:3] == ["issue", "create"]]
        self.assertEqual(sorted(titles), ["Pinned tool update: Demo_Model 3.8.0 -> 3.9.0 [ci-pin:demo_model]",
                                          "Pinned tool update: demotool 1.2.0, 1.2.5 -> 1.3.0 [ci-pin:demotool]"])
        self.assertIn("| scanner | unknown | leave", text)


if __name__ == "__main__":
    unittest.main()
