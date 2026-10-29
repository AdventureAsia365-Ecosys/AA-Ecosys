"""Median of Lighthouse runs per page: performance, LCP, FCP, TBT, CLS, LCP element, LCP resource bytes."""
import glob
import json
import os
import statistics
import sys
from collections import defaultdict

out = sys.argv[1]
rows = defaultdict(list)
for f in sorted(glob.glob(os.path.join(out, "*.json"))):
    name = os.path.basename(f).rsplit("-", 1)[0]
    d = json.load(open(f))
    a = d["audits"]
    el = ""
    try:
        el = a["largest-contentful-paint-element"]["details"]["items"][0]["items"][0]["node"]["selector"]
    except Exception:
        pass
    lcp_req = None
    for r in a.get("network-requests", {}).get("details", {}).get("items", []):
        if r.get("resourceType") == "Image" and r.get("priority") in ("High", "VeryHigh"):
            if "logo" in r["url"]:
                continue
            lcp_req = (r["url"].split("/")[-1][:60], r.get("transferSize"))
            break
    rows[name].append({
        "perf": round((d["categories"]["performance"]["score"] or 0) * 100),
        "lcp": a["largest-contentful-paint"]["numericValue"],
        "fcp": a["first-contentful-paint"]["numericValue"],
        "tbt": a["total-blocking-time"]["numericValue"],
        "cls": a["cumulative-layout-shift"]["numericValue"],
        "el": el, "img": lcp_req,
    })
summary = {}
print(f"{'page':14} {'runs':>4} {'perf':>5} {'LCP s':>6} {'FCP s':>6} {'TBT ms':>7} {'CLS':>6}  LCP runs (s)  element / first high-priority image")
for name, rs in rows.items():
    med = {k: statistics.median([r[k] for r in rs]) for k in ("perf", "lcp", "fcp", "tbt", "cls")}
    summary[name] = {**med, "lcp_runs": [round(r["lcp"] / 1000, 2) for r in rs], "element": rs[0]["el"], "image": rs[0]["img"]}
    print(f"{name:14} {len(rs):>4} {med['perf']:>5.0f} {med['lcp']/1000:>6.2f} {med['fcp']/1000:>6.2f} {med['tbt']:>7.0f} {med['cls']:>6.3f}  "
          f"{summary[name]['lcp_runs']}  {rs[0]['el']} {rs[0]['img']}")
json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)
