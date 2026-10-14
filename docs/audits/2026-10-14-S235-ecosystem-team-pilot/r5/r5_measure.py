"""S235 r5 deterministic metrics — $0, no LLM, no DB, no network. Comparable with S234 r1–r4.

Cách chấm (how it scores): every number below is computed by code on the stored pieces; nothing is a
model opinion. The panel (r5_panel.md) is the separate, judged half.

Run from the AA-CIS-App checkout that is DEPLOYED (main after AA-773/775 merge; before that, the
aa-775 worktree, which stacks AA-773 + AA-775 on main with AA-774/776/785/786):
  cd /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App && ENVIRONMENT=test PYTHONPATH=. .venv/bin/python \
      /home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/r5_measure.py \
      r4=/home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/pieces_r4_full.json \
      r5=/home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/pieces_r5.json \
      --out /home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/measure_r5.json
(Use `--repo <path>` instead of PYTHONPATH to point at a worktree.) Any number of label=path sets; the
LAST one is scored against the targets. A set without stored ledgers (the S234 pieces_r4.json export)
gets None for the ledger metrics — export r4 with r5_export.py --label r4 for a like-for-like baseline.

Metrics (issue -> metric -> target):
  hard errors     S234 measure_r4.py core total, unchanged script (regression guard)        r4 = 4
  AA-785          F1 violations on a year form ("1637–38", "1630s") in final + discarded       0
                  ledgers and repair_log
  AA-786          F9 classes; F9 violations mentioning citation/marker/[R:]/[F:]                0
                  t10_judge prompt_version (llm_call_log)                                  all f9_v1.1
                  t10_judge calls with piece_tag_free=false                                      0
                  LinkedIn held on F9_cta_fact                                    0 (unless sentences_left)
  AA-776          repair_log entries whose feedback is F4_seo_surface only -> repair_mode     all seo_fields
                  (slug-only F4 excluded: it legitimately rewrites)
  AA-774          seed "Place background" bullets of kind visiting/practical                    0
                  permit/access sentences per blog (permit|access requires|multi-hour …ride)  0/8 (r4 7/8)
  AA-773          seeds with a "Status: OFFERED, NOT INCLUDED" line (route blogs)              8/8 blogs
                  F17 "presents … as part of the plan" in final ledgers                         0
                  offline optional_as_fixed() on the final text (also scores r4)                info
                  blogs with a failed promises_an_option in the final ledger               ≤2/8 (Nghiệp's call)
  AA-775          pace sentences per tenant (PACE_RE over body spans, CTA + CTA paraphrase     Terra ≤2,
                  excluded — the aa775_pace_replay.py counter)                                  A&H ≤1
                  holds whose ONLY blocking reason is an F17 pace_promise                       0
                  LinkedIn holds on pace_promise                                                0
  cost            per piece / per channel / total (job llm_call_log)                         ≤ $1.40 total
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

S234 = Path("/home/nghiep/projects/AA-Ecosys/.tmp-session/s234")
PERMIT_RE = re.compile(r"\bpermit|\baccess requires|multi-hour (?:horse|reindeer) ride", re.I)
YEAR_FORM_RE = re.compile(r"\b(?:1\d{3}|20\d{2})\s*[–—-]\s*\d{2,4}\b|\b(?:1\d{3}|20\d{2})s\b")
F1_TOKENS_RE = re.compile(r"sentence states \[(.*?)\] not present in the content seed: '(.*)'", re.S)
CITATION_RE = re.compile(r"citation|marker|\[R:|\[F:", re.I)
OPTIONAL_AS_PLAN = "as part of the plan"
PACE_MSG = "pace or rest promise"
DROP_KINDS = {"visiting", "practical"}
# AA-774 heuristic for a bullet with no card match (the fact may have been merged away)
PRACTICAL_RE = re.compile(r"^(Visitors|Access|The hike|Trails lead|The road from|Summers are short|The region "
                          r"experiences|Water levels|Winters are severe)|\b(permit|must leave|required to wear|"
                          r"can swim|should be prepared|reached from)\b", re.I)
SHORT = {"Atlas & Hearth": "A&H", "Terra Family Expeditions": "Terra", "Trail Pulse": "Trail",
         "WildKind Travel": "WildKind"}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── per-piece helpers ───────────────────────────────────────────────────────────────────────────

def _failed(entries, gate=None):
    return [g for g in entries or [] if not g.get("passed") and (gate is None or g.get("gate") == gate)]


def all_ledgers(p):
    """(where, ledger) for the final ledger and every discarded attempt's ledger."""
    out = [("final", p.get("gate_ledger") or [])]
    for d in p.get("discarded_attempts") or []:
        out.append((f"discarded_a{d.get('attempt_number')}", d.get("gate_ledger") or []))
    return out


def f1_year_forms(p) -> list[str]:
    seen, hits = set(), []
    texts = [v for _, led in all_ledgers(p) for g in _failed(led, "F1_grounding") for v in g.get("violations") or []]
    for e in p.get("repair_log") or []:
        texts += [v for v in (e.get("violations") or []) if isinstance(v, str)]
        texts += [v.split(": ", 1)[1] for v in (e.get("feedback") or [])
                  if isinstance(v, str) and v.startswith("F1_grounding: ")]
    for v in texts:
        m = F1_TOKENS_RE.search(v)
        if not m or v in seen:
            continue
        seen.add(v)
        toks = [t.strip(" '\"") for t in m.group(1).split(",") if t.strip(" '\"")]
        forms = " ".join(x.group(0) for x in YEAR_FORM_RE.finditer(m.group(2)))
        if forms and toks and all(t in forms for t in toks):
            hits.append(v[:220])
    return hits


def f9_info(p) -> dict:
    final = [g for g in p.get("gate_ledger") or [] if g.get("gate") == "F9_cta_fact"]
    classes = defaultdict(int)
    citation = 0
    for _, led in all_ledgers(p):
        for g in _failed(led, "F9_cta_fact"):
            for v in g.get("violations") or []:
                citation += bool(CITATION_RE.search(str(v)))
    for e in p.get("repair_log") or []:
        for v in (e.get("feedback") or []) + (e.get("violations") or []):
            if isinstance(v, str) and v.startswith(("F9_cta_fact", "audit", "TEXT_INTEGRITY")):
                citation += bool(CITATION_RE.search(v))
    for g in _failed(final):
        for v in g.get("violations") or []:
            s = str(v)
            k = ("text_integrity" if s.startswith("TEXT_INTEGRITY") else
                 "title_meta" if s.startswith(("title ", "meta ")) else
                 "reasonless" if "judge gave no checkable reason" in s else
                 "cta_not_reflected" if "CTA_NOT_REFLECTED" in s else
                 "fact_check" if "FACT_CHECK" in s else "other")
            classes[k] += 1
    f9 = final[0] if final else {}
    return {"present": bool(final), "failed": bool(final) and not f9.get("passed"),
            "blocking": bool(f9.get("blocking", True)) if final and not f9.get("passed") else False,
            "waived": bool(f9.get("waived")), "sentences_cut": f9.get("sentences_cut"),
            "sentences_left": f9.get("sentences_left"), "classes": dict(classes), "citation_notes": citation,
            "prompt_versions": p.get("judge_prompt_versions"), "judge_tagged_calls": p.get("judge_tagged_calls")}


def repair_modes(p) -> dict:
    log = p.get("repair_log") or []
    f4_only, f4_seo, f4_miss, slug_only = 0, 0, [], 0
    for i, e in enumerate(log):
        fb = [v for v in (e.get("feedback") or []) if isinstance(v, str)]
        if not fb or not all(v.startswith("F4_seo_surface:") for v in fb):
            continue
        if all(re.search(r"\bslug\b", v) for v in fb):
            slug_only += 1
            continue
        f4_only += 1
        if e.get("repair_mode") == "seo_fields":
            f4_seo += 1
        elif i < len(log) - 1 or e.get("repair_mode"):
            f4_miss.append(f"attempt {e.get('attempt')}: mode={e.get('repair_mode')}")
        # last entry with no mode = the piece stopped there (no next attempt ran) — not a miss
    return {"modes": [e.get("repair_mode") or ("(none)" if e.get("gate_targeted") else "-") for e in log],
            "f4_only": f4_only, "f4_only_seo_fields": f4_seo, "f4_only_not_seo": f4_miss, "f4_slug_only": slug_only}


def seed_info(p) -> dict:
    seed = p.get("seed") or ""
    kinds = p.get("bg_bullet_kinds")
    if kinds is None:  # S234 export: no kinds stored -> heuristic only
        bullets, on = [], False
        for ln in seed.splitlines():  # "Place background" bullets only (not the sibling-trip lines)
            if ln.startswith("Place background"):
                on = True
            elif on and ln.startswith("- "):
                bullets.append(ln[2:].strip())
            else:
                on = False
        dropped = [b for b in bullets if PRACTICAL_RE.search(b)]
        src = "heuristic"
    else:
        dropped = [b["text"] for b in kinds if set(b["kinds"]) & DROP_KINDS
                   or ("<no card match>" in b["kinds"] and PRACTICAL_RE.search(b["text"]))]
        src = "place_card kinds"
    return {"bg_practical_bullets": [d[:120] for d in dropped], "bg_kind_source": src,
            "status_offered_lines": len(re.findall(r"^Status: OFFERED", seed, re.M)),
            "status_included_lines": len(re.findall(r"^Status: included", seed, re.M)),
            "seed_permit": bool(PERMIT_RE.search(seed))}


# ── main ────────────────────────────────────────────────────────────────────────────────────────

def measure_set(label: str, pieces: list[dict], mods) -> dict:
    hyg, tf, m4 = mods
    rows = []
    for i, p in enumerate(pieces):
        text = p.get("text") or ""
        tenant = p["tenant"]
        cta = p.get("cta") or (p.get("brand_pack") or {}).get("default_cta")
        has_ledger = "gate_ledger" in p
        # hard errors: the unchanged S234 script
        hard = m4.measure(p, i)
        # AA-775 pace sentences (the aa775_pace_replay.py counter)
        body = [sp["clean"] for sp in tf._body_spans(text, cta)]
        pace = [t for t in body if tf.PACE_RE.search(t) and not tf._cta_paraphrase(t, cta, tenant)]
        own = hyg.split_seed(p.get("seed") or "")[0]
        pace_wired = tf.pace_claims(text, own, cta, tenant)
        # AA-773 offline: optional activity written as part of the plan (deterministic, also on r4)
        moments = tf.parse_moments(p.get("seed") or "")
        opt_fixed = tf.optional_as_fixed(text, moments, cta)
        row = {"idx": i, "piece_id": p["piece_id"], "tenant": tenant, "t": SHORT.get(tenant, tenant),
               "channel": p["channel"], "status": p["status"], "attempt": p.get("attempt"),
               "failed": p.get("failed") or [], "held_reason": p.get("held_reason"),
               "hard_total": hard["hard_total"], "hard_counts": hard["hard_counts"],
               "permit_sentences": [s for s in body if PERMIT_RE.search(s)],
               "pace_sentences": pace, "pace_wired_offline": pace_wired,
               "optional_as_fixed_offline": opt_fixed,
               "seed": seed_info(p), "cost_usd": p.get("cost_usd"), "has_ledger": has_ledger}
        if has_ledger:
            final = p.get("gate_ledger") or []
            f17 = [str(v) for g in _failed(final, "F17_trip_fact") for v in g.get("violations") or []]
            blocking = [g for g in final if not g.get("passed") and g.get("blocking", True)]
            row.update({
                "f1_year_forms": f1_year_forms(p),
                "f9": f9_info(p),
                "repair": repair_modes(p),
                "f17_optional_as_plan": [v for v in f17 if OPTIONAL_AS_PLAN in v],
                "f17_pace_promise": [v for v in f17 if PACE_MSG in v],
                "promises_an_option": bool(_failed(final, "promises_an_option")) or any(
                    g.get("gate") == "promises_an_option" for g in p.get("flags") or []),
                "held_only_on_pace": p["status"] == "held" and len(blocking) == 1
                and blocking[0].get("gate") == "F17_trip_fact"
                and all(PACE_MSG in str(v) for v in blocking[0].get("violations") or []),
                "li_held_f9": p["channel"] == "linkedin" and p["status"] == "held"
                and any(g.get("gate") == "F9_cta_fact" for g in blocking),
            })
        rows.append(row)
    return {"label": label, "pieces": rows, "summary": summarize(rows)}


def summarize(rows: list[dict]) -> dict:
    blogs = [r for r in rows if r["channel"] == "blog"]
    li = [r for r in rows if r["channel"] == "linkedin"]
    led = [r for r in rows if r["has_ledger"]]
    led_blogs = [r for r in blogs if r["has_ledger"]]
    pace_t = defaultdict(int)
    pace_tc = defaultdict(int)
    for r in rows:
        pace_t[r["t"]] += len(r["pace_sentences"])
        pace_tc[f"{r['t']} {r['channel']}"] += len(r["pace_sentences"])
    cost = [r["cost_usd"] for r in rows if r["cost_usd"] is not None]
    s = {
        "n": len(rows), "blogs": len(blogs), "linkedin": len(li),
        "approved": sum(r["status"] == "approved" for r in rows),
        "held": sum(r["status"] == "held" for r in rows), "failed": sum(r["status"] == "failed" for r in rows),
        "blog_held": f"{sum(r['status'] == 'held' for r in blogs)}/{len(blogs)}",
        "li_held": f"{sum(r['status'] == 'held' for r in li)}/{len(li)}",
        "hard_errors_core": sum(r["hard_total"] for r in rows),
        "pieces_clean_core": sum(r["hard_total"] == 0 for r in rows),
        "permit_blogs": f"{sum(bool(r['permit_sentences']) for r in blogs)}/{len(blogs)}",
        "permit_sentences": sum(len(r["permit_sentences"]) for r in blogs),
        "pace_sentences_by_tenant": dict(pace_t), "pace_sentences_by_cell": dict(pace_tc),
        "pace_wired_offline_blog": sum(len(r["pace_wired_offline"]) for r in blogs),
        "optional_as_fixed_offline_blogs": f"{sum(bool(r['optional_as_fixed_offline']) for r in blogs)}/{len(blogs)}",
        "optional_as_fixed_offline_sentences": sum(len(r["optional_as_fixed_offline"]) for r in rows),
        "seed_practical_bullets": sum(len(r["seed"]["bg_practical_bullets"]) for r in rows),
        "seed_kind_source": sorted({r["seed"]["bg_kind_source"] for r in rows}),
        "blogs_with_status_offered": f"{sum(r['seed']['status_offered_lines'] > 0 for r in blogs)}/{len(blogs)}",
        "li_with_status_offered": f"{sum(r['seed']['status_offered_lines'] > 0 for r in li)}/{len(li)}",
        "cost_total": round(sum(cost), 4) if cost else None,
        "cost_mean_blog": round(sum(r["cost_usd"] or 0 for r in blogs) / len(blogs), 4) if blogs and cost else None,
        "cost_mean_li": round(sum(r["cost_usd"] or 0 for r in li) / len(li), 4) if li and cost else None,
    }
    if led:
        s.update({
            "ledger_pieces": len(led),
            "f1_year_form_hits": sum(len(r["f1_year_forms"]) for r in led),
            "f9_failed_final": sum(r["f9"]["failed"] for r in led),
            "f9_classes_final": _merge([r["f9"]["classes"] for r in led]),
            "f9_citation_notes": sum(r["f9"]["citation_notes"] for r in led),
            "f9_prompt_versions": sorted({v for r in led for v in (r["f9"]["prompt_versions"] or [])}),
            "f9_judge_tagged_calls": sum(r["f9"]["judge_tagged_calls"] or 0 for r in led),
            "f9_waived": sum(r["f9"]["waived"] for r in led),
            "li_held_on_f9": sum(r["li_held_f9"] for r in led),
            "li_held_on_f9_with_sentences_left": sum(r["li_held_f9"] and bool(r["f9"]["sentences_left"]) for r in led),
            "repair_modes": _merge([{m: 1} for r in led for m in r["repair"]["modes"]]),
            "f4_only_entries": sum(r["repair"]["f4_only"] for r in led),
            "f4_only_seo_fields": sum(r["repair"]["f4_only_seo_fields"] for r in led),
            "f4_only_not_seo": [x for r in led for x in r["repair"]["f4_only_not_seo"]],
            "f17_optional_as_plan_final": sum(len(r["f17_optional_as_plan"]) for r in led),
            "f17_optional_as_plan_pieces": sum(bool(r["f17_optional_as_plan"]) for r in led),
            "f17_pace_promise_final": sum(len(r["f17_pace_promise"]) for r in led),
            "promises_an_option_blogs": f"{sum(r['promises_an_option'] for r in led_blogs)}/{len(led_blogs)}",
            "held_only_on_pace": sum(r["held_only_on_pace"] for r in led),
            "li_pace_promise_in_ledger": sum(bool(r["f17_pace_promise"]) for r in led if r["channel"] == "linkedin"),
        })
    return s


def _merge(dicts):
    out = defaultdict(int)
    for d in dicts:
        for k, v in d.items():
            out[k] += v
    return dict(out)


def verdicts(s: dict) -> list[tuple[str, str, str, str]]:
    """(issue, metric, value, met/not met) for the scored set."""
    def v(key, default="n/a"):
        return s.get(key, default)
    pt = s["pace_sentences_by_tenant"]
    led = "ledger_pieces" in s
    out = [
        ("hygiene", "core hard errors (S234 measure_r4)", str(s["hard_errors_core"]),
         "met" if s["hard_errors_core"] <= 4 else "not met (r4 = 4)"),
        ("AA-785", "F1 year-form hits", str(v("f1_year_form_hits")),
         "n/a" if not led else "met" if s["f1_year_form_hits"] == 0 else "not met"),
        ("AA-786", "F9 citation/marker notes", str(v("f9_citation_notes")),
         "n/a" if not led else "met" if s["f9_citation_notes"] == 0 else "not met"),
        ("AA-786", "t10_judge prompt_version", str(v("f9_prompt_versions")),
         "n/a" if not led else "met" if s["f9_prompt_versions"] == ["f9_v1.1"] else "not met"),
        ("AA-786", "judge calls with tagged text", str(v("f9_judge_tagged_calls")),
         "n/a" if not led else "met" if s["f9_judge_tagged_calls"] == 0 else "not met"),
        ("AA-786", "LinkedIn held on F9 (with sentences_left)",
         f"{v('li_held_on_f9')} ({v('li_held_on_f9_with_sentences_left')})",
         "n/a" if not led else "met" if s["li_held_on_f9"] == s["li_held_on_f9_with_sentences_left"] else "not met"),
        ("AA-776", "F4-only repair entries -> seo_fields", f"{v('f4_only_seo_fields')}/{v('f4_only_entries')}",
         "n/a" if not led else "no F4-only ledger in r5 (close on unit tests)" if s["f4_only_entries"] == 0
         else "met" if not s["f4_only_not_seo"] else "not met"),
        ("AA-774", "seed visiting/practical bullets", str(s["seed_practical_bullets"]),
         "met" if s["seed_practical_bullets"] == 0 else "not met"),
        ("AA-774", "blogs with permit/access sentences", s["permit_blogs"],
         "met" if s["permit_blogs"].startswith("0/") else "not met (target 0/8)"),
        ("AA-773", "blogs whose seed has Status: OFFERED", s["blogs_with_status_offered"],
         "met" if s["blogs_with_status_offered"].split("/")[0] == s["blogs_with_status_offered"].split("/")[1]
         and s["blogs"] else "not met"),
        ("AA-773", "F17 optional-as-plan in final ledgers", str(v("f17_optional_as_plan_final")),
         "n/a" if not led else "met" if s["f17_optional_as_plan_final"] == 0 else "not met"),
        ("AA-773", "promises_an_option warn per blog (≤2/8, Nghiệp's call)", str(v("promises_an_option_blogs")),
         "n/a" if not led else "met" if int(s["promises_an_option_blogs"].split("/")[0]) <= 2 else "not met"),
        ("AA-775", "pace sentences Terra (≤2)", str(pt.get("Terra", 0)), "met" if pt.get("Terra", 0) <= 2 else "not met"),
        ("AA-775", "pace sentences A&H (≤1)", str(pt.get("A&H", 0)), "met" if pt.get("A&H", 0) <= 1 else "not met"),
        ("AA-775", "holds only on a pace_promise", str(v("held_only_on_pace")),
         "n/a" if not led else "met" if s["held_only_on_pace"] == 0 else "check: seed-supported? (target 0 FP)"),
        ("AA-775", "LinkedIn pace_promise in ledger", str(v("li_pace_promise_in_ledger")),
         "n/a" if not led else "met" if s["li_pace_promise_in_ledger"] == 0 else "not met"),
        ("cost", "pipeline cost total", f"${s['cost_total']}" if s["cost_total"] is not None else "n/a",
         "n/a" if s["cost_total"] is None else "met" if s["cost_total"] <= 1.40 else "not met (plan ≤ $1.40)"),
    ]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="+", help="label=path to a pieces JSON (S234 export or r5_export.py shape)")
    ap.add_argument("--repo", help="AA-CIS-App checkout to import services/ from (default: PYTHONPATH)")
    ap.add_argument("--out", help="write the full JSON here")
    a = ap.parse_args()
    if a.repo:
        sys.path.insert(0, a.repo)
    from services.acp_content_writing import hygiene as hyg
    from services.acp_content_writing import trip_facts as tf
    m4 = load_module("measure_r4", S234 / "measure_r4.py")
    results = []
    for spec in a.sets:
        label, path = spec.split("=", 1)
        results.append(measure_set(label, json.loads(Path(path).read_text()), (hyg, tf, m4)))
    keys = list(dict.fromkeys(k for r in results for k in r["summary"]))
    print("| metric | " + " | ".join(r["label"] for r in results) + " |")
    print("|---|" + "---|" * len(results))
    for k in keys:
        print(f"| {k} | " + " | ".join(json.dumps(r["summary"].get(k, "–"), ensure_ascii=False)
                                         for r in results) + " |")
    last = results[-1]
    print(f"\nTargets on `{last['label']}` (issue | metric | value | verdict):")
    for row in verdicts(last["summary"]):
        print(" | ".join(row))
    print(f"\nPer piece ({last['label']}):")
    for r in last["pieces"]:
        extra = ""
        if r["has_ledger"]:
            extra = (f" f9={r['f9']['classes'] or '-'} rep={r['repair']['modes']} opt17={len(r['f17_optional_as_plan'])}"
                     f" pao={int(r['promises_an_option'])} y={len(r['f1_year_forms'])}")
        print(f"#{r['idx']:>2} {r['t']:<8} {r['channel']:<8} {r['status']:<8} hard={r['hard_total']} "
              f"pace={len(r['pace_sentences'])} permit={len(r['permit_sentences'])} "
              f"optfix={len(r['optional_as_fixed_offline'])} prac={len(r['seed']['bg_practical_bullets'])} "
              f"offered={r['seed']['status_offered_lines']}{extra} ${r['cost_usd'] or 0:.3f}")
    if a.out:
        Path(a.out).write_text(json.dumps({"sets": results, "verdicts": verdicts(last["summary"])},
                                          indent=1, ensure_ascii=False, default=str))
        print("->", a.out)


if __name__ == "__main__":
    main()
