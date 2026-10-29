"""Local side of the no-S3 mode of tools/ecs/ecsx.sh (S257). Called by ecsx.sh; not meant to be run by hand.

For containers whose task role cannot write the bronze bucket (Booking, CRM), the output never goes through S3:
  1. ship   the script and ecsx_runner.py reach /tmp of the container, either through presigned S3 GET URLs that
            the container fetches with Python urllib (no curl in the Booking/CRM images; a GET needs no task-role
            permission) or, when that fails or ECSX_SHIP=inline, as base64 chunks inside the exec command itself;
            both files are checked against their sha256 before anything runs.
  2. start  the runner detaches (own session) and streams the output into /tmp/ecsx-<id>.out.
  3. read   short exec calls print byte ranges of that file as "ECSX_CHUNK" lines (base64 + CRC32); this side checks
            offset, length and CRC, prints the bytes, and asks again for anything the SSM terminal dropped.
  4. clean  after the .done marker and the last byte, the /tmp files are removed.

Every exec call is bounded by a timeout (an SSM session can hang with no output, lesson log S253) and runs in its own
process group, so a cut call takes its session-manager-plugin with it.

  python3 ecsx_local.py --task ARN --container NAME --id ID [--resume OFFSET] <script.py> [VAR=value ...]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import signal
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path

CLUSTER = "aa-cis-dev-cluster"
REGION = "us-west-1"
HERE = Path(__file__).resolve().parent
RUNNER = HERE / "ecsx_runner.py"
VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=[A-Za-z0-9_.:,/@+-]*$")
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
CHUNK_RE = re.compile(r"ECSX_CHUNK (\d+) (\d+) (-?\d+) (run|missing|rc=-?\d+) ([0-9a-f]{8}) ([A-Za-z0-9+/=]+|-)")
# Python code run with `python3 -c "..."` inside `sh -c '...'`: no quotes, $, backslash or backtick allowed in it.
FETCH_PY = ("import sys,urllib.request as u;a=sys.argv[1:];"
            "[u.urlretrieve(a[i],a[i+1]) for i in range(0,len(a),2)]")
VERIFY_PY = ("import sys,hashlib,pathlib;a=sys.argv[1:];"
             "sys.exit(0 if all(hashlib.sha256(pathlib.Path(a[i]).read_bytes()).hexdigest()==a[i+1] "
             "for i in range(0,len(a),2)) else 9)")


def env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def log(msg: str) -> None:
    print(f"ecsx: {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- pure helpers (unit-tested in test_ecsx.py)

def inline_chunks(data: bytes, size: int) -> list[str]:
    """Base64 of `data` split into pieces of at most `size` characters (each is one exec command argument)."""
    if size < 4:
        raise ValueError("chunk size must be at least 4")
    b64 = base64.b64encode(data).decode("ascii")
    return [b64[i:i + size] for i in range(0, len(b64), size)] or [""]


@dataclass
class ReadResult:
    data: bytes   # contiguous bytes accepted from `offset` on
    offset: int   # offset after them
    size: int     # output file size the container reported (-1: missing)
    state: str    # "run", "missing" or "rc=<n>"
    lines: int    # chunk lines accepted

    @property
    def finished(self) -> bool:
        return self.state.startswith("rc=") and self.offset >= self.size

    @property
    def rc(self) -> int:
        return int(self.state[3:]) if self.state.startswith("rc=") else -1


def parse_chunks(transcript: str, offset: int) -> ReadResult | None:
    """Accept ECSX_CHUNK lines from an exec transcript that continue exactly at `offset` and pass length + CRC.

    The transcript may hold session banners, carriage returns and a cut last line; parsing stops at the first line
    that does not fit, since the bytes after a gap cannot be used. None when not one line is usable.
    """
    got, pos, last = bytearray(), offset, None
    accepted = 0
    for m in CHUNK_RE.finditer(transcript):
        off, n, size, state, crc, b64 = int(m[1]), int(m[2]), int(m[3]), m[4], m[5], m[6]
        if off != pos:
            break
        try:
            data = b"" if b64 == "-" else base64.b64decode(b64, validate=True)
        except ValueError:
            break
        if len(data) != n or f"{zlib.crc32(data):08x}" != crc:
            break
        got += data
        pos += n
        last = (size, state)
        accepted += 1
    if last is None:
        return None
    return ReadResult(bytes(got), pos, last[0], last[1], accepted)


def ship_s3_command(run_id: str, url_script: str, url_runner: str, sha_script: str, sha_runner: str) -> str:
    s, r = f"/tmp/ecsx-{run_id}.py", f"/tmp/ecsx-{run_id}.runner.py"
    return (f"sh -c 'python3 -c \"{FETCH_PY}\" \"{url_script}\" {s} \"{url_runner}\" {r}"
            f" && python3 -c \"{VERIFY_PY}\" {s} {sha_script} {r} {sha_runner} && echo ECSX_SHIPPED'")


def inline_append_command(run_id: str, name: str, index: int, piece: str) -> str:
    # One file per piece (overwritten, never appended), so a retried call cannot duplicate data.
    return f"sh -c 'printf %s {piece} > /tmp/ecsx-{run_id}.{name}.b64.{index:04d} && echo ECSX_OK{index}'"


def inline_finish_command(run_id: str, sha_script: str, sha_runner: str) -> str:
    p = f"ecsx-{run_id}"
    # The glob sorts the zero-padded piece numbers in order.
    return (f"sh -c 'cd /tmp && cat {p}.s.b64.[0-9]* | python3 -m base64 -d > {p}.py && cat {p}.r.b64.[0-9]* | "
            f"python3 -m base64 -d > {p}.runner.py && rm -f {p}.s.b64.* {p}.r.b64.* && python3 -c \"{VERIFY_PY}\" "
            f"{p}.py {sha_script} {p}.runner.py {sha_runner} && echo ECSX_SHIPPED'")


def start_command(run_id: str, env_pairs: list[str]) -> str:
    env = " ".join(env_pairs) + " " if env_pairs else ""
    return (f"sh -c 'cd /tmp && {env}python3 /tmp/ecsx-{run_id}.runner.py local-start "
            f"/tmp/ecsx-{run_id}.py {run_id}'")


def read_command(run_id: str, offset: int, length: int, count: int) -> str:
    return f"python3 /tmp/ecsx-{run_id}.runner.py read {run_id} {offset} {length} {count}"


def clean_command(run_id: str) -> str:
    p = f"/tmp/ecsx-{run_id}"
    return (f"sh -c 'rm -f {p}.py {p}.runner.py {p}.out {p}.done {p}.done.tmp {p}.s.b64.* {p}.r.b64.*"
            " && echo ECSX_CLEANED'")


# ---------------------------------------------------------------- AWS calls (aws CLI, like the S3 mode)

class Aws:
    def __init__(self, task: str, container: str, profile: str):
        self.task, self.container, self.profile = task, container, profile

    def cli(self, *args: str, timeout: int = 60) -> str:
        p = subprocess.run(["aws", *args, "--profile", self.profile, "--region", REGION], capture_output=True,
                           text=True, timeout=timeout, check=True)
        return p.stdout

    def exec(self, command: str, timeout: int | None = None) -> str:
        """One ECS exec call; returns the transcript ('' when the call hung and was cut)."""
        timeout = timeout or env_int("ECSX_EXEC_TIMEOUT", 60)
        args = ["aws", "ecs", "execute-command", "--cluster", CLUSTER, "--task", self.task, "--container",
                self.container, "--interactive", "--command", command, "--profile", self.profile, "--region", REGION]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            out, _ = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            out, _ = p.communicate()
            log(f"exec call cut after {timeout}s")
            out += b"\nECSX_EXEC_CUT\n"
        return out.decode("utf-8", "replace")


def ship(aws: Aws, run_id: str, script: bytes, runner: bytes, script_path: Path) -> bool:
    sha_s, sha_r = hashlib.sha256(script).hexdigest(), hashlib.sha256(runner).hexdigest()
    mode = os.environ.get("ECSX_SHIP", "auto")
    if mode not in ("auto", "s3", "inline"):
        raise SystemExit(f"ecsx: ECSX_SHIP must be auto, s3 or inline (got {mode})")
    if mode in ("auto", "s3"):
        bucket = os.environ.get("ECSX_BUCKET", "aa-cis-bronze-005097885195")
        keys = (f"scripts/ecsx/{run_id}.py", f"scripts/ecsx/{run_id}.runner.py")
        out = ""
        try:
            aws.cli("s3", "cp", str(script_path), f"s3://{bucket}/{keys[0]}", "--quiet")
            aws.cli("s3", "cp", str(RUNNER), f"s3://{bucket}/{keys[1]}", "--quiet")
            urls = [aws.cli("s3", "presign", f"s3://{bucket}/{k}", "--expires-in", "600").strip() for k in keys]
            out = aws.exec(ship_s3_command(run_id, urls[0], urls[1], sha_s, sha_r))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            log(f"S3 upload/presign failed ({e.__class__.__name__})")
        finally:
            for k in keys:
                subprocess.run(["aws", "s3", "rm", f"s3://{bucket}/{k}", "--quiet", "--profile", aws.profile,
                                "--region", REGION], capture_output=True, check=False)
        if "ECSX_SHIPPED" in out:
            log("script shipped through a presigned S3 URL")
            return True
        if mode == "s3":
            log("presigned S3 fetch not confirmed (ECSX_SHIP=s3, no fallback)")
            return False
        log("presigned S3 fetch not confirmed; shipping inline")
    size = env_int("ECSX_INLINE_CHUNK", 2000)
    for name, data in (("s", script), ("r", runner)):
        pieces = inline_chunks(data, size)
        for i, piece in enumerate(pieces):
            for attempt in range(3):
                if f"ECSX_OK{i}" in aws.exec(inline_append_command(run_id, name, i, piece)):
                    break
                log(f"inline piece {name}{i} not confirmed (attempt {attempt + 1} of 3)")
        log(f"shipped {name} inline in {len(pieces)} chunk(s)")
    out = aws.exec(inline_finish_command(run_id, sha_s, sha_r))
    if "ECSX_SHIPPED" in out:
        return True
    log("inline ship not confirmed (sha256 check failed or output dropped); trying to start anyway")
    return True


def poll(aws: Aws, run_id: str, offset: int) -> tuple[bool, int]:
    """Print the output from `offset` on. Returns (finished, rc); rc 3/4 with finished=False means gave up."""
    length, count = env_int("ECSX_READ_CHUNK", 1024), env_int("ECSX_READ_LINES", 1)
    wait, pause, max_misses = env_int("ECSX_TIMEOUT", 900), env_int("ECSX_POLL", 3), env_int("ECSX_MAX_MISSES", 8)
    deadline, misses = time.monotonic() + wait, 0
    while True:
        res = parse_chunks(aws.exec(read_command(run_id, offset, length, count)), offset)
        if res is None or res.state == "missing":
            misses += 1
            if misses >= max_misses:
                why = "no output file in the container" if res else "no readable ECSX_CHUNK line"
                log(f"giving up after {misses} reads ({why}); files kept: /tmp/ecsx-{run_id}.*")
                return False, 4
            time.sleep(2)
            continue
        misses = 0
        if res.data:
            sys.stdout.buffer.write(res.data)
            sys.stdout.buffer.flush()
        offset = res.offset
        if res.finished:
            log(f"{res.state} bytes={res.size}")
            return True, res.rc
        if not res.data:
            if time.monotonic() > deadline:
                log(f"no result after {wait}s; resume with: tools/ecs/ecsx.sh --resume {run_id} {offset}")
                return False, 3
            time.sleep(pause)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True)
    ap.add_argument("--container", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--resume", type=int, default=None, help="only read from this offset (run already started)")
    ap.add_argument("script", nargs="?")
    ap.add_argument("env", nargs="*")
    a = ap.parse_args(argv)
    if not ID_RE.match(a.id):
        raise SystemExit(f"ecsx: bad id: {a.id}")
    bad = [kv for kv in a.env if not VAR_RE.match(kv)]
    if bad:
        raise SystemExit(f"ecsx: bad VAR=value: {bad[0]}")
    aws = Aws(a.task, a.container, os.environ.get("ECSX_PROFILE", "aa365-admin"))
    offset = 0
    if a.resume is None:
        script_path = Path(a.script or "")
        if not script_path.is_file():
            raise SystemExit("ecsx: script not found")
        if not ship(aws, a.id, script_path.read_bytes(), RUNNER.read_bytes(), script_path):
            return 5
        if "ECSX_STARTED" not in aws.exec(start_command(a.id, a.env)):
            log("started (session output not seen, normal when SSM drops it); reading the output")
    else:
        offset = a.resume
    log(f"run id {a.id}")
    finished, rc = poll(aws, a.id, offset)
    if not finished:
        return rc
    if os.environ.get("ECSX_KEEP") == "1":
        log(f"ECSX_KEEP=1: files kept in /tmp/ecsx-{a.id}.*")
    elif "ECSX_CLEANED" not in aws.exec(clean_command(a.id)):
        log(f"clean-up not confirmed; files may remain: /tmp/ecsx-{a.id}.*")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
