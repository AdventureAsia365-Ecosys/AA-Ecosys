"""Container side of tools/ecs/ecsx.sh: run one script detached from the SSM session and put its output on S3.

ECS exec sessions drop long stdout ("Cannot perform start session: EOF", lesson log S237/S248/S251/S253), and a
dropped session can take the process with it. This runner forks into its own session (setsid), so the SSM session
may end at once; the child runs `python3 <script>` with cwd /app and /app on sys.path, captures stdout + stderr,
and writes `<out_key>` (text) and then `<out_key>.done` ("rc=<n> bytes=<m>") to the bucket. The local side polls
for the .done marker, downloads, prints and deletes both.

  python3 /tmp/ecsx_runner.py <script path> <bucket> <out_key>
"""
import os
import subprocess
import sys


def main(script: str, bucket: str, key: str) -> None:
    if os.fork():
        print(f"ECSX_STARTED {key}", flush=True)
        return
    os.setsid()
    if os.fork():
        os._exit(0)
    env = dict(os.environ, PYTHONPATH="/app" + (":" + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else ""))
    try:
        p = subprocess.run([sys.executable, script], cwd="/app", env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=int(os.environ.get("ECSX_SCRIPT_TIMEOUT", "3300")))
        out, rc = p.stdout, p.returncode
    except subprocess.TimeoutExpired as e:
        out, rc = (e.stdout or b"") + b"\nECSX: script timed out\n", 124
    import boto3
    s3 = boto3.client("s3")
    s3.put_object(Bucket=bucket, Key=key, Body=out)
    s3.put_object(Bucket=bucket, Key=key + ".done", Body=f"rc={rc} bytes={len(out)}".encode())
    os._exit(0)


if __name__ == "__main__":
    main(*sys.argv[1:4])
