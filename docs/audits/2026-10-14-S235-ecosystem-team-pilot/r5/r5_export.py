"""S235 r5 export — READ-ONLY ($0). One file, two sides:

  local     : python3 r5_export.py [--state checkpoint_r5.json] [--label r5] [--out pieces_r5.json]
              uploads the piece-id list + this script to S3, runs it in the aa-cis-dev-api container via
              the S3-mediated ECS exec pattern, downloads the JSON the container wrote to S3, then adds
              local fields (offered lines, S234-compatible keys) and writes --out.
  container : python3 r5_export.py container <label>   (what ECS exec runs; never run it by hand)
              SELECT-only, in a read-only transaction (default_transaction_read_only=on). Writes the result
              to s3://aa-cis-bronze-005097885195/scripts/s235/r5/raw_<label>.json and prints ONE short line
              (stdout over ECS exec truncates, so nothing large goes to stdout).

Also exports the r4 baseline with the same fields (stored final ledgers, repair logs, costs):
  python3 r5_export.py --state ../../s234/checkpoint_r4.json --label r4 --out pieces_r4_full.json

Per piece: content_text, seo_title/meta/slug, status, held_reason, attempt_number, gate_ledger, flags,
repair_log, discarded_attempts, writer_input (seed, scope, angle, brand_pack, keyword), request cta,
angle option name, job status, cost (shared.llm_call_log by job, by stage), the t10_judge prompt
versions + tag-free signal from llm_call_log.quality_signal (AA-786), and the place-card kind of every
"Place background" bullet in the seed (AA-774: matched on acp_shared.place_card.facts text).
Secrets: the container reads aa-cis/dev/rds itself; nothing secret is printed or written.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

BUCKET = "aa-cis-bronze-005097885195"
PREFIX = "scripts/s235/r5"
PROFILE, REGION = "aa365-admin", "us-west-1"
CLUSTER, SERVICE, CONTAINER = "aa-cis-dev-cluster", "aa-cis-dev-api", "api"


def fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).lower().split())


def bg_bullets(seed: str) -> list[str]:
    out, on = [], False
    for line in (seed or "").splitlines():
        if line.startswith("Place background"):
            on = True
            continue
        if on and line.startswith("- "):
            out.append(line[2:].strip())
        else:
            on = False
    return out


# ════════════════════════════════════ container side ════════════════════════════════════════════

Q_PIECES = """
SELECT cp.piece_id::text, t.name AS tenant, t.slug AS tenant_slug, COALESCE(cp.channel, r.channel) AS channel,
       cp.status, cp.held_reason, cp.attempt_number, cp.created_at::text, cp.seo_title, cp.meta_description,
       cp.slug, cp.content_text, cp.gate_ledger, cp.flags, cp.repair_log, cp.discarded_attempts,
       cp.writer_input, cp.job_id::text, cp.angle_gate_request_id::text AS request_id, r.cta AS request_cta,
       o.name AS angle_name, j.status AS job_status, j.kind AS job_kind
FROM acp_shared.content_piece cp
JOIN shared.tenants t ON t.tenant_id = cp.tenant_id
JOIN acp_shared.angle_gate_request r ON r.request_id = cp.angle_gate_request_id
LEFT JOIN acp_shared.angle_gate_option o ON o.option_id = cp.angle_gate_option_id
LEFT JOIN shared.job j ON j.id = cp.job_id
WHERE cp.piece_id = ANY($1::uuid[])
"""
Q_COST = """
SELECT job_id::text, stage, role, count(*)::int AS calls, coalesce(sum(cost_usd), 0)::float AS cost_usd,
       array_remove(array_agg(DISTINCT quality_signal->>'prompt_version'), NULL) AS prompt_versions,
       count(*) FILTER (WHERE (quality_signal->>'piece_tag_free') = 'false')::int AS judge_tagged_calls,
       count(*) FILTER (WHERE (quality_signal->>'reasonless') = 'true')::int AS judge_reasonless_calls
FROM shared.llm_call_log WHERE job_id = ANY($1::uuid[])
GROUP BY 1, 2, 3
"""
Q_FACTS = """
SELECT f->>'text' AS text, f->>'kind' AS kind
FROM acp_shared.place_card pc
CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(pc.facts) = 'array' THEN pc.facts
                                             ELSE '[]'::jsonb END) AS f
WHERE jsonb_typeof(f) = 'object' AND f->>'text' IS NOT NULL
"""
Q_JOBS = "SELECT id::text, kind, status FROM shared.job WHERE id = ANY($1::uuid[])"


def _j(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return v
    return v


def container(label: str) -> None:
    import asyncio
    from urllib.parse import urlparse

    import asyncpg
    import boto3

    s3 = boto3.client("s3", region_name=REGION)
    ids = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{PREFIX}/ids_{label}.json")["Body"].read())

    async def run():
        sm = boto3.client("secretsmanager", region_name=REGION)
        u = urlparse(sm.get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"].strip())
        conn = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password,
                                     database=u.path.lstrip("/"), ssl="require",
                                     server_settings={"default_transaction_read_only": "on"})
        try:
            async with conn.transaction(readonly=True):
                rows = [dict(r) for r in await conn.fetch(Q_PIECES, ids["piece_ids"])]
                job_ids = [r["job_id"] for r in rows if r["job_id"]] + list(ids.get("extra_job_ids") or [])
                cost = [dict(r) for r in await conn.fetch(Q_COST, job_ids)] if job_ids else []
                jobs = [dict(r) for r in await conn.fetch(Q_JOBS, job_ids)] if job_ids else []
                kinds = {}
                for f in await conn.fetch(Q_FACTS):
                    kinds.setdefault(fold(f["text"])[:72], set()).add(f["kind"] or "what_it_is")
        finally:
            await conn.close()
        for r in rows:
            for k in ("gate_ledger", "flags", "repair_log", "discarded_attempts", "writer_input"):
                r[k] = _j(r[k])
            seed = (r.get("writer_input") or {}).get("seed") or ""
            r["bg_bullet_kinds"] = [{"text": b, "kinds": sorted(kinds.get(fold(b)[:72], {"<no card match>"}))}
                                    for b in bg_bullets(seed)]
            mine = [c for c in cost if c["job_id"] == r["job_id"]]
            r["cost_by_stage"] = mine
            r["cost_usd"] = round(sum(c["cost_usd"] for c in mine), 6)
            r["judge_prompt_versions"] = sorted({v for c in mine if c["stage"] == "t10_judge"
                                                 for v in (c["prompt_versions"] or [])})
            r["judge_tagged_calls"] = sum(c["judge_tagged_calls"] for c in mine if c["stage"] == "t10_judge")
        extra = [c for c in cost if c["job_id"] in set(ids.get("extra_job_ids") or [])]
        return {"label": label, "pieces": rows, "extra_jobs": jobs, "extra_job_cost": extra,
                "missing": sorted(set(ids["piece_ids"]) - {r["piece_id"] for r in rows})}

    out = asyncio.run(run())
    s3.put_object(Bucket=BUCKET, Key=f"{PREFIX}/raw_{label}.json",
                  Body=json.dumps(out, default=str, ensure_ascii=False).encode())
    print(f"R5_EXPORT_OK label={label} pieces={len(out['pieces'])} missing={len(out['missing'])}")


# ═════════════════════════════════════ local side ═══════════════════════════════════════════════

_STATUS_OFFERED_RE = re.compile(r"^Status: OFFERED", re.M)


def offered_lines(seed: str) -> list[str]:
    """Each 'Status: OFFERED, NOT INCLUDED (…)' line with the source line above it (AA-773)."""
    lines = (seed or "").splitlines()
    out = []
    for i, ln in enumerate(lines):
        if ln.startswith("Status: OFFERED"):
            prev = next((lines[j] for j in range(i - 1, -1, -1) if lines[j].strip()), "")
            out.append(f"{prev.strip()[:200]}  ->  {ln.strip()[:240]}")
    return out


def to_piece(r: dict, slug_by_piece: dict) -> dict:
    """S234 pieces_r*.json shape (export_pieces.py) + the r5 extras."""
    wi = r.get("writer_input") or {}
    ledger = r.get("gate_ledger") or []
    seed = wi.get("seed") or ""
    return {
        # S234-compatible keys (measure_r4.py / panel read these)
        "piece_id": r["piece_id"], "tenant": r["tenant"], "channel": r["channel"], "status": r["status"],
        "attempt": r["attempt_number"], "seo_title": r.get("seo_title"), "meta": r.get("meta_description"),
        "text": r.get("content_text"), "seed": seed, "scope": wi.get("scope"), "angle": wi.get("angle"),
        "brand_pack": wi.get("brand_pack"), "keyword": wi.get("keyword"),
        "failed": [g["gate"] for g in ledger if not g.get("passed") and g.get("blocking", True)],
        # r5 extras
        "slug_tenant": r.get("tenant_slug") or slug_by_piece.get(r["piece_id"]), "held_reason": r.get("held_reason"),
        "request_id": r.get("request_id"), "cta": r.get("request_cta"), "angle_name": r.get("angle_name"),
        "gate_ledger": ledger, "flags": r.get("flags") or [], "repair_log": r.get("repair_log") or [],
        "discarded_attempts": r.get("discarded_attempts") or [], "job_id": r.get("job_id"),
        "job_status": r.get("job_status"), "cost_usd": r.get("cost_usd"), "cost_by_stage": r.get("cost_by_stage"),
        "judge_prompt_versions": r.get("judge_prompt_versions"), "judge_tagged_calls": r.get("judge_tagged_calls"),
        "bg_bullet_kinds": r.get("bg_bullet_kinds"), "offered_lines": offered_lines(seed),
        "status_offered_lines": len(_STATUS_OFFERED_RE.findall(seed)),
        "status_included_lines": len(re.findall(r"^Status: included", seed, re.M)),
        "created_at": r.get("created_at"),
    }


def _aws(*args: str) -> str:
    return subprocess.check_output(["aws", *args, "--profile", PROFILE, "--region", REGION], text=True).strip()


def local(argv: list[str]) -> None:
    import argparse
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(here / "checkpoint_r5.json"))
    ap.add_argument("--label", default="r5")
    ap.add_argument("--out", default=None)
    ap.add_argument("--from-raw", help="skip ECS exec; post-process an already downloaded raw_<label>.json")
    a = ap.parse_args(argv)
    out = Path(a.out or here / f"pieces_{a.label}.json")
    raw_path = Path(a.from_raw) if a.from_raw else here / f"raw_{a.label}.json"
    state = json.loads(Path(a.state).read_text())
    order = [p["piece_id"] for p in state["pieces"] if p.get("piece_id")]
    slug_by_piece = {p["piece_id"]: p["slug"] for p in state["pieces"] if p.get("piece_id")}
    if not a.from_raw:
        extra = [state["regen"]["job_id"]] if (state.get("regen") or {}).get("job_id") else []
        ids_file = here / f"ids_{a.label}.json"
        ids_file.write_text(json.dumps({"piece_ids": order, "extra_job_ids": extra}))
        _aws("s3", "cp", str(ids_file), f"s3://{BUCKET}/{PREFIX}/ids_{a.label}.json", "--quiet")
        _aws("s3", "cp", __file__, f"s3://{BUCKET}/{PREFIX}/r5_export.py", "--quiet")
        url = _aws("s3", "presign", f"s3://{BUCKET}/{PREFIX}/r5_export.py", "--expires-in", "600")
        task = _aws("ecs", "list-tasks", "--cluster", CLUSTER, "--service-name", SERVICE,
                    "--query", "taskArns[0]", "--output", "text")
        cmd = f"sh -c 'curl -s \"{url}\" -o /tmp/r5x.py && python3 /tmp/r5x.py container {a.label}'"
        res = subprocess.run(["timeout", "300", "aws", "ecs", "execute-command", "--cluster", CLUSTER, "--task", task,
                              "--container", CONTAINER, "--interactive", "--command", cmd,
                              "--profile", PROFILE, "--region", REGION], capture_output=True, text=True)
        tail = [ln for ln in res.stdout.splitlines() if "R5_EXPORT" in ln or "Error" in ln or "Traceback" in ln]
        print("ecs exec:", res.returncode, " | ".join(tail)[-600:] or res.stderr[-400:])
        _aws("s3", "cp", f"s3://{BUCKET}/{PREFIX}/raw_{a.label}.json", str(raw_path), "--quiet")
    raw = json.loads(raw_path.read_text())
    by_id = {r["piece_id"]: r for r in raw["pieces"]}
    pieces = [to_piece(by_id[pid], slug_by_piece) for pid in order if pid in by_id]
    out.write_text(json.dumps(pieces, indent=1, ensure_ascii=False))
    extra_cost = sum(c["cost_usd"] for c in raw.get("extra_job_cost") or [])
    total = sum(p["cost_usd"] or 0 for p in pieces) + extra_cost
    print(f"{len(pieces)} pieces -> {out}  missing={raw.get('missing')}  "
          f"pieces ${total - extra_cost:.3f} + regen ${extra_cost:.3f} = ${total:.3f}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "container":
        container(sys.argv[2])
    else:
        local(sys.argv[1:])
