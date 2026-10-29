"""AA-790 round 9 (S256): build the blind panel (stored r6 + fresh-angle control r9c + its repeat r9c2 + r9) and its
workflow script. $0, local. Run after the three paid runs, with their JSON pulled from S3 into ./out/.

  python3 build_blind_r9.py panel-r9 r9c=out/aa790-r9c.json r9c2=out/aa790-r9c2.json r9=out/aa790-r9.json

Same item shape, S251 rubric and 4 lenses as the S252 / S254 / S255 panels; every arm is scored in the same run
(lesson S252: judges drift between runs). Only pieces present with text in EVERY new arm are kept (pairs by piece_id;
a piece an arm lacks is dropped from all arms). Writes <dir>/panel-batch-N.json, <dir>/blind-key.json and
<dir>/panel_wf.js (the Workflow script)."""
import hashlib
import json
import os
import sys

ROOT = "/home/nghiep/projects/AA-Ecosys/.tmp-session"
S251 = f"{ROOT}/s251/aa790writer/out"
S252 = f"{ROOT}/s252/aa790"
HERE = os.path.dirname(os.path.abspath(__file__))

out_dir = os.path.join(HERE, sys.argv[1])
new_arms = dict(a.split("=", 1) for a in sys.argv[2:])
os.makedirs(out_dir, exist_ok=True)
r1 = {r["id"]: r for r in json.load(open(f"{S251}/aa790-repanel.json"))}
arms = {"r6": {r["id"]: r for r in json.load(open(f"{S252}/aa790-repanel-r6.json"))}}
briefs = {}
for a, f in new_arms.items():
    rows = json.load(open(f if os.path.isabs(f) else os.path.join(HERE, f)))
    arms[a] = {r["id"]: r for r in rows if r.get("text")}
    for r in rows:
        if r.get("text"):
            briefs.setdefault(r["id"], {})[a] = r.get("brief_seen")
    bad = [r["id"] for r in rows if not r.get("text")]
    if bad:
        print(f"arm {a}: {len(bad)} rows without text, dropped from every arm: {bad}")
    off_seed = [r["id"] for r in rows if r.get("text") and r.get("seed_match") is False]
    if off_seed:
        print(f"arm {a}: seed_match False on {off_seed} (T8 read a newer seed than the writer); read with care")
ids = [i for i in r1 if all(i in arms[a] for a in new_arms)]
seeds = json.load(open(f"{S251}/seeds.json"))
old = {b["blind_id"]: b for i in range(4) for b in json.load(open(f"{S251}/panel-batch-{i}.json"))}
order = ["r6"] + list(new_arms)
key, items = {}, []
for pid in ids:
    a = r1[pid]
    facts = next((o["source_facts"] for o in old.values() if o.get("text") in (a["before_text"], a["text"])),
                 seeds.get(a["piece_id"]))
    for arm in order:
        bid = hashlib.sha256(f"s256r9:{sys.argv[1]}:{pid}:{arm}".encode()).hexdigest()[:8]
        key[bid] = {"id": pid, "arm": arm, "tenant": a["tenant"], "channel": a["channel"], "status": a["status"]}
        items.append({"blind_id": bid, "tenant": a["tenant"], "channel": a["channel"], "brand_pack": a["brand_pack"],
                      "cta": a["cta"], "text": arms[arm][pid]["text"], "source_facts": facts})
items.sort(key=lambda x: x["blind_id"])
n_batches = (len(items) + 7) // 8
for i in range(n_batches):
    json.dump(items[i * 8:(i + 1) * 8], open(f"{out_dir}/panel-batch-{i}.json", "w"), ensure_ascii=False, indent=1)
json.dump({"arms": order, "key": key, "pieces": ids, "briefs": briefs}, open(f"{out_dir}/blind-key.json", "w"),
          ensure_ascii=False, indent=1)
wf = open(os.path.join(HERE, "panel_wf_r9.template.js")).read()
wf = wf.replace("__DIR__", out_dir).replace("__BATCHES__", str(n_batches)).replace(
    "__ARMS__", " / ".join(order)).replace("__ITEMS__", str(len(items)))
open(f"{out_dir}/panel_wf.js", "w").write(wf)
changed = sum(1 for p in ids if briefs.get(p, {}).get("r9") != briefs.get(p, {}).get("r9c"))
print("pieces", len(ids), "items", len(items), "batches", n_batches, "arms", order, "-> ", out_dir)
print(f"briefs changed by the r9 grounding: {changed} / {len(ids)} pieces")
