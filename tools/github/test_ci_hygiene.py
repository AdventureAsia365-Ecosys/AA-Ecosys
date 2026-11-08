"""Tests for ci_hygiene.py (AA-1024, S273). Offline: gh is a stub. Run: python3 -m unittest discover -s tools/github"""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_hygiene as h  # noqa: E402

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
GB = 10**9

CLEAN_WF = textwrap.dedent("""
    on: push
    jobs:
      a:
        runs-on: ubuntu-24.04
        steps:
          - uses: ./.github/actions/release-bin
            with:
              tool: demotool
    """)
DIRTY_WF = textwrap.dedent("""
    on: pull_request
    jobs:
      build:
        runs-on: ubuntu-24.04
        steps:
          - uses: actions/setup-python@v7
            with:
              cache: pip
          - name: Fetch demotool
            run: curl -fsSL -o d.tgz https://github.com/demo-org/demotool/releases/download/v1.0.0/d.tar.gz
    """)
ACTION = "name: demo\nruns:\n  using: composite\n  steps:\n    - shell: bash\n      run: echo ok\n"


def c(cid, ref, size, key, accessed="2026-11-08T11:00:00Z"):
    return {"id": cid, "ref": ref, "key": key, "size_in_bytes": size, "last_accessed_at": accessed}


STATE = {
    "AA-CIS-App": {
        "caches": [c(1, "refs/heads/main", 5 * GB, "setup-uv-2-x86_64-unknown-linux-gnu-ubuntu-26.04-3.12.16-0123456789abcdef"),
                   c(2, "refs/pull/10/merge", 3 * GB, "setup-uv-2-x86_64-unknown-linux-gnu-ubuntu-26.04-3.12.16-fedcba9876543210"),
                   c(3, "refs/pull/11/merge", 1 * GB, "node-cache-Linux-x64-npm-0123456789abcdef0123"),
                   c(4, "refs/heads/gh-readonly-queue/main/pr-12-abc", GB // 2, "cache-trivy-2026-11-07",
                     "2026-11-08T08:00:00Z"),
                   c(5, "refs/heads/main", GB // 4, "codeql-overlay-base-database-1-0123456789ab-python-1-42474989735-1")],
        "open": [11], "files": {".github/workflows/ci.yml": DIRTY_WF, ".github/actions/demo/action.yml": ACTION}},
}


ORG_REPOS = [{"name": n, "visibility": "public", "archived": False} for n in h.REPOS]


class FakeGh:
    def __init__(self, state=STATE, broken=("AA-Partner",), org_repos=ORG_REPOS, no_actions=(), org_broken=False):
        self.state, self.broken, self.deleted = state, broken, []
        self.org_repos, self.no_actions, self.org_broken = org_repos, no_actions, org_broken

    def __call__(self, cmd, **kw):
        if "DELETE" in cmd:
            self.deleted.append(int(cmd[-1].rsplit("/", 1)[1]))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if any(a.startswith(f"orgs/{h.ORG}/repos") for a in cmd):
            if self.org_broken:
                return subprocess.CompletedProcess(cmd, 1, "", "HTTP 502")
            return subprocess.CompletedProcess(cmd, 0, "".join(json.dumps(r) + "\n" for r in self.org_repos), "")
        path = next(a for a in cmd if a.startswith("repos/"))
        repo = path.split("/")[2]
        if repo in self.broken:
            return subprocess.CompletedProcess(cmd, 1, "", "HTTP 502")
        if repo in self.no_actions and "/actions/caches" in path:
            return subprocess.CompletedProcess(cmd, 1, "", "gh: Resource not accessible by integration (HTTP 403)")
        st = self.state.get(repo, {"caches": [], "open": [], "files": {".github/workflows/a.yml": CLEAN_WF}})
        if path == f"repos/{h.ORG}/{repo}":
            return subprocess.CompletedProcess(cmd, 0, "main\n", "")
        if "/actions/caches" in path:
            return subprocess.CompletedProcess(cmd, 0, "".join(json.dumps(x) + "\n" for x in st["caches"]), "")
        if "/pulls" in path:
            return subprocess.CompletedProcess(cmd, 0, "".join(f"{n}\n" for n in st["open"]), "")
        if "/git/trees/" in path:
            return subprocess.CompletedProcess(cmd, 0, "\n".join([*st["files"], "README.md", ".github/x.yml"]), "")
        if "/contents/" in path:
            text = st["files"][path.split("/contents/", 1)[1]]
            return subprocess.CompletedProcess(cmd, 0, base64.b64encode(text.encode()).decode() + "\n", "")
        raise AssertionError(cmd)


class Helpers(unittest.TestCase):
    def test_family_folds_hashes_dates_versions_and_run_ids(self):
        self.assertEqual(h.family("cache-trivy-2026-11-07"), "cache-trivy-*")
        self.assertEqual(h.family("codeql-overlay-base-database-1-0123456789ab-python-1-42474989735-1"),
                         "codeql-overlay-base-database-1-*-python-1-*-1")
        self.assertEqual(h.family("trivy-binary-v0.70.0-Linux-X64"), "trivy-binary-v*-Linux-X64")

    def test_ref_kind(self):
        self.assertEqual([h.ref_kind(r, "master") for r in ("refs/heads/master", "refs/pull/3/merge",
                                                             "refs/heads/gh-readonly-queue/master/pr-3-a",
                                                             "refs/heads/feature/x")],
                         ["default", "pull", "queue", "other"])


class Collect(unittest.TestCase):
    def test_red_over_the_threshold_and_on_an_uncached_download(self):
        row = h.collect("AA-CIS-App", warn_gb=8, run=FakeGh(), now=NOW, log=lambda m: None)
        self.assertEqual(row["bytes"], int(9.75 * GB))
        self.assertEqual(row["by_ref"]["pull"], 4 * GB)
        self.assertEqual(row["top"][0]["family"], "setup-uv-2-x86_64-unknown-linux-gnu-ubuntu-26.04-*-*")
        self.assertEqual((row["stale"], row["stale_bytes"]), (2, int(3.5 * GB)))  # PR 10 closed + the old queue ref
        self.assertEqual(len(row["red"]), 2)
        self.assertEqual(len(row["wl5"]), 1)
        self.assertIn("demotool/releases/download", row["wl5"][0])
        self.assertEqual(len(row["wl4"]), 1)

    def test_clean_deletes_only_stale_and_lowers_the_usage(self):
        fake = FakeGh()
        row = h.collect("AA-CIS-App", warn_gb=8, clean=True, run=fake, now=NOW, log=lambda m: None)
        self.assertEqual(sorted(fake.deleted), [2, 4])
        self.assertEqual(row["deleted"], 2)
        self.assertEqual(row["red"], ["1 uncached external download(s)"])  # 6.25 GB left, under 8

    def test_main_exit_codes_and_table(self):
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(h.main(["--repos", "AA-CIS-App", "AA-Partner"], run=FakeGh(), now=NOW), 1)
        text = out.getvalue()
        self.assertIn("RED AA-CIS-App", text)
        self.assertIn("(CodeQL default setup: not configurable)", text)
        self.assertIn("??? AA-Partner", text)
        self.assertIn("--clean deletes them", text)
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(h.main(["--repos", "AA-Booking"], run=FakeGh(), now=NOW), 0)
            self.assertEqual(h.main(["--repos", "AA-Booking", "AA-Partner"], run=FakeGh(), now=NOW), 2)
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            h.main(["--json", "--repos", "AA-CIS-App"], run=FakeGh(), now=NOW)
        self.assertEqual(json.loads(out.getvalue())["red"], 1)

    def test_local_root_scans_checkouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            wf = Path(tmp, "apps", "AA-Booking", ".github", "workflows")
            wf.mkdir(parents=True)
            (wf / "ci.yml").write_text(DIRTY_WF, encoding="utf-8")
            row = h.collect("AA-Booking", warn_gb=8, local_root=Path(tmp), run=FakeGh(), now=NOW, log=lambda m: None)
        self.assertEqual(row["files"], 1)
        self.assertEqual(len(row["wl5"]), 1)


UPLOADS = textwrap.dedent("""
    on: push
    jobs:
      a:
        runs-on: ubuntu-24.04
        steps:
          - name: No retention
            uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
            with:
              name: report
              path: out/
          - uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
            with:
              name: short
              path: out/
              retention-days: 7
          - name: Long, no reason
            uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
            with:
              path: out/
              retention-days: 30
          # retention: the audit bundle is read at the monthly review
          - name: Long, with reason above
            uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
            with:
              path: out/
              retention-days: 45
          - name: Long, with reason inside
            uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
            with:
              path: out/
              retention-days: "90"  # retention: release evidence
          - name: Expression
            uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
            with:
              path: out/
              retention-days: ${{ inputs.days }}
          # - uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 (commented out)
          - name: Next step
            run: echo done
    """)
COMPOSITE_UPLOAD = textwrap.dedent("""
    name: demo
    runs:
      using: composite
      steps:
        - uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
          with:
            path: x
    """)


class Retention(unittest.TestCase):
    def test_wl7_missing_and_long_without_reason(self):
        found = h.retention_findings(".github/workflows/u.yml", UPLOADS)
        self.assertEqual(len(found), 2, found)
        self.assertIn("without retention-days", found[0])
        self.assertTrue(found[0].startswith(".github/workflows/u.yml:8:WL7"))
        self.assertIn("keeps 30 days", found[1])

    def test_wl7_in_a_composite_action(self):
        self.assertEqual(len(h.retention_findings(".github/actions/demo/action.yml", COMPOSITE_UPLOAD)), 1)

    def test_comment_of_the_next_step_does_not_count_for_the_previous_one(self):
        text = textwrap.dedent("""
            jobs:
              a:
                steps:
                  - uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567 # v6.0.0
                    with:
                      retention-days: 20
                  # retention: this belongs to the next step
                  - run: echo hi
            """)
        self.assertEqual(len(h.retention_findings("w.yml", text)), 1)

    def test_retention_scan_prints_annotations_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            wf = Path(tmp, ".github", "workflows")
            wf.mkdir(parents=True)
            (wf / "u.yml").write_text(UPLOADS, encoding="utf-8")
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                self.assertEqual(h.main(["--retention-scan", tmp], run=FakeGh()), 0)
        text = out.getvalue()
        self.assertIn("::warning file=.github/workflows/u.yml,line=8::WL7", text)
        self.assertIn("2 warning(s)", text)

    def test_collect_reports_wl7_without_making_the_repo_red(self):
        state = {"AA-Booking": {"caches": [], "open": [], "files": {".github/workflows/u.yml": UPLOADS}}}
        row = h.collect("AA-Booking", warn_gb=8, run=FakeGh(state=state), now=NOW, log=lambda m: None)
        self.assertEqual(len(row["wl7"]), 2)
        self.assertEqual(row["red"], [])


class OrgAndPermissions(unittest.TestCase):
    def test_unknown_public_repo(self):
        repos = [*ORG_REPOS, {"name": "scratch-demo", "visibility": "public", "archived": False},
                 {"name": "private-notes", "visibility": "private", "archived": False}]
        self.assertEqual(h.unknown_public(repos), ["scratch-demo"])
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(h.main(["--json", "--repos", "AA-Booking"], run=FakeGh(org_repos=repos), now=NOW), 1)
        report = json.loads(out.getvalue())
        self.assertEqual(report["org"]["unknown_public"], ["scratch-demo"])
        self.assertEqual(report["red"], 1)
        self.assertEqual(report["warn_gb"], 8.0)

    def test_org_unreadable_is_an_error_not_a_finding(self):
        org = h.org_check(FakeGh(org_broken=True))
        self.assertEqual(org["unknown_public"], [])
        self.assertIn("HTTP 502", org["error"])

    def test_no_org_flag_skips_the_call(self):
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            h.main(["--json", "--no-org", "--repos", "AA-Booking"], run=FakeGh(org_broken=True), now=NOW)
        self.assertIsNone(json.loads(out.getvalue())["org"])

    def test_cache_403_keeps_the_repo_readable(self):
        row = h.collect("AA-CIS-App", warn_gb=8, run=FakeGh(no_actions=("AA-CIS-App",)), now=NOW, log=lambda m: None)
        self.assertIn("needs Actions: read", row["cache_error"])
        self.assertEqual(row["bytes"], 0)
        self.assertEqual(row["red"], ["1 uncached external download(s)"])
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            h.main(["--repos", "AA-CIS-App"], run=FakeGh(no_actions=("AA-CIS-App",)), now=NOW)
        self.assertIn("???: the token cannot read", out.getvalue())

    def test_other_cache_errors_still_mark_the_repo_unreadable(self):
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(h.main(["--repos", "AA-Booking", "AA-Partner"], run=FakeGh(), now=NOW), 2)


if __name__ == "__main__":
    unittest.main()
