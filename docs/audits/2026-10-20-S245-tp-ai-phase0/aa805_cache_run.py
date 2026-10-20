"""AA-805 closing check: narration cache hit + session ownership, live, through the public BFF.

HTTP only (https://aa-tripplanner.vercel.app/api/trip), no keys: the BFF adds the edge key and the
middleware mints the HttpOnly guest cookie, exactly as for a browser. Each client keeps its own
cookie jar and sends a same-origin Origin header.

Steps (all on one new trip):
  1. owner: add the given components (one per call), then op=narrate mode=compose.
  2. If that answer is source llm/mixed (cacheable), the owner asks again: expect cached:true.
     A source of master/master_basic/basic is never cached (narration_cache.CACHEABLE_SOURCES):
     the script stops and says so, so the caller can retry with other components ($0 spent).
  3. ownership (AA-827 + AA-805): a second client with no cookie, sending the owner's session id
     -> expect 401; a third client with its own session and cookie -> expect 403.

Cost: at most one tp_compose model call (step 1, only when a day has no AA master text); step 2
and 3 make no model call. Prints status codes, source/cached flags and the narration length only.

Usage: python3 aa805_cache_run.py [--skip-ownership] <component_id> [<component_id> ...]
Writes aa805_cache_results.json next to this file (rename it between tries).
"""
from __future__ import annotations

import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

SITE = "https://aa-tripplanner.vercel.app"
BFF = f"{SITE}/api/trip"
OUT = Path(__file__).with_name("aa805_cache_results.json")
CACHEABLE = ("llm", "mixed")


class Client:
    def __init__(self, name: str) -> None:
        self.name = name
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def post(self, body: dict) -> tuple[int, dict]:
        req = urllib.request.Request(
            BFF, data=json.dumps(body).encode(), method="POST",
            headers={"content-type": "application/json", "origin": SITE})
        try:
            with self.opener.open(req, timeout=90) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, {"raw": raw.decode(errors="replace")[:200]}

    def has_cookie(self) -> bool:
        return any(c.name.endswith("tp_guest") for c in self.jar)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def summary(status: int, body: dict) -> dict:
    """What the evidence needs; never the narration text itself."""
    keep = {k: body.get(k) for k in ("error", "detail", "mode", "source", "ai_generated", "cached",
                                      "ai_budget_exhausted") if k in body}
    if "narration" in body:
        keep["narration_chars"] = len(body["narration"] or "")
    if "itinerary" in body:
        keep["itinerary_days"] = len(body["itinerary"] or [])
    return {"status": status, **keep}


def main(argv: list[str]) -> int:
    skip_ownership = "--skip-ownership" in argv
    component_ids = [a for a in argv if not a.startswith("--")]
    trip_id, owner_session = str(uuid.uuid4()), str(uuid.uuid4())
    owner = Client("owner")
    log: list[dict] = []

    def step(label: str, client: Client, body: dict) -> dict:
        # A 429 is API Gateway's route throttle (narrate: 2 rps, burst 5), answered before the
        # Lambda runs: record it and try again after a pause (at most 3 attempts).
        for attempt in range(1, 4):
            status, resp = client.post(body)
            row = {"at": now(), "step": label, "attempt": attempt, "client": client.name,
                   **summary(status, resp)}
            log.append(row)
            print(json.dumps(row), flush=True)
            if status != 429:
                break
            time.sleep(3)
        return row

    for cid in component_ids:
        step(f"add {cid}", owner, {"op": "add", "trip_id": trip_id, "session_id": owner_session,
                                   "component_id": cid})
    first = step("narrate #1", owner, {"op": "narrate", "trip_id": trip_id,
                                       "session_id": owner_session, "mode": "compose"})
    verdict = "stopped"
    if first["status"] == 200 and first.get("source") in CACHEABLE:
        second = step("narrate #2 (same itinerary)", owner,
                      {"op": "narrate", "trip_id": trip_id, "session_id": owner_session,
                       "mode": "compose"})
        verdict = ("PASS" if first.get("cached") is False and second.get("cached") is True
                   else "CHECK")
    elif first["status"] == 200:
        print(f"source={first.get('source')} is not cacheable: retry with other components",
              flush=True)

    # Ownership: no cookie + owner's session id -> 401; own session + own cookie -> 403.
    if not skip_ownership:
        _ownership(trip_id, owner_session, component_ids[0], step)

    OUT.write_text(json.dumps({"trip_id": trip_id, "owner_session_prefix": owner_session[:8],
                               "owner_cookie_set": owner.has_cookie(), "cache_verdict": verdict,
                               "steps": log}, indent=1))
    print(f"cache_verdict={verdict} trip_id={trip_id}", flush=True)
    return 0


def _ownership(trip_id: str, owner_session: str, component_id: str, step) -> None:
    stranger = Client("foreign-no-cookie")
    step("narrate, foreign client, owner's session id, no cookie", stranger,
         {"op": "narrate", "trip_id": trip_id, "session_id": owner_session, "mode": "compose"})
    other = Client("foreign-own-session")
    other_session = str(uuid.uuid4())
    # A first mutating call on a trip of its own gives this client its cookie + session row.
    step("add on own trip (foreign client gets its cookie)", other,
         {"op": "add", "trip_id": str(uuid.uuid4()), "session_id": other_session,
          "component_id": component_id})
    step("narrate, foreign client, own session + cookie", other,
         {"op": "narrate", "trip_id": trip_id, "session_id": other_session, "mode": "compose"})


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
