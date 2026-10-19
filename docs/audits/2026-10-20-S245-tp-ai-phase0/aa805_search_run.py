"""AA-805 live check (S237 runner, re-run in S245 with the ranking field recorded): run the 30-query labelled set against the deployed /browse/search.

HTTP only, through the public TripPlanner BFF (no keys needed). One Cohere query embed per query
(stage tp_search_embed, < $0.01 for the set). Sequential with a pause, well under the 10 rps route
throttle. Writes aa805_search_results.json next to this file: per query the status, the returned
destination ids (input of the read-only inactive-tour DB join listed in aa805-evidence.md §5), and the countries of the first
5 destinations (read from /browse/destinations/{id}, a cached browse read).

Usage: python3 aa805_search_run.py <path to search_labelled_30.json>
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://aa-tripplanner.vercel.app/api/browse"
OUT = Path(__file__).with_name("aa805_search_results.json")


def get(params: dict) -> tuple[int, dict]:
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def main(fixture: str) -> None:
    labelled = json.loads(Path(fixture).read_text())
    country_of: dict[str, str] = {}
    rows = []
    started = datetime.now(timezone.utc).isoformat()
    for q in labelled["queries"]:
        status, body = get({"resource": "search", "q": q["query"]})
        dests = body.get("destinations", []) if status == 200 else []
        top5 = []
        for d in dests[:5]:
            if d["id"] not in country_of:
                s, detail = get({"resource": "destination", "id": d["id"]})
                country_of[d["id"]] = detail.get("country") if s == 200 else f"?{s}"
                time.sleep(0.2)
            top5.append({"name": d["name"], "country": country_of[d["id"]]})
        hits = sum(1 for t in top5 if t["country"] in q["expected_countries"])
        rows.append({
            "id": q["id"], "query": q["query"], "status": status, "returned": len(dests),
            "ranking": body.get("ranking") if status == 200 else None,
            "destination_ids": [d["id"] for d in dests],
            "top5": top5, "top5_in_expected": hits,
            "relevance_pass": status == 200 and hits >= q["min_top5_in_expected"],
        })
        print(f'{q["id"]:>2} {status} n={len(dests):>2} top5_in_expected={hits}/{q["min_top5_in_expected"]} '
              f'{"PASS" if rows[-1]["relevance_pass"] else "FAIL"} {rows[-1]["ranking"]}  {q["query"]}')
        time.sleep(0.5)
    OUT.write_text(json.dumps({"started_utc": started, "ended_utc": datetime.now(timezone.utc).isoformat(),
                               "base": BASE, "results": rows}, indent=1))
    print("ok_200:", sum(r["status"] == 200 for r in rows), "/", len(rows),
          "relevance_pass:", sum(r["relevance_pass"] for r in rows), "/", len(rows))


if __name__ == "__main__":
    main(sys.argv[1])
