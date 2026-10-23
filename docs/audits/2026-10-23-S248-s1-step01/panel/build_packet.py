#!/usr/bin/env python3
"""S248 S1-first step 0/1 — build the panel repeatability packet ($0, no LLM).

Picks 12 golden S1 pages (seed 248: 4 labelled pass + 8 labelled fail, spread over the fixture strata) and writes
one packet per pass with the FULL source and the page, in a different order per pass, without labels, pipeline
verdicts or code-check findings (the panel must not see them). Two independent passes (fresh agents, same rubric)
then score the same pages; score_repeatability.py measures how much the panel agrees with itself.

  python3 build_packet.py --fixture ../../../eval/aa729/fixture-1.1.0.json
"""
import argparse
import json
import random

PAGE_FIELDS = ("name", "subtitle", "summary", "highlights", "itineraries", "seo_title", "seo_meta")


def pick(samples, seed=248):
    rnd = random.Random(seed)
    s1 = [s for s in samples if s["kind"] == "s1"]
    passes = sorted((s for s in s1 if s["label"]["verdict"] == "pass"), key=lambda s: s["sample_id"])
    fails = sorted((s for s in s1 if s["label"]["verdict"] != "pass"), key=lambda s: s["sample_id"])
    chosen = rnd.sample(passes, 4)
    by_reason = {}
    for s in fails:
        key = s["pick_reason"].split(":")[0]
        by_reason.setdefault(key, []).append(s)
    pool = []
    for key in sorted(by_reason):           # one per stratum first, then fill at random
        pool.append(rnd.choice(by_reason[key]))
    rest = [s for s in fails if s not in pool]
    rnd.shuffle(rest)
    chosen += (pool + rest)[:8]
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    args = ap.parse_args()
    fx = json.load(open(args.fixture))
    chosen = pick(fx["samples"])
    ids = [s["sample_id"] for s in chosen]
    json.dump({"seed": 248, "sample_ids": ids}, open("selection.json", "w"), indent=1)
    for name, seed in (("a", 1), ("b", 2)):
        order = list(chosen)
        random.Random(seed).shuffle(order)
        pages = [{"page_id": f"p{i + 1:02d}", "sample_id": s["sample_id"], "source": s["input"]["tour"],
                  "page": {f: s["output"].get(f) for f in PAGE_FIELDS}} for i, s in enumerate(order)]
        json.dump({"pass": name, "rubric": "rubric.md", "pages": pages}, open(f"packet-{name}.json", "w"),
                  indent=1, ensure_ascii=False)
    print("selected:", ids)


if __name__ == "__main__":
    main()
