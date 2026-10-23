#!/usr/bin/env python3
"""S248 S1-first — derive rubric v1.1 verdicts from a panel pass ($0, no LLM).

The v1.1 verdict is NOT the panel's holistic call: it is computed here from the error list (rubric-v1.1.md §5).

  # one pass, with labels (agreement) — page text comes from the packet or the fixture
  python3 apply_v11.py pass-h1.json --packet packet-holdout.json --labels <fixture>
  # two blind passes: repeatability of the derived verdict, serious count and rate, plus label agreement
  python3 apply_v11.py pass-h1.json pass-h2.json --packet packet-holdout.json --labels <fixture>
  # threshold sweep (fitting; only ever on TRAIN pages)
  python3 apply_v11.py train-v1.1-self.json --fixture <fixture> --labels <fixture> --sweep

Rule (v1.1, fitted on the 30 train pages only):
  hard   = distinct errors with hard_fail true          S = distinct serious errors (hard ones included)
  n      = sentences of >= 4 words in the page (name .. seo_meta), counted here, not by the panel
  reject        if any scope_drift error, or hard >= 3
  heavy_edit    elif hard >= 1, or (S >= 2 and S / n > TAU)
  publish_verbatim elif no errors at all
  light_edit    otherwise
  pass = publish_verbatim | light_edit
"""
import argparse
import json
import re
from collections import Counter

TAU = 0.017
FIELDS = ("name", "subtitle", "summary", "highlights", "itineraries", "seo_title", "seo_meta")


def sentences(page):
    parts = []
    for f in FIELDS:
        v = page.get(f)
        parts.append(" ".join(v) if isinstance(v, list) else (v or ""))
    text = "\n".join(parts)
    return sum(1 for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.split()) >= 4)


def page_lengths(args):
    if args.packet:
        return {p["sample_id"]: sentences(p["page"]) for p in json.load(open(args.packet))["pages"]}
    if args.fixture:
        return {s["sample_id"]: sentences(s["output"]) for s in json.load(open(args.fixture))["samples"]
                if s["kind"] == "s1"}
    raise SystemExit("need --packet or --fixture for the page length")


def derive(p, n, tau=TAU):
    errs = p.get("errors") or []
    hard = sum(1 for e in errs if e.get("hard_fail"))
    serious = sum(1 for e in errs if e.get("severity") == "serious")
    rate = serious / max(1, n)
    if any(e.get("class") == "scope_drift" for e in errs) or hard >= 3:
        v = "reject"
    elif hard >= 1 or (serious >= 2 and rate > tau):
        v = "heavy_edit"
    elif not errs:
        v = "publish_verbatim"
    else:
        v = "light_edit"
    return {"verdict": v, "hard": hard, "serious": serious, "minor": len(errs) - serious, "n": n,
            "rate": round(rate, 4)}


def binary(v):
    return "pass" if v in ("publish_verbatim", "light_edit") else "fail"


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def agreement(rows, labels):
    got = [r for r in rows if r["sample_id"] in labels]
    tp = sum(1 for r in got if binary(r["verdict"]) == "pass" and labels[r["sample_id"]] == "pass")
    tn = sum(1 for r in got if binary(r["verdict"]) == "fail" and labels[r["sample_id"]] == "fail")
    np_ = sum(1 for r in got if labels[r["sample_id"]] == "pass")
    nf = len(got) - np_
    return {"pages": len(got), "agree": tp + tn, "agreement": round((tp + tn) / max(1, len(got)), 3),
            "pass_recall": f"{tp}/{np_}", "fail_recall": f"{tn}/{nf}",
            "balanced_accuracy": round(((tp / np_ if np_ else 0) + (tn / nf if nf else 0)) / 2, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("passes", nargs="+")
    ap.add_argument("--packet")
    ap.add_argument("--fixture")
    ap.add_argument("--labels")
    ap.add_argument("--tau", type=float, default=TAU)
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()
    lens = page_lengths(args)
    labels = {}
    if args.labels:
        labels = {s["sample_id"]: s["label"]["verdict"] for s in json.load(open(args.labels))["samples"]}
    runs = []
    for path in args.passes:
        pages = {p["sample_id"]: p for p in json.load(open(path))["pages"]}
        rows = [{"sample_id": sid, **derive(p, lens[sid], args.tau), "label": labels.get(sid)}
                for sid, p in sorted(pages.items())]
        runs.append((path, pages, rows))
    out = {"tau": args.tau, "passes": {}}
    for path, pages, rows in runs:
        out["passes"][path] = {"rows": rows, "label_agreement": agreement(rows, labels) if labels else None}
        if args.sweep:
            sw = []
            for tau in [x / 1000 for x in range(5, 61)]:
                rr = [{"sample_id": sid, **derive(p, lens[sid], tau)} for sid, p in pages.items()]
                a = agreement(rr, labels)
                sw.append((tau, a["agree"], a["pass_recall"], a["fail_recall"]))
            out["passes"][path]["sweep"] = [f"tau={t:.3f} agree={g} pass={p} fail={f}" for t, g, p, f in sw]
            rr = []
            for sid, p in pages.items():
                d = derive(p, lens[sid], 1.0)
                hard = d["hard"] >= 1 or d["verdict"] == "reject"
                rr.append({"sample_id": sid, "verdict": "heavy_edit" if hard or d["serious"] >= 2 else "light_edit"})
            out["passes"][path]["alt_count_rule_serious_le_1"] = agreement(rr, labels)
            rr = []
            for sid, p in pages.items():
                d = derive(p, lens[sid], 1.0)
                hard = d["hard"] >= 1 or d["verdict"] == "reject"
                rr.append({"sample_id": sid, "verdict": "heavy_edit" if hard or d["rate"] > 0.02 else "light_edit"})
            out["passes"][path]["alt_rate_only_0.02_no_floor"] = agreement(rr, labels)
    if len(runs) == 2:
        (_, _, ra), (_, _, rb) = runs
        a = {r["sample_id"]: r for r in ra}
        b = {r["sample_id"]: r for r in rb}
        ids = sorted(set(a) & set(b))
        va = [a[i]["verdict"] for i in ids]
        vb = [b[i]["verdict"] for i in ids]
        sa = sum(a[i]["serious"] for i in ids)
        sb = sum(b[i]["serious"] for i in ids)
        out["repeatability"] = {
            "pages": len(ids),
            "verdict_agreement_4level": round(sum(x == y for x, y in zip(va, vb)) / len(ids), 3),
            "kappa_4level": kappa(va, vb),
            "pass_fail_agreement": round(sum(binary(x) == binary(y) for x, y in zip(va, vb)) / len(ids), 3),
            "kappa_pass_fail": kappa([binary(x) for x in va], [binary(y) for y in vb]),
            "serious_errors_total": {"a": sa, "b": sb, "ratio_b_over_a": round(sb / sa, 3) if sa else None},
            "hard_fail_page_agreement": round(sum((a[i]["hard"] > 0) == (b[i]["hard"] > 0) for i in ids) / len(ids), 3),
            "rate_mean_abs_diff": round(sum(abs(a[i]["rate"] - b[i]["rate"]) for i in ids) / len(ids), 4),
        }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
