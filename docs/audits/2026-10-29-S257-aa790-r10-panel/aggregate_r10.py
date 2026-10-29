"""AA-790 round 10 (S257): aggregate the blind panel and check the bars set BEFORE the run.

  python3 aggregate_r10.py <panel dir> <workflow output json>

Arms: r6 (stored round-6 texts), r9 (stored round-9 texts: same T8 angles, grounding on, no checklist), r10c (control:
same angles, flags as live = grounding off + checklist off), r10c2 (the control written again: run-to-run noise), r10
(grounding r9 + reader checklist r10). The decision compares r10 with r10c, paired by piece;
noise = |mean(r10c2 - r10c)| per lens, floor 0.15 (the S254 / S256 definition).

BARS (fixed before the paid run, carried over from round 9 with reader_value as the lever's target; all of 1-6 must
pass to turn T9_BRIEF_GROUNDING_MODE=r9 + T9_READER_CHECKLIST_MODE=r10 on in Dev):
  1. source_fidelity  r10 - r10c >= -max(noise, 0.15)        (round 9's gain must not be given back)
  2. reader_value     r10 - r10c >= -max(noise, 0.15)        (no loss; the round-9 failure)
                      TARGET tier: r10 - r10c >= +max(noise, 0.15) (reported; see bar 6)
  3. brand_voice      r10 - r10c >= -max(noise, 0.15)
  4. ai_tells         r10 >= 5.5 and r10 - r10c >= -max(noise, 0.15)
  5. the A/B measured something: the checklist block is in the r10 prompt (and not in r10c) on at least half of the
     pieces, and the grounding changed the brief on at least half
  6. at least one lens gains beyond noise: reader_value r10 - r10c >= +max(noise, 0.15) or source_fidelity
     r10 - r10c > max(noise, 0.15) (do not ship two switches that move nothing)
Informational, not bars: r10 - r9 per lens (the checklist alone, both arms grounded, same angles; r9 was written in
another run), brand_voice per tenant (AA-790 Done-when >= 7 each) at n = 2-3 pieces a tenant."""
import json
import statistics as st
import sys
from collections import defaultdict

LENSES = ("ai_tells", "brand_voice", "source_fidelity", "reader_value")
FLOOR = 0.15

d = sys.argv[1]
kb = json.load(open(f"{d}/blind-key.json"))
arms, key, pieces = kb["arms"], kb["key"], kb["pieces"]
briefs, checklists = kb.get("briefs") or {}, kb.get("checklists") or {}
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
print("\npaired deltas (mean, W/T/L):   r10 - r10c | r10c2 - r10c (noise) | r10 - r9 (checklist alone) | r10 - r6")
for lens in LENSES:
    dv, wtl = paired("r10", "r10c", lens)
    nz = round(abs(paired("r10c2", "r10c", lens)[0]), 3)
    noise[lens] = max(nz, FLOOR)
    d9, w9 = paired("r10", "r9", lens)
    d6, w6 = paired("r10", "r6", lens)
    print(f"  {lens:16} {dv:+.3f} {wtl:>7} | {nz:.3f} | {d9:+.3f} {w9:>7} | {d6:+.3f} {w6:>7}")

bars = []


def bar(ok, label):
    bars.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")


print("\nBARS (set before the run)")
sf, _ = paired("r10", "r10c", "source_fidelity")
rv, _ = paired("r10", "r10c", "reader_value")
bar(sf >= -noise["source_fidelity"], f"1 source_fidelity r10 - r10c = {sf:+.3f} >= -{noise['source_fidelity']:.3f}")
tier = "TARGET" if rv >= noise["reader_value"] else "no-loss" if rv >= -noise["reader_value"] else "loss"
bar(rv >= -noise["reader_value"], f"2 reader_value r10 - r10c = {rv:+.3f} >= -{noise['reader_value']:.3f}  "
                                  f"[tier: {tier}; target >= +{noise['reader_value']:.3f}]")
bv, _ = paired("r10", "r10c", "brand_voice")
bar(bv >= -noise["brand_voice"], f"3 brand_voice r10 - r10c = {bv:+.3f} >= -{noise['brand_voice']:.3f}")
at = m(g[("r10", "ai_tells", "all")]) or 0.0
dv, _ = paired("r10", "r10c", "ai_tells")
bar(at >= 5.5 and dv >= -noise["ai_tells"],
    f"4 ai_tells r10 = {at} >= 5.5 and r10 - r10c = {dv:+.3f} >= -{noise['ai_tells']:.3f}")
blocks = sum(1 for p in pieces if (checklists.get(p) or {}).get("r10") and not (checklists.get(p) or {}).get("r10c"))
changed = sum(1 for p in pieces if (briefs.get(p) or {}).get("r10") != (briefs.get(p) or {}).get("r10c"))
bar(blocks * 2 >= len(pieces) and changed * 2 >= len(pieces),
    f"5 checklist block in r10 only: {blocks} / {len(pieces)}; brief changed by the grounding: {changed} / {len(pieces)}")
bar(rv >= noise["reader_value"] or sf > noise["source_fidelity"],
    f"6 a gain beyond noise: reader_value {rv:+.3f} >= +{noise['reader_value']:.3f} or source_fidelity {sf:+.3f} > "
    f"{noise['source_fidelity']:.3f}")

print("\nInformational: brand_voice per tenant (Done-when >= 7 each)")
for t in sorted({r["tenant"] for r in rows}):
    print(f"  {t:28} r10 {m(g[('r10', 'brand_voice', t)])}  r10c {m(g[('r10c', 'brand_voice', t)])}  "
          f"r9 {m(g[('r9', 'brand_voice', t)])}  r6 {m(g[('r6', 'brand_voice', t)])}")
verdict = ("PASS -> set T9_BRIEF_GROUNDING_MODE=r9 and T9_READER_CHECKLIST_MODE=r10 on worker + api (Dev)"
           if all(bars) else "FAIL -> keep both flags off")
print(f"\nround 10: {verdict}")
