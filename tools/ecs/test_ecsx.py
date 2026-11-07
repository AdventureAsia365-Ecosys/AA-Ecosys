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


class RunStateTest(unittest.TestCase):
    """AA-1024 G3: the pid claim tells a lost start from a dead run, and a run id never starts twice."""

    def test_states(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(R, "TMP_DIR", d):
            out, done = R.paths("r1")
            self.assertIn(" nostart ", R.read_chunks(out, done, 0, 10, run_id="r1")[0])
            self.assertTrue(R.claim("r1"))
            self.assertFalse(R.claim("r1"))
            Path(out).write_bytes(b"abc")
            self.assertIn(" run ", R.read_chunks(out, done, 0, 10, run_id="r1")[0])  # claimed, pid not yet written
            Path(R.pid_path("r1")).write_text(str(os.getpid()))
            self.assertIn(" run ", R.read_chunks(out, done, 0, 10, run_id="r1")[0])
            gone = subprocess.Popen([sys.executable, "-c", "pass"])
            gone.wait()
            Path(R.pid_path("r1")).write_text(str(gone.pid))
            res = L.parse_chunks(R.read_chunks(out, done, 0, 10, run_id="r1")[0], 0)
            self.assertEqual((res.state, res.data), ("dead", b"abc"))
            Path(done).write_text("rc=0 bytes=3")
            self.assertTrue(L.parse_chunks(R.read_chunks(out, done, 0, 10, run_id="r1")[0], 0).finished)

    def test_second_local_start_of_one_id_does_not_run_again(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as app:
            script = Path(tmp) / "ecsx-t9.py"
            script.write_text("print('ran')\n")
            env = dict(os.environ, ECSX_TMP_DIR=tmp, ECSX_APP_DIR=app)
            cmd = [sys.executable, str(L.RUNNER), "local-start", str(script), "t9"]
            self.assertIn("ECSX_STARTED", subprocess.run(cmd, env=env, capture_output=True, text=True).stdout)
            self.assertIn("ECSX_ALREADY", subprocess.run(cmd, env=env, capture_output=True, text=True).stdout)
            for _ in range(100):
                if Path(tmp, "ecsx-t9.done").exists():
                    break
                time.sleep(0.05)
            self.assertEqual(Path(tmp, "ecsx-t9.out").read_text(), "ran\n")


class LostStartTest(unittest.TestCase):
    def test_lost_start_is_started_again_once_and_output_is_kept_locally(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as app, \
                tempfile.TemporaryDirectory() as outdir:
            script = Path(tmp) / "probe.py"
            script.write_text("print('hello once')\n")
            aws = FakeAws(tmp, app)
            env = {"ECSX_SHIP": "inline", "ECSX_POLL": "0", "ECSX_NOSTART_READS": "2", "ECSX_OUT_DIR": outdir}
            stdout = io.TextIOWrapper(io.BytesIO())
            starts = []
            with mock.patch.dict(os.environ, env), mock.patch.object(sys, "stdout", stdout), \
                    mock.patch.object(time, "sleep", lambda s: None):
                self.assertTrue(L.ship(aws, "t5", script.read_bytes(), L.RUNNER.read_bytes(), script))
                # the first start never reaches the container (the SSM session dropped before the runner ran)

                def restart():
                    starts.append(1)
                    aws.exec(L.start_command("t5", []))
                with open(L.out_file("t5"), "wb") as sink:
                    finished, rc = L.poll(aws, "t5", 0, restart=restart, sink=sink)
            self.assertEqual((finished, rc, len(starts)), (True, 0, 1))
            self.assertEqual(stdout.buffer.getvalue(), b"hello once\n")
            self.assertEqual(Path(outdir, "t5.out").read_bytes(), b"hello once\n")

    def test_no_restart_gives_up(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as app:
            aws = FakeAws(tmp, app)
            Path(tmp, "ecsx-t6.runner.py").write_bytes(L.RUNNER.read_bytes())
            with mock.patch.dict(os.environ, {"ECSX_NOSTART_READS": "2"}), mock.patch.object(time, "sleep",
                                                                                              lambda s: None):
                self.assertEqual(L.poll(aws, "t6", 0), (False, 4))


FAKE_AWS = r'''#!/usr/bin/env python3
"""A scripted aws CLI for test_ecsx.py: S3 is a directory, ECS exec runs the command here with /tmp mapped."""
import os, re, subprocess, sys
S3, TMP, LOG = os.environ["FAKE_S3"], os.environ["ECSX_TMP_DIR"], os.environ["FAKE_LOG"]
a = [x for x in sys.argv[1:]]
def opt(name):
    return a[a.index(name) + 1] if name in a else None
def local(uri):
    b, _, k = uri[5:].partition("/")
    return os.path.join(S3, b, k)
with open(LOG, "a") as f:
    f.write(" ".join(a[:2]) + "\n")
if a[:2] == ["ecs", "list-tasks"]:
    print("arn:aws:ecs:us-west-1:000000000000:task/fake")
elif a[:2] == ["s3", "cp"]:
    src, dst = a[2], a[3]
    data = open(local(src), "rb").read() if src.startswith("s3://") else open(src, "rb").read()
    if dst == "-":
        sys.stdout.buffer.write(data)
    else:
        p = local(dst) if dst.startswith("s3://") else dst
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(data)
elif a[:2] == ["s3", "presign"]:
    print("file://" + local(a[2]))
elif a[:2] == ["s3", "rm"]:
    try:
        os.remove(local(a[2]))
    except FileNotFoundError:
        pass
elif a[:2] == ["s3api", "head-object"]:
    sys.exit(0 if os.path.exists(os.path.join(S3, opt("--bucket"), opt("--key"))) else 255)
elif a[:2] == ["ecs", "execute-command"]:
    n = len([l for l in open(LOG) if l.startswith("ecs execute-command")])
    if n <= int(os.environ.get("FAKE_DROP_STARTS", "0")):
        sys.exit(0)  # the session dropped before anything ran
    cmd = re.sub(r"(?<=\s)/tmp/", TMP + "/", opt("--command"))  # not inside a file:// URL
    r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
else:
    sys.exit("fake aws: unhandled " + " ".join(a))
'''


class S3ModeTest(unittest.TestCase):
    """ecsx.sh S3 mode end to end against the scripted aws above: heartbeat, one restart, local copy, rc."""

    def run_ecsx(self, d: Path, script_text: str, *pairs: str, drop: int = 0) -> subprocess.CompletedProcess:
        bin_dir, s3, tmp, app, out = (d / x for x in ("bin", "s3", "tmp", "app", "out"))
        for x in (bin_dir, s3, tmp, app):
            x.mkdir(exist_ok=True)
        (bin_dir / "aws").write_text(FAKE_AWS)
        (bin_dir / "aws").chmod(0o755)
        script = d / "probe.py"
        script.write_text(script_text)
        env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", FAKE_S3=str(s3), FAKE_LOG=str(d / "aws.log"),
                   ECSX_TMP_DIR=str(tmp), ECSX_APP_DIR=str(app), ECSX_S3_DIR=str(s3), ECSX_OUT_DIR=str(out),
                   ECSX_START_WAIT="3", ECSX_HEARTBEAT_S="1", ECSX_TIMEOUT="60", FAKE_DROP_STARTS=str(drop),
                   ECSX_BUCKET="bucket-x", ECSX_SERVICE="aa-cis-dev-api")
        return subprocess.run(["bash", str(Path(L.HERE) / "ecsx.sh"), str(script), *pairs], env=env,
                              capture_output=True, text=True, timeout=120)

    def test_run_prints_output_keeps_a_local_copy_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_ecsx(Path(d), "import os\nprint('ok', os.environ.get('LIMIT'))\nraise SystemExit(5)\n",
                              "LIMIT=3")
            self.assertEqual(r.returncode, 5, r.stderr)
            self.assertEqual(r.stdout, "ok 3\n")
            copies = list((Path(d) / "out").glob("*.out"))
            self.assertEqual([c.read_text() for c in copies], ["ok 3\n"])
            self.assertIn("output also in", r.stderr)
            left = [p.name for p in (Path(d) / "s3" / "bucket-x").rglob("*") if p.is_file()]
            self.assertEqual(left, [])  # script, runner, output, .done and .running all removed

    def test_lost_start_is_started_again_once(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_ecsx(Path(d), "print('after restart')\n", drop=1)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout, "after restart\n")
            self.assertIn("starting the run again, once", r.stderr)
            starts = [x for x in (Path(d) / "aws.log").read_text().splitlines() if x == "ecs execute-command"]
            self.assertEqual(len(starts), 2)

    def test_script_timeout_longer_than_the_wait_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_ecsx(Path(d), "print(1)\n", "ECSX_SCRIPT_TIMEOUT=7200")
            self.assertEqual(r.returncode, 2)
            self.assertIn("longer than the wait", r.stderr)


if __name__ == "__main__":
    unittest.main()
