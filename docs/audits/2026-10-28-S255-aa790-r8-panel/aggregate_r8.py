"""AA-790 round 8 (S255): aggregate the blind panel and check the bars set BEFORE the run.

  python3 aggregate_r8.py <panel dir> <workflow output json>

Noise reference: S254 measured |r6b - r6| (two runs of the round-6 prompt, same panel run) at ai_tells 0.07,
brand_voice 0.08, source_fidelity 0.17, reader_value 0.07; the bars use max(noise, 0.15). The r6b texts are gone, so
panel A uses the stored r6 as the control; panel B adds the fresh-angle control r8c (mode off)."""
import json
import statistics as st
import sys
from collections import defaultdict

NOISE = {"ai_tells": 0.07, "brand_voice": 0.08, "source_fidelity": 0.17, "reader_value": 0.07}
LENSES = ("ai_tells", "brand_voice", "source_fidelity", "reader_value")
TENANTS = ["Atlas & Hearth", "Terra Family Expeditions", "Trail Pulse", "WildKind Travel"]
DIMS = ["all"] + TENANTS + ["blog", "linkedin"]

d = sys.argv[1]
kb = json.load(open(f"{d}/blind-key.json"))
arms, key = kb["arms"], kb["key"]
out = json.load(open(sys.argv[2]))
rows, missing_batches = [], 0
for j in out:
    if not j.get("scores"):
        missing_batches += 1
    for s in (j.get("scores") or []):
        k = key.get(s["blind_id"])
        if k:
            rows.append({**k, "lens": j["lens"], "score": s["score"], "reason": s["reason"], "blind_id": s["blind_id"]})
json.dump(rows, open(f"{d}/panel-scores.json", "w"), ensure_ascii=False, indent=1)
expect = len(key) * len(LENSES)
print(f"scores {len(rows)} / {expect}" + ("" if len(rows) == expect else "  <-- INCOMPLETE: re-run the missing batches")
      + (f" ({missing_batches} empty batches)" if missing_batches else ""))


def m(xs):
    return round(st.mean(xs), 2) if xs else None


g = defaultdict(list)
per = {}
for r in rows:
    for dim in ("all", r["tenant"], r["channel"]):
        g[(r["arm"], r["lens"], dim)].append(r["score"])
    per[(r["arm"], r["lens"], r["id"])] = r["score"]
for lens in LENSES:
    print(f"\n{lens}")
    print("arm    " + " | ".join(x[:12] for x in DIMS))
    for arm in arms:
        print(f"{arm:6} " + " | ".join(f"{m(g[(arm, lens, x)])}" for x in DIMS))


def wtl(a, b, lens):
    ids = {i for (x, ln, i) in per if x == a and ln == lens}
    w = t = l_ = 0
    for i in ids:
        if (b, lens, i) not in per:
            continue
        diff = per[(a, lens, i)] - per[(b, lens, i)]
        w, t, l_ = w + (diff > 0), t + (diff == 0), l_ + (diff < 0)
    return f"{w}/{t}/{l_}"


pairs = [("r8", "r6"), ("r8", "r3")] + ([("r8", "r8c"), ("r8c", "r6")] if "r8c" in arms else [])
print("\nW/T/L per lens: " + " | ".join(f"{a} vs {b}" for a, b in pairs))
for lens in LENSES:
    print(f"  {lens:18} " + " | ".join(f"{wtl(a, b, lens):>9}" for a, b in pairs))

bars = []


def bar(ok, label):
    bars.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")


def mean(arm, lens, dim="all"):
    return m(g[(arm, lens, dim)]) or 0.0


def floor(lens):
    return max(NOISE[lens], 0.15)


print("\nBARS (set before the run)")
bar(mean("r8", "ai_tells") >= 5.5, f"ai_tells r8 >= 5.5 ({mean('r8', 'ai_tells')})")
bar(mean("r8", "brand_voice") >= 7.0, f"brand_voice r8 >= 7 overall ({mean('r8', 'brand_voice')})")
per_tenant = {t: mean("r8", "brand_voice", t) for t in TENANTS}
bar(sum(v >= 7.0 for v in per_tenant.values()) >= 3, f"brand_voice r8 >= 7 for 3 of 4 tenants {per_tenant}")
controls = ["r6"] + (["r8c"] if "r8c" in arms else [])
for c in controls:
    diff = round(mean("r8", "brand_voice") - mean(c, "brand_voice"), 2)
    bar(diff > floor("brand_voice"), f"brand_voice r8 - {c} = {diff} > {floor('brand_voice')}")
    for lens in ("reader_value", "source_fidelity"):
        diff = round(mean("r8", lens) - mean(c, lens), 2)
        bar(diff >= -floor(lens), f"{lens} r8 - {c} = {diff} >= -{floor(lens)}")
if "r8c" in arms:
    print(f"  info  fresh angles alone: brand_voice r8c - r6 = {round(mean('r8c', 'brand_voice') - mean('r6', 'brand_voice'), 2)}, "
          f"reader_value r8c - r6 = {round(mean('r8c', 'reader_value') - mean('r6', 'reader_value'), 2)}")
verdict = all(bars) and len(rows) == expect
step = "SHIP round 8 (set T8_ANGLE_BRIEF_MODE=r8)" if "r8c" in arms else "spend the r8c control (step 2), then panel B"
print(f"\nround 8: {'PASS -> ' + step if verdict else 'FAIL -> keep the flag off; iterate or stop'}")
