"""AA-1170 — unit tests of the root compliance collector (tools/compliance/collect.py) and the public-repo guard of the
collector files. No network: GitHub answers are invented dicts; the repo checks run on a temporary tree with invented
pages. Run: python3 -m unittest discover -s tools/compliance -p 'test_*.py'"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collect as c  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 11, 21, 3, 0, tzinfo=timezone.utc)
CFG = {"org": "ExampleOrg", "root_repo": "Root", "repos": ["Root", "AppA"], "image_repos": ["AppA"],
       "ci_workflow": "ci.yml", "ci_runs_inspected": 10, "secret_scan_workflow": "secret-scan-history.yml", "guard_window_days": 8,
       "docs_skip_status": ["archived"]}


def fake(answers: dict):
    calls = []

    def fetch(path: str):
        calls.append(path)
        for prefix, value in answers.items():
            if path.startswith(prefix):
                return value
        return None
    fetch.calls = calls   # type: ignore[attr-defined]
    return fetch


class GithubChecksTest(unittest.TestCase):
    def test_branch_protection_counts_rulesets_and_protected_flags(self):
        f = fake({"/repos/ExampleOrg/Root/rules": [{"type": "pull_request"}],
                  "/repos/ExampleOrg/AppA/rules": [], "/repos/ExampleOrg/AppA/branches": {"protected": False},
                  "/repos/ExampleOrg/Root": {"default_branch": "master"},
                  "/repos/ExampleOrg/AppA": {"default_branch": "main"}})
        r = c.check_branch_protection(f, CFG)
        self.assertEqual(r["status"], "fail")
        self.assertEqual(r["detail"], {"repos": 2, "protected": 1, "unprotected": ["AppA"]})
        self.assertIn("/repos/ExampleOrg/Root/rules/branches/master", f.calls)

    def test_codeql_needs_an_active_codeql_workflow_everywhere(self):
        ok = {"workflows": [{"path": "dynamic/github-code-scanning/codeql", "name": "CodeQL", "state": "active"}]}
        r = c.check_codeql(fake({"/repos/ExampleOrg/": ok}), CFG)
        self.assertEqual((r["status"], r["detail"]["with_codeql"]), ("pass", 2))
        off = {"workflows": [{"path": ".github/workflows/codeql.yml", "name": "CodeQL", "state": "disabled_manually"}]}
        r = c.check_codeql(fake({"/repos/ExampleOrg/AppA": off, "/repos/ExampleOrg/": ok}), CFG)
        self.assertEqual((r["status"], r["detail"]["without"]), ("fail", ["AppA"]))

    def test_scheduled_guards_take_the_latest_run_per_workflow_in_the_window(self):
        runs = {"workflow_runs": [
            {"name": "Nightly", "created_at": "2026-11-20T01:00:00Z", "status": "completed", "conclusion": "success"},
            {"name": "Nightly", "created_at": "2026-11-19T01:00:00Z", "status": "completed", "conclusion": "failure"},
            {"name": "Weekly", "created_at": "2026-11-18T01:00:00Z", "status": "completed", "conclusion": "failure"},
            {"name": "Old", "created_at": "2026-10-01T01:00:00Z", "status": "completed", "conclusion": "failure"},
        ]}
        r = c.check_scheduled_guards(fake({"/repos/ExampleOrg/Root/actions/runs": runs}), CFG, NOW)
        self.assertEqual(r["status"], "fail")
        self.assertEqual(r["detail"], {"workflows": 2, "red": ["Root: Weekly"]})
        r = c.check_scheduled_guards(fake({}), CFG, NOW)
        self.assertEqual(r["status"], "error")   # no scheduled run at all is not a pass

    SCAN = "Scan image for vulnerabilities (Trivy, failing on fixable CRITICAL/HIGH)"
    SBOM = "Generate SBOM (syft, CycloneDX)"

    def _scan_jobs(self, scan="success", sbom="success"):
        return {"jobs": [{"steps": [{"name": self.SCAN, "conclusion": scan}, {"name": self.SBOM, "conclusion": sbom}]}]}

    def test_image_scan_and_sbom_steps_must_both_pass(self):
        runs = {"workflow_runs": [{"id": 7, "head_branch": "gh-readonly-queue/main/pr-12-abc", "conclusion": "success",
                                   "created_at": "2026-11-21T01:00:00Z"}]}
        jobs = self._scan_jobs()
        f = fake({"/repos/ExampleOrg/AppA/actions/workflows/ci.yml/runs?event=merge_group": runs,
                  "/repos/ExampleOrg/AppA/actions/runs/7/jobs": jobs})
        r = c.check_image_scan_sbom(f, CFG)
        self.assertEqual((r["status"], r["detail"]["last_date"]), ("pass", "2026-11-21"))
        jobs["jobs"][0]["steps"][1]["conclusion"] = "failure"
        self.assertEqual(c.check_image_scan_sbom(f, CFG)["status"], "fail")
        jobs["jobs"][0]["steps"][1]["conclusion"] = "skipped"   # the only run did not scan: no evidence, not a pass
        r = c.check_image_scan_sbom(f, CFG)
        self.assertEqual((r["status"], r["detail"]["missing_or_red"]), ("fail", ["AppA"]))
        self.assertNotIn("last_date", r["detail"])

    def test_image_scan_reads_the_merge_queue_not_an_old_push_on_main(self):
        # CI runs on merge_group since the push trigger on main was dropped: the old push run must not decide
        queue = {"workflow_runs": [
            {"id": 30, "head_branch": "gh-readonly-queue/main/pr-40-def", "conclusion": "cancelled",
             "created_at": "2026-11-21T02:00:00Z"},
            {"id": 31, "head_branch": "gh-readonly-queue/main/pr-41-abc", "conclusion": "failure",
             "created_at": "2026-11-20T09:00:00Z"},
            {"id": 32, "head_branch": "gh-readonly-queue/other/pr-9-x", "conclusion": "success",
             "created_at": "2026-11-21T05:00:00Z"}]}
        push = {"workflow_runs": [{"id": 5, "head_branch": "main", "conclusion": "success",
                                   "created_at": "2026-11-06T17:00:00Z"}]}
        f = fake({"/repos/ExampleOrg/AppA/actions/workflows/ci.yml/runs?event=merge_group": queue,
                  "/repos/ExampleOrg/AppA/actions/workflows/ci.yml/runs?event=push": push,
                  "/repos/ExampleOrg/AppA/actions/runs/31/jobs": self._scan_jobs(scan="failure"),
                  "/repos/ExampleOrg/AppA/actions/runs/5/jobs": self._scan_jobs(),
                  "/repos/ExampleOrg/AppA": {"default_branch": "main"}})
        r = c.check_image_scan_sbom(f, CFG)
        self.assertEqual((r["status"], r["detail"]["run_dates"]), ("fail", {"AppA": "2026-11-20"}))
        self.assertNotIn("/repos/ExampleOrg/AppA/actions/runs/30/jobs", f.calls)   # cancelled run skipped
        self.assertNotIn("/repos/ExampleOrg/AppA/actions/runs/32/jobs", f.calls)   # another branch's queue
        self.assertNotIn("/repos/ExampleOrg/AppA/actions/runs/5/jobs", f.calls)    # the newer queue run decided
        # only the old push run scanned: it passes, but its date is published so CIS can fail it on age
        f = fake({"/repos/ExampleOrg/AppA/actions/workflows/ci.yml/runs?event=push": push,
                  "/repos/ExampleOrg/AppA/actions/runs/5/jobs": self._scan_jobs()})
        r = c.check_image_scan_sbom(f, CFG)
        self.assertEqual((r["status"], r["detail"]["last_date"]), ("pass", "2026-11-06"))
        self.assertIn("2026-11-06", r["summary"])

    def test_image_scan_fact_is_the_oldest_newest_scan_across_repos(self):
        cfg = dict(CFG, image_repos=["AppA", "AppB"])
        f = fake({"/repos/ExampleOrg/AppA/actions/workflows/ci.yml/runs?event=merge_group": {"workflow_runs": [
                      {"id": 1, "head_branch": "gh-readonly-queue/main/pr-1-a", "conclusion": "success",
                       "created_at": "2026-11-21T01:00:00Z"}]},
                  "/repos/ExampleOrg/AppB/actions/workflows/ci.yml/runs?event=merge_group": {"workflow_runs": [
                      {"id": 2, "head_branch": "gh-readonly-queue/main/pr-2-b", "conclusion": "success",
                       "created_at": "2026-11-09T01:00:00Z"}]},
                  "/repos/ExampleOrg/AppA/actions/runs/1/jobs": self._scan_jobs(),
                  "/repos/ExampleOrg/AppB/actions/runs/2/jobs": self._scan_jobs()})
        r = c.check_image_scan_sbom(f, cfg)
        self.assertEqual((r["status"], r["detail"]["last_date"]), ("pass", "2026-11-09"))
        self.assertEqual(r["detail"]["run_dates"], {"AppA": "2026-11-21", "AppB": "2026-11-09"})

    def test_secret_scan_reads_the_newest_completed_run(self):
        f = fake({"/repos/ExampleOrg/Root/actions/workflows/secret-scan-history.yml/runs": {"workflow_runs": [
            {"conclusion": "success", "created_at": "2026-11-20T00:00:00Z",
             "html_url": "https://github.com/ExampleOrg/Root/actions/runs/1"}]}})
        r = c.check_secret_scan(f, CFG)
        self.assertEqual((r["status"], r["detail"]["run_date"]), ("pass", "2026-11-20"))


def _tree(tmp: Path) -> Path:
    (tmp / "docs" / "ops" / "drills").mkdir(parents=True)
    (tmp / "docs" / "security").mkdir(parents=True)
    (tmp / "docs" / "guides").mkdir(parents=True)
    (tmp / "docs" / "ops" / "drills" / "README.md").write_text(
        "| Date | Drill | Runbook | Result |\n|---|---|---|---|\n"
        "| 2026-09-01 | Sample restore | [r](x.md) | pass: 3/3 tables |\n"
        "| 2026-10-05 | Sample rollback | [r](y.md) | fail: timed out |\n", encoding="utf-8")
    (tmp / "docs" / "security" / "README.md").write_text(
        "| Quarter | Record |\n|---|---|\n| 2026-Q3 | [2026-08-02-S100-access-review](x) |\n"
        "| 2026-Q4 | [2026-11-01-S200-access-review](y) |\n", encoding="utf-8")
    (tmp / "docs" / "security" / "vuln-exceptions.toml").write_text(
        '[[exception]]\nrepo = "AppA"\nid = "GHSA-aaaa-bbbb-cccc"\nexpires = 2026-12-31\n\n'
        '[[exception]]\nrepo = "AppA"\nid = "GHSA-dddd-eeee-ffff"\nexpires = 2026-11-01\n', encoding="utf-8")
    page = "---\nid: X\nstatus: {s}\nlast_reviewed: {d}\nreview_every_days: 30\n---\n# Page\n"
    (tmp / "docs" / "guides" / "fresh.md").write_text(page.format(s="draft", d="2026-11-10"), encoding="utf-8")
    (tmp / "docs" / "guides" / "old.md").write_text(page.format(s="draft", d="2026-09-01"), encoding="utf-8")
    (tmp / "docs" / "guides" / "gone.md").write_text(page.format(s="archived", d="2025-01-01"), encoding="utf-8")
    return tmp


class RepoChecksTest(unittest.TestCase):
    def test_register_facts(self):
        with tempfile.TemporaryDirectory() as d:
            root = _tree(Path(d))
            drill = c.check_last_drill(root)
            self.assertEqual((drill["status"], drill["detail"]["last_date"]), ("pass", "2026-09-01"))   # a fail row never counts
            review = c.check_last_access_review(root)
            self.assertEqual(review["detail"], {"last_date": "2026-11-01", "reviews": 2})
            docs = c.check_docs_overdue(root, date(2026, 11, 21), ("archived",))
            self.assertEqual(docs["detail"], {"overdue": 1, "pages": 2})
            vuln = c.check_vuln_exceptions(root, date(2026, 11, 21))
            self.assertEqual((vuln["status"], vuln["detail"]["expired"]), ("fail", ["AppA: GHSA-dddd-eeee-ffff"]))

    def test_missing_registers_are_errors_not_passes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(c.check_last_drill(Path(d))["status"], "error")
            self.assertEqual(c.check_last_access_review(Path(d))["status"], "error")
            self.assertEqual(c.check_vuln_exceptions(Path(d), date(2026, 11, 21))["status"], "error")


class BundleTest(unittest.TestCase):
    def test_offline_bundle_shape(self):
        with tempfile.TemporaryDirectory() as d:
            b = c.collect(None, CFG, _tree(Path(d)), NOW, "abc1234", "compliance-evidence #5")
        self.assertEqual((b["format"], b["source"], b["generated_at"]), (1, "root_daily", "2026-11-21T03:00:00Z"))
        ids = [x["check_id"] for x in b["checks"]]
        self.assertEqual(ids[-1], "collector_heartbeat")
        self.assertEqual(len(ids), len(set(ids)))
        for x in b["checks"]:
            self.assertIn(x["status"], ("pass", "fail", "error", "manual"))
            self.assertRegex(x["check_id"], r"^[a-z][a-z0-9_]{1,63}$")
        self.assertEqual(c.assert_publishable(b), [])

    def test_a_failing_check_does_not_stop_the_others(self):
        def broken(path):
            raise RuntimeError("boom")
        with tempfile.TemporaryDirectory() as d:
            b = c.collect(broken, CFG, _tree(Path(d)), NOW, None, None)
        states = {x["check_id"]: x["status"] for x in b["checks"]}
        self.assertEqual(states["repo_branch_protection"], "error")
        self.assertEqual(states["last_restore_drill"], "pass")
        self.assertEqual(len(states), 10)

    def test_forbidden_text_refuses_the_file(self):
        bad = {"checks": [{"summary": "role arn:aws:iam::" + "1" * 12 + ":role/x"}]}
        self.assertEqual(c.assert_publishable(bad), ["an account ID", "an ARN"])
        self.assertEqual(c.assert_publishable({"x": "s3://some-bucket/key"}), ["an S3 URI (a bucket name)"])


class PublicRepoGuardTest(unittest.TestCase):
    """The collector files are public: no account ID, ARN, bucket name or e-mail; the workflow never traces its shell,
    never runs on pull_request_target and prints counts only (root advisory section 4 C.5)."""

    FILES = ("tools/compliance/collect.py", "tools/compliance/checks.json", ".github/workflows/compliance-evidence.yml")

    def test_no_identifiers_in_the_collector_files(self):
        for name in self.FILES:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"(?<![0-9A-Za-z])\d{12}(?![0-9A-Za-z])", text), name)
            self.assertNotIn("arn:aws:", text, name)
            self.assertIsNone(re.search(r"s3://[a-z0-9]", text), name)   # the bucket comes from a secret
            self.assertIsNone(re.search(r"\b[\w.+-]+@adventure", text), name)

    def test_workflow_shape(self):
        text = (ROOT / ".github/workflows/compliance-evidence.yml").read_text(encoding="utf-8")
        wf = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))   # code, not comments
        self.assertNotIn("pull_request_target", wf)
        self.assertIsNone(re.search(r"set -[a-z]*x", wf))
        self.assertNotIn("ACTIONS_STEP_DEBUG", wf)
        self.assertNotIn("upload-artifact", wf)   # the evidence goes to private storage only
        self.assertIn("refs/heads/master", wf)
        self.assertIn("schedule:", wf)
        self.assertIn("docs-reader/compliance", wf)

    def test_config_names_every_repo_once(self):
        cfg = json.loads((ROOT / "tools/compliance/checks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cfg["repos"]), len(set(cfg["repos"])))
        self.assertTrue(set(cfg["image_repos"]) <= set(cfg["repos"]))


if __name__ == "__main__":
    unittest.main()
