"""AA-859 S240 — W6 (PATCH /v1/tours/versions/{id}) live verify on the tenant pool.

Why a separate run: no E2E tenant has an *approved* T2 version on Dev (all 50 are ai_generated), and the API
cannot set a version back to ai_generated. So this run:
  1. picks one of tenant A's versions V (with content, no pending sibling) and records its STORED status
     through a read-only ECS exec query;
  2. turns aa859:t2_version_write_pool ON;
  3. as A: approve V -> 200 approved; reject V -> 200 rejected; approve V -> 200; edit with {} -> 400;
     edit with V's own content -> 200, new version N with version_number = max + 1;
     as B: approve / reject / edit V -> 404 each; A on a random uuid -> 404;
  4. checks the log lines (aa859_t2_version_write used_tenant_pool=True, none False);
  5. restores: A rejects N through the API (it stays as a normal tenant_edit row, now rejected), and V's
     stored status is set back to the recorded value with ONE UPDATE on that row (ECS exec, admin DSN);
  6. turns the flag OFF again if any step failed (otherwise it stays ON).
Output: flip_raw/t2_version_write_run2/*.json and an entry appended to flip_report.json.
"""
import json
import sys
import time
import uuid

import aa859_flip_verify as fv

SHORT = "t2_version_write"
KEY = fv.FLAGS[SHORT]


def exec_sql(py_body, name):
    """Run a tiny asyncpg script in the api task; it writes JSON to S3; returns the parsed JSON."""
    script = f'''import asyncio, asyncpg, boto3, json
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    out = {{}}
{py_body}
    await c.close()
    boto3.client("s3", region_name="us-west-1").put_object(Bucket="{fv.BUCKET}", Key="scripts/out/s240_{name}.json", Body=json.dumps(out, default=str).encode())
    print("OK")
asyncio.run(main())
'''
    path = fv.HERE / f"_tmp_{name}.py"
    path.write_text(script)
    try:
        fv.aws("s3", "cp", str(path), f"s3://{fv.BUCKET}/scripts/s240_{name}.py", "--quiet")
        for _ in range(6):
            fv.subprocess.run(["aws", "s3", "rm", f"s3://{fv.BUCKET}/scripts/out/s240_{name}.json", "--quiet", *fv.PROFILE],
                              capture_output=True)
            url = fv.aws("s3", "presign", f"s3://{fv.BUCKET}/scripts/s240_{name}.py", "--expires-in", "300")
            task = fv.aws("ecs", "list-tasks", "--cluster", "aa-cis-dev-cluster", "--service-name", "aa-cis-dev-api",
                          "--desired-status", "RUNNING", "--query", "taskArns[0]", "--output", "text")
            cmd = f"sh -c 'curl -s \"{url}\" -o /tmp/q.py && python3 /tmp/q.py'"
            fv.subprocess.run(["aws", "ecs", "execute-command", "--cluster", "aa-cis-dev-cluster", "--task", task,
                               "--container", "api", "--interactive", "--command", cmd, *fv.PROFILE],
                              capture_output=True, text=True, timeout=120)
            got = fv.subprocess.run(["aws", "s3", "cp", f"s3://{fv.BUCKET}/scripts/out/s240_{name}.json", "-",
                                     *fv.PROFILE], capture_output=True, text=True)
            if got.returncode == 0 and got.stdout.strip():
                return json.loads(got.stdout)
            time.sleep(20)
        raise RuntimeError(f"exec_sql {name} failed")
    finally:
        path.unlink(missing_ok=True)


def content_of(v):
    c = v.get("rewritten_content")
    if isinstance(c, str):
        try:
            c = json.loads(c)
        except ValueError:
            return None
    return c if isinstance(c, dict) and c else None


def main():
    rec = {"flag": KEY, "run": "w6_verify (run 2: ai_generated V, DB restore of V's stored status)",
           "started": fv.now(), "checks": [], "kept_on": False}
    checks = rec["checks"]

    def add(i, d, ok, e):
        checks.append({"id": i, "desc": d, "pass": bool(ok), "evidence": e})
        print(("PASS " if ok else "FAIL ") + f"[W6] {i} {d} | {e}")

    ctx = fv.Ctx(SHORT + "_run2")
    A, B = ctx.A, ctx.B
    st, body = ctx.call(A, "GET", "/v1/tours/my-versions?page_size=100", "0_my_versions_a")
    rows = (body.get("data") if isinstance(body, dict) else body) or []
    V = None
    for v in rows:
        if not content_of(v):
            continue
        s2, b2 = ctx.call(A, "GET", f"/v1/tours/versions/{v['id']}", f"0_version_{str(v['id'])[:8]}")
        hist = (b2 or {}).get("version_history") or []
        if s2 == 200 and not any(h.get("status") == "pending" for h in hist):
            V, content, ptid = str(v["id"]), content_of(v), str(v["published_tour_id"])
            break
    if V is None:
        add("0", "precondition: a version with content and no pending sibling", False, f"rows={len(rows)}")
        return finish(rec, ctx, revert=False)
    snap = exec_sql(f'''    out["v"] = dict(await c.fetchrow("SELECT id, tenant_id, status, version_number, edited_at FROM gold_aa_internal.tenant_tour_versions WHERE id = $1::uuid", "{V}"))
    out["max_n"] = await c.fetchval("SELECT max(version_number) FROM gold_aa_internal.tenant_tour_versions WHERE tenant_id = $1::uuid AND published_tour_id = $2::uuid", "{ctx.tid[A]}", "{ptid}")''', "w6_snap")
    (ctx.out / "0_db_snapshot.json").write_text(json.dumps(snap, indent=1, default=str))
    orig = snap["v"]["status"]
    add("0", "precondition: V found, stored status recorded (DB, read-only)", True,
        f"V={V[:8]} stored_status={orig} version_number={snap['v']['version_number']} max={snap['max_n']}")

    t0 = int(time.time()) - 5
    fv.flag("on", [KEY])
    N = None
    try:
        for i, (act, want) in enumerate([("approve", "approved"), ("reject", "rejected"), ("approve", "approved")], 1):
            s, b = ctx.call(A, "PATCH", f"/v1/tours/versions/{V}", f"{i}_a_{act}", json={"action": act})
            add(str(i), f"A {act} V -> 200 {want}", s == 200 and (b or {}).get("status") in (want, None),
                f"status={s} body_status={(b or {}).get('status')}")
        s, b = ctx.call(A, "PATCH", f"/v1/tours/versions/{V}", "4_a_edit_empty", json={"action": "edit", "edited_content": {}})
        add("4", "A edit with {} -> 400", s == 400, f"status={s}")
        s, b = ctx.call(A, "PATCH", f"/v1/tours/versions/{V}", "5_a_edit", json={"action": "edit", "edited_content": content})
        newn = (b or {}).get("version_number")
        N = (b or {}).get("id") or (b or {}).get("version_id") or (b or {}).get("new_version_id")
        add("5", "A edit -> 200, new version number = max + 1", s == 200 and newn == (snap["max_n"] or 0) + 1,
            f"status={s} new_version_number={newn} expected={(snap['max_n'] or 0) + 1} new_id={str(N)[:8]}")
        for j, act in enumerate(["approve", "reject", "edit"], 6):
            payload = {"action": act} if act != "edit" else {"action": "edit", "edited_content": content}
            s, b = ctx.call(B, "PATCH", f"/v1/tours/versions/{V}", f"{j}_b_{act}", json=payload)
            add(str(j), f"B {act} A's V -> 404", s == 404, f"status={s}")
        s, b = ctx.call(A, "PATCH", f"/v1/tours/versions/{uuid.uuid4()}", "9_a_random", json={"action": "approve"})
        add("9", "A on a random uuid -> 404", s == 404, f"status={s}")
    except Exception as e:
        add("CRASH", "check raised", False, repr(e)[:300])
    time.sleep(20)
    logs = fv.log_pool_lines(["aa859_t2_version_write"], t0, int(time.time()) + 5)
    rec["logs"] = logs
    add("LOG", "used_tenant_pool=True seen, no False with the flag on", logs["true"] >= 1 and logs["false"] == 0,
        f"true={logs['true']} false={logs['false']}")

    # restore
    try:
        if N:
            s, b = ctx.call(A, "PATCH", f"/v1/tours/versions/{N}", "R1_a_reject_new", json={"action": "reject"})
            n_ok = s == 200
        else:
            n_ok = True
        res = exec_sql(f'''    out["updated"] = await c.execute("UPDATE gold_aa_internal.tenant_tour_versions SET status = $2 WHERE id = $1::uuid AND tenant_id = $3::uuid", "{V}", "{orig}", "{ctx.tid[A]}")
    out["v"] = dict(await c.fetchrow("SELECT id, status FROM gold_aa_internal.tenant_tour_versions WHERE id = $1::uuid", "{V}"))''', "w6_restore")
        (ctx.out / "R2_db_restore.json").write_text(json.dumps(res, indent=1, default=str))
        add("R", "restore: N rejected via API, V's stored status back to the recorded value",
            n_ok and res["v"]["status"] == orig and res["updated"] == "UPDATE 1",
            f"N={str(N)[:8]} reject_ok={n_ok} V_status={res['v']['status']} (was {orig}) {res['updated']}")
    except Exception as e:
        add("R", "restore", False, repr(e)[:300])
    return finish(rec, ctx, revert=not all(c["pass"] for c in checks))


def finish(rec, ctx, revert):
    if revert:
        fv.flag("off", [KEY])
        rec["reverted"] = fv.now()
    else:
        rec["kept_on"] = True
    rec["after"] = fv.flag("get", [KEY])["after"][KEY]
    rec["finished"] = fv.now()
    print(f"[W6] {'KEPT ON' if rec['kept_on'] else 'REVERTED (off)'}")
    p = fv.HERE / "flip_report.json"
    rep = json.loads(p.read_text()) if p.exists() else []
    rep.append(rec)
    p.write_text(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
