"""Container side of tools/ecs/ecsx.sh: run one script detached from the SSM session, keep ALL of its output.

ECS exec sessions drop long stdout ("Cannot perform start session: EOF", lesson log S237/S248/S251/S253/S256), and
a dropped session can take the process with it. This runner forks into its own session (setsid), so the SSM session
may end at once; the child runs `python3 <script>` with cwd /app and /app on sys.path. Stdlib only, except boto3 in
the S3 mode (every app image has Python 3.12; the Booking and CRM images have no curl).

S3 mode (CIS containers; the task role can write the bronze bucket):
  python3 ecsx_runner.py <script path> <bucket> <out_key>
  Captures stdout + stderr (into /tmp/ecsx-<id>.out while it runs) and writes <out_key> (text), then <out_key>.done
  ("rc=<n> bytes=<m>"); the local side polls for the marker, downloads, prints and deletes both. While the script
  runs, <out_key>.running is rewritten every HEARTBEAT_S seconds (AA-1024 G3): the local side sees a start the SSM
  session did not report, and the CIS deploy gate refuses a deploy that would kill the script (lesson S234: a deploy
  replaced the task under a long script twice).

Both modes claim /tmp/ecsx-<id>.pid (O_EXCL) before they start, and the detached process writes its pid there: a
second start of the same run id (the local side's one auto-resume after a lost start) never runs the script twice
(it prints ECSX_ALREADY), and a read can tell a run that never started ("nostart") from one whose process died
without a result ("dead").

Local mode (Booking, CRM: their task roles cannot write the bronze bucket; S257):
  python3 ecsx_runner.py local-start <script path> <id>
  Streams stdout + stderr into /tmp/ecsx-<id>.out while the script runs; at the end writes /tmp/ecsx-<id>.done
  ("rc=<n> bytes=<m>", atomic rename).
  python3 ecsx_runner.py read <id> <offset> <length> [count]
  Prints up to <count> lines "ECSX_CHUNK <offset> <n> <size> <state> <crc32> <base64|->" covering the output from
  <offset> on, <length> bytes each. <state> is "run", "rc=<n>" (finished; read before the size, so the size is
  final), "missing" (no output file), "nostart" (no pid claim: the start never reached the container) or "dead"
  (the process is gone and wrote no result: a deploy, OOM or crash killed it). Short lines only: the SSM terminal keeps those (S251). The local side
  (ecsx_local.py) checks offset, length and CRC of every line and asks again for what it did not get.
"""
import base64
import os
import subprocess
import sys
import time
import zlib

CHUNK_TAG = "ECSX_CHUNK"
# Overridable only so test_ecsx.py can run the whole local mode on a workstation.
TMP_DIR = os.environ.get("ECSX_TMP_DIR", "/tmp")
APP_DIR = os.environ.get("ECSX_APP_DIR", "/app")


# Test only: S3 objects become files under this directory (no boto3 on a workstation).
S3_DIR = os.environ.get("ECSX_S3_DIR")
HEARTBEAT_S = int(os.environ.get("ECSX_HEARTBEAT_S", "30"))


def paths(run_id: str) -> tuple[str, str]:
    return f"{TMP_DIR}/ecsx-{run_id}.out", f"{TMP_DIR}/ecsx-{run_id}.done"


def pid_path(run_id: str) -> str:
    return f"{TMP_DIR}/ecsx-{run_id}.pid"


def claim(run_id: str) -> bool:
    """Take the run id once: False when a start of this id already happened (never run a script twice)."""
    try:
        os.close(os.open(pid_path(run_id), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
        return True
    except FileExistsError:
        return False


def alive(pid: int) -> bool:
    try:
        with open(f"/proc/{pid}/status", encoding="ascii", errors="replace") as f:
            for line in f:
                if line.startswith("State:"):
                    return "Z" not in line.split()[1]  # a zombie (no init reaps it) is dead
        return True
    except FileNotFoundError:
        return False
    except OSError:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True


def run_state(run_id: str) -> str:
    """'run' (claimed, starting or running), 'nostart' (never claimed) or 'dead' (its process is gone)."""
    try:
        with open(pid_path(run_id), encoding="ascii") as f:
            text = f.read().strip()
    except FileNotFoundError:
        return "nostart"
    if not text:
        return "run"  # claimed; the detached process writes its pid a moment later
    return "run" if alive(int(text)) else "dead"


def script_env() -> dict:
    pp = os.environ.get("PYTHONPATH")
    return dict(os.environ, PYTHONPATH=APP_DIR + (":" + pp if pp else ""), PYTHONUNBUFFERED="1")


def script_timeout() -> int:
    return int(os.environ.get("ECSX_SCRIPT_TIMEOUT", "3300"))


def detach(started_line: str, run_id: str | None = None) -> bool:
    """Double fork. The caller returns True in the grandchild (detached, own session) and False in the parent. The
    grandchild writes its pid into the run's claim file."""
    if os.fork():
        print(started_line, flush=True)
        return False
    os.setsid()
    if os.fork():
        os._exit(0)
    if run_id:
        with open(pid_path(run_id), "w", encoding="ascii") as f:
            f.write(str(os.getpid()))
    # Let go of the session's terminal: nothing of the detached run may hold the SSM pty (or a caller's pipe) open.
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    return True


def format_chunk(offset: int, data: bytes, size: int, state: str) -> str:
    b64 = base64.b64encode(data).decode("ascii") or "-"
    return f"{CHUNK_TAG} {offset} {len(data)} {size} {state} {zlib.crc32(data):08x} {b64}"


def read_chunks(out_path: str, done_path: str, offset: int, length: int, count: int = 1,
                run_id: str | None = None) -> list[str]:
    try:
        with open(done_path, encoding="ascii") as f:
            state = f.read().split()[0]  # "rc=<n>"
    except (OSError, IndexError):
        state = run_state(run_id) if run_id else "run"
        if state == "nostart":
            return [format_chunk(offset, b"", -1, "nostart")]
        if state == "dead" and os.path.exists(done_path):
            state = "run"  # it finished between the two reads: the next read says rc=<n>
    try:
        size = os.path.getsize(out_path)  # after the done check: once done exists the size is final
    except OSError:
        return [format_chunk(offset, b"", -1, "missing")]
    lines = []
    with open(out_path, "rb") as f:
        f.seek(offset)
        for _ in range(max(1, count)):
            data = f.read(length)
            if not data and lines:
                break
            lines.append(format_chunk(offset, data, size, state))
            offset += len(data)
            if not data:
                break
    return lines


class _Store:
    """put_object on the bucket (boto3 in the container), or files under ECSX_S3_DIR in tests."""

    def __init__(self, bucket: str):
        self.bucket = bucket
        self.s3 = None
        if not S3_DIR:
            import boto3
            self.s3 = boto3.client("s3")

    def put(self, key: str, body: bytes) -> None:
        if self.s3 is None:
            p = os.path.join(S3_DIR, self.bucket, key)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(body)
        else:
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=body)


def run_s3(script: str, bucket: str, key: str) -> None:
    run_id = os.path.basename(key).rsplit(".", 1)[0]
    if not claim(run_id):
        print(f"ECSX_ALREADY {key}", flush=True)
        return
    if not detach(f"ECSX_STARTED {key}", run_id):
        return
    store = _Store(bucket)
    out_path = paths(run_id)[0]

    def beat() -> None:
        try:
            store.put(key + ".running", f"pid={os.getpid()} t={int(time.time())}".encode())
        except Exception:  # noqa: BLE001 - a missed heartbeat must not stop the script
            pass

    with open(out_path, "wb", buffering=0) as out:
        p = subprocess.Popen([sys.executable, script], cwd=APP_DIR, env=script_env(), stdout=out,
                             stderr=subprocess.STDOUT)
        deadline = time.monotonic() + script_timeout()
        rc = None
        while rc is None:
            beat()
            try:
                rc = p.wait(timeout=max(1, min(HEARTBEAT_S, deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                if time.monotonic() >= deadline:
                    p.kill()
                    p.wait()
                    out.write(b"\nECSX: script timed out\n")
                    rc = 124
    with open(out_path, "rb") as f:
        data = f.read()
    store.put(key, data)
    store.put(key + ".done", f"rc={rc} bytes={len(data)}".encode())
    try:
        os.remove(out_path)
    except OSError:
        pass
    os._exit(0)


def run_local(script: str, run_id: str) -> None:
    out_path, done_path = paths(run_id)
    if not claim(run_id):
        print(f"ECSX_ALREADY {run_id}", flush=True)
        return
    open(out_path, "wb").close()  # exists before the parent reports the start, so a first read never says missing
    if not detach(f"ECSX_STARTED {run_id}", run_id):
        return
    with open(out_path, "ab", buffering=0) as out:
        try:
            rc = subprocess.run([sys.executable, script], cwd=APP_DIR, env=script_env(), stdout=out,
                                stderr=subprocess.STDOUT, timeout=script_timeout()).returncode
        except subprocess.TimeoutExpired:
            out.write(b"\nECSX: script timed out\n")
            rc = 124
    tmp = done_path + ".tmp"
    with open(tmp, "w", encoding="ascii") as f:
        f.write(f"rc={rc} bytes={os.path.getsize(out_path)}")
    os.replace(tmp, done_path)
    os._exit(0)


def main(argv: list[str]) -> None:
    if argv and argv[0] == "local-start":
        run_local(argv[1], argv[2])
    elif argv and argv[0] == "read":
        run_id, offset, length = argv[1], int(argv[2]), int(argv[3])
        count = int(argv[4]) if len(argv) > 4 else 1
        for line in read_chunks(*paths(run_id), offset, length, count, run_id=run_id):
            print(line, flush=True)
    else:
        run_s3(*argv[0:3])


if __name__ == "__main__":
    main(sys.argv[1:])
