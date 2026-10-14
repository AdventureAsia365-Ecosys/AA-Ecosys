"""AA-786 — F9_cta_fact v1.1 offline replay + 3-run stability (paid, hard cap $0.50).

Runs the DEPLOYED quality_gates.gate_brand_voice (must report F9_PROMPT_VERSION == "f9_v1.1", i.e. after
the AA-786 PR is merged and Deploy Dev is COMPLETED) on 23 stored S234 pieces x RUNS (default 3):
  - the 20 r4 final texts, and
  - the 4 notes-only fallback holds r1#9, r3#4, r3#12, r4#12 (r4#12 is in both sets → 23 pieces).
Inputs per piece, exactly what T9 used: content_text, seo_title / meta_description (blog only),
grounding = service.grounding_from_writer_input(writer_input), cta / brand_rubric / brand voice from
writer_input. Read-only SELECT on acp_shared.content_piece.

Every judge call: LLMClient.generate pinned to --model (default gpt-5.6-luna, today's t10_judge model;
model_tier pinned → no route fallback, no shadow) + record_call_sync(stage="adhoc_aa786", role="judge").
The gate's own t10_judge log call is silenced so nothing lands under the production stage. Before
every call the budget checks max(logged cost, chars/4 estimate) against --max-usd (default 0.50) and
stops the run (partial results are still written) when the next call would cross it.

Expected: 23 pieces x 3 runs = 69 calls, ~ $0.004-0.006 each → ~ $0.30-0.40.

Output (also uploaded to S3 when --s3-out is given): aa786_replay.json + aa786_replay.md
  - notes mentioning 'citation' / 'marker' (Done-when: 0),
  - each fallback piece: per-run outcome (pass / blocking-quoted / warn) — Done-when: none ends as an
    unquoted blocking fail,
  - stability table: per-piece verdict agreement over the runs and mean pairwise Jaccard of the
    flagged-sentence sets (claims + TEXT_INTEGRITY).

WHERE TO RUN — a one-off ECS task (lessons.md: never a long adhoc run inside the api/worker task while
backend PRs are pending), started from the api task definition with a command override; the script
is fetched from S3 by a presigned URL. Single-line commands (orchestrator; needs Nghiệp's go for the
paid run):

  aws s3 cp /home/nghiep/projects/AA-Ecosys/.tmp-session/s235/aa786_replay.py s3://aa-cis-bronze-005097885195/scripts/s235/aa786_replay.py --profile aa365-admin --region us-west-1
  URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/s235/aa786_replay.py --profile aa365-admin --region us-west-1 --expires-in 900)
  (dry run first, $0)  same run-task as below with "--dry-run"
  aws ecs run-task --cluster aa-cis-dev-cluster --task-definition <current aa-cis-dev-api family:revision> --launch-type FARGATE --network-configuration "<same awsvpcConfiguration as the aa-cis-dev-api service>" --overrides "{\"containerOverrides\":[{\"name\":\"api\",\"command\":[\"sh\",\"-c\",\"cd /app && curl -s '$URL' -o /tmp/r.py && PYTHONPATH=/app python3 /tmp/r.py --s3-out s3://aa-cis-bronze-005097885195/scripts/s235/aa786_out/\"]}]}" --profile aa365-admin --region us-west-1
  then: aws s3 cp s3://aa-cis-bronze-005097885195/scripts/s235/aa786_out/aa786_replay.md - --profile aa365-admin --region us-west-1

Local checks ($0, no DB, no LLM; texts from .tmp-session/s234/final/joined2.json + pieces*.json, so the
grounding lacks writer_input facts/trip — fine for exercising the pipeline):
  <venv python> aa786_replay.py --local --repo <worktree> --dry-run
  <venv python> aa786_replay.py --local --repo <worktree> --fake-llm
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import itertools
import json
import os
import re
import sys
import time
from pathlib import Path

STAGE = "adhoc_aa786"
PRICES = {"gpt-5.6-luna": (0.20, 1.20), "gpt-6-luna": (0.10, 0.50)}  # $/MTok in, out (catalog, S234)
OUT_EST = 2500  # output tokens assumed per F9 call (reasoning + JSON)
ROOT = Path("/home/nghiep/projects/AA-Ecosys/.tmp-session")
MARKER_RE = re.compile(r"citation|marker|\[R:|\[F:", re.IGNORECASE)
PIECES = {
    "49ed3642-30d5-4696-a228-479c017665a7": ("r4#0", False), "91e4b9d2-157a-4a5f-90b3-332b6d9f5338": ("r4#1", False),
    "1376c2c3-7560-4394-bed8-97063f4d5564": ("r4#2", False), "7c8bc7df-5de4-402b-8ffc-2b3b72afc67a": ("r4#3", False),
    "3fd85285-7010-4338-9172-34d4acbe4b0a": ("r4#4", False), "bb776a54-93cc-4f10-a108-6e26f9f05324": ("r4#5", False),
    "71ad6b1f-9eb5-4509-915c-5c7644a5b71a": ("r4#6", False), "6961b261-6956-4b66-b563-9d34b8f8b5da": ("r4#7", False),
    "e980728e-f77a-47ba-8b59-0b63a28e301c": ("r4#8", False), "d8990697-4227-4ddc-9541-793c8ae59993": ("r4#9", False),
    "68a56edf-32df-477c-b0c1-2413a1360472": ("r4#10", False), "6599b514-4fbb-4c45-ba22-f29b234e4143": ("r4#11", False),
    "bf00c670-4496-409c-b8ef-9938c339685c": ("r4#12", True), "e61ad7bc-6684-49d9-9727-cafec9de28b8": ("r4#13", False),
    "67f08753-4c50-4962-a8bd-10224ac2df78": ("r4#14", False), "9594430b-93c7-425d-ac19-9dde2c33fe88": ("r4#15", False),
    "2fc0a2fb-7708-4a38-a3b5-b1275c1e3089": ("r4#16", False), "9b65bd97-0e42-4ceb-96c3-2e50c3bb8058": ("r4#17", False),
    "4c2bb8c1-dfaf-4369-b349-36bde9e9e5c9": ("r4#18", False), "5939df86-f8d4-491e-affc-348d0618ddcd": ("r4#19", False),
    "f09734c1-d07c-4c17-a181-801e28daba92": ("r1#9", True), "530aec31-ac34-45a2-9018-7233ad61ef2a": ("r3#4", True),
    "c134808c-cbf5-428a-a178-62f8a60c1826": ("r3#12", True),
}


# ---------------------------------------------------------------- inputs

async def _rows_db(ids: list[str]) -> list[dict]:
    import asyncpg
    import boto3
    from urllib.parse import urlparse
    sm = boto3.client("secretsmanager", region_name="us-west-1")
    p = urlparse(sm.get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"].strip())
    conn = await asyncpg.connect(host=p.hostname, port=p.port or 5432, database=p.path.lstrip("/"),
                                 user=p.username, password=p.password, ssl="require")
    try:
        rows = await conn.fetch(
            """SELECT piece_id::text pid, content_text, seo_title, meta_description, writer_input::text wi
               FROM acp_shared.content_piece WHERE piece_id = ANY($1::uuid[])""", ids)
    finally:
        await conn.close()
    return [dict(r) for r in rows]


def load_inputs(args) -> list[dict]:
    from services.acp_content_writing.service import grounding_from_writer_input, grounding_text_from
    out = []
    if args.local:
        local = {}
        for f in ("pieces.json", "pieces_r2.json", "pieces_r3.json", "pieces_r4.json"):
            for p in json.loads((ROOT / "s234" / f).read_text()):
                local[p["piece_id"]] = p
        joined = {x["pid"]: x for x in json.loads((ROOT / "s234/final/joined2.json").read_text())}
        for pid in PIECES:
            p, x = local[pid], joined[pid]
            out.append({"pid": pid, "channel": x["ch"], "text": x["text"], "seo_title": x.get("seo_title"),
                        "meta": x.get("meta"), "cta": "Ask us about the dates.", "rubric": "(local run — no rubric)",
                        "voice": (p.get("brand_pack") or {}).get("voice"),
                        "grounding": grounding_text_from(seed=p.get("seed") or "", facts_text=None,
                                                         brand_audience=p.get("brand_pack"), trip_name=None,
                                                         destination=None)})
        return out
    for r in asyncio.run(_rows_db(list(PIECES))):
        wi = json.loads(r["wi"]) if r["wi"] else {}
        out.append({"pid": r["pid"], "channel": wi.get("channel"), "text": r["content_text"] or "",
                    "seo_title": r["seo_title"], "meta": r["meta_description"], "cta": wi.get("cta") or "",
                    "rubric": wi.get("brand_rubric") or "", "voice": (wi.get("brand_pack") or {}).get("voice"),
                    "grounding": grounding_from_writer_input(wi)})
    return out


# ---------------------------------------------------------------- budget + judge

class BudgetStop(Exception):
    pass


class Budget:
    def __init__(self, cap: float, model: str):
        self.cap, self.model, self.spent, self.calls, self.stopped = cap, model, 0.0, 0, False

    def estimate(self, chars: int, out_tokens: int = OUT_EST) -> float:
        pin, pout = PRICES.get(self.model, (0.20, 1.20))
        return (chars / 4 * pin + out_tokens * pout) / 1e6

    def check(self, chars: int) -> None:
        est = self.estimate(chars)
        if self.spent + est > self.cap:
            self.stopped = True
            raise BudgetStop(f"next call ~${est:.4f} would pass the cap (${self.spent:.4f} of ${self.cap:.2f})")

    def charge(self, resp, chars: int) -> float:
        pin, pout = PRICES.get(self.model, (0.20, 1.20))
        by_tokens = (max(resp.input_tokens or 0, chars // 4) * pin + (resp.output_tokens or 0) * pout) / 1e6
        charged = max(resp.cost_usd or 0.0, by_tokens)
        self.spent += charged
        self.calls += 1
        return charged


class FakeResp:
    def __init__(self, content: str):
        self.content, self.model_used, self.provider = content, "fake", "fake"
        self.input_tokens, self.output_tokens, self.cost_usd = 0, 300, 0.0
        self.stop_reason, self.satellite_account, self.fallback_used = "end_turn", None, False


def _fake_reply(user_prompt: str, k: int) -> str:
    """Synthetic judge replies cycling pass / quoted TEXT_INTEGRITY / notes-only."""
    piece = user_prompt.split("PIECE:\n", 1)[1].split("\n\n", 1)[0]
    first = piece.split(". ")[0][:200]
    base = {"status": "pass", "brand_fit": "1", "cta_clear": "1", "human_read": "1", "failure_codes": [],
            "flagged_phrases": [], "notes": "", "unsupported_claims": [], "broken_sentences": []}
    if k % 3 == 1:
        base.update(status="flagged", failure_codes=["TEXT_INTEGRITY"],
                    broken_sentences=[{"sentence": first, "problem": "fake"}])
    elif k % 3 == 2:
        base.update(status="manual_check", notes="something is off")
    return json.dumps(base)


_FAKE_COUNTER = itertools.count()


def make_judge(args, budget: Budget, sink: dict, meta: dict):

    def judge(system_prompt, user_prompt, max_tokens=2048, *, stage):
        chars = len(system_prompt) + len(user_prompt)
        budget.check(chars)
        sink["prompt_has_tags"] = bool(re.search(r"\[(?:R|F):", user_prompt.split("SOURCE (", 1)[0]))
        if args.fake_llm:
            resp = FakeResp(_fake_reply(user_prompt, next(_FAKE_COUNTER)))
            budget.charge(resp, 0)
        else:
            from shared.llm_client.call_log import record_call_sync
            from shared.llm_client.client import LLMClient
            from shared.llm_client.models import LLMRequest
            t0 = time.time()
            resp = LLMClient().generate(LLMRequest(system_prompt=system_prompt, user_prompt=user_prompt,
                                                   max_tokens=max_tokens, temperature=0, model_tier=args.model))
            charged = budget.charge(resp, chars)
            record_call_sync(stage=STAGE, role="judge", model=resp.model_used,
                             tokens_in=max(resp.input_tokens or 0, chars // 4), tokens_out=resp.output_tokens,
                             cost_usd=round(charged, 6),
                             quality_signal={"issue": "AA-786", "gate": "F9_brand_voice", "est_tokens_in": chars // 4,
                                             "provider_tokens_in": resp.input_tokens,
                                             "provider_cost_usd": resp.cost_usd,
                                             "latency_s": round(time.time() - t0, 2), **meta},
                             stop_reason=resp.stop_reason, account=resp.satellite_account,
                             fallback_used=resp.fallback_used)
        sink["raw"] = resp.content
        return {"text": resp.content, "model_used": resp.model_used, "provider": resp.provider,
                "input_tokens": resp.input_tokens, "output_tokens": resp.output_tokens,
                "stop_reason": resp.stop_reason, "account": resp.satellite_account,
                "fallback_used": resp.fallback_used, "cost_usd": resp.cost_usd}
    return judge


# ---------------------------------------------------------------- one run

SENT_RE = re.compile(r'"(.+?)" \(claims: ')
TI_RE = re.compile(r"^TEXT_INTEGRITY: '(.+)'$", re.DOTALL)


def classify(f9: dict) -> str:
    if f9["passed"]:
        return "pass"
    if not f9.get("blocking", True):
        return "warn_reasonless" if any(v.startswith("judge gave no checkable reason") for v in f9["violations"]) \
            else "warn_title_meta" if all(v.startswith(("title ", "meta ")) for v in f9["violations"]) else "warn"
    quoted = any(TI_RE.match(v) or "unsupported claim(s)" in v for v in f9["violations"])
    if any("CTA_NOT_REFLECTED" in v for v in f9["violations"]):
        return "block_cta"
    return "block_quoted" if quoted else "block_unquoted"


def flagged_sentences(f9: dict) -> set[str]:
    out = set()
    for v in f9["violations"]:
        m = TI_RE.match(v)
        if m:
            out.add(" ".join(m.group(1).lower().split()))
        elif "unsupported claim" in v:
            out |= {" ".join(s.lower().split()) for s in SENT_RE.findall(v)}
    return out


def run_one(args, budget, item: dict, run: int) -> dict:
    from services.acp_content_writing import quality_gates as qg
    sink: dict = {}
    meta = {"pid": item["pid"], "label": PIECES[item["pid"]][0], "run": run}
    orig_judge, orig_log = qg.invoke_judge, qg._log_t10_judge_call
    qg.invoke_judge, qg._log_t10_judge_call = make_judge(args, budget, sink, meta), (lambda *a, **k: None)
    try:
        seo = {"seo_title": item["seo_title"], "meta_description": item["meta"]} if item["channel"] == "blog" else {}
        results = qg.gate_brand_voice(qg.strip_citation_tags(item["text"]), item["cta"], item["rubric"],
                                      source_text=item["grounding"], voice=item["voice"], **seo)
    finally:
        qg.invoke_judge, qg._log_t10_judge_call = orig_judge, orig_log
    f9 = next(r for r in results if r["gate"] == "F9_cta_fact")
    try:
        notes = str(json.loads(sink.get("raw") or "{}").get("notes") or "")
    except Exception:
        notes = (sink.get("raw") or "")[:2000]
    return {**meta, "class": classify(f9), "blocking": f9.get("blocking", True), "violations": f9["violations"],
            "sentences": sorted(flagged_sentences(f9)), "notes": notes[:1500],
            "marker_note": bool(MARKER_RE.search(notes) or any(MARKER_RE.search(v) for v in f9["violations"])),
            "prompt_has_tags": sink.get("prompt_has_tags")}


# ---------------------------------------------------------------- report

def jaccard(a: set, b: set) -> float:
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def summarise(results: list[dict], runs: int) -> dict:
    by_pid = collections.defaultdict(list)
    for r in results:
        by_pid[r["pid"]].append(r)
    table = []
    for pid, rs in by_pid.items():
        label, fallback = PIECES[pid]
        classes = [r["class"] for r in rs]
        top = collections.Counter(classes).most_common(1)[0][1]
        pairs = list(itertools.combinations([set(r["sentences"]) for r in rs], 2))
        table.append({"label": label, "fallback": fallback, "runs": len(rs), "classes": classes,
                      "agreement": round(top / len(rs), 2),
                      "jaccard": round(sum(jaccard(a, b) for a, b in pairs) / len(pairs), 2) if pairs else None})
    table.sort(key=lambda t: (not t["fallback"], int(t["label"][1]), int(t["label"].split("#")[1])))
    full = [t for t in table if t["runs"] == runs]
    return {
        "calls": len(results),
        "marker_notes": sum(r["marker_note"] for r in results),
        "prompt_with_tags": sum(bool(r["prompt_has_tags"]) for r in results),
        "fallback_unquoted_block": [t["label"] for t in table if t["fallback"] and "block_unquoted" in t["classes"]],
        "classes": dict(collections.Counter(r["class"] for r in results)),
        "mean_agreement": round(sum(t["agreement"] for t in full) / len(full), 3) if full else None,
        "unanimous_pieces": sum(t["agreement"] == 1.0 for t in full),
        "mean_jaccard": (round(sum(t["jaccard"] for t in full if t["jaccard"] is not None) / len(full), 3)
                         if full else None),
        "table": table,
    }


def report_md(meta: dict, s: dict, budget: Budget) -> str:
    lines = [
        "# AA-786 — F9 v1.1 replay + 3-run stability", "",
        f"- mode: {meta['mode']}, model: {meta['model']}, prompt: {meta['prompt_version']}, runs: {meta['runs']}",
        f"- calls: {s['calls']}, charged ${budget.spent:.4f} of cap ${budget.cap:.2f}"
        + (" — STOPPED AT CAP" if budget.stopped else ""),
        f"- notes mentioning citation/marker: **{s['marker_notes']}** (Done-when: 0)",
        f"- prompts that still carried a tag: {s['prompt_with_tags']}",
        f"- fallback pieces ending as an unquoted blocking fail: **{s['fallback_unquoted_block'] or 'none'}**",
        f"- verdict classes: {s['classes']}",
        f"- mean verdict agreement: {s['mean_agreement']} ({s['unanimous_pieces']}/{len(s['table'])} unanimous); "
        f"mean pairwise Jaccard of flagged sentences: {s['mean_jaccard']}", "",
        "| piece | fallback | run classes | agreement | Jaccard |", "|---|---|---|---|---|",
    ]
    for t in s["table"]:
        lines.append(f"| {t['label']} | {'yes' if t['fallback'] else ''} | {', '.join(t['classes'])} | "
                     f"{t['agreement']} | {t['jaccard']} |")
    lines += ["", "Classes: pass; block_quoted (claim or TEXT_INTEGRITY sentence — repairable); block_cta; "
              "block_unquoted (must be 0 on fallback pieces); warn_reasonless (no checkable reason — ships "
              "flagged); warn_title_meta (title/meta claim only — ships flagged)."]
    return "\n".join(lines) + "\n"


def upload(args, paths: list[str]) -> None:
    if not args.s3_out:
        return
    import boto3
    m = re.match(r"s3://([^/]+)/(.*)$", args.s3_out)
    bucket, prefix = m.group(1), m.group(2).rstrip("/") + "/"
    s3 = boto3.client("s3", region_name="us-west-1")
    for p in paths:
        s3.upload_file(p, bucket, prefix + os.path.basename(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/app", help="code root (the container: /app; local: a worktree)")
    ap.add_argument("--local", action="store_true", help="texts from .tmp-session/s234 (no DB)")
    ap.add_argument("--dry-run", action="store_true", help="no LLM call, no log write; prints the plan and $ estimate")
    ap.add_argument("--fake-llm", action="store_true", help="synthetic judge replies, $0, no log write")
    ap.add_argument("--max-usd", type=float, default=0.50)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--out", default="/tmp/aa786_out")
    ap.add_argument("--s3-out", default=None)
    args = ap.parse_args()
    if args.max_usd > 0.50:
        raise SystemExit("cap is $0.50 for AA-786 (S235 plan) — refusing a higher --max-usd")
    sys.path.insert(0, args.repo)
    os.environ.setdefault("ENVIRONMENT", "test" if args.local else os.environ.get("ENVIRONMENT", "dev"))
    from services.acp_content_writing import quality_gates as qg
    version = getattr(qg, "F9_PROMPT_VERSION", None)
    if version != "f9_v1.1":
        raise SystemExit(f"deployed gate is not F9 v1.1 (F9_PROMPT_VERSION={version!r}) — deploy AA-786 first")
    items = load_inputs(args)
    budget = Budget(args.max_usd, args.model)
    # + ~6000 chars of fixed prompt (rules, anchor, contract) per call
    est = args.runs * sum(budget.estimate(len(i["text"]) + len(i["grounding"]) + len(i["rubric"]) + 6000)
                          for i in items)
    meta = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "mode": "dry-run" if args.dry_run else
            ("fake-llm" if args.fake_llm else "PAID"), "model": args.model, "prompt_version": version,
            "runs": args.runs, "pieces": len(items), "missing": sorted(set(PIECES) - {i["pid"] for i in items}),
            "est_usd": round(est, 4), "cap_usd": args.max_usd}
    print(json.dumps(meta, indent=1))
    if args.dry_run:
        return
    results: list[dict] = []
    try:
        for run in range(1, args.runs + 1):  # interleaved, so a cap stop leaves comparable runs
            for item in items:
                results.append(run_one(args, budget, item, run))
            print(f"run {run} done — ${budget.spent:.4f}", flush=True)
    except BudgetStop as e:
        print(f"STOPPED: {e}", flush=True)
    s = summarise(results, args.runs)
    os.makedirs(args.out, exist_ok=True)
    out_json, out_md = f"{args.out}/aa786_replay.json", f"{args.out}/aa786_replay.md"
    json.dump({"meta": meta, "budget": {"cap": budget.cap, "charged": round(budget.spent, 6), "calls": budget.calls,
                                        "stopped": budget.stopped}, "summary": s, "results": results},
              open(out_json, "w"), indent=1, ensure_ascii=False)
    md = report_md(meta, s, budget)
    open(out_md, "w").write(md)
    upload(args, [out_json, out_md])
    print(md)


if __name__ == "__main__":
    main()
