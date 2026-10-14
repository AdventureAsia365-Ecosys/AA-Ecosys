"""S235 T2 rerun scoring (AA-792 + AA-794) — local, $0, reads the score_dump.py output.

  python3 score.py dump.txt            # prints the report; writes score.json next to this file

Metric (synthesis R3 / plan correction 8): the judge's brand_fit_score from
shared.llm_call_log.quality_signal — NOT tenant_tour_versions.quality_score (which also carries
validate, and whose T2 gate rule changed in this release). Per job we take the LAST judge row
(stage t2_judge, or s1_judge for the S234 baseline jobs, which predate the AA-763 stage keys) =
the score of the draft the graph finished on. The S234 baseline is computed from the same dump
with the same rule, so before/after are like for like.

Claim rule: a per-tenant delta is only claimed when it is larger than the A/A' spread — the
|brand_fit(run) - brand_fit(repeat)| of the two Bhutan repeat pairs (Terra, WildKind), taken from
both the S234 baseline and this rerun (the larger one wins).
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET_BRAND_FIT = 7.0
COST_CAP = 5.00
META_MIN, META_MAX = 140, 155

# AA-794 heuristic detector for a meta that ends on a cut content word ("…with expert.").
# It is a flag for a human read, not a gate: the 14 metas are always listed in full as well.
_CONNECTOR_END = {"and", "with", "including", "or", "plus", "to", "for", "from", "in", "on", "at",
                  "a", "an", "the", "by", "of", "via", "into", "through", "between", "as", "across",
                  "along", "among", "around", "while", "where", "which"}
_MODIFIER_END = {"expert", "daily", "fragile", "distinct", "local", "private", "active", "ancient",
                 "guided", "traditional", "cultural", "scenic", "remote", "rural", "coastal", "historic",
                 "sacred", "wild", "natural", "small", "high", "full", "key", "main", "rich", "open",
                 "quiet", "national", "regional", "seasonal"}
# Nouns that usually modify a following noun ("mountain regions", "valley harvests"). Flagged only in
# lower case — "the Gobi Desert." / "the Paro Valley." are proper names, not cuts.
_NOUN_MODIFIER_END = {"mountain", "valley", "river", "forest", "desert", "lake", "family", "village",
                      "farm", "temple", "rice", "tea", "hill", "wildlife", "heritage", "food"}
_ADJ_SUFFIX = re.compile(r"(?:al|ive|ous|ic|ful|ile|ary|ian)$")


def suspect_cut(meta: str) -> str | None:
    m = (meta or "").strip()
    if not m.endswith("."):
        return "no period"
    words = m[:-1].split()
    if not words:
        return "empty"
    last = re.sub(r"[^a-z]", "", words[-1].lower())
    prev = re.sub(r"[^a-z]", "", words[-2].lower()) if len(words) > 1 else ""
    if last in _CONNECTOR_END:
        return f"ends on connector '{last}'"
    if last in _MODIFIER_END:
        return f"ends on modifier '{last}'"
    if last in _NOUN_MODIFIER_END and words[-1][:1].islower():
        return f"ends on noun modifier '{last}'"
    if _ADJ_SUFFIX.search(last) and prev in _CONNECTOR_END:
        return f"'{prev} {last}' looks like a cut noun phrase"
    return None


def wrong_country(meta: str, country: str, aa_name: str) -> str | None:
    """A ', in <X>.' tail on a multi-country tour (S234: 'Cuc Phuong National Park, in Laos.')."""
    m = (meta or "").strip()
    tail = re.search(r",\s+in ([A-Z][\w ]+)\.$", m)
    multi = sum(c in (aa_name or "") for c in ("Laos", "Vietnam", "Cambodia", "Thailand", "Myanmar",
                                              "China", "Tibet", "Nepal", "India", "Bhutan"))
    if tail and multi >= 2:
        return f"country tail '{tail.group(0)}' on a multi-country tour"
    return None


def parse_dump(path: str) -> dict:
    text = Path(path).read_text()
    body = text.split("===DUMP===", 1)[1].split("===END===", 1)[0]
    return json.loads(body.strip())


def last_judge(judges: list[dict]) -> dict | None:
    return judges[-1]["qs"] if judges else None


def main(path: str) -> None:
    d = parse_dump(path)
    pairs = json.loads((HERE / "pairs.json").read_text())["runs"]
    state = json.loads((HERE / "state.json").read_text())["runs"] if (HERE / "state.json").exists() else []
    by_job_j: dict[str, list] = {}
    for j in d["judges"]:
        by_job_j.setdefault(j["job_id"], []).append(j)
    cost_by_job: dict[str, float] = {}
    for c in d["costs"]:
        cost_by_job[c["job_id"]] = cost_by_job.get(c["job_id"], 0.0) + c["cost"]
    ver_by_job = {v["job_id"]: v for v in d["versions"]}

    rows = []
    for p in pairs:
        s = next((r for r in state if r["s234_version_id"] == p["s234_version_id"]), {})
        for side, job in (("s234", p["s234_job_id"]), ("rerun", s.get("job_id"))):
            if not job:
                continue
            qs = last_judge(by_job_j.get(job, [])) or {}
            v = ver_by_job.get(job, {})
            rows.append({
                "side": side, "wave": p["wave"], "slug": p["slug"], "country": p["country"], "job_id": job,
                "version_id": v.get("version_id"), "brand_fit": qs.get("brand_fit_score"),
                "judge_score": qs.get("judge_score"), "distinct": qs.get("cross_brand_distinct"),
                "mission": qs.get("mission_present"), "gate": qs.get("gate"),
                "mission_source": qs.get("mission_source"),
                "judge_calls": len(by_job_j.get(job, [])), "quality_score": v.get("quality_score"),
                "status": v.get("status"), "qa_status": v.get("qa_status"),
                "brand_loaded": (v.get("job_result") or {}).get("brand_loaded"),
                "cost": round(cost_by_job.get(job, 0.0), 4), "seo_meta": v.get("seo_meta"),
                "aa_name": v.get("aa_name") or p["aa_name"],
            })

    def tenant_mean(side: str, slug: str) -> float | None:
        vals = [r["brand_fit"] for r in rows if r["side"] == side and r["slug"] == slug and r["brand_fit"] is not None]
        return round(statistics.mean(vals), 2) if vals else None

    def spread(side: str) -> float:
        out = []
        for slug in ("terra-family", "wildkind-travel"):
            bh = [r["brand_fit"] for r in rows if r["side"] == side and r["slug"] == slug
                  and r["country"] == "Bhutan" and r["brand_fit"] is not None]
            if len(bh) == 2:
                out.append(abs(bh[0] - bh[1]))
        return max(out) if out else 0.0

    aa_spread = max(spread("s234"), spread("rerun"))
    print(f"A/A' spread (Bhutan repeats, max of S234 {spread('s234')} and rerun {spread('rerun')}): {aa_spread}\n")
    print(f"{'tenant':16} {'S234 bf':>8} {'rerun bf':>9} {'delta':>6}  claim  target>=7")
    report = {"aa_spread": aa_spread, "tenants": {}, "checks": {}}
    for slug in ("atlas-hearth", "terra-family", "trail-pulse", "wildkind-travel"):
        b, n = tenant_mean("s234", slug), tenant_mean("rerun", slug)
        delta = round(n - b, 2) if (b is not None and n is not None) else None
        claim = delta is not None and abs(delta) > aa_spread
        ok = n is not None and n >= TARGET_BRAND_FIT
        report["tenants"][slug] = {"s234": b, "rerun": n, "delta": delta, "claimable": claim, "target_met": ok}
        print(f"{slug:16} {b!s:>8} {n!s:>9} {delta!s:>6}  {'yes' if claim else 'no ':5}  {'OK' if ok else 'MISS'}")

    rr = [r for r in rows if r["side"] == "rerun"]
    checks = report["checks"]
    checks["runs_finished"] = len(rr)
    checks["failed_or_no_brand"] = [r["version_id"] for r in rr if r["status"] == "failed" or not r["brand_loaded"]]
    # Gate B (Nghiệp, 14/10): judge_score = brand_fit, capped at 6.0 when the tenant's own mission (core_idea)
    # is absent; a tenant with no core_idea is never capped (mission_source "none").
    def expected_judge(r: dict) -> float | None:
        bf = r["brand_fit"]
        if bf is None:
            return None
        if r["mission_source"] == "tenant_core_idea" and r["mission"] is False:
            return min(bf, 6.0)
        return bf

    checks["gate_mismatch"] = [r["version_id"] for r in rr
                               if r["gate"] != "brand_fit_mission" or r["judge_score"] != expected_judge(r)]
    checks["mission_source_not_tenant"] = [r["version_id"] for r in rr if r["mission_source"] != "tenant_core_idea"]
    checks["mission_absent_rate"] = (f"{sum(1 for r in rr if r['mission'] is False)}/{len(rr)} "
                                     "(S234 baseline 72/104 judge calls)")
    checks["diagnostics_missing"] = [r["version_id"] for r in rr if r["mission"] is None or r["distinct"] is None]
    checks["capped_despite_brand_fit"] = [  # brand_fit >= 7 but the version saved < 7: validate or a cap?
        {"version_id": r["version_id"], "brand_fit": r["brand_fit"], "quality_score": r["quality_score"]}
        for r in rr if (r["brand_fit"] or 0) >= 7 and (r["quality_score"] or 0) < 7]
    checks["cost_total"] = round(sum(r["cost"] for r in rr), 4)
    checks["cost_ok"] = checks["cost_total"] <= COST_CAP
    checks["meta_out_of_band"] = [r["version_id"] for r in rr
                                  if not (META_MIN <= len((r["seo_meta"] or "").strip()) <= META_MAX)]
    checks["meta_suspect_cut"] = [{"version_id": r["version_id"], "why": suspect_cut(r["seo_meta"])}
                                  for r in rr if suspect_cut(r["seo_meta"])]
    checks["meta_wrong_country"] = [{"version_id": r["version_id"], "why": wrong_country(r["seo_meta"], r["country"],
                                                                                         r["aa_name"])}
                                    for r in rr if wrong_country(r["seo_meta"], r["country"], r["aa_name"])]
    checks["s234_detector_sanity"] = [r["version_id"] for r in rows if r["side"] == "s234" and suspect_cut(r["seo_meta"])]
    print("\nchecks:")
    for k, v in checks.items():
        print(f"  {k}: {v}")
    print("  (s234_detector_sanity should list the 5 S234 fragment versions: cbba9416 9a4b7959 81102180 "
          "26e0ba34 5b442cdf)")

    print("\nthe 14 rerun metas (human read):")
    for r in rr:
        print(f"  [{len((r['seo_meta'] or '').strip())}] {r['slug']:16} {r['country']:9} {r['seo_meta']}")
    print("\nfor Nghiệp's voice read (Trail Pulse + Atlas & Hearth, rerun vs S234):")
    for slug in ("trail-pulse", "atlas-hearth"):
        for r in [x for x in rows if x["slug"] == slug]:
            print(f"  {r['side']:5} {slug:13} {r['country']:9} version={r['version_id']} brand_fit={r['brand_fit']}")
    print(f"\ncost: rerun ${checks['cost_total']} (cap ${COST_CAP}); "
          f"per version ${round(checks['cost_total'] / max(1, len(rr)), 3)} (S234 $0.372)")
    report["rows"] = rows
    (HERE / "score.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "dump.txt"))
