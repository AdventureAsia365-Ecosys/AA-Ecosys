"""Container side of tools/ecs/ecsx.sh: run one script detached from the SSM session, keep ALL of its output.

ECS exec sessions drop long stdout ("Cannot perform start session: EOF", lesson log S237/S248/S251/S253/S256), and
a dropped session can take the process with it. This runner forks into its own session (setsid), so the SSM session
may end at once; the child runs `python3 <script>` with cwd /app and /app on sys.path. Stdlib only, except boto3 in
the S3 mode (every app image has Python 3.12; the Booking and CRM images have no curl).

S3 mode (CIS containers; the task role can write the bronze bucket):
  python3 ecsx_runner.py <script path> <bucket> <out_key>
  Captures stdout + stderr and writes <out_key> (text), then <out_key>.done ("rc=<n> bytes=<m>"); the local side
  polls for the marker, downloads, prints and deletes both.

Local mode (Booking, CRM: their task roles cannot write the bronze bucket; S257):
  python3 ecsx_runner.py local-start <script path> <id>
  Streams stdout + stderr into /tmp/ecsx-<id>.out while the script runs; at the end writes /tmp/ecsx-<id>.done
  ("rc=<n> bytes=<m>", atomic rename).
  python3 ecsx_runner.py read <id> <offset> <length> [count]
  Prints up to <count> lines "ECSX_CHUNK <offset> <n> <size> <state> <crc32> <base64|->" covering the output from
  <offset> on, <length> bytes each. <state> is "run", "rc=<n>" (finished; read before the size, so the size is
  final) or "missing" (no output file). Short lines only: the SSM terminal keeps those (S251). The local side
  (ecsx_local.py) checks offset, length and CRC of every line and asks again for what it did not get.
"""
import base64
import os
import subprocess
import sys
import zlib

CHUNK_TAG = "ECSX_CHUNK"
# Overridable only so test_ecsx.py can run the whole local mode on a workstation.
TMP_DIR = os.environ.get("ECSX_TMP_DIR", "/tmp")
APP_DIR = os.environ.get("ECSX_APP_DIR", "/app")


def paths(run_id: str) -> tuple[str, str]:
    return f"{TMP_DIR}/ecsx-{run_id}.out", f"{TMP_DIR}/ecsx-{run_id}.done"


def script_env() -> dict:
    pp = os.environ.get("PYTHONPATH")
    return dict(os.environ, PYTHONPATH=APP_DIR + (":" + pp if pp else ""), PYTHONUNBUFFERED="1")


def script_timeout() -> int:
    return int(os.environ.get("ECSX_SCRIPT_TIMEOUT", "3300"))


def detach(started_line: str) -> bool:
    """Double fork. The caller returns True in the grandchild (detached, own session) and False in the parent."""
    if os.fork():
        print(started_line, flush=True)
        return False
    os.setsid()
    if os.fork():
        os._exit(0)
    # Let go of the session's terminal: nothing of the detached run may hold the SSM pty (or a caller's pipe) open.
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    return True


def format_chunk(offset: int, data: bytes, size: int, state: str) -> str:
    b64 = base64.b64encode(data).decode("ascii") or "-"
    return f"{CHUNK_TAG} {offset} {len(data)} {size} {state} {zlib.crc32(data):08x} {b64}"


def read_chunks(out_path: str, done_path: str, offset: int, length: int, count: int = 1) -> list[str]:
    try:
        with open(done_path, encoding="ascii") as f:
            state = f.read().split()[0]  # "rc=<n>"
    except (OSError, IndexError):
        state = "run"
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


def run_s3(script: str, bucket: str, key: str) -> None:
    if not detach(f"ECSX_STARTED {key}"):
        return
    try:
        p = subprocess.run([sys.executable, script], cwd=APP_DIR, env=script_env(), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=script_timeout())
        out, rc = p.stdout, p.returncode
    except subprocess.TimeoutExpired as e:
        out, rc = (e.stdout or b"") + b"\nECSX: script timed out\n", 124
    import boto3
    s3 = boto3.client("s3")
    s3.put_object(Bucket=bucket, Key=key, Body=out)
    s3.put_object(Bucket=bucket, Key=key + ".done", Body=f"rc={rc} bytes={len(out)}".encode())
    os._exit(0)


def run_local(script: str, run_id: str) -> None:
    out_path, done_path = paths(run_id)
    open(out_path, "wb").close()  # exists before the parent reports the start, so a first read never says missing
    if not detach(f"ECSX_STARTED {run_id}"):
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
        for line in read_chunks(*paths(run_id), offset, length, count):
            print(line, flush=True)
    else:
        run_s3(*argv[0:3])


if __name__ == "__main__":
    main(sys.argv[1:])
