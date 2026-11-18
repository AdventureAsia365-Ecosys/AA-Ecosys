"""Unit tests of tools/delivery/delivery_metrics.py (AA-1108) on recorded GitHub API answers of an invented repo.

fixtures/demo_github.json holds the runs, jobs, merged pull requests, deployments and pull request files of one
invented repo (example-org/demo-app) over five days, written to cover every definition of the delivery metrics:
a green deploy, a red post-deploy verify repaired by a hotfix pull request, a rollback, a revert, a failed deploy job
repaired by a redeploy, a bot pull request, a docs-only pull request, a merge-queue ejection, a flaky job and a red
main. AA-1125 adds the main branch's commits with their files (one older than the 90-day window, a dependabot bump,
a person's change, a ci-bot docs copy, a release-please release) and the merge-queue timelines of pull requests 10
(straight merge) and 11 (ejected on red checks, back in the queue with no new commit, merged). No network: a fake
transport answers from the fixture.

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

import delivery_engine as de  # noqa: E402
import delivery_metrics as dm  # noqa: E402
import sync_engine  # noqa: E402

FIX = json.loads((HERE / "fixtures" / "demo_github.json").read_text(encoding="utf-8"))
NOW = dm.ts(FIX["now"])


def demo_config(**over) -> dict:
    cfg = copy.deepcopy(dm.load_config())
    cfg.update({"org": FIX["org"], "request_budget": 400, "rate_limit_floor": 10})
    cfg["apps"] = [{"id": "demo", "name": "Demo", "repo": FIX["repo"], "default_branch": "main",
                    "deploy_workflows": ["deploy.yml"], "deploy_job": "^Deploy to Dev$",
                    "verify_job": "^Post-deploy verify", "ci_workflows": ["ci.yml"],
                    "no_deploy_paths": ["docs/**", "*.md", "**/*.md"], "merge_queue": True}]
    cfg.update(over)
    return cfg


class FakeGitHub:
    """Answers GET https://api.github.com/... from the fixture, 100 items a page."""

    def __init__(self, remaining: int = 900, aliases: tuple = ()):
        self.calls: list[str] = []
        self.remaining = remaining
        self.repos = (FIX["repo"], *aliases)   # S284: extra repo names answered from the same fixture

    def __call__(self, url: str):
        self.calls.append(url)
        parsed = urllib.parse.urlparse(url)
        q = dict(urllib.parse.parse_qsl(parsed.query))
        parts = parsed.path.strip("/").split("/")
        page, per = int(q.get("page", 1)), int(q.get("per_page", 100))
        self.remaining -= 1
        headers = {"x-ratelimit-remaining": str(self.remaining)}
        if parts[:2] != ["repos", FIX["org"]] or len(parts) < 3 or parts[2] not in self.repos:
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
        elif rest == ["commits"]:
            items = [c for c in FIX["commits"] if c["commit"]["committer"]["date"] >= q.get("since", "")]
            body = paged(items)
        elif len(rest) == 2 and rest[0] == "commits":
            if rest[1] not in FIX["commit_details"]:
                return 404, headers, b"{}"
            body = FIX["commit_details"][rest[1]]
        elif len(rest) == 3 and rest[0] == "issues" and rest[2] == "timeline":
            body = paged(FIX["timelines"].get(rest[1], []))
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
                                 "aa.jobs.read", "aa.vcs.commit", "aa.merge_queue.timeline"})
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
        # 3 run days, 1 pull request page, 1 deployment page, 1 commit page; no job, file, settled queue timeline or
        # backfill read again
        self.assertEqual(len(fake.calls), 6, fake.calls)
        self.assertTrue(fake.calls[-1].startswith(f"{dm.API}/repos/{FIX['org']}/{FIX['repo']}/commits?"))

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
                    "failed_deploys", "changes", "trend", "window", "complete_since", "queue", "git"):
            self.assertIn(key, self.app)

    def test_incomplete_history_clips_the_window(self):
        store = dm.Store(copy.deepcopy(self.store.events), copy.deepcopy(self.store.state))
        store.repo_state(FIX["repo"])["runs_complete_since"] = "2026-03-18"
        app = dm.summarize(self.cfg, store, NOW)["apps"][0]
        self.assertEqual(app["window"]["start"], "2026-03-18T00:00:00Z")
        self.assertEqual(app["window"]["covered_days"], 2.5)
        # pull requests merged before the complete history are not matched to a deploy
        self.assertTrue(all(c["number"] >= 15 for c in app["changes"]["slowest"]))


class TestMergeQueue(SummaryFixture):
    """AA-1125: the merge-queue section (pull request 10 straight in, 11 ejected on red checks then back and merged)."""

    def test_entries_wait_and_outcomes(self):
        q = self.app["queue"]
        self.assertEqual((q["entries"], q["prs"], q["merged"], q["ejected"], q["removed"], q["in_queue"]),
                         (3, 2, 2, 1, 0, 0))
        self.assertEqual(q["wait"], {"p50_h": 0.233, "p95_h": 0.367, "n": 2})
        # from the first entry to the merge: pull request 11 waited through its ejection
        self.assertEqual(q["to_merge"], {"p50_h": 0.367, "p95_h": 0.45, "n": 2})
        self.assertEqual(q["ejection_rate"], {"value": 0.3333, "n": 3, "ejected": 1})

    def test_ejection_reason_and_flaky_signal(self):
        q = self.app["queue"]
        self.assertEqual(len(q["reasons"]), 1)
        r = q["reasons"][0]
        self.assertEqual((r["reason"], r["n"], r["workflows"], r["last_pr"]), ("checks_failed", 1, {"CI": 1}, 11))
        self.assertTrue(r["last_url"].endswith("/actions/runs/1005"))
        self.assertEqual(q["flaky"], {"value": 0.3333, "n": 3, "flaky": 1, "rerun_green": 0, "reentry_green": 1})
        self.assertEqual([(e["pr"], e["attempt"], e["flaky"]) for e in q["flaky_entries"]], [(11, 1, "reentry_green")])

    def test_each_run_counts_for_one_entry(self):
        rows = {(e["pr"], e["attempt"]): e for e in self.app["queue"]["recent"]}
        self.assertEqual(set(rows), {(10, 1), (11, 1), (11, 2)})
        self.assertTrue(rows[(11, 1)]["run_url"].endswith("/runs/1005"))
        self.assertTrue(rows[(11, 2)]["run_url"].endswith("/runs/1006"))   # 10:46, the second entry's own run
        self.assertEqual((rows[(11, 1)]["runs"], rows[(11, 2)]["runs"]), (1, 1))
        self.assertFalse(rows[(11, 2)]["new_commit"])
        self.assertEqual(rows[(10, 1)]["url"], f"https://github.com/{FIX['org']}/{FIX['repo']}/pull/10")

    def test_merge_group_ci(self):
        ci = self.app["queue"]["ci"]
        self.assertEqual((ci["runs"], ci["failures"], ci["failure_rate"], ci["reruns"]), (3, 1, 0.3333, 0))
        self.assertGreater(ci["minutes"], 0)
        self.assertEqual([w["name"] for w in ci["workflows"]], ["CI"])

    def test_throughput_per_day(self):
        days = {d["date"]: d for d in self.app["queue"]["throughput"]}
        self.assertEqual(len(days), self.cfg["headline_days"] + 1)   # the window starts and ends at noon
        self.assertEqual(days["2026-03-16"], {"date": "2026-03-16", "merged": 2, "ejected": 1, "removed": 0})

    def test_timelines_take_turns_across_apps(self):
        """S284: one app's backlog must not starve the next app (Booking and Partner read 0 timelines behind CIS)."""
        cfg = demo_config()
        twin = copy.deepcopy(cfg["apps"][0])
        twin.update({"id": "twin", "name": "Twin", "repo": "demo-twin"})
        cfg["apps"].append(twin)
        fake = FakeGitHub(aliases=("demo-twin",))
        store = dm.Store()
        dm.collect(cfg, store, dm.GitHub(fake, cfg["request_budget"], cfg["rate_limit_floor"]), NOW)
        order = [u.split("/repos/")[1].split("/")[1] for u in fake.calls if "/timeline" in u]
        self.assertEqual(order, [FIX["repo"], "demo-twin", FIX["repo"], "demo-twin"])
        for repo in (FIX["repo"], "demo-twin"):
            self.assertEqual(len(store.of("aa.merge_queue.timeline", repo)), 2, repo)

    def test_app_without_merge_queue_has_no_section(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["apps"][0]["merge_queue"] = False
        self.assertIsNone(dm.summarize(cfg, self.store, NOW)["apps"][0]["queue"])


class TestRanges(SummaryFixture):
    """AA-1135: the presets of the range picker and the custom range from the published day files (the parity)."""

    def test_presets_per_app(self):
        ranges = self.app["ranges"]
        self.assertEqual(sorted(ranges), ["d28", "d7", "d90"])
        self.assertEqual(self.summary["definitions"]["range_presets"], [7, 28, 90])
        for n in (7, 28, 90):
            r = ranges[f"d{n}"]
            self.assertEqual(r["window"]["days"], n)
            self.assertEqual(r["window"]["end"], FIX["now"])
            for key in ("dora", "lead_time_segments", "ci", "merge_queue", "flaky", "verify", "deploys",
                        "failed_deploys", "changes", "queue", "git"):
                self.assertIn(key, r)

    def test_the_28_day_preset_is_the_headline(self):
        r = self.app["ranges"]["d28"]
        for key in ("dora", "lead_time_segments", "ci", "merge_queue", "flaky", "verify", "changes", "queue"):
            self.assertEqual(r[key], self.app[key], key)
        self.assertEqual(r["window"]["start"], self.app["window"]["start"])

    def test_a_short_preset_counts_less(self):
        cfg = demo_config(range_presets=[1, 7])
        app = dm.summarize(cfg, self.store, NOW)["apps"][0]
        one, week = app["ranges"]["d1"], app["ranges"]["d7"]
        self.assertEqual(one["window"]["requested_start"], "2026-03-19T12:00:00Z")
        self.assertLess(one["dora"]["deployment_frequency"]["attempts"],
                        week["dora"]["deployment_frequency"]["attempts"])
        self.assertLessEqual(len(one["deploys"]), len(week["deploys"]))
        self.assertEqual(len(one["git"]["daily"]), 2)   # noon to noon touches two days

    def test_segments_carry_p95(self):
        seg = {s["segment"]: s for s in self.app["lead_time_segments"]}
        self.assertIn("p95_h", seg["to_merge"])
        self.assertGreaterEqual(seg["to_merge"]["p95_h"], seg["to_merge"]["p50_h"])

    def test_definitions_name_the_engine_and_the_store(self):
        d = self.summary["definitions"]
        self.assertEqual(d["engine_sha256"], de.engine_sha256())
        self.assertEqual(len(d["engine_sha256"]), 64)
        self.assertEqual(d["store_from"], "2025-12-12")   # 98 days before 2026-03-20
        self.assertEqual(self.summary["config"]["apps"][0]["repo"], FIX["repo"])

    def published(self) -> tuple[dict, dict]:
        """The summary and the day files as the workflow uploads them, read back the way CIS reads them."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            days = {(e.get("time") or "")[:10] for e in self.store.events.values()}
            dm.write_outputs(out, self.summary, self.store.day_files(days))
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            texts = [(out / k).read_text(encoding="utf-8") if (out / k).exists() else None
                     for k in de.day_keys(summary["config"], NOW)]
        return summary, de.load_events(texts)

    def test_custom_range_equals_each_preset(self):
        """The parity test: a custom range over a preset's window gives the preset's numbers exactly."""
        summary, events = self.published()
        self.assertEqual(len(events), len(self.store.events))
        for n in (7, 28, 90):
            got = de.custom_range(summary, events, NOW - dm.timedelta(days=n), NOW)
            self.assertEqual(got["engine_sha256"], summary["definitions"]["engine_sha256"])
            self.assertEqual(got["apps"][0]["id"], "demo")
            self.assertEqual(json.dumps(got["apps"][0]["range"], sort_keys=True),
                             json.dumps(summary["apps"][0]["ranges"][f"d{n}"], sort_keys=True), f"d{n}")

    def test_custom_range_of_any_window_equals_the_store(self):
        summary, events = self.published()
        a, b = dm.ts("2026-03-16T00:00:00Z"), dm.ts("2026-03-18T00:00:00Z")
        got = de.custom_range(summary, events, a, b)["apps"][0]["range"]
        ctx = de.app_context(self.cfg, self.cfg["apps"][0], self.store, NOW)
        want = de.range_block(self.cfg, self.cfg["apps"][0], ctx, a, b)
        self.assertEqual(json.dumps(got, sort_keys=True), json.dumps(want, sort_keys=True))
        self.assertEqual(got["window"]["days"], 2.0)

    def test_an_older_copy_in_an_earlier_day_file_loses(self):
        e = next(e for e in self.store.events.values() if e["event"] == "cicd.pipeline.run")
        stale = copy.deepcopy(e)
        stale["time"] = "2026-03-01T00:00:00Z"
        stale["attributes"]["cicd.pipeline.result"] = None
        line = json.dumps(e) + "\n"
        events = de.load_events([json.dumps(stale) + "\n", None, line, "\n"])
        self.assertEqual(events[e["id"]], e)
        events = de.load_events([line, json.dumps(stale) + "\n"])   # order of the files does not matter
        self.assertEqual(events[e["id"]], e)

    def test_events_before_the_store_are_left_out(self):
        summary, events = self.published()
        old = copy.deepcopy(next(e for e in events.values() if e["event"] == "deployment"))
        old["id"], old["time"] = "demo/deployment/old", "2025-12-01T00:00:00Z"
        got = de.custom_range(summary, {**events, old["id"]: old}, NOW - dm.timedelta(days=7), NOW)
        self.assertEqual(json.dumps(got["apps"][0]["range"], sort_keys=True),
                         json.dumps(summary["apps"][0]["ranges"]["d7"], sort_keys=True))

    def test_definitions_carry_the_store_fingerprint(self):
        fp = self.summary["definitions"]["store_fingerprint"]
        self.assertEqual(sorted(fp), [FIX["repo"]])
        self.assertEqual(fp[FIX["repo"]]["events"], len(self.store.events))
        self.assertEqual(len(fp[FIX["repo"]]["sha256"]), 64)
        # the order the events were stored in does not change it
        shuffled = dict(reversed(list(self.store.events.items())))
        self.assertEqual(de.store_fingerprint(shuffled.values(), de.store_cut(self.cfg, NOW)), fp)

    def test_a_day_file_missing_an_event_is_refused(self):
        """A failed upload or a lost cache: the day files no longer rebuild the store, so no custom range."""
        summary, events = self.published()
        dropped = next(k for k, e in events.items() if e["event"] == "deployment")
        with self.assertRaises(de.StoreMismatch) as err:
            de.custom_range(summary, {k: v for k, v in events.items() if k != dropped}, NOW - dm.timedelta(days=7),
                            NOW)
        self.assertIn(FIX["repo"], str(err.exception))

    def test_a_day_file_with_a_changed_or_extra_event_is_refused(self):
        summary, events = self.published()
        run = copy.deepcopy(next(e for e in events.values() if e["event"] == "cicd.pipeline.run"))
        run["attributes"]["cicd.pipeline.result"] = "failure" if run["attributes"].get(
            "cicd.pipeline.result") != "failure" else "success"
        with self.assertRaises(de.StoreMismatch):
            de.custom_range(summary, {**events, run["id"]: run}, NOW - dm.timedelta(days=7), NOW)
        extra = {**copy.deepcopy(run), "id": "demo/run/extra"}
        with self.assertRaises(de.StoreMismatch):
            de.custom_range(summary, {**events, extra["id"]: extra}, NOW - dm.timedelta(days=7), NOW)

    def test_a_summary_without_a_fingerprint_is_refused(self):
        summary, events = self.published()
        summary["definitions"].pop("store_fingerprint")
        with self.assertRaises(de.StoreMismatch):
            de.custom_range(summary, events, NOW - dm.timedelta(days=7), NOW)

    def test_an_event_that_moves_day_rewrites_its_old_day(self):
        store = dm.Store(copy.deepcopy(self.store.events))
        e = copy.deepcopy(next(e for e in store.events.values() if e["event"] == "cicd.pipeline.run"))
        old_day = e["time"][:10]
        e["time"] = "2026-03-20T09:00:00Z" if old_day != "2026-03-20" else "2026-03-19T09:00:00Z"
        store.touched_days.clear()
        self.assertTrue(store.put(e))
        self.assertEqual(store.touched_days, {old_day, e["time"][:10]})
        files = store.day_files(store.touched_days)
        self.assertNotIn(e["id"], [x["id"] for x in files.get(old_day, [])])

    def test_all_days_writes_every_day_of_the_store(self):
        """A run without a cached store (or a repair) overwrites every day file, so stale S3 days cannot linger."""
        files = dm.output_days(self.cfg, self.store, NOW, all_days=True)
        self.assertEqual(sorted(files), de.store_days(self.cfg, NOW))
        self.assertEqual(files["2025-12-12"], [])
        self.assertEqual(sum(len(v) for v in files.values()), len(self.store.events))
        self.store.touched_days.clear()
        self.assertEqual(dm.output_days(self.cfg, self.store, NOW, all_days=False), {})
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            stale = out / "events" / "2025" / "12" / "12.ndjson"
            stale.parent.mkdir(parents=True)
            stale.write_text(json.dumps({**next(iter(self.store.events.values())), "id": "demo/old/stale"}) + "\n",
                             encoding="utf-8")
            dm.write_outputs(out, self.summary, files)
            self.assertEqual(stale.read_text(encoding="utf-8"), "")
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            texts = [(out / k).read_text(encoding="utf-8") for k in de.day_keys(summary["config"], NOW)]
        got = de.custom_range(summary, de.load_events(texts), NOW - dm.timedelta(days=7), NOW)
        self.assertEqual(json.dumps(got["apps"][0]["range"], sort_keys=True),
                         json.dumps(summary["apps"][0]["ranges"]["d7"], sort_keys=True))

    def test_store_order_is_deterministic(self):
        shuffled = dm.Store(dict(reversed(list(self.store.events.items()))), self.store.state)
        self.assertEqual([e["id"] for e in shuffled.of("cicd.pipeline.run")],
                         [e["id"] for e in self.store.of("cicd.pipeline.run")])

    def test_day_keys_cover_the_store(self):
        keys = de.day_keys(self.cfg, NOW)
        self.assertEqual(keys[0], "events/2025/12/12.ndjson")
        self.assertEqual(keys[-1], "events/2026/03/20.ndjson")
        self.assertEqual(len(keys), self.cfg["store_days"] + 1)

    def test_queue_histogram_and_weekly(self):
        q = self.app["queue"]
        hist = q["wait_histogram"]
        self.assertEqual([(h["lo_h"], h["hi_h"]) for h in hist[:2]], [(0.0, 0.25), (0.25, 0.5)])
        self.assertIsNone(hist[-1]["hi_h"])
        self.assertEqual(sum(h["n"] for h in hist), q["wait"]["n"])
        weeks = {w["week"]: w for w in q["weekly"]}
        self.assertEqual(weeks["2026-W12"], {"week": "2026-W12", "start": "2026-03-16", "merged": 2, "ejected": 1,
                                             "removed": 0, "ejection_rate": 0.3333})

    def test_sync_engine_writes_and_checks_the_cis_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            cis = Path(tmp)
            (cis / "api" / "services").mkdir(parents=True)
            self.assertEqual(sync_engine.main(["--cis", str(cis), "--check"]), 1)
            self.assertEqual(sync_engine.main(["--cis", str(cis)]), 0)
            self.assertEqual((cis / sync_engine.COPY).read_bytes(), (HERE / "delivery_engine.py").read_bytes())
            lock = json.loads((cis / sync_engine.LOCK).read_text(encoding="utf-8"))
            self.assertEqual(lock["sha256"], de.engine_sha256())
            self.assertEqual(lock["definitions_version"], de.DEFINITIONS_VERSION)
            self.assertEqual(sync_engine.main(["--cis", str(cis), "--check"]), 0)
            (cis / sync_engine.COPY).write_text("# edited\n", encoding="utf-8")
            self.assertEqual(sync_engine.main(["--cis", str(cis), "--check"]), 1)
            self.assertEqual(sync_engine.main(["--cis", str(cis / "nope")]), 2)

    def test_histogram_and_weekly_helpers(self):
        rows = de.wait_histogram([0.1, 0.25, 3.0, 30.0, None], [0.25, 1.0, 24.0])
        self.assertEqual([r["n"] for r in rows], [1, 1, 1, 1])
        self.assertEqual(de.queue_weekly([], NOW, NOW), [])
        weeks = de.queue_weekly([], dm.ts("2026-03-01T00:00:00Z"), dm.ts("2026-03-16T00:00:00Z"))
        self.assertEqual([w["week"] for w in weeks], ["2026-W09", "2026-W10", "2026-W11"])
        self.assertTrue(all(w["ejection_rate"] is None for w in weeks))


class TestQueueEntries(unittest.TestCase):
    Q = {"login": "github-merge-queue[bot]", "type": "Bot"}
    AGENT = {"login": "aa-agent[bot]", "type": "Bot"}
    PERSON = {"login": "river-otter", "type": "User"}

    def timeline(self, *items):
        cfg = demo_config()
        rows = [{"event": e, "created_at": w, "actor": a} if e != "committed" else {"event": e, "committer": {"date": w}}
                for e, w, a in items]
        return dm.queue_event("demo", 7, rows, cfg)

    def test_removed_by_a_person_then_still_queued(self):
        tl = self.timeline(("added_to_merge_queue", "2026-03-10T10:00:00Z", self.AGENT),
                           ("removed_from_merge_queue", "2026-03-10T10:05:00Z", self.PERSON),
                           ("committed", "2026-03-10T10:20:00Z", None),
                           ("added_to_merge_queue", "2026-03-10T10:30:00Z", self.AGENT))
        self.assertFalse(dm._attr(tl, "aa.queue.settled"))
        self.assertTrue(dm.open_entry(dm._attr(tl, "aa.queue.events")))
        entries = dm.queue_entries(tl)
        self.assertEqual([(e["outcome"], e["new_commit"]) for e in entries], [("removed", False), ("queued", True)])
        self.assertEqual(entries[0]["removed_by"], "human")   # the kind only: no login is kept
        self.assertNotIn("river-otter", json.dumps(tl))

    def test_queue_removal_with_a_close_is_not_an_ejection(self):
        tl = self.timeline(("added_to_merge_queue", "2026-03-10T10:00:00Z", self.AGENT),
                           ("removed_from_merge_queue", "2026-03-10T10:05:00Z", self.Q),
                           ("closed", "2026-03-10T10:05:20Z", self.PERSON))
        self.assertEqual([e["outcome"] for e in dm.queue_entries(tl)], ["removed"])
        self.assertTrue(dm._attr(tl, "aa.queue.settled"))

    def test_merge_in_the_same_second_in_any_order(self):
        for order in ((("merged", self.AGENT), ("removed_from_merge_queue", self.Q)),
                      (("removed_from_merge_queue", self.Q), ("merged", self.AGENT))):
            tl = self.timeline(("added_to_merge_queue", "2026-03-10T10:00:00Z", self.AGENT),
                               *[(e, "2026-03-10T10:09:00Z", a) for e, a in order])
            self.assertEqual([e["outcome"] for e in dm.queue_entries(tl)], ["merged"])

    def test_no_queue_event_is_none(self):
        self.assertIsNone(self.timeline(("merged", "2026-03-10T10:00:00Z", self.AGENT)))

    def test_rerun_that_turned_green_is_flaky(self):
        cfg, app = demo_config(), demo_config()["apps"][0]
        tl = self.timeline(("added_to_merge_queue", "2026-03-10T10:00:00Z", self.AGENT),
                           ("removed_from_merge_queue", "2026-03-10T10:30:00Z", self.Q),
                           ("merged", "2026-03-10T10:30:00Z", self.AGENT))
        run = dm.run_event("demo", {"id": 5, "name": "CI", "path": ".github/workflows/ci.yml", "event": "merge_group",
                                    "head_branch": "gh-readonly-queue/main/pr-7-abc", "status": "completed",
                                    "conclusion": "success", "run_attempt": 2, "created_at": "2026-03-10T10:01:00Z",
                                    "run_started_at": "2026-03-10T10:15:00Z", "updated_at": "2026-03-10T10:28:00Z"})
        job = {"attributes": {"aa.run_attempt": 1, "cicd.pipeline.task.run.result": "failure", "aa.duration_s": 300}}
        entries = dm.classify_entries(cfg, app, [tl], [run], {5: [job]}, [])
        self.assertEqual([(e["outcome"], e["flaky"], e["reruns"]) for e in entries], [("merged", "rerun_green", 1)])

    def test_ejection_without_runs(self):
        cfg, app = demo_config(), demo_config()["apps"][0]
        tl = self.timeline(("added_to_merge_queue", "2026-03-10T10:00:00Z", self.AGENT),
                           ("removed_from_merge_queue", "2026-03-10T11:00:00Z", self.Q))
        entries = dm.classify_entries(cfg, app, [tl], [], {}, [])
        self.assertEqual([(e["outcome"], e["reason"]) for e in entries], [("ejected", "no_checks")])


class TestGitActivity(SummaryFixture):
    """AA-1125: commits of the main branch with their files."""

    def test_window_and_daily_counts(self):
        g = self.app["git"]
        self.assertEqual(g["commits"], 11)        # the commit older than 90 days is never read
        self.assertEqual(g["files_coverage"], 1.0)
        self.assertEqual(len(g["daily"]), self.cfg["git_days"] + 1)
        days = {d["date"]: d["n"] for d in g["daily"]}
        self.assertEqual((days["2026-03-16"], days["2026-03-20"], days["2026-01-10"]), (3, 1, 1))
        self.assertEqual(sum(days.values()), 11)
        self.assertEqual(g["complete_since"], "2025-12-20")

    def test_author_kinds(self):
        d30, d90 = self.app["git"]["windows"]["d30"], self.app["git"]["windows"]["d90"]
        self.assertEqual(d30["by_kind"], {"agent": 6, "ci_bot": 1, "release_please": 1, "dependabot": 1, "bot": 0,
                                          "human": 1})
        self.assertEqual(d90["by_kind"]["agent"], 7)
        self.assertEqual((d30["commits"], d90["commits"]), (10, 11))

    def test_churn_by_directory_with_drill_down(self):
        d30 = self.app["git"]["windows"]["d30"]
        self.assertEqual([d["path"] for d in d30["dirs"]], ["app", "docs", "frontend", "tests", "(root)"])
        app = d30["dirs"][0]
        self.assertEqual((app["churn"], app["commits"], app["files"]), (414, 6, 4))
        self.assertEqual(app["by_kind"], {"agent": 5, "human": 1})
        self.assertEqual([c["path"] for c in app["children"]], ["app/harbour", "app/tides", "app/lanterns"])
        self.assertEqual((app["children"][0]["churn"], app["children"][0]["last_at"]), (282, "2026-03-18T12:00:00Z"))
        # lock files are left out of the churn (apps.json churn_exclude)
        self.assertNotIn("package-lock.json", json.dumps(d30["dirs"]))

    def test_top_files(self):
        files = self.app["git"]["windows"]["d30"]["files"]
        self.assertEqual([f["path"] for f in files[:3]], ["docs/schema.md", "app/harbour/map.py",
                                                          "app/harbour/night.py"])
        self.assertEqual((files[1]["churn"], files[1]["commits"]), (162, 4))
        self.assertLessEqual(len(files), self.cfg["top_files"])

    def test_merges_by_branch_prefix(self):
        d30 = self.app["git"]["windows"]["d30"]
        self.assertEqual((d30["merges"], d30["merges_by_prefix"]), (8, {"feat": 8}))

    def test_commit_graph(self):
        graph = self.app["git"]["graph"]
        self.assertEqual(len(graph), 11)
        head = graph[0]
        self.assertEqual((head["title"], head["pr"], head["kind"]), ("chore(main): release 1.4.0 (#18)", 18,
                                                                    "release_please"))
        self.assertTrue(head["pr_url"].endswith("/pull/18"))
        self.assertEqual(head["parents"], [graph[1]["sha"]])
        fix = next(c for c in graph if c["title"].startswith("fix: harbour"))
        self.assertEqual(fix["pr"], 12)                     # the last "(#n)" of a squash title is its pull request
        self.assertEqual((fix["additions"], fix["deletions"], fix["files"]), (5, 3, 1))
        self.assertEqual(len(dm.summarize(self.cfg, self.store, NOW, None, None)["apps"][0]["git"]["graph"]), 11)

    def test_a_person_login_is_never_stored(self):
        commits = {dm._attr(c, "aa.commit.title"): c for c in self.store.of("aa.vcs.commit")}
        person = commits["feat: paint the harbour map (#11)"]["attributes"]
        self.assertEqual((person["aa.author.kind"], person["aa.author.login"]), ("human", None))
        self.assertNotIn("river-otter", json.dumps(self.summary))

    def test_files_survive_a_reread_and_the_cap_flags_truncation(self):
        fake = FakeGitHub()
        store = dm.Store(copy.deepcopy(self.store.events), copy.deepcopy(self.store.state))
        dm.collect(self.cfg, store, dm.GitHub(fake, 400, 10), NOW)
        self.assertTrue(all(dm._attr(c, "aa.files") is not None for c in store.of("aa.vcs.commit")))
        _cfg, store2, _r, _f = collected(demo_config(commit_files_cap=1))
        c = next(c for c in store2.of("aa.vcs.commit") if dm._attr(c, "vcs.change.id") == 11)
        self.assertEqual((len(dm._attr(c, "aa.files")), dm._attr(c, "aa.files_truncated")), (1, True))
        self.assertEqual(dm._attr(c, "aa.additions"), 700)   # the commit's own totals, not the capped list

    def test_helpers(self):
        cfg = demo_config()
        kind = dm.commit_author_kind
        self.assertEqual(kind({"login": "aa-agent[bot]", "type": "Bot"}, "feat: x (#1)", cfg), "agent")
        self.assertEqual(kind({"login": "aa-ecosys-ci-bot[bot]", "type": "Bot"}, "chore(main): release 2.0.0", cfg),
                         "release_please")
        self.assertEqual(kind({"login": "aa-ecosys-ci-bot[bot]", "type": "Bot"}, "docs: copy", cfg), "ci_bot")
        self.assertEqual(kind({"login": "some-tool[bot]", "type": "Bot"}, "chore: x", cfg), "bot")
        self.assertEqual(kind(None, "a commit with no GitHub user", cfg), "human")
        self.assertEqual(dm.branch_prefix("feat/aa1125-tabs"), "feat")
        self.assertEqual(dm.branch_prefix("release-please--branches--main"), "release-please")
        self.assertEqual(dm.branch_prefix("dependabot/pip/x"), "dependabot")
        self.assertEqual(dm.branch_prefix("main"), "other")


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
