#!/usr/bin/env python3
"""S248 S1-first step 0 follow-up — train / held-out split for panel rubric v1.1 ($0, no LLM).

The 50 golden S1 pages are split once, seeded, stratified by label (pass / fail):
- the 12 pages of the v1 repeatability packet (selection.json) are forced into TRAIN, because the v1.1 diagnosis
  read their panel errors and labels;
- the rest of TRAIN is filled at random (seed 2481) to 30 pages with the label mix of the whole set
  (6 pass / 44 fail -> 4 pass / 26 fail in train, 2 pass / 18 fail held out); fail pages are drawn per fixture
  stratum (pick_reason prefix) in proportion to what is left, so strata stay spread;
- the 20 others are HELD OUT: v1.1 is not fitted on them; the orchestrator runs two blind passes on them.

  python3 split_v11.py --fixture ../../../../docs/eval/aa729/fixture-1.1.0.json      # writes split-v1.1.json
"""
import argparse
import json
import random

SEED = 2481
TRAIN_SIZE = 30


def stratum(s):
    return s["pick_reason"].split(":")[0]


def split(samples, forced):
    s1 = sorted((s for s in samples if s["kind"] == "s1"), key=lambda s: s["sample_id"])
    rnd = random.Random(SEED)
    n_pass = sum(1 for s in s1 if s["label"]["verdict"] == "pass")
    want_pass = round(TRAIN_SIZE * n_pass / len(s1))           # 30 * 6 / 50 = 3.6 -> 4
    want_fail = TRAIN_SIZE - want_pass
    train = [s for s in s1 if s["sample_id"] in forced]
    for verdict, want in (("pass", want_pass), ("fail", want_fail)):
        have = [s for s in train if (s["label"]["verdict"] == "pass") == (verdict == "pass")]
        left = [s for s in s1 if s not in train and (s["label"]["verdict"] == "pass") == (verdict == "pass")]
        need = want - len(have)
        if need <= 0:
            continue
        by = {}
        for s in left:
            by.setdefault(stratum(s), []).append(s)
        # proportional allocation per stratum (largest remainder), then a seeded draw inside each stratum
        quota = {k: need * len(v) / len(left) for k, v in by.items()}
        alloc = {k: int(q) for k, q in quota.items()}
        for k in sorted(quota, key=lambda k: (-(quota[k] - alloc[k]), k))[: need - sum(alloc.values())]:
            alloc[k] += 1
        for k in sorted(by):
            train += rnd.sample(by[k], alloc[k])
    train_ids = sorted(s["sample_id"] for s in train)
    hold_ids = sorted(s["sample_id"] for s in s1 if s["sample_id"] not in train_ids)
    return train_ids, hold_ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--selection", default="selection.json")
    ap.add_argument("--out", default="split-v1.1.json")
    args = ap.parse_args()
    fx = json.load(open(args.fixture))
    forced = set(json.load(open(args.selection))["sample_ids"])
    train, hold = split(fx["samples"], forced)
    lab = {s["sample_id"]: s["label"]["verdict"] for s in fx["samples"]}
    out = {"seed": SEED, "forced_into_train": sorted(forced), "train": train, "holdout": hold,
           "train_labels": {k: sum(lab[i] == k for i in train) for k in ("pass", "fail")},
           "holdout_labels": {k: sum(lab[i] == k for i in hold) for k in ("pass", "fail")}}
    json.dump(out, open(args.out, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
