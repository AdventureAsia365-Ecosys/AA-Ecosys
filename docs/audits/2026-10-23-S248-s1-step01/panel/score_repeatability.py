#!/usr/bin/env python3
"""S248 S1-first step 0/1 — how much the panel agrees with itself (two passes, same rubric, same 12 pages). $0.

  python3 score_repeatability.py pass-a.json pass-b.json [--labels ../../../eval/aa729/fixture-1.1.0.json]

Reports, per page and overall:
- verdict agreement (4 levels) and the pass/fail split (publish_verbatim + light_edit = pass), with Cohen's kappa;
- serious-error count per page in each pass, the mean absolute difference and the A/A ratio (sum b / sum a) — the
  noise band a W/A+ ratio in step 3 must clear;
- error-rate per checkable claim per page and its pass-to-pass difference;
- with --labels: agreement of each pass with the golden label (pass/fail).
"""
import argparse
import json
from collections import Counter


def load(path):
    return {p["sample_id"]: p for p in json.load(open(path))["pages"]}


def binary(v):
    return "pass" if v in ("publish_verbatim", "light_edit") else "fail"


def kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def serious(p):
    return sum(1 for e in p.get("errors") or [] if e.get("severity") == "serious")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--labels")
    args = ap.parse_args()
    a, b = load(args.a), load(args.b)
    ids = sorted(set(a) & set(b))
    labels = {}
    if args.labels:
        labels = {s["sample_id"]: s["label"]["verdict"] for s in json.load(open(args.labels))["samples"]}
    rows = []
    for sid in ids:
        pa, pb = a[sid], b[sid]
        ra = serious(pa) / max(1, pa.get("checkable_claims") or 1)
        rb = serious(pb) / max(1, pb.get("checkable_claims") or 1)
        rows.append({"sample_id": sid, "verdict_a": pa["verdict"], "verdict_b": pb["verdict"],
                     "serious_a": serious(pa), "serious_b": serious(pb), "rate_a": round(ra, 3),
                     "rate_b": round(rb, 3), "label": labels.get(sid)})
    va = [r["verdict_a"] for r in rows]
    vb = [r["verdict_b"] for r in rows]
    sa = sum(r["serious_a"] for r in rows)
    sb = sum(r["serious_b"] for r in rows)
    out = {
        "pages": len(rows),
        "verdict_agreement_4level": round(sum(x == y for x, y in zip(va, vb)) / len(rows), 3) if rows else None,
        "kappa_4level": kappa(va, vb),
        "pass_fail_agreement": round(sum(binary(x) == binary(y) for x, y in zip(va, vb)) / len(rows), 3)
        if rows else None,
        "kappa_pass_fail": kappa([binary(x) for x in va], [binary(y) for y in vb]),
        "serious_errors_total": {"a": sa, "b": sb, "ratio_b_over_a": round(sb / sa, 3) if sa else None},
        "serious_errors_mean_abs_diff": round(sum(abs(r["serious_a"] - r["serious_b"]) for r in rows) / len(rows), 3)
        if rows else None,
        "rate_mean_abs_diff": round(sum(abs(r["rate_a"] - r["rate_b"]) for r in rows) / len(rows), 4) if rows else None,
        "label_agreement": {k: round(sum(binary(r[f"verdict_{k}"]) == r["label"] for r in rows if r["label"])
                                     / max(1, sum(1 for r in rows if r["label"])), 3) for k in ("a", "b")}
        if labels else None,
        "rows": rows,
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
