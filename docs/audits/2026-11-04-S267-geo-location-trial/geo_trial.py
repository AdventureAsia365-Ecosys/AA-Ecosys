"""AA-1043 trial, step 2 — geocode the ~50 sampled places with Amazon Location Places API v2 and compare each answer
with the Geoapify point we already store. Workstation script; writes ONLY local files under --out. No DB access.

Paid calls: geo-places Geocode (+ SearchText fallback when Geocode finds nothing, + one local-script Geocode probe for
non-Latin places). IntendedUse='Storage' -> the Stored bucket, USD 4.00 / 1,000 requests in us-west-2 (AWS price list,
publication 2026-09-11). HARD CAP: MAX_REQUESTS = 120 (=> at most USD 0.48). The cap counts every attempt, including
failed ones, and boto3 retries are off, so one counted attempt = at most one billed request.

Region: Amazon Location is NOT offered in us-west-1 (no endpoint, no price list region); the default is us-west-2.

Python with boto3 >= 1.35 (geo-places): apps/AA-CIS-App/.venv/bin/python (boto3 1.43.49 checked).

Usage (from the workspace root):
  PY=apps/AA-CIS-App/.venv/bin/python
  $PY .tmp-session/S267/trials/geo_trial.py --sample .tmp-session/S267/trials/geo_sample.json --dry-run
  # credentials: either --profile aa365-admin (boto3 asks for MFA itself), or the workspace pattern
  #   C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ;
  #   grep -q '^AWS_ACCESS_KEY_ID=' <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr '\n' ' ' <<<"$C") $PY ...
  $PY .tmp-session/S267/trials/geo_trial.py --sample .tmp-session/S267/trials/geo_sample.json

--sample accepts the clean JSON or the raw ecsx output (the part between ===GEO_SAMPLE_JSON_BEGIN/END=== is used).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

MAX_REQUESTS = 120                  # hard cap for the whole run; --max-requests may only lower it
EXPECT_ACCOUNT = "<acc2-account-id>"     # acc2
DEFAULT_REGION = "us-west-2"
UNSUPPORTED_REGIONS = {"us-west-1"}
# USD per request, us-west-2, AWS public price list (AmazonLocationService, publication 2026-09-11):
#   Places Core Geocode/SearchText $0.50 / 1k, Advanced $1.50 / 1k, Stored $4.00 / 1k, Label $0.20 / 1k.
PRICE = {"Label": 0.0002, "Core": 0.0005, "Advanced": 0.0015, "Stored": 0.004}
WORST_PRICE = PRICE["Stored"]
COARSE_TYPES = {"Country", "Region", "SubRegion", "PostalCode"}
TRIAL_DIR = Path(__file__).resolve().parent

# Rough country centroids [lat, lng] — the SearchText fallback needs ONE of BiasPosition / BoundingBox / Circle; a
# country-level bias keeps the test fair (the stored point is never used as the bias unless --bias stored).
CENTROID = {
    "TH": (15.87, 100.99), "VN": (14.06, 108.28), "KH": (12.57, 104.99), "LA": (19.86, 102.50),
    "MM": (21.91, 95.96), "MY": (4.21, 101.98), "ID": (-0.79, 113.92), "PH": (12.88, 121.77),
    "SG": (1.35, 103.82), "BN": (4.54, 114.73), "TL": (-8.87, 125.73), "CN": (35.86, 104.20),
    "HK": (22.32, 114.17), "MO": (22.20, 113.54), "TW": (23.70, 120.96), "JP": (36.20, 138.25),
    "KR": (35.91, 127.77), "MN": (46.86, 103.85), "IN": (20.59, 78.96), "NP": (28.39, 84.12),
    "BT": (27.51, 90.43), "LK": (7.87, 80.77), "BD": (23.68, 90.36), "MV": (3.20, 73.22),
    "PK": (30.38, 69.35), "UZ": (41.38, 64.59), "KZ": (48.02, 66.92), "KG": (41.20, 74.77),
    "TJ": (38.86, 71.28), "TM": (38.97, 59.56), "AU": (-25.27, 133.78), "NZ": (-40.90, 174.89),
}
EXTRA_CODES = {"CN": ["CN", "HK", "MO"]}   # same widening as the Geoapify path (guards.search_codes)


class CapReached(RuntimeError):
    pass


class Budget:
    def __init__(self, cap: int):
        self.cap, self.used, self.by_op, self.buckets = cap, 0, Counter(), Counter()

    def take(self, op: str) -> None:
        if self.used >= self.cap:
            raise CapReached(f"MAX_REQUESTS={self.cap} reached")
        self.used += 1
        self.by_op[op] += 1

    @property
    def left(self) -> int:
        return self.cap - self.used


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_sample(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    b, e = "===GEO_SAMPLE_JSON_BEGIN===", "===GEO_SAMPLE_JSON_END==="
    if b in text:
        text = text.split(b, 1)[1].split(e, 1)[0]
    data = json.loads(text.strip())
    if not data.get("places"):
        sys.exit("sample has no places")
    return data


def query_text(p: dict) -> str:
    name = (p.get("name") or "").strip()
    loc = (p.get("card_locality") or p.get("pn_locality") or "").strip()
    q = name if not loc or loc.lower() in name.lower() else f"{name}, {loc}"
    return q[:200]


def codes_for(iso2: str) -> list[str]:
    return EXTRA_CODES.get(iso2, [iso2])


def bias_for(p: dict, mode: str, country_mean: dict) -> tuple[list[float], str]:
    """BiasPosition as [lng, lat] (API order) and where it came from."""
    if mode == "stored":
        return [float(p["lng"]), float(p["lat"])], "stored"
    c = CENTROID.get(p["iso2"])
    if c:
        return [c[1], c[0]], "country_centroid"
    lat, lng = country_mean[p["iso2"]]
    return [lng, lat], "sample_country_mean"


def trim_item(it: dict) -> dict:
    addr = it.get("Address") or {}
    return {
        "PlaceType": it.get("PlaceType"), "Title": it.get("Title"), "Label": addr.get("Label"),
        "Country": (addr.get("Country") or {}).get("Code2"), "Region": (addr.get("Region") or {}).get("Name"),
        "Locality": addr.get("Locality"), "Position": it.get("Position"),
        "MatchScores": it.get("MatchScores"),
        "Categories": [c.get("Name") for c in (it.get("Categories") or [])][:3],
    }


def evaluate(p: dict, items: list) -> dict:
    """Top answer vs the stored point; also the nearest of the returned items (is the right place in the list?)."""
    if not items:
        return {"n_results": 0}
    top = items[0]
    lng, lat = top["Position"][0], top["Position"][1]
    km = haversine_km(float(p["lat"]), float(p["lng"]), lat, lng)
    best = min(haversine_km(float(p["lat"]), float(p["lng"]), it["Position"][1], it["Position"][0])
               for it in items if it.get("Position"))
    ms = top.get("MatchScores") or {}
    ret_iso = ((top.get("Address") or {}).get("Country") or {}).get("Code2")
    return {
        "n_results": len(items), "place_type": top.get("PlaceType"), "title": top.get("Title"),
        "label": (top.get("Address") or {}).get("Label"), "ret_iso2": ret_iso,
        "country_match": (ret_iso or "").upper() in codes_for(p["iso2"]) if ret_iso else None,
        "ret_lat": round(lat, 6), "ret_lng": round(lng, 6), "km": round(km, 3), "best_km_in_list": round(best, 3),
        "coarse": top.get("PlaceType") in COARSE_TYPES,
        "match_overall": ms.get("Overall"), "match_title": (ms.get("Components") or {}).get("Title"),
        "category": ((top.get("Categories") or [{}])[0] or {}).get("Name"),
    }


def stats(rows: list[dict]) -> dict:
    found = [r for r in rows if r.get("n_results")]
    kms = sorted(r["km"] for r in found)
    def within(x):
        return sum(1 for k in kms if k <= x)
    cm = [r["country_match"] for r in found if r.get("country_match") is not None]
    return {
        "places": len(rows), "found": len(found),
        "found_rate": round(len(found) / len(rows), 3) if rows else None,
        "median_km": round(statistics.median(kms), 3) if kms else None,
        "p90_km": round(kms[min(len(kms) - 1, int(0.9 * len(kms)))], 3) if kms else None,
        "within_1km": within(1), "within_5km": within(5), "within_25km": within(25), "over_25km": len(kms) - within(25),
        "country_match_rate": round(sum(cm) / len(cm), 3) if cm else None,
        "coarse_answers": sum(1 for r in found if r.get("coarse")),
        "right_place_in_list_1km": sum(1 for r in found if (r.get("best_km_in_list") or 1e9) <= 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", default=str(TRIAL_DIR / "geo_sample.json"))
    ap.add_argument("--out", default=str(TRIAL_DIR / "out"))
    ap.add_argument("--dry-run", action="store_true", help="plan + cost bound only; no AWS call at all")
    ap.add_argument("--max-requests", type=int, default=MAX_REQUESTS)
    ap.add_argument("--region", default=DEFAULT_REGION)
    ap.add_argument("--profile", default="aa365-admin", help="used only when AWS_ACCESS_KEY_ID is not in the env")
    ap.add_argument("--intended-use", default="Storage", choices=["Storage", "SingleUse"])
    ap.add_argument("--bias", default="country", choices=["country", "stored"],
                    help="SearchText fallback bias: country centroid (fair, default) or the stored point")
    ap.add_argument("--no-fallback", action="store_true", help="skip SearchText when Geocode finds nothing")
    ap.add_argument("--no-local-probe", action="store_true", help="skip the local-script Geocode probe")
    ap.add_argument("--limit", type=int, default=0, help="only the first N places (0 = all)")
    ap.add_argument("--language", default="en")
    a = ap.parse_args()

    if a.max_requests < 1 or a.max_requests > MAX_REQUESTS:
        sys.exit(f"--max-requests must be 1..{MAX_REQUESTS} (hard cap)")
    if a.region in UNSUPPORTED_REGIONS:
        sys.exit(f"Amazon Location (geo-places) has no endpoint in {a.region}; use {DEFAULT_REGION}")

    data = load_sample(Path(a.sample))
    places = data["places"][: a.limit] if a.limit else data["places"]
    for p in places:
        p["iso2"] = (p.get("iso2") or "").strip().upper()
    country_mean = {}
    for iso in {p["iso2"] for p in places}:
        pts = [(float(p["lat"]), float(p["lng"])) for p in places if p["iso2"] == iso]
        country_mean[iso] = (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts))

    n = len(places)
    probes = 0 if a.no_local_probe else sum(1 for p in places if p.get("local_name"))
    worst = n + (0 if a.no_fallback else n) + probes
    planned = min(worst, a.max_requests)
    print(f"plan: {n} places | Geocode {n} + SearchText fallback <= {0 if a.no_fallback else n} + local probes {probes}"
          f" = worst case {worst}; capped at {a.max_requests} -> at most {planned} requests")
    print(f"cost bound: {planned} x ${WORST_PRICE:.4f} (Stored, {a.region}) = ${planned * WORST_PRICE:.2f} "
          f"(trial limit $2.00)")
    if planned * WORST_PRICE > 2.0:
        sys.exit("cost bound above $2 — refusing")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.dry_run:
        plan_path = out / "aws_location_trial_plan.csv"
        with plan_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "iso2", "tags", "geo_precision", "geocode_query", "local_probe", "fallback_bias"])
            for p in places:
                b, src = bias_for(p, a.bias, country_mean)
                w.writerow([p["id"], p["iso2"], "|".join(p.get("tags") or []), p.get("geo_precision"),
                            query_text(p), p.get("local_name") or "", f"{src}:{b[1]:.2f},{b[0]:.2f}"])
        print(f"dry run: no AWS call made; plan written to {plan_path}")
        return 0

    import boto3                                    # only for a real run
    from botocore.config import Config
    from botocore.exceptions import ClientError

    if os.environ.get("AWS_ACCESS_KEY_ID"):
        sess = boto3.Session(region_name=a.region)
    else:
        sess = boto3.Session(profile_name=a.profile, region_name=a.region)
    acct = sess.client("sts").get_caller_identity()["Account"]
    if acct != EXPECT_ACCOUNT:
        sys.exit(f"wrong account {acct}: this trial runs on acc2 only")
    cfg = Config(retries={"total_max_attempts": 1, "mode": "standard"}, connect_timeout=10, read_timeout=20)
    geo = sess.client("geo-places", region_name=a.region, config=cfg)
    budget = Budget(a.max_requests)

    def call(op: str, **kw) -> tuple[list, str | None, str | None]:
        """One counted request. Returns (items, pricing bucket, error code)."""
        budget.take(op)
        try:
            resp = (geo.geocode if op.startswith("Geocode") else geo.search_text)(**kw)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "ClientError")
            if code in ("AccessDeniedException", "UnrecognizedClientException", "ExpiredTokenException"):
                raise
            return [], None, code
        finally:
            time.sleep(0.2)
        bucket = resp.get("PricingBucket") or resp.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get(
            "x-amz-geo-pricing-bucket")
        if bucket:
            budget.buckets[bucket] += 1
        return resp.get("ResultItems") or [], bucket, None

    rows, raw_f = [], (out / "aws_location_trial_raw.jsonl").open("w", encoding="utf-8")
    stopped, consecutive_err = None, 0
    try:
        for p in places:
            base = {"id": p["id"], "name": p.get("name"), "iso2": p["iso2"], "tags": "|".join(p.get("tags") or []),
                    "geo_precision": p.get("geo_precision"), "stored_lat": p["lat"], "stored_lng": p["lng"],
                    "geoapify_result_type": p.get("g_result_type"), "geoapify_confidence": p.get("g_confidence")}
            q = query_text(p)
            common = {"IntendedUse": a.intended_use, "Language": a.language, "MaxResults": 5}
            items, bucket, err = call("Geocode", QueryText=q, Filter={"IncludeCountries": codes_for(p["iso2"])},
                                      **common)
            op = "Geocode"
            if not items and not a.no_fallback and budget.left > 0:
                bias, src = bias_for(p, a.bias, country_mean)
                items, bucket, err2 = call("SearchText", QueryText=q, BiasPosition=bias,
                                           Filter={"IncludeCountries": codes_for(p["iso2"])}, **common)
                op, err = f"SearchText({src})", err2 or err
            consecutive_err = consecutive_err + 1 if err else 0
            row = {**base, "role": "final", "op": op, "query": q, "pricing_bucket": bucket, "error": err,
                   **evaluate(p, items)}
            rows.append(row)
            raw_f.write(json.dumps({"id": p["id"], "op": op, "query": q, "items": [trim_item(i) for i in items]},
                                   ensure_ascii=False) + "\n")
            if p.get("local_name") and not a.no_local_probe and budget.left > 0:
                lq = p["local_name"][:200]
                litems, lb, lerr = call("Geocode_local", QueryText=lq,
                                        Filter={"IncludeCountries": codes_for(p["iso2"])},
                                        IntendedUse=a.intended_use, MaxResults=5)
                rows.append({**base, "role": "local_probe", "op": "Geocode_local", "query": lq,
                             "pricing_bucket": lb, "error": lerr, **evaluate(p, litems)})
                raw_f.write(json.dumps({"id": p["id"], "op": "Geocode_local", "query": lq,
                                        "items": [trim_item(i) for i in litems]}, ensure_ascii=False) + "\n")
            if consecutive_err >= 3:
                stopped = f"3 consecutive errors (last: {err})"
                break
    except CapReached as e:
        stopped = str(e)
    except ClientError as e:
        stopped = f"auth/permission error: {e.response.get('Error', {}).get('Code')} — fix access, then rerun"
    finally:
        raw_f.close()

    done_ids = {r["id"] for r in rows}
    skipped = [p["id"] for p in places if p["id"] not in done_ids]

    cols = ["id", "name", "iso2", "tags", "geo_precision", "role", "op", "query", "n_results", "place_type", "title",
            "label", "category", "ret_iso2", "country_match", "coarse", "ret_lat", "ret_lng", "stored_lat",
            "stored_lng", "km", "best_km_in_list", "match_overall", "match_title", "pricing_bucket", "error",
            "geoapify_result_type", "geoapify_confidence"]
    csv_path = out / "aws_location_trial.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    final = [r for r in rows if r["role"] == "final"]
    probes_rows = [r for r in rows if r["role"] == "local_probe"]
    by_tag, by_iso, by_prec = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in final:
        for t in (r["tags"] or "").split("|"):
            if t:
                by_tag[t].append(r)
        by_iso[r["iso2"]].append(r)
        by_prec[r["geo_precision"] or "null"].append(r)
    est = sum(PRICE.get(b, WORST_PRICE) * c for b, c in budget.buckets.items())
    unbucketed = budget.used - sum(budget.buckets.values())
    est += unbucketed * WORST_PRICE                       # failed / unknown-bucket attempts priced at the worst rate
    summary = {
        "issue": "AA-1043", "region": a.region, "intended_use": a.intended_use, "fallback_bias": a.bias,
        "sample_seed": data.get("seed"), "places_in_sample": len(places), "places_done": len(final),
        "skipped_ids": skipped, "stopped": stopped,
        "requests": {"total": budget.used, "cap": a.max_requests, "by_op": dict(budget.by_op),
                     "pricing_buckets": dict(budget.buckets), "no_bucket_reported": unbucketed},
        "cost_usd_estimate": round(est, 4),
        "cost_line": (f"{budget.used} requests; buckets {dict(budget.buckets)}; at the official {a.region} prices "
                      f"(Stored $4.00/1k, Core $0.50/1k) = ${est:.4f}; Core free tier (20k/month for 3 months) "
                      f"does not cover Stored"),
        "overall": stats(final),
        "by_op": {op: stats([r for r in final if r["op"] == op]) for op in sorted({r["op"] for r in final})},
        "by_tag": {t: stats(v) for t, v in sorted(by_tag.items())},
        "by_country": {k: stats(v) for k, v in sorted(by_iso.items())},
        "by_geo_precision": {k: stats(v) for k, v in sorted(by_prec.items())},
        "local_script_probe": stats(probes_rows) if probes_rows else None,
        "worst_20": sorted(({"id": r["id"], "name": r["name"], "iso2": r["iso2"], "km": r.get("km"),
                             "title": r.get("title"), "place_type": r.get("place_type"), "tags": r["tags"]}
                            for r in final if r.get("n_results")), key=lambda x: -(x["km"] or 0))[:20],
        "not_found": [{"id": r["id"], "name": r["name"], "iso2": r["iso2"], "error": r.get("error")}
                      for r in final if not r.get("n_results")],
        "files": {"csv": str(csv_path), "raw": str(out / "aws_location_trial_raw.jsonl")},
        "note": "The stored point is Geoapify's accepted answer, not ground truth: a large km means the two providers "
                "disagree; check worst_20 by hand before calling either one wrong.",
    }
    (out / "aws_location_trial_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                                         encoding="utf-8")
    o = summary["overall"]
    print(f"done: {len(final)}/{len(places)} places, found {o['found']} (rate {o['found_rate']}), median "
          f"{o['median_km']} km, p90 {o['p90_km']} km, <=1km {o['within_1km']}, <=5km {o['within_5km']}, "
          f"country match {o['country_match_rate']}" + (f" | stopped: {stopped}" if stopped else ""))
    print("cost:", summary["cost_line"])
    print("files:", csv_path, out / "aws_location_trial_summary.json")
    return 0 if not stopped or stopped.startswith("MAX_REQUESTS") else 1


if __name__ == "__main__":
    sys.exit(main())
