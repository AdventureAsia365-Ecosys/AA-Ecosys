"""AA-790 round 9 (S256): aggregate the blind panel and check the bars set BEFORE the run.

  python3 aggregate_r9.py <panel dir> <workflow output json>

Arms: r6 (stored round-6 texts, the link to rounds 1-8), r9c (control: live T8 angles regenerated once, round-6 writer,
grounding off), r9c2 (the same control written again from the same angles: run-to-run noise), r9 (same angles, grounding
r9). The decision compares r9 with r9c, paired by piece; noise = mean |r9c2 - r9c| per lens, floor 0.15.

BARS (fixed before the paid run; all must pass to turn T9_BRIEF_GROUNDING_MODE=r9 on in Dev):
  1. source_fidelity  r9 - r9c > max(noise, 0.15)            (the lever's target: the brief's unsupported asks)
  2. reader_value     r9 - r9c >= -max(noise, 0.15)          (no loss)
  3. brand_voice      r9 - r9c >= -max(noise, 0.15)          (no loss)
  4. ai_tells         r9 >= 5.5 and r9 - r9c >= -max(noise, 0.15)
  5. at least half of the pieces had their brief changed by the grounding (else the A/B measured nothing)
Informational, not a bar: brand_voice >= 7 per tenant (AA-790 Done-when) at n = 2-3 pieces a tenant."""
import json
import statistics as st
import sys
from collections import defaultdict

LENSES = ("ai_tells", "brand_voice", "source_fidelity", "reader_value")
FLOOR = 0.15

d = sys.argv[1]
kb = json.load(open(f"{d}/blind-key.json"))
arms, key, pieces, briefs = kb["arms"], kb["key"], kb["pieces"], kb.get("briefs") or {}
out = json.load(open(sys.argv[2]))
rows, empty = [], 0
for j in out:
    if not j.get("scores"):
        empty += 1
    for s in (j.get("scores") or []):
        k = key.get(s["blind_id"])
        if k:
            rows.append({**k, "lens": j["lens"], "score": s["score"], "reason": s["reason"], "blind_id": s["blind_id"]})
json.dump(rows, open(f"{d}/panel-scores.json", "w"), ensure_ascii=False, indent=1)
expect = len(key) * len(LENSES)
print(f"scores {len(rows)} / {expect}" + ("" if len(rows) == expect else "  <-- INCOMPLETE: re-run the missing batches")
      + (f" ({empty} empty batches)" if empty else ""))

per = {(r["arm"], r["lens"], r["id"]): r["score"] for r in rows}
g = defaultdict(list)
for r in rows:
    for dim in ("all", r["tenant"], r["channel"]):
        g[(r["arm"], r["lens"], dim)].append(r["score"])
dims = ["all"] + sorted({r["tenant"] for r in rows}) + sorted({r["channel"] for r in rows})


def m(xs):
    return round(st.mean(xs), 2) if xs else None


for lens in LENSES:
    print(f"\n{lens}")
    print("arm    " + " | ".join(x[:12] for x in dims))
    for arm in arms:
        print(f"{arm:6} " + " | ".join(f"{m(g[(arm, lens, x)])}" for x in dims))


def paired(a, b, lens):
    """mean of (a - b) over the pieces both arms have for this lens, and W/T/L."""
    diffs = [per[(a, lens, i)] - per[(b, lens, i)] for i in pieces if (a, lens, i) in per and (b, lens, i) in per]
    w = sum(x > 0 for x in diffs)
    t = sum(x == 0 for x in diffs)
    return (round(st.mean(diffs), 3) if diffs else 0.0), f"{w}/{t}/{len(diffs) - w - t}"


noise = {}
print("\npaired deltas (mean, W/T/L):   r9 - r9c | r9c2 - r9c (noise) | r9 - r6")
for lens in LENSES:
    dv, wtl = paired("r9", "r9c", lens)
    nz = round(abs(paired("r9c2", "r9c", lens)[0]), 3)  # |mean(r9c2 - r9c)|, the S254 r6b-vs-r6 definition
    noise[lens] = max(nz, FLOOR)
    d6, w6 = paired("r9", "r6", lens)
    print(f"  {lens:16} {dv:+.3f} {wtl:>7} | {nz:.3f} | {d6:+.3f} {w6:>7}")

bars = []


def bar(ok, label):
    bars.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")


print("\nBARS (set before the run)")
sf, _ = paired("r9", "r9c", "source_fidelity")
bar(sf > noise["source_fidelity"], f"source_fidelity r9 - r9c = {sf:+.3f} > {noise['source_fidelity']:.3f}")
for lens in ("reader_value", "brand_voice"):
    dv, _ = paired("r9", "r9c", lens)
    bar(dv >= -noise[lens], f"{lens} r9 - r9c = {dv:+.3f} >= -{noise[lens]:.3f}")
at = m(g[("r9", "ai_tells", "all")]) or 0.0
dv, _ = paired("r9", "r9c", "ai_tells")
bar(at >= 5.5 and dv >= -noise["ai_tells"], f"ai_tells r9 = {at} >= 5.5 and r9 - r9c = {dv:+.3f} >= -{noise['ai_tells']:.3f}")
changed = sum(1 for p in pieces if (briefs.get(p) or {}).get("r9") != (briefs.get(p) or {}).get("r9c"))
bar(changed * 2 >= len(pieces), f"briefs changed by the grounding: {changed} / {len(pieces)} pieces")

print("\nInformational: brand_voice per tenant, r9 (Done-when >= 7 each)")
for t in sorted({r["tenant"] for r in rows}):
    print(f"  {t:28} r9 {m(g[('r9', 'brand_voice', t)])}  r9c {m(g[('r9c', 'brand_voice', t)])}  "
          f"r6 {m(g[('r6', 'brand_voice', t)])}")
print(f"\nround 9: {'PASS -> set T9_BRIEF_GROUNDING_MODE=r9 on worker + api (Dev)' if all(bars) else 'FAIL -> keep the flag off'}")
