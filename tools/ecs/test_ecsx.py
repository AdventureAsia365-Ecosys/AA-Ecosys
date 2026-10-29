"""Run: python3 -m unittest discover -s tools/ecs -p 'test_*.py' (from the repo root). No AWS calls.

Covers the chunk/parse helpers of the no-S3 mode and runs the whole local mode (inline ship, detached start, range
reads, clean-up) against a fake ECS exec that runs each command on this machine and drops part of the read output,
as the SSM terminal does.
"""
import base64
import io
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecsx_local as L  # noqa: E402
import ecsx_runner as R  # noqa: E402


class InlineChunksTest(unittest.TestCase):
    def test_round_trip_and_bounds(self):
        data = bytes(range(256)) * 13
        pieces = L.inline_chunks(data, 100)
        self.assertTrue(all(len(p) <= 100 for p in pieces))
        self.assertEqual(base64.b64decode("".join(pieces)), data)

    def test_empty_and_tiny_size(self):
        self.assertEqual(L.inline_chunks(b"", 100), [""])
        with self.assertRaises(ValueError):
            L.inline_chunks(b"x", 3)

    def test_pieces_survive_the_exec_quoting(self):
        # sh -c '...' must arrive as one argument; base64 has no quote, space or $ in it.
        for i, piece in enumerate(L.inline_chunks(os.urandom(5000), 2000)):
            args = shlex.split(L.inline_append_command("20991231T000000-1-x", "s", i, piece))
            self.assertEqual(args[:2], ["sh", "-c"])
            self.assertEqual(len(args), 3)


class ParseChunksTest(unittest.TestCase):
    def test_round_trip_with_session_noise(self):
        data = "héllo\n".encode() * 50
        lines = [R.format_chunk(0, data[:100], len(data), "run"), R.format_chunk(100, data[100:], len(data), "rc=0")]
        transcript = "\r\nStarting session with SessionId: ecs-execute-command-abc\r\n" + "\r\n".join(lines) + \
            "\r\n\r\nExiting session with sessionId: ecs-execute-command-abc.\r\n"
        res = L.parse_chunks(transcript, 0)
        self.assertEqual(res.data, data)
        self.assertEqual(res.offset, len(data))
        self.assertTrue(res.finished)
        self.assertEqual(res.rc, 0)
        self.assertEqual(res.lines, 2)

    def test_cut_line_keeps_the_good_prefix(self):
        a, b = b"a" * 300, b"b" * 300
        transcript = R.format_chunk(0, a, 600, "run") + "\r\n" + R.format_chunk(300, b, 600, "run")[:200]
        res = L.parse_chunks(transcript, 0)
        self.assertEqual(res.data, a)
        self.assertEqual(res.offset, 300)
        self.assertFalse(res.finished)

    def test_wrong_offset_or_crc_is_rejected(self):
        line = R.format_chunk(10, b"xyz", 13, "run")
        self.assertIsNone(L.parse_chunks(line, 0))
        bad = line.replace(line.split()[5], "00000000")
        self.assertIsNone(L.parse_chunks(bad, 10))
        self.assertIsNone(L.parse_chunks("Cannot perform start session: EOF", 0))

    def test_empty_chunk_states(self):
        res = L.parse_chunks(R.format_chunk(42, b"", 42, "rc=3"), 42)
        self.assertEqual((res.data, res.finished, res.rc), (b"", True, 3))
        res = L.parse_chunks(R.format_chunk(0, b"", -1, "missing"), 0)
        self.assertEqual(res.state, "missing")
        self.assertFalse(res.finished)


class ReadChunksTest(unittest.TestCase):
    def test_read_states_and_count(self):
        with tempfile.TemporaryDirectory() as d:
            out, done = f"{d}/x.out", f"{d}/x.done"
            self.assertIn(" missing ", R.read_chunks(out, done, 0, 10)[0])
            Path(out).write_bytes(b"0123456789" * 3)
            lines = R.read_chunks(out, done, 5, 10, count=5)
            self.assertEqual(len(lines), 3)  # 10 + 10 + 5 bytes, no trailing empty line
            res = L.parse_chunks("\n".join(lines), 5)
            self.assertEqual((res.offset, res.state), (30, "run"))
            Path(done).write_text("rc=0 bytes=30")
            res = L.parse_chunks("\n".join(R.read_chunks(out, done, 30, 10)), 30)
            self.assertTrue(res.finished)


class CommandQuotingTest(unittest.TestCase):
    def test_embedded_python_has_no_shell_specials(self):
        for code in (L.FETCH_PY, L.VERIFY_PY):
            for ch in "'\"$`\\":
                self.assertNotIn(ch, code)

    def test_compound_commands_are_one_sh_argument(self):
        rid, sha = "20991231T000000-1-x", "0" * 64
        url = "https://example.invalid/scripts/ecsx/x.py?X-Amz-Signature=abc&X-Amz-Expires=600"
        for cmd in (L.ship_s3_command(rid, url, url, sha, sha), L.inline_finish_command(rid, sha, sha),
                    L.start_command(rid, ["LIMIT=5"]), L.clean_command(rid)):
            args = shlex.split(cmd)
            self.assertEqual(args[:2], ["sh", "-c"], cmd)
            self.assertEqual(len(args), 3, cmd)
        self.assertIn(f'"{url}"', shlex.split(L.ship_s3_command(rid, url, url, sha, sha))[2])


class FakeAws(L.Aws):
    """Runs each exec command here, with /tmp mapped to a temp dir; every other read transcript is cut short."""

    def __init__(self, tmp: str, app: str):
        super().__init__("arn:task", "api", "none")
        self.tmp, self.app, self.reads, self.calls = tmp, app, 0, []

    def exec(self, command, timeout=None):
        self.calls.append(command)
        args = [a.replace("/tmp/ecsx-", f"{self.tmp}/ecsx-").replace("cd /tmp ", f"cd {self.tmp} ")
                for a in shlex.split(command)]
        env = dict(os.environ, ECSX_TMP_DIR=self.tmp, ECSX_APP_DIR=self.app)
        out = subprocess.run(args, capture_output=True, text=True, env=env, timeout=30).stdout
        if " read " in command:
            self.reads += 1
            if self.reads % 2 == 0:
                out = out[: len(out) // 3]  # the SSM terminal dropped the rest
        return out


class LocalModeEndToEndTest(unittest.TestCase):
    def test_inline_ship_detached_run_and_range_reads(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as app:
            script = Path(tmp) / "probe.py"
            script.write_text(
                "import os, sys, time\n"
                "for i in range(120):\n"
                "    print(f'line {i:03d} ünïcode {os.environ.get(\"LIMIT\")} ' + 'x' * 40)\n"
                "    if i == 60:\n"
                "        sys.stdout.flush(); time.sleep(0.5)\n"
                "print('to stderr', file=sys.stderr)\n"
                "sys.exit(3)\n")
            expected = "".join(f"line {i:03d} ünïcode 7 " + "x" * 40 + "\n" for i in range(120)) + "to stderr\n"
            aws = FakeAws(tmp, app)
            env = {"ECSX_SHIP": "inline", "ECSX_INLINE_CHUNK": "700", "ECSX_READ_CHUNK": "500",
                   "ECSX_READ_LINES": "2", "ECSX_POLL": "0"}
            stdout = io.TextIOWrapper(io.BytesIO())
            with mock.patch.dict(os.environ, env), mock.patch.object(sys, "stdout", stdout), \
                    mock.patch.object(time, "sleep", lambda s: None):
                self.assertTrue(L.ship(aws, "t1", script.read_bytes(), L.RUNNER.read_bytes(), script))
                self.assertIn("ECSX_STARTED", aws.exec(L.start_command("t1", ["LIMIT=7"])))
                finished, rc = L.poll(aws, "t1", 0)
                self.assertIn("ECSX_CLEANED", aws.exec(L.clean_command("t1")))
            self.assertTrue(finished)
            self.assertEqual(rc, 3)
            self.assertEqual(stdout.buffer.getvalue().decode(), expected)
            self.assertGreater(aws.reads, 2)
            self.assertEqual(sorted(os.listdir(tmp)), ["probe.py"])  # every ecsx-t1.* file removed

    def test_s3_ship_command_fetches_and_verifies(self):
        # urllib also opens file:// URLs, so the presigned-GET command runs here unchanged.
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as src:
            script = Path(src) / "probe.py"
            script.write_text("print('ok')\n")
            sha_s = L.hashlib.sha256(script.read_bytes()).hexdigest()
            sha_r = L.hashlib.sha256(L.RUNNER.read_bytes()).hexdigest()
            aws = FakeAws(tmp, src)
            cmd = L.ship_s3_command("t2", script.as_uri(), L.RUNNER.as_uri(), sha_s, sha_r)
            self.assertIn("ECSX_SHIPPED", aws.exec(cmd))
            self.assertEqual((Path(tmp) / "ecsx-t2.py").read_bytes(), script.read_bytes())
            bad = L.ship_s3_command("t3", script.as_uri(), L.RUNNER.as_uri(), "0" * 64, sha_r)
            self.assertNotIn("ECSX_SHIPPED", aws.exec(bad))


if __name__ == "__main__":
    unittest.main()
