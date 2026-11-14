"""Tests for tools/uat/check_takes_uploaded.py (lesson S280/S281: PASS takes lost with their worktree).

Stdlib only, invented take names, a scripted rclone; no media, no network. Run:
python -m unittest discover -s tools/uat/tests -p 'test_check_takes_uploaded.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_takes_uploaded as ctu  # noqa: E402


class Rclone:
    """Scripted rclone: answers copy / check with the given exit codes and records the calls."""

    def __init__(self, copy: int = 0, check: int = 0):
        self.codes = {"copy": copy, "check": check}
        self.calls: list[list[str]] = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        rc = self.codes[argv[1]]
        return rc, ("0 differences found\n" if rc == 0 else "ERROR : 1 differences found\n")


class TakesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="uat-takes-")
        self.wt = Path(self.tmp.name) / "s999-l1-lanterns"
        self.uat = self.wt / "tools" / "uat"
        (self.uat / "out" / "packages").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def take(self, stem: str, verdict: str = "PASS", zipped: bool = False) -> None:
        out = self.uat / "out"
        (out / f"{stem}.mp4").write_bytes(b"not a real video")
        (out / f"{stem}.result.json").write_text(json.dumps({"id": stem.split("_")[0], "verdict": verdict}),
                                                 encoding="utf-8")
        if zipped:
            (out / "packages" / f"{stem}.zip").write_bytes(b"zip of " + stem.encode())

    def stems(self) -> list[str]:
        return [t.stem for t in ctu.pending_takes(self.uat)]

    def test_pass_take_without_zip_or_marker_is_pending_fail_is_not(self):
        self.take("LANTERN-01_20261101_v1")
        self.take("LANTERN-02_20261101_v1", zipped=True)
        self.take("LANTERN-03_20261101_v1", verdict="FAIL")
        (self.uat / "out" / "LANTERN-04_20261101_v1.mp4").write_bytes(b"no result file")
        takes = ctu.pending_takes(ctu.uat_dir(self.wt))
        self.assertEqual([t.stem for t in takes], ["LANTERN-01_20261101_v1", "LANTERN-02_20261101_v1"])
        self.assertIn("no zip", takes[0].reason)
        self.assertIn("no .uploaded marker", takes[1].reason)

    def test_verify_writes_the_marker_only_after_a_clean_check(self):
        self.take("LANTERN-02_20261101_v1", zipped=True)
        bad = Rclone(check=1)
        err = ctu.verify(self.uat, "LANTERN-02_20261101_v1", "drive:Lanterns/round-1", bad)
        self.assertIn("rclone check exit 1", err)
        self.assertEqual(self.stems(), ["LANTERN-02_20261101_v1"])
        good = Rclone()
        fixed = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
        self.assertIsNone(ctu.verify(self.uat, "LANTERN-02_20261101_v1", "drive:Lanterns/round-1", good,
                                     now=lambda: fixed))
        self.assertEqual(good.calls, [["rclone", "check", str(self.uat / "out" / "packages"), "drive:Lanterns/round-1",
                                       "--one-way", "--include", "LANTERN-02_20261101_v1.zip"]])
        marker = json.loads((self.uat / "out" / "packages" / "LANTERN-02_20261101_v1.uploaded").read_text())
        self.assertEqual((marker["remote"], marker["checked_at"]), ("drive:Lanterns/round-1", "2026-11-01T09:00:00Z"))
        self.assertEqual(self.stems(), [])

    def test_zip_repackaged_after_the_check_is_pending_again(self):
        self.take("LANTERN-02_20261101_v1", zipped=True)
        self.assertIsNone(ctu.verify(self.uat, "LANTERN-02_20261101_v1", "drive:L", Rclone()))
        (self.uat / "out" / "packages" / "LANTERN-02_20261101_v1.zip").write_bytes(b"a newer package")
        takes = ctu.pending_takes(self.uat)
        self.assertEqual(len(takes), 1)
        self.assertIn("changed after its rclone check", takes[0].reason)

    def test_upload_copies_then_checks_and_a_failed_copy_writes_nothing(self):
        self.take("LANTERN-05_20261101_v2", zipped=True)
        failing = Rclone(copy=1)
        self.assertIn("rclone copy exit 1", ctu.upload(self.uat, "LANTERN-05_20261101_v2", "drive:L", failing))
        self.assertEqual([c[1] for c in failing.calls], ["copy"])
        ok = Rclone()
        self.assertIsNone(ctu.upload(self.uat, "LANTERN-05_20261101_v2", "drive:L", ok))
        self.assertEqual([c[1] for c in ok.calls], ["copy", "check"])
        self.assertEqual(self.stems(), [])
        self.assertIn("package it first", ctu.upload(self.uat, "LANTERN-06_20261101_v1", "drive:L", ok))

    def test_cli_exit_codes(self):
        self.take("LANTERN-01_20261101_v1", zipped=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ctu.main([str(self.wt)]), 1)
            self.assertEqual(ctu.main(["verify", "--remote", "drive:L", "--uat", str(self.uat),
                                       "LANTERN-01_20261101_v1"], run=Rclone()), 0)
            self.assertEqual(ctu.main(["check", str(self.wt)]), 0)
            self.assertEqual(ctu.main(["upload", "--remote", "drive:L", "--uat", str(self.wt), "NOPE_1_v1"],
                                      run=Rclone()), 1)
        text = out.getvalue()
        self.assertIn("WAIT", text)
        self.assertIn("marker LANTERN-01_20261101_v1.uploaded written", text)
        self.assertIn("FAIL NOPE_1_v1", text)

    def test_missing_out_dir_is_nothing_pending(self):
        self.assertEqual(ctu.pending_takes(Path(self.tmp.name) / "no-such"), [])


if __name__ == "__main__":
    unittest.main()
