"""AA-859 S240 — automated flag flip: ON -> verify tenant A/B through the public Dev API -> verify the per-request
`used_tenant_pool=True` log line -> keep it ON if everything passes, otherwise turn it OFF again (SET "false").

Nghiệp's S240 decision: no manual approval per flag; one report at the end. Rollback of a flag = SET "false"
(no deploy). Since S241 D-12 the flags fail closed: a missing key is ON, so DEL is not a rollback.

    python3 aa859_flip_verify.py <flag-short-name> [...]      e.g. piece_edit unpublish
    python3 aa859_flip_verify.py --off <flag-short-name> ...  turn flags off (manual rollback)

Pieces:
  - aa859_flag.py runs inside the api task (S3-mediated ECS exec) and does get / on / off on Redis.
  - Each flag has a CHECKS entry: a function (ctx) -> list of (id, desc, ok, evidence). Checks must leave
    Dev data as they found it (restore what they change) and must work with the flag ON (the app reads the
    flag on every request).
  - LOG_EVENTS[flag] = the structlog event names the moved route logs with used_tenant_pool=...; after the
    checks, a Logs Insights query over the check window must show >= 1 line with used_tenant_pool=True and
    0 lines with used_tenant_pool=False for those events (a False line with the flag on = fallback).

Secrets (tenant api keys, WP app password) are read at run time and never printed or saved.
Output: flip_raw/<flag>/*.json, flip_report.json (appended per run).
"""
import json
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone

import requests

API = "https://api-cis.lumiguides.it.com"
HERE = pathlib.Path(__file__).resolve().parent
PROFILE = ["--profile", "aa365-admin", "--region", "us-west-1"]
BUCKET = "aa-cis-bronze-005097885195"
TENANTS = ["terra-family", "atlas-hearth"]          # A does the writes, B is the foreign tenant
FLAGS = {
    "piece_edit": "aa859:piece_edit_pool",
    "t2_version_write": "aa859:t2_version_write_pool",
    "angle_gate_decide": "aa859:angle_gate_decide_pool",
    "unpublish": "aa859:unpublish_pool",
    "t2_version_reads": "aa859:t2_version_reads_pool",
    "integration_connect": "aa859:integration_connect_pool",
}
LOG_EVENTS = {}   # flag short name -> list of event names (filled per route PR)
CHECKS = {}       # flag short name -> fn(ctx) -> list[(id, desc, ok, evidence)]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def aws(*args, text=True):
    return subprocess.check_output(["aws", *args, *PROFILE], text=text).strip()


def secret(name):
    return aws("secretsmanager", "get-secret-value", "--secret-id", name, "--query", "SecretString", "--output", "text")


# ── Redis flags through ECS exec ─────────────────────────────────────────────────────────────────
def flag(action, keys):
    src = HERE / "aa859_flag.py"
    aws("s3", "cp", str(src), f"s3://{BUCKET}/scripts/s240_aa859_flag.py", "--quiet")
    out_uri = f"s3://{BUCKET}/scripts/out/s240_aa859_flag.json"
    last = ""
    for attempt in range(6):   # a task replaced by a deploy needs ~1 min before ECS exec works
        subprocess.run(["aws", "s3", "rm", out_uri, "--quiet", *PROFILE], capture_output=True)   # never read a stale result
        url = aws("s3", "presign", f"s3://{BUCKET}/scripts/s240_aa859_flag.py", "--expires-in", "300")
        task = aws("ecs", "list-tasks", "--cluster", "aa-cis-dev-cluster", "--service-name", "aa-cis-dev-api",
                   "--desired-status", "RUNNING", "--query", "taskArns[0]", "--output", "text")
        cmd = f"sh -c 'curl -s \"{url}\" -o /tmp/f.py && python3 /tmp/f.py {action} {' '.join(keys)}'"
        p = subprocess.run(["aws", "ecs", "execute-command", "--cluster", "aa-cis-dev-cluster", "--task", task,
                            "--container", "api", "--interactive", "--command", cmd, *PROFILE],
                           capture_output=True, text=True, timeout=120)
        got = subprocess.run(["aws", "s3", "cp", out_uri, "-", *PROFILE], capture_output=True, text=True)
        if p.returncode == 0 and got.returncode == 0 and got.stdout.strip():
            break
        last = (p.stderr or p.stdout)[-300:]
        time.sleep(20)
    else:
        raise RuntimeError(f"flag {action} {keys}: ECS exec failed 6 times: {last}")
    out = json.loads(got.stdout)
    if "error" in out or out.get("action") != action:
        raise RuntimeError(f"flag {action} failed: {out}")
    return out


# ── Logs Insights: used_tenant_pool per moved event ─────────────────────────────────────────────
def log_pool_lines(events, start_epoch, end_epoch):
    pattern = "|".join(events)
    q = (f"fields @message | filter @logStream like /^api\\// | filter @message like /{pattern}/ "
         f"| filter @message like /used_tenant_pool=/ | limit 200")
    qid = aws("logs", "start-query", "--log-group-name", "/ecs/aa-cis-dev", "--start-time", str(start_epoch),
              "--end-time", str(end_epoch), "--query-string", q, "--query", "queryId", "--output", "text")
    while True:
        res = json.loads(aws("logs", "get-query-results", "--query-id", qid, "--output", "json"))
        if res["status"] in ("Complete", "Failed", "Cancelled", "Timeout"):
            break
        time.sleep(3)
    msgs = [next(c["value"] for c in r if c["field"] == "@message") for r in res.get("results", [])]
    return {"true": sum("used_tenant_pool=True" in m for m in msgs),
            "false": sum("used_tenant_pool=False" in m for m in msgs), "sample": [m[:240] for m in msgs[:6]]}


# ── API helpers for the checks ───────────────────────────────────────────────────────────────────
class Ctx:
    def __init__(self, short):
        self.short = short
        self.out = HERE / "flip_raw" / short
        self.out.mkdir(parents=True, exist_ok=True)
        self.h = {}
        self.tid = {}
        for slug in TENANTS:
            r = requests.post(API + "/auth/tenant-login",
                              json={"api_key": secret(f"aa-cis/dev/e2e-tenant/{slug}")}, timeout=30)
            r.raise_for_status()
            j = r.json()
            self.tid[slug], self.h[slug] = j["tenant_id"], {"Authorization": "Bearer " + j["token"]}
        self.A, self.B = TENANTS

    def call(self, slug, method, path, name, **kw):
        r = requests.request(method, API + path, headers=self.h[slug], timeout=120, **kw)
        try:
            body = r.json()
        except ValueError:
            body = r.text[:500]
        (self.out / f"{name}.json").write_text(json.dumps(
            {"at": now(), "tenant": slug, "method": method, "path": path, "status": r.status_code,
             "body": _trim(body)}, indent=1, default=str))
        return r.status_code, body


def _trim(o):
    if isinstance(o, dict):
        return {k: (v[:160] + "...") if isinstance(v, str) and len(v) > 160 else _trim(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_trim(x) for x in o[:15]]
    return o


# ── The flip ritual ──────────────────────────────────────────────────────────────────────────────
def flip_one(short):
    key = FLAGS[short]
    rec = {"flag": key, "started": now(), "checks": [], "kept_on": False}
    if short not in CHECKS or short not in LOG_EVENTS:
        rec["error"] = "no checks registered for this flag; not flipped"
        return rec
    rec["before"] = flag("get", [key])["after"][key]
    ctx = Ctx(short)
    t0 = int(time.time()) - 5
    flag("on", [key])
    try:
        rec["checks"] = [{"id": i, "desc": d, "pass": bool(ok), "evidence": e} for i, d, ok, e in CHECKS[short](ctx)]
    except Exception as e:  # a crashing check is a failed check
        rec["checks"].append({"id": "CRASH", "desc": "check function raised", "pass": False, "evidence": repr(e)[:300]})
    time.sleep(20)   # let the log lines reach CloudWatch
    logs = log_pool_lines(LOG_EVENTS[short], t0, int(time.time()) + 5)
    rec["logs"] = logs
    rec["checks"].append({"id": "LOG", "desc": "used_tenant_pool=True seen, no False with the flag on",
                          "pass": logs["true"] >= 1 and logs["false"] == 0,
                          "evidence": f"true={logs['true']} false={logs['false']}"})
    ok = all(c["pass"] for c in rec["checks"])
    if ok:
        rec["kept_on"] = True
    else:
        flag("off", [key])
        rec["reverted"] = now()
    rec["after"] = flag("get", [key])["after"][key]
    rec["finished"] = now()
    for c in rec["checks"]:
        print(("PASS " if c["pass"] else "FAIL ") + f"[{short}] {c['id']} {c['desc']} | {c['evidence']}")
    print(f"[{short}] {'KEPT ON' if rec['kept_on'] else 'REVERTED (off)'}")
    return rec


def main(argv):
    if argv and argv[0] == "--off":
        print(json.dumps(flag("off", [FLAGS[s] for s in argv[1:]])))
        return
    report_path = HERE / "flip_report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else []
    for short in argv:
        rec = flip_one(short)
        report.append(rec)
        report_path.write_text(json.dumps(report, indent=1, default=str))


# Per-route checks are registered by aa859_flip_checks.py (kept separate so each route PR's checks can
# be reviewed on their own).
try:
    import aa859_flip_checks  # noqa: F401  (registers into CHECKS / LOG_EVENTS)
    aa859_flip_checks.register(CHECKS, LOG_EVENTS)
except ImportError:
    pass

if __name__ == "__main__":
    main(sys.argv[1:])
