"""Unit tests of tools/delivery/delivery_metrics.py (AA-1108) on recorded GitHub API answers of an invented repo.

fixtures/demo_github.json holds the runs, jobs, merged pull requests, deployments and pull request files of one
invented repo (example-org/demo-app) over five days, written to cover every definition of the delivery metrics:
a green deploy, a red post-deploy verify repaired by a hotfix pull request, a rollback, a revert, a failed deploy job
repaired by a redeploy, a bot pull request, a docs-only pull request, a merge-queue ejection, a flaky job and a red
main. No network: a fake transport answers from the fixture.

    python3 -m unittest discover -s tools/delivery -p 'test_*.py'
"""
from __future__ import annotations

import copy
import gzip
import json
import sys
import tempfile
import unittest
import urllib.parse
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import delivery_metrics as dm  # noqa: E402

FIX = json.loads((HERE / "fixtures" / "demo_github.json").read_text(encoding="utf-8"))
NOW = dm.ts(FIX["now"])


def demo_config(**over) -> dict:
    cfg = copy.deepcopy(dm.load_config())
    cfg.update({"org": FIX["org"], "request_budget": 400, "rate_limit_floor": 10})
    cfg["apps"] = [{"id": "demo", "name": "Demo", "repo": FIX["repo"], "default_branch": "main",
                    "deploy_workflows": ["deploy.yml"], "deploy_job": "^Deploy to Dev$",
                    "verify_job": "^Post-deploy verify", "ci_workflows": ["ci.yml"],
                    "no_deploy_paths": ["docs/**", "*.md", "**/*.md"]}]
    cfg.update(over)
    return cfg


class FakeGitHub:
    """Answers GET https://api.github.com/... from the fixture, 100 items a page."""

    def __init__(self, remaining: int = 900):
        self.calls: list[str] = []
        self.remaining = remaining

    def __call__(self, url: str):
        self.calls.append(url)
        parsed = urllib.parse.urlparse(url)
        q = dict(urllib.parse.parse_qsl(parsed.query))
        parts = parsed.path.strip("/").split("/")
        page, per = int(q.get("page", 1)), int(q.get("per_page", 100))
        self.remaining -= 1
        headers = {"x-ratelimit-remaining": str(self.remaining)}
        if parts[:3] != ["repos", FIX["org"], FIX["repo"]]:
            return 404, headers, b'{"message": "Not Found"}'
        rest = parts[3:]

        def paged(items):
            return items[(page - 1) * per: page * per]

        if rest == ["actions", "runs"]:
            day = q["created"]
            items = [r for r in FIX["runs"] if r["created_at"][:10] == day]
            body = {"total_count": len(items), "workflow_runs": paged(items)}
        elif len(rest) == 4 and rest[:2] == ["actions", "runs"] and rest[3] == "jobs":
            items = FIX["jobs"].get(rest[2], [])
            body = {"total_count": len(items), "jobs": paged(items)}
        elif rest == ["pulls"]:
            body = paged(sorted(FIX["pulls"], key=lambda p: p["updated_at"], reverse=True))
        elif len(rest) == 3 and rest[0] == "pulls" and rest[2] == "files":
            body = paged(FIX["files"].get(rest[1], []))
        elif rest == ["deployments"]:
            body = paged(sorted((d for d in FIX["deployments"] if d["environment"] == q.get("environment")),
                                key=lambda d: d["id"], reverse=True))
        else:
            return 404, headers, b"{}"
        return 200, headers, json.dumps(body).encode()


def collected(cfg=None) -> tuple[dict, dm.Store, dict, FakeGitHub]:
    cfg = cfg or demo_config()
    fake = FakeGitHub()
    store = dm.Store()
    report = dm.collect(cfg, store, dm.GitHub(fake, cfg["request_budget"], cfg["rate_limit_floor"]), NOW)
    return cfg, store, report, fake


class SummaryFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.store, cls.report, cls.fake = collected()
        cls.summary = dm.summarize(cls.cfg, cls.store, NOW, {"repo": "AA-Ecosys"}, cls.report)
        cls.app = cls.summary["apps"][0]

    def deploy(self, sha: str, redeploy: bool = False) -> dict:
        found = [d for d in self.app["deploys"] if d["sha"].startswith(sha) and d["redeploy"] == redeploy]
        self.assertTrue(found, f"no deploy of {sha}")
        return found[-1]   # oldest first among the matches (the list is newest first)


class TestCollect(SummaryFixture):
    def test_reads_every_kind_of_event_and_keeps_state(self):
        kinds = {e["event"] for e in self.store.events.values()}
        self.assertEqual(kinds, {"cicd.pipeline.run", "cicd.pipeline.task.run", "vcs.change", "deployment",
                                 "aa.jobs.read"})
        st = self.store.repo_state(FIX["repo"])
        self.assertEqual(st["runs_forward_day"], "2026-03-20")
        first = NOW.date() - dm.timedelta(days=self.cfg["store_days"])
        self.assertEqual(st["runs_complete_since"], first.isoformat())
        self.assertEqual(st["deployments_max_id"], 9002)
        self.assertIsNone(self.report["stopped"])
        self.assertEqual(self.report["errors"], [])

    def test_second_run_is_incremental(self):
        fake = FakeGitHub()
        cfg = self.cfg
        store = dm.Store(copy.deepcopy(self.store.events), copy.deepcopy(self.store.state))
        dm.collect(cfg, store, dm.GitHub(fake, cfg["request_budget"], cfg["rate_limit_floor"]), NOW)
        # 3 run days, 1 pull request page, 1 deployment page; no job, file or backfill read again
        self.assertEqual(len(fake.calls), 5, fake.calls)

    def test_budget_stop_keeps_what_was_read(self):
        cfg = demo_config(request_budget=4)
        _cfg, store, report, fake = collected(cfg)
        self.assertEqual(len(fake.calls), 4)
        self.assertIn("used 4 of 4", report["stopped"])
        self.assertTrue(store.events)

    def test_cold_store_shares_the_budget_between_phases(self):
        cfg = demo_config(request_budget=40)
        _cfg, store, report, fake = collected(cfg)
        st = store.repo_state(FIX["repo"])
        # backfill stops at 60 % of the budget, so the deploy runs' jobs and later phases still get requests
        self.assertGreater(st["runs_complete_since"], (NOW.date() - dm.timedelta(days=cfg["store_days"])).isoformat())
        self.assertLess(st["runs_complete_since"], "2026-03-18")
        self.assertTrue(any("/jobs" in u for u in fake.calls))
        self.assertTrue(any("/files" in u for u in fake.calls))
        self.assertLessEqual(report["requests"], 40)

    def test_rate_limit_floor_stops(self):
        cfg = demo_config()
        fake = FakeGitHub(remaining=12)
        report = dm.collect(cfg, dm.Store(), dm.GitHub(fake, 400, 10), NOW)
        self.assertIsNotNone(report["stopped"])
        self.assertLessEqual(len(fake.calls), 3)

    def test_unknown_repo_is_an_error_not_a_crash(self):
        cfg = demo_config()
        cfg["apps"][0]["repo"] = "no-such-repo"
        _c, _s, report, _f = collected(cfg)
        self.assertTrue(any("HTTP 404" in e for e in report["errors"]))
        self.assertFalse(report["repos"]["no-such-repo"]["read"])

    def test_docs_only_from_files(self):
        prs = {e["attributes"]["vcs.change.id"]: e for e in self.store.of("vcs.change")}
        self.assertTrue(prs[14]["attributes"]["aa.docs_only"])
        self.assertFalse(prs[10]["attributes"]["aa.docs_only"])

    def test_store_round_trip_and_day_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.store.save(Path(tmp))
            again = dm.Store.load(Path(tmp))
            self.assertEqual(again.events, self.store.events)
            self.assertEqual(again.state, self.store.state)
            with gzip.open(Path(tmp) / dm.STORE_EVENTS, "rt") as fh:
                self.assertEqual(sum(1 for _ in fh), len(self.store.events))
        files = self.store.day_files(self.store.touched_days)
        self.assertIn("2026-03-16", files)
        for day, events in files.items():
            self.assertTrue(all(e["time"].startswith(day) for e in events))

    def test_prune_drops_old_events(self):
        store = dm.Store(copy.deepcopy(self.store.events))
        dropped = store.prune(dm.ts("2026-03-18T00:00:00Z"))
        self.assertGreater(dropped, 0)
        self.assertTrue(all(e["time"] >= "2026-03-18" for e in store.events.values()))


class TestNormalise(unittest.TestCase):
    def test_run_event_uses_otel_names(self):
        r = next(r for r in FIX["runs"] if r["name"] == "Deploy Dev" and r["conclusion"] == "success")
        e = dm.run_event(FIX["repo"], r)
        a = e["attributes"]
        self.assertEqual(e["event"], "cicd.pipeline.run")
        self.assertEqual(a["cicd.pipeline.name"], "Deploy Dev")
        self.assertEqual(a["cicd.pipeline.result"], "success")
        self.assertEqual(a["cicd.pipeline.run.state"], "finalizing")
        self.assertEqual(a["aa.workflow.file"], "deploy.yml")
        self.assertEqual(a["vcs.ref.head.name"], "main")
        self.assertEqual(a["aa.duration_s"], 15 * 60)

    def test_result_values(self):
        self.assertEqual(dm.RESULTS["cancelled"], "cancellation")
        self.assertEqual(dm.RESULTS["timed_out"], "timeout")
        running = dm.run_event("r", {"id": 1, "status": "in_progress", "conclusion": None,
                                     "created_at": "2026-03-20T10:00:00Z", "updated_at": "2026-03-20T10:01:00Z"})
        self.assertIsNone(running["attributes"]["cicd.pipeline.result"])
        self.assertEqual(running["attributes"]["cicd.pipeline.run.state"], "executing")

    def test_pr_event_revert_fix_and_author(self):
        prs = {p["number"]: dm.pr_event(FIX["repo"], p, ["aa-agent[bot]"])["attributes"] for p in FIX["pulls"]}
        self.assertEqual(prs[16]["aa.revert_of"], 15)
        self.assertEqual(prs[16]["aa.change_type"], "revert")
        self.assertEqual(prs[12]["aa.change_type"], "fix")
        self.assertEqual(prs[12]["aa.references"], [11])
        self.assertEqual(prs[11]["aa.author.kind"], "human")
        self.assertIsNone(prs[11]["aa.author.login"], "a person's login is not stored")
        self.assertEqual(prs[13]["aa.author.kind"], "bot")
        self.assertEqual(prs[10]["aa.author.kind"], "agent")
        self.assertEqual(prs[10]["vcs.change.time_to_merge"], 80 * 60)
        self.assertEqual(prs[10]["vcs.change.state"], "merged")


class TestDeploys(SummaryFixture):
    def test_outcomes_and_reasons(self):
        self.assertEqual(self.deploy("s10")["outcome"], "success")
        self.assertEqual(self.deploy("s10")["deployment_records"], 2)
        d2 = self.deploy("s11")
        self.assertEqual(d2["outcome"], "verify_failed")
        self.assertEqual(sorted(d2["failed"]), ["hotfix", "verify_red"])
        self.assertEqual(d2["recovery_h"], 1.083)        # verify red 12:15 -> hotfix deploy verified 13:20
        self.assertEqual(self.deploy("s12")["rework"], ["hotfix"])
        d5 = self.deploy("s15")
        self.assertEqual(sorted(d5["failed"]), ["reverted", "rolled_back"])
        self.assertEqual(d5["recovery_h"], 1.917)        # 09:20 -> the rollback verified 11:15
        rollback = next(d for d in self.app["deploys"] if d["started_at"] == "2026-03-18T11:00:00Z")
        self.assertTrue(rollback["sha"].startswith("s13"))
        self.assertFalse(rollback["redeploy"], "an older commit after another one is a rollback, not a redeploy")
        self.assertEqual(rollback["rework"], ["rollback"])
        self.assertEqual(self.deploy("s16")["rework"], ["reverted"])
        d8 = self.deploy("s17")
        self.assertEqual(d8["outcome"], "deploy_failed")
        self.assertEqual(d8["failed"], ["deploy_job_failed"])
        self.assertEqual(d8["recovery_h"], 0.917)        # 09:25 -> the redeploy verified 10:20
        self.assertTrue(self.deploy("s17", redeploy=True)["redeploy"])

    def test_cancelled_and_running_runs_are_not_deploys(self):
        shas = {d["sha"] for d in self.app["deploys"]}
        self.assertNotIn("s99", shas)
        self.assertNotIn("s98", shas)

    def test_dora_keys_with_n(self):
        d = self.app["dora"]
        self.assertEqual(d["deployment_frequency"]["n"], 6)
        self.assertEqual(d["deployment_frequency"]["attempts"], 8)
        self.assertEqual(d["deployment_frequency"]["value"], 1.5)       # 6 green deploys in 4 weeks
        self.assertEqual(d["change_failure_rate"]["value"], 0.375)       # 3 of 8
        self.assertEqual(d["change_failure_rate"]["by_reason"],
                         {"deploy_job_failed": 1, "hotfix": 1, "reverted": 1, "rolled_back": 1, "verify_red": 1})
        self.assertEqual(d["rework_rate"]["value"], 0.375)               # hotfix, rollback, revert deploys
        self.assertEqual(d["recovery_time"], {"p50_h": 1.083, "p90_h": 1.917, "n": 3, "open": 0})
        self.assertEqual(d["lead_time"]["n"], 6)                          # bot (13) and docs-only (14) left out
        self.assertEqual(d["lead_time"]["p50_h"], 1.333)

    def test_lead_time_segments(self):
        seg = {s["segment"]: s for s in self.app["lead_time_segments"]}
        self.assertEqual(set(seg), {"to_first_green", "to_queue", "to_merge", "to_deploy", "to_verify"})
        self.assertEqual(seg["to_first_green"]["n"], 2)    # PR 10 (linked run) and PR 11 (head branch fallback)
        rows = {c["number"]: c for c in self.app["changes"]["slowest"]}
        self.assertEqual(rows[10]["segments"], {"to_first_green": 0.333, "to_queue": 0.667, "to_merge": 0.333,
                                                "to_deploy": 0.25, "to_verify": 0.083})
        self.assertEqual(rows[11]["segments"]["to_first_green"], 0.5)
        self.assertEqual(rows[11]["lead_time_h"], 3.333)   # its own deploy failed verify: the hotfix deploy counts

    def test_changes_by_kind(self):
        ch = self.app["changes"]
        self.assertEqual(ch["merged"], 8)
        self.assertEqual(ch["by_kind"], {"agent": 6, "human": 1, "bot": 1})
        self.assertEqual(ch["docs_only"], 1)
        self.assertEqual([b["number"] for b in ch["bot"]], [13])

    def test_merge_queue(self):
        self.assertEqual(self.app["merge_queue"], {"wait_p50_h": 0.333, "wait_p95_h": 0.417, "n": 2, "ejections": 1})


class TestCiHealth(SummaryFixture):
    def test_main_red_since(self):
        main = self.app["ci"]["main"]
        self.assertEqual(main["state"], "red")
        self.assertEqual(main["red_since"], "2026-03-20T09:00:00Z")
        self.assertEqual(main["red_hours"], 3.0)
        self.assertEqual(main["failure_rate"], 0.3333)
        self.assertEqual(main["n"], 12)

    def test_workflow_table(self):
        wf = {w["name"]: w for w in self.app["ci"]["workflows"]}
        self.assertEqual(wf["CI"]["kind"], "ci")
        self.assertEqual(wf["Deploy Dev"]["kind"], "deploy")
        self.assertEqual(wf["CI"]["reruns"], 1)
        self.assertEqual(wf["Deploy Dev"]["failures"], 2)
        self.assertIsNotNone(wf["Deploy Dev"]["p95_s"])
        self.assertEqual(self.app["ci"]["slowest"]["name"], "CI")          # the 28-minute pull request run
        self.assertGreater(self.app["ci"]["minutes"]["total"], 0)
        self.assertGreater(self.app["ci"]["minutes"]["coverage"], 0.9)

    def test_flaky_job(self):
        self.assertEqual(self.app["flaky"][0]["job"], "unit tests")
        self.assertEqual(self.app["flaky"][0]["flips"], 1)

    def test_verify_block(self):
        v = self.app["verify"]
        self.assertEqual(v["red"], 1)
        self.assertEqual(v["last_red_at"], "2026-03-16T12:15:00Z")


class TestTrendAndShape(SummaryFixture):
    def test_trend_weeks_and_months(self):
        weeks = self.app["trend"]["weeks"]
        self.assertEqual(len(weeks), self.cfg["trend_weeks"])
        self.assertEqual(weeks[-1]["week"], "2026-W12")
        self.assertTrue(weeks[-1]["partial"])
        self.assertEqual(weeks[-1]["deploys"], 6)
        months = self.app["trend"]["months"]
        self.assertEqual([m["month"] for m in months], ["2026-01", "2026-02", "2026-03"])
        self.assertEqual(months[-1]["failed"], 3)
        self.assertEqual(len(months[-1]["failed_deploys"]), 3)

    def test_summary_shape(self):
        s = self.summary
        self.assertEqual(s["format"], 1)
        self.assertEqual(s["environment"], "dev")
        self.assertEqual(s["definitions"]["rework_hours"], 48)
        json.dumps(s)   # serialisable
        for key in ("dora", "lead_time_segments", "ci", "merge_queue", "flaky", "verify", "deploys",
                    "failed_deploys", "changes", "trend", "window", "complete_since"):
            self.assertIn(key, self.app)

    def test_incomplete_history_clips_the_window(self):
        store = dm.Store(copy.deepcopy(self.store.events), copy.deepcopy(self.store.state))
        store.repo_state(FIX["repo"])["runs_complete_since"] = "2026-03-18"
        app = dm.summarize(self.cfg, store, NOW)["apps"][0]
        self.assertEqual(app["window"]["start"], "2026-03-18T00:00:00Z")
        self.assertEqual(app["window"]["covered_days"], 2.5)
        # pull requests merged before the complete history are not matched to a deploy
        self.assertTrue(all(c["number"] >= 15 for c in app["changes"]["slowest"]))


class TestRunOutcome(unittest.TestCase):
    APP = {"deploy_job": "^Deploy to Dev$", "verify_job": "^Post-deploy verify"}

    def run_(self, result="success"):
        return {"attributes": {"cicd.pipeline.result": result, "cicd.pipeline.run.state": "finalizing"}}

    def job(self, name, result, attempt=1):
        return {"attributes": {"cicd.pipeline.task.name": name, "cicd.pipeline.task.run.result": result,
                               "aa.run_attempt": attempt}}

    def test_cases(self):
        o = dm.run_outcome
        self.assertEqual(o(self.APP, self.run_(), None), "unclassified")
        self.assertEqual(o(self.APP, self.run_("cancellation"), []), "cancelled")
        self.assertEqual(o(self.APP, self.run_("failure"), [self.job("Build image", "failure")]), "not_deployed")
        self.assertEqual(o(self.APP, self.run_("failure"), [self.job("Deploy to Dev", "failure")]), "deploy_failed")
        self.assertEqual(o(self.APP, self.run_("failure"), [self.job("Deploy to Dev", "success"),
                                                           self.job("Post-deploy verify", "failure")]), "verify_failed")
        # the latest attempt decides: a re-run that passed is green
        self.assertEqual(o(self.APP, self.run_(), [self.job("Deploy to Dev", "failure", 1),
                                                   self.job("Deploy to Dev", "success", 2)]), "success")
        running = {"attributes": {"cicd.pipeline.result": None, "cicd.pipeline.run.state": "executing"}}
        self.assertEqual(o(self.APP, running, []), "running")
        self.assertEqual(o({"deploy_job": "^Docs sync$", "verify_job": None}, self.run_(),
                           [self.job("Docs sync", "success")]), "success")


class TestHelpers(unittest.TestCase):
    def test_percentile_nearest_rank(self):
        self.assertIsNone(dm.percentile([], 50))
        self.assertEqual(dm.percentile([3, 1, 2], 50), 2)
        self.assertEqual(dm.percentile([1, 2, 3, 4], 95), 4)
        self.assertEqual(dm.percentile([5], 95), 5)

    def test_expired_keys(self):
        keys = ["docs-reader/delivery/events/2025/01/01.ndjson", "docs-reader/delivery/events/2026/03/01.ndjson",
                "docs-reader/delivery/summary.json", "docs-reader/delivery/events/2025/02/10.ndjson",
                "docs-reader/delivery/events/2025/02/15.ndjson"]
        # 400 days before 2026-03-20 is 2025-02-13
        self.assertEqual(dm.expired_keys(keys, date(2026, 3, 20), 400),
                         ["docs-reader/delivery/events/2025/01/01.ndjson",
                          "docs-reader/delivery/events/2025/02/10.ndjson"])

    def test_repo_config_is_valid(self):
        cfg = dm.load_config()
        self.assertEqual({a["repo"] for a in cfg["apps"]},
                         {"AA-Ecosys", "AA-CIS-App", "AA-Booking", "AA-Partner", "AA-TripPlanner-Web", "AA-CIS-Infra"})
        self.assertEqual(cfg["rework_hours"], 48)
        self.assertEqual(cfg["raw_retention_days"], 400)
        self.assertLessEqual(cfg["request_budget"], 900, "GITHUB_TOKEN allows 1,000 requests an hour")

    def test_bad_config_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "apps.json"
            p.write_text(json.dumps({"format": 1, "apps": []}))
            with self.assertRaises(dm.ConfigError):
                dm.load_config(p)

    def test_cli_summarize_and_expired(self):
        cfg, store, _r, _f = collected()
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "cfg.json").write_text(json.dumps(cfg))
            store.save(t / "store")
            rc = dm.main(["summarize", "--config", str(t / "cfg.json"), "--store", str(t / "store"), "--out",
                          str(t / "out"), "--now", FIX["now"]])
            self.assertEqual(rc, 0)
            summary = json.loads((t / "out" / "summary.json").read_text())
            self.assertEqual(summary["apps"][0]["id"], "demo")
            self.assertTrue((t / "out" / "events" / "2026" / "03" / "16.ndjson").exists())
            (t / "keys.txt").write_text("docs-reader/delivery/events/2020/01/01.ndjson\n")
            self.assertEqual(dm.main(["expired", "--keys", str(t / "keys.txt"), "--today", "2026-03-20"]), 0)


if __name__ == "__main__":
    unittest.main()
