"""AA-773 offline evidence ($0): rebuild the S234 r4 seeds with Status lines and replay
promises_an_option (approx. route tags via names_moment) + F17 optional_as_fixed on the r4 texts."""
import json
import re
import sys
from collections import Counter

from services.acp_shared import atom_seed as A
from services.acp_shared import offered as O
from services.acp_content_writing import quality_gates as Q
from services.acp_content_writing import trip_facts as tf

pieces = json.load(open(sys.argv[1]))
DAY_MEMBER = re.compile(r"^Day (\d+) of the trip: (.*?)(?: — Source itinerary: (.*))?$")


def parts_from_seed(seed):
    parts, blocks = [], [b for b in re.split(r"\n\s*\n", seed) if b.strip()]
    for bi, b in enumerate(blocks):
        lines = b.split("\n")
        label = lines[0]
        members = [DAY_MEMBER.match(ln) for ln in lines if DAY_MEMBER.match(ln)]
        card = {"card_id": f"b{bi}", "display_name": f"b{bi}", "facts": []}
        if members:
            for m in members:
                parts.append({"block": bi, "text": m.group(2), "evidence": m.group(3) or "", "day": int(m.group(1)),
                              "card": card})
        else:
            day = next((int(re.match(r"Day (\d+)", ln).group(1)) for ln in lines if re.match(r"Day \d+ of the trip$", ln)), None)
            ev = next((ln[len("Source itinerary: "):] for ln in lines if ln.startswith("Source itinerary: ")), "")
            parts.append({"block": bi, "text": label, "evidence": ev, "day": day, "card": card})
    return blocks, parts


def seed_with_status(seed):
    blocks, parts = parts_from_seed(seed)
    parts = A.route_moment_statuses(parts)
    out = []
    for bi, b in enumerate(blocks):
        mine = [p for p in parts if p["block"] == bi]
        lines, k = [], 0
        for ln in b.split("\n"):
            lines.append(ln)
            if ln.startswith("Source itinerary: ") or DAY_MEMBER.match(ln):
                if k < len(mine) and mine[k].get("status_line"):
                    lines.append(mine[k]["status_line"])
                k += 1
        out.append("\n".join(lines))
    return "\n\n".join(out), parts


def single_with_status(seed):
    lines = seed.split("\n")
    out = []
    for ln in lines:
        out.append(ln)
        if ln.startswith("Source itinerary: "):
            st = O.single_status_line(ln[len("Source itinerary: "):], lines[0])
            if st:
                out.append(st)
    return "\n".join(out)


def promised_route(text, blocks_old, blocks_new):
    """Approximate [R:] tags: a sentence is tagged with every block whose moment it names."""
    mom_old = [tf.parse_moments(b) for b in blocks_old]
    flagged_old, flagged_new = [], []
    body = text.partition("## FAQ")[0]
    for sent in Q._SENT_SPLIT_RE.split(body):
        plain = sent.lower()
        if not plain.strip() or any(h in plain for h in Q._HEDGE_PHRASES):
            continue
        hit_blocks = [i for i, ms in enumerate(mom_old) if ms and any(tf.names_moment(sent, m) for m in ms)]
        if any(O.has_offered_phrase(blocks_old[i]) for i in hit_blocks):
            flagged_old.append(sent.strip())
        new_ids = [i for i in hit_blocks if Q._is_offered(blocks_new[i])
                   and Q._names_offered(plain, Q._status_activities(blocks_new[i]))]
        if new_ids:
            flagged_new.append(sent.strip())
    return flagged_old, flagged_new


report = {"route": None, "single": [], "blogs": []}
blog_seed = next(p["seed"] for p in pieces if p["channel"] == "blog")
new_seed, parts = seed_with_status(blog_seed)
report["route"] = {
    "moments": len(parts),
    "status_lines": sum(1 for p in parts if p.get("status_line")),
    "offered": [(p["day"], p["text"]) for p in parts if p["status"] == O.OFFERED],
    "included_line": [(p["day"], p["text"]) for p in parts if p.get("status_line") == O.INCLUDED_LINE],
    "unknown": [(p["day"], p["text"]) for p in parts if p["status"] is None],
}
open(sys.argv[2] + ".route_seed.txt", "w").write(new_seed)
for s in dict.fromkeys(p["seed"] for p in pieces if p["channel"] != "blog"):
    ns = single_with_status(s)
    report["single"].append({"label": s.split("\n")[0], "status_lines": ns.count("\nStatus:")})

blocks_old = [b for b in re.split(r"\n\s*\n", blog_seed) if b.strip()]
blocks_new = [b for b in re.split(r"\n\s*\n", new_seed) if b.strip()]
tot = Counter()
for p in pieces:
    if p["channel"] != "blog":
        continue
    text = p["text"]
    f17_old = tf.optional_as_fixed(text, tf.parse_moments(blog_seed))
    f17_new = tf.optional_as_fixed(text, tf.parse_moments(new_seed))
    po_old, po_new = promised_route(text, blocks_old, blocks_new)
    row = {"piece": p["piece_id"][:8], "tenant": p["tenant"], "status": p["status"],
           "f17_old": len(f17_old), "f17_new": len(f17_new), "f17_examples": f17_old[:3],
           "promise_old": len(po_old), "promise_new": len(po_new), "promise_new_examples": po_new[:3]}
    report["blogs"].append(row)
    tot["blogs"] += 1
    tot["blogs_f17_old"] += bool(f17_old)
    tot["blogs_f17_new"] += bool(f17_new)
    tot["f17_old"] += len(f17_old)
    tot["f17_new"] += len(f17_new)
    tot["blogs_promise_old"] += bool(po_old)
    tot["blogs_promise_new"] += bool(po_new)
    tot["promise_old"] += len(po_old)
    tot["promise_new"] += len(po_new)
report["totals"] = dict(tot)
json.dump(report, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
print(json.dumps(report["route"], ensure_ascii=False, indent=1))
print(json.dumps(report["single"], ensure_ascii=False))
print(json.dumps(report["totals"]))
for r in report["blogs"]:
    print(r["piece"], r["status"], "F17", r["f17_old"], "->", r["f17_new"], "| promise", r["promise_old"], "->", r["promise_new"])
