#!/usr/bin/env python3
"""S248 S1-first — packet for the rubric v1.1 held-out check ($0, no LLM).

build_packet.py picks its own 12 pages and has no id-list option, so this script builds the packet the same way
(same PAGE_FIELDS, FULL raw source, written page, no labels / pipeline verdicts / code-check findings) for the 20
HELD-OUT ids in split-v1.1.json, in one seeded shuffled order. The orchestrator gives the same packet to two fresh
blind agents (pass-h1.json / pass-h2.json) with rubric-v1.1.md, then runs apply_v11.py on both.

  python3 build_packet_holdout.py --fixture ../../../../docs/eval/aa729/fixture-1.1.0.json
"""
import argparse
import json
import random

from build_packet import PAGE_FIELDS

SEED = 11


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--split", default="split-v1.1.json")
    ap.add_argument("--out", default="packet-holdout.json")
    args = ap.parse_args()
    ids = json.load(open(args.split))["holdout"]
    by_id = {s["sample_id"]: s for s in json.load(open(args.fixture))["samples"]}
    order = [by_id[i] for i in ids]
    random.Random(SEED).shuffle(order)
    pages = [{"page_id": f"h{n + 1:02d}", "sample_id": s["sample_id"], "source": s["input"]["tour"],
              "page": {f: s["output"].get(f) for f in PAGE_FIELDS}} for n, s in enumerate(order)]
    json.dump({"pass": "holdout", "rubric": "rubric-v1.1.md", "pages": pages}, open(args.out, "w"), indent=1,
              ensure_ascii=False)
    print("holdout pages:", [p["sample_id"] for p in pages])


if __name__ == "__main__":
    main()
