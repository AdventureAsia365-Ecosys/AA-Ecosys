"""AA-790 round 10 (S257): build the blind panel and its workflow script. $0, local. Run after the three paid runs, with
their JSON pulled from S3 into ./out/ by chain_r10.sh.

  python3 build_blind_r10.py panel-r10 r10c=out/aa790-r10c.json r10c2=out/aa790-r10c2.json r10=out/aa790-r10.json

Arms scored in ONE run (lesson S252: judges drift between runs):
  r6     stored round-6 texts (the link to rounds 1-9)                                    $0, stored
  r9     stored round-9 texts (S256: same T8 angles, grounding on, no checklist)          $0, stored
  r10c   control: same angles, flags as live (grounding off, checklist off)               paid
  r10c2  the control written again (run-to-run noise)                                     paid
  r10    same angles, grounding r9 + reader checklist r10                                 paid
Same item shape, S251 rubric and 4 lenses as the S252 / S254 / S255 / S256 panels. Only pieces present with text in
EVERY arm are kept (pairs by piece_id). Writes <dir>/panel-batch-N.json, <dir>/blind-key.json and <dir>/panel_wf.js."""
import hashlib
import json
import os
import sys

ROOT = "/home/nghiep/projects/AA-Ecosys/.tmp-session"
S251 = f"{ROOT}/s251/aa790writer/out"
S252 = f"{ROOT}/s252/aa790"
HERE = os.path.dirname(os.path.abspath(__file__))
STORED_R9 = os.path.join(HERE, "stored", "aa790-r9.json")   # copy of S256/aa790/out/aa790-r9.json

out_dir = os.path.join(HERE, sys.argv[1])
new_arms = dict(a.split("=", 1) for a in sys.argv[2:])
assert set(new_arms) == {"r10c", "r10c2", "r10"}, f"expected r10c / r10c2 / r10, got {sorted(new_arms)}"
os.makedirs(out_dir, exist_ok=True)
r1 = {r["id"]: r for r in json.load(open(f"{S251}/aa790-repanel.json"))}
arms = {"r6": {r["id"]: r for r in json.load(open(f"{S252}/aa790-repanel-r6.json"))},
        "r9": {r["id"]: r for r in json.load(open(STORED_R9)) if r.get("text")}}
briefs, checklists = {}, {}
for a, f in new_arms.items():
    rows = json.load(open(f if os.path.isabs(f) else os.path.join(HERE, f)))
    arms[a] = {r["id"]: r for r in rows if r.get("text")}
    for r in rows:
        if r.get("text"):
            briefs.setdefault(r["id"], {})[a] = r.get("brief_seen")
            checklists.setdefault(r["id"], {})[a] = r.get("checklist_seen") or ""
    bad = [r["id"] for r in rows if not r.get("text")]
    if bad:
        print(f"arm {a}: {len(bad)} rows without text, dropped from every arm: {bad}")
    off_seed = [r["id"] for r in rows if r.get("text") and r.get("seed_match") is False]
    if off_seed:
        print(f"arm {a}: seed_match False on {off_seed} (T8 read a newer seed than the writer); read with care")
for pid, r in arms["r9"].items():
    briefs.setdefault(pid, {})["r9"] = r.get("brief_seen")
order = ["r6", "r9", "r10c", "r10c2", "r10"]
ids = [i for i in r1 if all(i in arms[a] for a in order)]
seeds = json.load(open(f"{S251}/seeds.json"))
old = {b["blind_id"]: b for i in range(4) for b in json.load(open(f"{S251}/panel-batch-{i}.json"))}
key, items = {}, []
for pid in ids:
    a = r1[pid]
    facts = next((o["source_facts"] for o in old.values() if o.get("text") in (a["before_text"], a["text"])),
                 seeds.get(a["piece_id"]))
    for arm in order:
        bid = hashlib.sha256(f"s257r10:{sys.argv[1]}:{pid}:{arm}".encode()).hexdigest()[:8]
        key[bid] = {"id": pid, "arm": arm, "tenant": a["tenant"], "channel": a["channel"], "status": a["status"]}
        items.append({"blind_id": bid, "tenant": a["tenant"], "channel": a["channel"], "brand_pack": a["brand_pack"],
                      "cta": a["cta"], "text": arms[arm][pid]["text"], "source_facts": facts})
items.sort(key=lambda x: x["blind_id"])
n_batches = (len(items) + 7) // 8
for i in range(n_batches):
    json.dump(items[i * 8:(i + 1) * 8], open(f"{out_dir}/panel-batch-{i}.json", "w"), ensure_ascii=False, indent=1)
json.dump({"arms": order, "key": key, "pieces": ids, "briefs": briefs, "checklists": checklists},
          open(f"{out_dir}/blind-key.json", "w"), ensure_ascii=False, indent=1)
wf = open(os.path.join(HERE, "panel_wf_r10.template.js")).read()
wf = wf.replace("__DIR__", out_dir).replace("__BATCHES__", str(n_batches)).replace(
    "__ARMS__", " / ".join(order)).replace("__ITEMS__", str(len(items)))
open(f"{out_dir}/panel_wf.js", "w").write(wf)
changed = sum(1 for p in ids if briefs.get(p, {}).get("r10") != briefs.get(p, {}).get("r10c"))
with_block = sum(1 for p in ids if checklists.get(p, {}).get("r10") and not checklists.get(p, {}).get("r10c"))
print("pieces", len(ids), "items", len(items), "batches", n_batches, "arms", order, "-> ", out_dir)
print(f"briefs changed by the grounding (r10 vs r10c): {changed} / {len(ids)} pieces")
print(f"checklist block in r10 and not in r10c: {with_block} / {len(ids)} pieces")
