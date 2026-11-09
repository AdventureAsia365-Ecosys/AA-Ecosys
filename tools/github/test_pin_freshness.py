"""Tests for pin_freshness.py (AA-1024, S273). Offline: gh is a stub. Run: python3 -m unittest discover -s tools/github"""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pin_freshness as p  # noqa: E402

SHA = "ab" * 32
RELEASE_BIN = (
    "# demo pins\n"
    f"demotool v1.2.0 x86_64 {SHA} https://github.com/demo-org/demotool/releases/download/v1.2.0/demotool_1.2.0_linux_amd64.tar.gz demotool\n"
    f"demotool v1.2.0 aarch64 {SHA} https://github.com/demo-org/demotool/releases/download/v1.2.0/demotool_1.2.0_linux_arm64.tar.gz demotool\n"
    f"plugin 1.0.5.0 x86_64 {SHA} https://downloads.example.com/plugin/1.0.5.0/plugin.deb -\n"
)
LYCHEE = f"# lychee\nv0.24.2 x86_64-unknown-linux-gnu {SHA}\nv0.24.2 aarch64-unknown-linux-gnu {SHA}\n"
REQS = ("fastapi==0.1.0\n"
        f"demo_model_sm @ https://github.com/demo-org/demo-models/releases/download/demo_model_sm-3.8.0/demo_model_sm-3.8.0-py3-none-any.whl#sha256={SHA}\n")
WF = f"env:\n  SCAN_IMAGE: ghcr.io/demo-org/scanner:v8.30.1@sha256:{'cd' * 32}\n  DB: pgvector/demo@sha256:{'ef' * 32}\n"

RELEASES = {
    "demo-org/demotool": [("v1.3.0", False, True), ("v1.2.5", False, False), ("v1.2.0", False, False)],
    "lycheeverse/lychee": [("nightly", False, False), ("lychee-v0.24.2", False, False), ("lychee-lib-v0.30.0", False, False)],
    "demo-org/demo-models": [("demo_model_lg-3.9.0", False, False), ("demo_model_sm-3.9.1", False, False),
                             ("demo_model_sm-3.10.0", True, False), ("demo_model_sm-3.8.0", False, False)],
    "demo-org/scanner": [("v8.30.1", False, False)],
}


class FakeGh:
    def __init__(self, files=None, broken=(), upstream_broken=()):
        self.files = files if files is not None else {
            "AA-CIS-App": {".github/actions/release-bin/pins.txt": RELEASE_BIN, "requirements.txt": REQS,
                           ".github/workflows/scan.yml": WF},
            "AA-Booking": {".github/actions/lychee/pins.txt": LYCHEE,
                           ".github/actions/release-bin/pins.txt": RELEASE_BIN.replace("v1.2.0", "v1.2.5")
                           .replace("1.2.0_", "1.2.5_")},
        }
        self.broken, self.upstream_broken, self.calls = broken, upstream_broken, []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        path = next(a for a in cmd if a.startswith("repos/"))
        parts = path.split("?")[0].split("/")
        if parts[3] == "releases":
            up = f"{parts[1]}/{parts[2]}"
            if up in self.upstream_broken:
                return subprocess.CompletedProcess(cmd, 1, "", "HTTP 404")
            # jq filter applied here: drafts and prereleases out
            out = "".join(f"{t}\thttps://github.com/{up}/releases/tag/{t}\n"
                          for t, draft, pre in RELEASES.get(up, []) if not draft and not pre)
            return subprocess.CompletedProcess(cmd, 0, out, "")
        repo = parts[2]
        if repo in self.broken:
            return subprocess.CompletedProcess(cmd, 1, "", "HTTP 502")
        files = self.files.get(repo, {})
        if "/git/trees/" in path:
            return subprocess.CompletedProcess(cmd, 0, "\n".join([*files, "README.md", "docs/requirements-notes.md"]), "")
        if "/contents/" in path:
            text = files[path.split("/contents/", 1)[1]]
            return subprocess.CompletedProcess(cmd, 0, base64.b64encode(text.encode()).decode(), "")
        raise AssertionError(cmd)


class Parse(unittest.TestCase):
    def test_split_tag_and_vkey(self):
        self.assertEqual(p.split_tag("lychee-v0.24.2"), ("lychee-v", "0.24.2"))
        self.assertEqual(p.split_tag("demo_model_sm-3.8.0"), ("demo_model_sm-", "3.8.0"))
        self.assertEqual(p.split_tag("v1.54.0"), ("v", "1.54.0"))
        self.assertGreater(p.vkey("3.10.0"), p.vkey("3.9.1"))

    def test_release_bin_lines(self):
        pins = p.parse_pins("AA-CIS-App", ".github/actions/release-bin/pins.txt", RELEASE_BIN)
        self.assertEqual([(x["key"], x["upstream"], x["prefix"], x["version"]) for x in pins],
                         [("demotool", "demo-org/demotool", "v", "1.2.0")] * 2 + [("plugin", None, "", "1.0.5.0")])
        self.assertEqual(pins[0]["where"], "AA-CIS-App:.github/actions/release-bin/pins.txt:2")

    def test_lychee_requirements_and_images(self):
        self.assertEqual({(x["key"], x["prefix"], x["version"])
                          for x in p.parse_pins("r", ".github/actions/lychee/pins.txt", LYCHEE)},
                         {("lychee", "lychee-v", "0.24.2")})
        req = p.parse_pins("r", "requirements.txt", REQS)
        self.assertEqual([(x["key"], x["upstream"], x["prefix"]) for x in req],
                         [("demo_model_sm", "demo-org/demo-models", "demo_model_sm-")])
        img = p.parse_pins("r", ".github/workflows/scan.yml", WF)
        self.assertEqual([(x["key"], x["upstream"], x["version"]) for x in img],
                         [("scanner", "demo-org/scanner", "8.30.1")])

    def test_wants(self):
        self.assertTrue(p.wants("requirements.txt"))
        self.assertTrue(p.wants("api/requirements-dev.txt"))
        self.assertFalse(p.wants("docs/requirements-notes.md"))
        self.assertTrue(p.wants(".github/workflows/x.yml"))


class Check(unittest.TestCase):
    def _report(self, **kw):
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            rc = p.main(["--json"], run=FakeGh(**kw))
        return rc, {g["key"]: g for g in json.loads(out.getvalue())["pins"]}, json.loads(out.getvalue())

    def test_outdated_current_manual_and_prefix_filter(self):
        rc, g, _ = self._report()
        self.assertEqual(rc, 1)
        tool = g["demotool"]
        self.assertEqual((tool["status"], tool["latest"], tool["versions"]), ("outdated", "1.2.5", ["1.2.0", "1.2.5"]))
        self.assertEqual(len(tool["where"]), 4)    # two lines in two repos; the 1.3.0 prerelease is ignored
        self.assertEqual((g["lychee"]["status"], g["lychee"]["latest"]), ("current", "0.24.2"))
        self.assertEqual((g["demo_model_sm"]["status"], g["demo_model_sm"]["latest"]), ("outdated", "3.9.1"))
        self.assertEqual(g["plugin"]["status"], "manual")
        self.assertEqual(g["scanner"]["status"], "current")

    def test_one_release_lookup_per_upstream(self):
        fake = FakeGh()
        with mock.patch("sys.stdout", io.StringIO()):
            p.main(["--json"], run=fake)
        lookups = [c for c in fake.calls if any("/releases?" in a for a in c)]
        self.assertEqual(len(lookups), 4)

    def test_unknown_upstream_and_unreadable_repo(self):
        files = {"AA-CIS-App": {".github/actions/lychee/pins.txt": LYCHEE}}
        rc, g, report = self._report(files=files, broken=("AA-Partner",), upstream_broken=("lycheeverse/lychee",))
        self.assertEqual(rc, 2)
        self.assertEqual(g["lychee"]["status"], "unknown")
        self.assertIn("HTTP 404", g["lychee"]["error"])
        self.assertEqual(report["unreadable"], ["AA-Partner"])

    def test_ip_allow_list_upstream_read_without_token(self):
        def run(cmd, **kw):
            msg = ("gh: Although you appear to have the correct authorization credentials, "
                   "the `aquasecurity` organization has an IP allow list enabled")
            return subprocess.CompletedProcess(cmd, 1, "", msg)
        rows = [{"tag_name": "v0.70.0", "html_url": "u70", "draft": False, "prerelease": False},
                {"tag_name": "v0.71.0-rc1", "html_url": "rc", "draft": False, "prerelease": True},
                {"tag_name": "v0.69.0", "html_url": "u69", "draft": False, "prerelease": False}]
        seen = []
        got = p.latest_release("aquasecurity/trivy", "v", run=run, fetch=lambda url: seen.append(url) or rows)
        self.assertEqual(got, ("0.70.0", "u70"))
        self.assertEqual(seen, ["https://api.github.com/repos/aquasecurity/trivy/releases?per_page=100"])

    def test_other_gh_errors_are_not_retried_without_token(self):
        def run(cmd, **kw):
            return subprocess.CompletedProcess(cmd, 1, "", "gh: HTTP 404 Not Found")
        with self.assertRaises(p.h.cc.GhError):
            p.latest_release("x/y", "v", run=run, fetch=lambda url: self.fail("no anonymous read"))

    def test_table_and_local_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "apps", "AA-Booking", ".github", "actions", "lychee")
            d.mkdir(parents=True)
            (d / "pins.txt").write_text(LYCHEE.replace("v0.24.2", "v0.20.0"), encoding="utf-8")
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                rc = p.main(["--local-root", tmp, "--repos", "AA-Booking"], run=FakeGh())
        self.assertEqual(rc, 1)
        self.assertIn("OLD lychee", out.getvalue())
        self.assertIn("1 outdated of 1", out.getvalue())


if __name__ == "__main__":
    unittest.main()
