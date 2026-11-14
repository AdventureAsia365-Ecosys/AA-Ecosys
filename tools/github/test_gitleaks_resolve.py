"""Tests for gitleaks_resolve.py (S281): which gitleaks the root pre-push and the PR opener run.

Fake binaries are small shell scripts in a temporary directory; nothing is downloaded. Run:
python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import gitleaks_resolve as gr

SHIM = "#!/bin/sh\necho 'mise ERROR No version is set for shim: gitleaks' >&2\nexit 1\n"


def fake(path: Path, version: str | None = None, body: str | None = None) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body if body is not None else f"#!/bin/sh\necho '{version}'\n", encoding="utf-8")
    path.chmod(0o755)
    return str(path)


class ResolveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="gitleaks-resolve-")
        self.d = Path(self.tmp.name)
        self.root = self.d / "workspace"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def local(self, version: str = gr.PIN) -> str:
        return fake(self.root / gr.LOCAL_REL, version)

    def test_shim_without_version_is_skipped_for_the_checked_download(self):
        shim = fake(self.d / "shims" / "gitleaks", body=SHIM)
        local = self.local()
        f = gr.resolve([self.root], env={"PATH": str(self.d / "shims")})
        self.assertEqual((f.path, f.version), (local, gr.PIN))
        # the download comes before PATH, so the shim is not even probed
        self.assertEqual(f.skipped, [])

    def test_broken_shim_on_path_is_skipped_for_a_later_path_entry(self):
        fake(self.d / "shims" / "gitleaks", body=SHIM)
        good = fake(self.d / "bin" / "gitleaks", "8.30.1")
        f = gr.resolve([self.root], env={"PATH": f"{self.d / 'shims'}{os.pathsep}{self.d / 'bin'}"})
        self.assertEqual(f.path, good)
        self.assertEqual(len(f.skipped), 1)
        self.assertIn("No version is set for shim", f.skipped[0])

    def test_only_a_broken_shim_finds_nothing_and_says_why(self):
        fake(self.d / "shims" / "gitleaks", body=SHIM)
        f = gr.resolve([self.root], env={"PATH": str(self.d / "shims")})
        self.assertIsNone(f.path)
        self.assertIn("exit 1", f.note())

    def test_explicit_env_wins_when_it_runs_even_off_pin(self):
        self.local()
        old = fake(self.d / "old" / "gitleaks", "v8.18.0")
        f = gr.resolve([self.root], env={"AA_GITLEAKS": old, "PATH": ""})
        self.assertEqual((f.path, f.version), (old, "8.18.0"))

    def test_broken_explicit_env_falls_through(self):
        local = self.local()
        broken = fake(self.d / "broken" / "gitleaks", body=SHIM)
        f = gr.resolve([self.root], env={"AA_GITLEAKS": broken, "PATH": ""})
        self.assertEqual(f.path, local)
        self.assertTrue(f.skipped[0].startswith(f"AA_GITLEAKS={broken}: "))
        missing = gr.resolve([self.root], env={"AA_GITLEAKS": str(self.d / "nope"), "PATH": ""})
        self.assertEqual(missing.path, local)
        self.assertIn("not found", missing.note())

    def test_download_off_pin_is_skipped_and_path_at_pin_preferred(self):
        self.local("8.29.0")
        older = fake(self.d / "a" / "gitleaks", "8.18.0")
        pinned = fake(self.d / "b" / "gitleaks", "8.30.1")
        f = gr.resolve([self.root], env={"PATH": f"{self.d / 'a'}{os.pathsep}{self.d / 'b'}"})
        self.assertEqual(f.path, pinned)
        self.assertIn("not the CI pin", f.note())
        # no candidate at the pin: the first working one, so the caller can report the version gap
        f = gr.resolve([self.root], env={"PATH": str(self.d / "a")})
        self.assertEqual((f.path, f.version), (older, "8.18.0"))

    def test_output_without_a_version_number_is_not_a_version(self):
        fake(self.d / "x" / "gitleaks", body="#!/bin/sh\necho 'usage: gitleaks'\n")
        f = gr.resolve([self.root], env={"PATH": str(self.d / "x")})
        self.assertIsNone(f.path)
        self.assertIn("printed no version", f.note())

    def test_same_file_is_probed_once(self):
        local = self.local()
        os.symlink(self.root / ".tmp-session" / "gitleaks-8301", self.d / "link")
        calls: list[str] = []

        def probe(exe):
            calls.append(exe)
            return "8.18.0", ""  # off pin, so every candidate is looked at

        gr.resolve([self.root, self.root], run_version=probe, env={"PATH": str(self.d / "link")})
        self.assertEqual(calls, [local])

    def test_injected_probe_and_path_list(self):
        seen = []

        def probe(exe):
            seen.append(exe)
            return (None, "`gitleaks version` exit 1") if "shim" in exe else ("8.30.1", "")

        f = gr.resolve([], run_version=probe, env={}, on_path=["/x/shim/gitleaks", "/y/gitleaks"])
        self.assertEqual(f.path, "/y/gitleaks")
        self.assertEqual(seen, ["/x/shim/gitleaks", "/y/gitleaks"])

    def test_version_of(self):
        self.assertEqual(gr.version_of(0, "v8.30.1\n"), ("8.30.1", ""))
        self.assertEqual(gr.version_of(1, "mise ERROR No version is set for shim: gitleaks\n")[0], None)
        self.assertIn("exit 127", gr.version_of(127, "")[1])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="gitleaks-resolve-cli-")
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args: str, path: str) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items() if k != "AA_GITLEAKS"}
        env["PATH"] = f"{path}{os.pathsep}/usr/bin{os.pathsep}/bin"
        return subprocess.run([sys.executable, "-B", str(Path(gr.__file__)), *args], capture_output=True, text=True,
                              env=env, timeout=60)

    def test_prints_the_download_when_the_shim_is_broken(self):
        fake(self.d / "shims" / "gitleaks", body=SHIM)
        local = fake(self.d / "ws" / gr.LOCAL_REL, gr.PIN)
        r = self.run_cli("--root", str(self.d / "ws"), path=str(self.d / "shims"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), local)

    def test_exit_1_with_the_reason_when_nothing_works(self):
        fake(self.d / "shims" / "gitleaks", body=SHIM)
        r = self.run_cli("--root", str(self.d / "empty"), path=str(self.d / "shims"))
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("No version is set for shim", r.stderr)
        self.assertIn(gr.LOCAL_REL, r.stderr)

    def test_main_in_process(self):
        local = fake(self.d / "ws" / gr.LOCAL_REL, gr.PIN)
        out, err = io.StringIO(), io.StringIO()
        old = os.environ.pop("AA_GITLEAKS", None)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(gr.main(["--root", str(self.d / "ws")]), 0)
        finally:
            if old is not None:
                os.environ["AA_GITLEAKS"] = old
        self.assertEqual(out.getvalue().strip(), local)


if __name__ == "__main__":
    unittest.main()
