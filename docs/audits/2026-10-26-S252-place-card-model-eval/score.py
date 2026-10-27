"""AA-784 place-card model eval: join the blind panel labels to the key and apply design.md §6/§7.

Inputs (all local): post/results.json, post/panel_key.json, panel/out/labels_<gid>_adj.json (+ _A/_B for kappa).
Output: post/metrics.json + a printed summary.
"""
import glob
import json
import math
from collections import Counter, defaultdict

R = json.load(open("post/results.json"))
K = json.load(open("post/panel_key.json"))
N_CARDS = 9186
WRITER_KINDS = {"what_it_is", "setting", "history", "naming"}
VENDOR = {"gpt-5.6-luna": "openai", "gpt-6-luna": "openai", "haiku": "anthropic", "haiku-5-5": "anthropic",
          "sonnet": "anthropic", "sonnet-5-5": "anthropic", "opus-5-5": "anthropic"}

drafts = {d["draft_id"]: d for d in R["drafts"]}
checks = list(R["checks"])
planted = R["planted"]

# ── labels ──────────────────────────────────────────────────────────────────────────────────────
V, F, L, REF = {}, {}, {}, {}
for p in glob.glob("panel/out/labels_*_adj.json"):
    a = json.load(open(p))
    REF[a["group_id"]] = a["reference"]
    for v in a["variants"]:
        V[v["vid"]] = v
    for f in a["facts"]:
        # merge rule: supported/contradicted need a URL + quote
        if f["verdict"] in ("supported", "contradicted") and not any(s.get("url") and s.get("quote") for s in f.get("sources") or []):
            f = dict(f, verdict="unverifiable")
        F[f["fid"]] = f
    for x in a.get("links") or []:
        L[x["lid"]] = x

import os as _os
if _os.path.exists('post/overrides.json') and _os.environ.get('OVERRIDES', '1') == '1':
    for _vid, _f in json.load(open('post/overrides.json')).items():
        V[_vid] = dict(V[_vid], **_f, overridden=True)

# ── key: draft fact -> fid, draft -> vid ────────────────────────────────────────────────────────
fact_of = {}
for fid, refs in K["fact"].items():
    for did, i in refs:
        fact_of[(did, i)] = fid
vid_of = {}
for vid, dids in K["identity"].items():
    for did in dids:
        vid_of[did] = vid


def ident_ok(vid):
    v = V.get(vid)
    if v is None:
        return None
    return (v["name"] == "ok" and v["locality"] != "wrong" and v["region"] != "wrong"
            and v["country"] == "correct" and v["entity"] == "same")


def card_of(did):
    if did.startswith("P@"):
        return planted[did[2:]]
    return drafts[did]["card"]


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - m) / d, 4), round((c + m) / d, 4)]


import os
IDENT = os.environ.get("IDENT", "yes").split(",")
identifiable = {g for g, ref in REF.items() if ref.get("identifiable") in IDENT}

# ── per pair (cell) ─────────────────────────────────────────────────────────────────────────────
cells = defaultdict(list)
for c in checks:
    run = c["target"].split("@")[0]
    cells[(run, c["checker"])].append(c)

pair = {}
for (run, ck), cs in sorted(cells.items()):
    if run == "P":
        continue
    dkey = R["drafters"][run.split("#")[0]]
    ckey = R["checkers"][ck]
    stored = [c for c in cs if c["outcome"] == "stored"]
    kept = contra = unver = leak_n = leak_d = useful = 0
    wi = wrong_country = 0
    for c in stored:
        did = c["target"]
        card = card_of(did)
        vid = vid_of.get(did)
        ok = ident_ok(vid)
        if ok is False:
            wi += 1
            if V[vid]["country"] == "wrong":
                wrong_country += 1
        for i in c["kept_idx"]:
            f = F.get(fact_of.get((did, i)))
            if f is None:
                continue
            kept += 1
            contra += f["verdict"] == "contradicted"
            unver += f["verdict"] == "unverifiable"
            if card["facts"][i]["kind"] in WRITER_KINDS:
                leak_d += 1
                leak_n += bool(f["trip_leak"])
                if f["verdict"] == "supported" and not f["trip_leak"] and not f["trivial"]:
                    useful += 1
    # cost per attempted group: draft + check (no-name drafts cost a draft only)
    run_drafts = [d for d in drafts.values() if d["run"] == run]
    cost = sum(d["cost"] or 0 for d in run_drafts) + sum(c["cost"] or 0 for c in cs)
    per_group = cost / len(run_drafts)
    groups_ident = {d["group_id"] for d in run_drafts} & identifiable
    stored_ident = {c["group_id"] for c in stored} & identifiable
    bad_drafts = sum(1 for d in run_drafts if d["error"] or not d["parse_ok"])
    bad_checks = sum(1 for c in cs if c["error"] or c["unusable"])
    pair[f"{run}x{ck}"] = {
        "drafter": dkey, "checker": ckey, "cross_vendor": VENDOR[dkey] != VENDOR[ckey],
        "stored": len(stored), "kept": kept, "contradicted_kept": contra, "unverifiable_kept": unver,
        "FK": round(contra / kept, 4) if kept else None, "FK_ci": wilson(contra, kept),
        "UK": round(unver / kept, 4) if kept else None,
        "LK": round(leak_n / leak_d, 4) if leak_d else None, "leaks_kept": leak_n,
        "WI": round(wi / len(stored), 4) if stored else None, "wrong_identity_stored": wi,
        "wrong_country_stored": wrong_country,
        "coverage": round(len(stored_ident) / len(groups_ident), 4) if groups_ident else None,
        "U": round(useful / len(stored), 3) if stored else None,
        "cost_per_group": round(per_group, 6), "projected_full": round(per_group * N_CARDS, 2),
        "bad_drafts": bad_drafts, "bad_checks": bad_checks,
    }

# ── per drafter ─────────────────────────────────────────────────────────────────────────────────
drafter = {}
for run in sorted({d["run"] for d in drafts.values()}):
    ds = [d for d in drafts.values() if d["run"] == run]
    cards = [d for d in ds if d.get("card")]
    oks = [ident_ok(vid_of.get(d["draft_id"])) for d in cards]
    loc_ok = [V[vid_of[d["draft_id"]]]["locality"] in ("correct", "acceptable_nearby") for d in cards if vid_of.get(d["draft_id"]) in V]
    mixed = sum(1 for d in cards if V.get(vid_of.get(d["draft_id"]), {}).get("entity") == "mixed")
    facts = [(d["draft_id"], i) for d in cards for i in range(len(d["card"]["facts"]))]
    lab = [F[fact_of[x]] for x in facts if fact_of.get(x) in F]
    no_name_ident = sum(1 for d in ds if not d.get("card") and d["group_id"] in identifiable)
    drafter[run] = {
        "model": R["drafters"][run.split("#")[0]], "cards": len(cards), "no_name": len(ds) - len(cards),
        "no_name_on_identifiable": no_name_ident,
        "identity_correct": round(sum(1 for o in oks if o) / len(cards), 4) if cards else None,
        "wrong_identities": sum(1 for o in oks if o is False),
        "locality_correct": round(sum(loc_ok) / len(loc_ok), 4) if loc_ok else None,
        "mixed": mixed, "facts": len(lab),
        "hallucination_rate": round(sum(f["verdict"] == "contradicted" for f in lab) / len(lab), 4) if lab else None,
        "contradicted": sum(f["verdict"] == "contradicted" for f in lab),
        "unverifiable_rate": round(sum(f["verdict"] == "unverifiable" for f in lab) / len(lab), 4) if lab else None,
        "leak_rate": round(sum(bool(f["trip_leak"]) for f in lab) / len(lab), 4) if lab else None,
        "errors": sum(1 for d in ds if d["error"] or not d["parse_ok"]),
        "cost_per_draft": round(sum(d["cost"] or 0 for d in ds) / len(ds), 6),
    }
# stability D1#1 vs D1#2
s1 = {d["group_id"]: d for d in drafts.values() if d["run"] == "D1#1"}
s2 = {d["group_id"]: d for d in drafts.values() if d["run"] == "D1#2"}
agree = sum(1 for g in s1 if g in s2 and (vid_of.get(s1[g]["draft_id"]) == vid_of.get(s2[g]["draft_id"])))
f1 = {fact_of.get((s1[g]["draft_id"], i)) for g in s1 if s1[g].get("card") for i in range(len(s1[g]["card"]["facts"]))}
f2 = {fact_of.get((s2[g]["draft_id"], i)) for g in s2 if s2[g].get("card") for i in range(len(s2[g]["card"]["facts"]))}
stability = {"identity_same_variant": f"{agree}/{len(s1)}", "fact_jaccard": round(len(f1 & f2) / len(f1 | f2), 3)}

# ── per checker: recall on natural + planted errors ─────────────────────────────────────────────
checker = {}
for ck, ckey in R["checkers"].items():
    cs = [c for c in checks if c["checker"] == ck]
    fr_n = fr_k = id_n = id_k = sup_n = sup_drop = 0
    by_vendor = defaultdict(lambda: [0, 0])
    p_fr_n = p_fr_k = p_id_n = p_id_k = 0
    for c in cs:
        did = c["target"]
        card = card_of(did)
        verdicts = c.get("verdicts") or []
        is_p = did.startswith("P@")
        if is_p:
            pinfo = planted[did[2:]]
            pf = pinfo["planted_fact"]
            idx = pf["index"]
            fid = fact_of.get((did, idx))
            lab = F.get(fid)
            # known false: mutation of a fact the panel supports in the source card, or fabricated not supported
            if pf["type"] == "fabricated":
                known_false = lab is not None and lab["verdict"] != "supported"
            else:
                src = fact_of.get(("D1#1@" + did[2:], idx))
                known_false = F.get(src, {}).get("verdict") == "supported" and lab is not None and lab["verdict"] != "supported"
            if known_false and c["outcome"] == "stored":
                p_fr_n += 1
                p_fr_k += (verdicts[idx] if idx < len(verdicts) else "supported") != "supported"
            elif known_false:  # identity rejected: the planted fact did not get stored
                p_fr_n += 1
                p_fr_k += 1
            if pinfo.get("planted_identity") and V.get(vid_of.get(did), {}).get("locality") == "wrong":
                p_id_n += 1
                p_id_k += c["identity_ok"] is False
            continue
        vid = vid_of.get(did)
        ok = ident_ok(vid)
        if ok is False:
            id_n += 1
            id_k += c["identity_ok"] is False
        if c["outcome"] != "stored" and c["identity_ok"] is not False:
            continue
        for i, fct in enumerate(card["facts"]):
            lab = F.get(fact_of.get((did, i)))
            if lab is None:
                continue
            v = verdicts[i] if i < len(verdicts) else "supported"
            dropped = c["identity_ok"] is False or v != "supported"
            if lab["verdict"] == "contradicted":
                fr_n += 1
                fr_k += dropped
                vend = "same" if VENDOR[drafts[did]["model_key"]] == VENDOR[ckey] else "cross"
                by_vendor[vend][0] += 1
                by_vendor[vend][1] += dropped
            elif lab["verdict"] == "supported" and c["identity_ok"] is not False:
                sup_n += 1
                sup_drop += v != "supported"
    fn, fk = fr_n + p_fr_n, fr_k + p_fr_k
    inn, ik = id_n + p_id_n, id_k + p_id_k
    checker[ck] = {
        "model": ckey,
        "fact_recall_natural": f"{fr_k}/{fr_n}", "fact_recall_planted": f"{p_fr_k}/{p_fr_n}",
        "fact_recall": round(fk / fn, 3) if fn else None, "fact_recall_n": fn, "fact_recall_ci": wilson(fk, fn),
        "identity_recall_natural": f"{id_k}/{id_n}", "identity_recall_planted": f"{p_id_k}/{p_id_n}",
        "identity_recall": round(ik / inn, 3) if inn else None, "identity_recall_n": inn,
        "false_drop_rate": round(sup_drop / sup_n, 4) if sup_n else None,
        "recall_same_vendor": f"{by_vendor['same'][1]}/{by_vendor['same'][0]}",
        "recall_cross_vendor": f"{by_vendor['cross'][1]}/{by_vendor['cross'][0]}",
    }

# ── kappa A vs B ────────────────────────────────────────────────────────────────────────────────
def kappa(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    if not pairs:
        return None
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


kin = defaultdict(list)
for p in glob.glob("panel/out/labels_*_adj.json"):
    for k, v in (json.load(open(p)).get("kappa_inputs") or {}).items():
        kin[k] += [tuple(map(lambda x: json.dumps(x, sort_keys=True), pr)) for pr in v if isinstance(pr, (list, tuple)) and len(pr) == 2]
kappas = {k: {"kappa": kappa(v), "n": len(v)} for k, v in kin.items()}

# ── §7 gates and decision ───────────────────────────────────────────────────────────────────────
live = pair["D1#1xC1"]
u_floor = min(2.5, 0.8 * live["U"])
eligible = {}
for name, p in pair.items():
    run, ck = name.split("x")
    cr = checker[ck]
    g = {
        "1_cross_vendor": p["cross_vendor"],
        "2_WI": p["wrong_identity_stored"] <= 1 and p["wrong_country_stored"] == 0,
        "3_FK": p["FK"] is not None and p["FK"] <= 0.03,
        "4_LK": p["LK"] is not None and p["LK"] <= 0.02,
        "5_coverage": (p["coverage"] or 0) >= 0.85 and p["bad_drafts"] <= 1 and p["bad_checks"] <= 1,
        "6_checker_floor": (cr["fact_recall_n"] >= 10 and cr["identity_recall_n"] >= 10
                            and cr["fact_recall"] >= 0.5 and cr["identity_recall"] >= 0.5),
        "7_cost": p["projected_full"] <= 150,
        "8_usefulness": (p["U"] or 0) >= u_floor,
    }
    p["gates"] = g
    p["eligible"] = all(g.values())
    if p["eligible"]:
        eligible[name] = p

decision = {"u_floor": round(u_floor, 3), "eligible": sorted(eligible)}
if eligible:
    best = min(eligible.values(), key=lambda p: p["FK"])
    band = [n for n, p in eligible.items()
            if p["FK"] - best["FK"] <= 0.02 or p["contradicted_kept"] - best["contradicted_kept"] <= 2]
    band.sort(key=lambda n: (-eligible[n]["U"], eligible[n]["WI"], eligible[n]["projected_full"]))
    winner = band[0]
    # U tie-break needs a 0.5 difference; otherwise next tie-breakers
    top_u = eligible[band[0]]["U"]
    near = [n for n in band if top_u - eligible[n]["U"] < 0.5]
    near.sort(key=lambda n: (eligible[n]["WI"], eligible[n]["projected_full"]))
    winner = near[0]
    decision.update({"lowest_FK": min(eligible, key=lambda n: eligible[n]["FK"]), "tie_band": band, "winner": winner,
                     "incumbent_in_band": "D1#1xC1" in band,
                     "result": "keep live route" if "D1#1xC1" in band else f"switch to {winner}"})
else:
    decision["result"] = "no pair passes: build multi-tour groups only with the best pair, propose grounded draft/check"

out = {"pairs": pair, "drafters": drafter, "stability": stability, "checkers": checker, "kappa": kappas,
       "decision": decision, "identifiable_groups": len(identifiable), "labelled_groups": len(REF),
       "facts_labelled": len(F), "variants_labelled": len(V), "spent_usd": R["spent_usd"]}
json.dump(out, open("post/metrics.json", "w"), indent=1, default=str)

print(f"groups {len(REF)} identifiable {len(identifiable)} facts {len(F)} variants {len(V)} spent ${R['spent_usd']}")
print("\nPAIR            FK      FK_ci           UK     LK     WI    wc cov   U     $/full  gates")
for n, p in pair.items():
    fails = ",".join(k.split("_")[0] for k, v in p["gates"].items() if not v) or "ALL PASS"
    print(f"{n:<14} {p['FK']!s:<7} {p['FK_ci']!s:<15} {p['UK']!s:<6} {p['LK']!s:<6} {p['WI']!s:<5} {p['wrong_country_stored']:<2} "
          f"{p['coverage']!s:<5} {p['U']!s:<5} {p['projected_full']:<7} {fails}")
print("\nDRAFTER")
for n, d in drafter.items():
    print(n, d)
print("stability", stability)
print("\nCHECKER")
for n, c in checker.items():
    print(n, c)
print("\nkappa", kappas)
print("\nDECISION", decision)
