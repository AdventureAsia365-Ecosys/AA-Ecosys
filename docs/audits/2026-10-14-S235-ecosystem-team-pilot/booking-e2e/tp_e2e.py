#!/usr/bin/env python3
"""S235 — one end-to-end TripPlanner Dev customer hand-off, to verify AA-Booking inquiry intake.

Calls the TripPlanner HTTP API (API Gateway 9vqkfbukvh, stage $default, acc2 us-west-1) the same way
the Next.js BFF does (frontend/app/api/trip/route.ts), with the X-TripPlanner-Key edge secret read
from Secrets Manager `tripplanner/dev/api-key`. The key is never printed.

Sequence (same as a real visitor who starts from a proposed AA route, PR-11):
  0. STS check: must be acc2 005097885195.
  1. GET  /browse/countries                      -> pick "Bhutan" (fallback "Vietnam")
  2. GET  /browse/routes?country=<c>&days=<n>    -> first proposal with >= 2 pinnable components
  3. (client) session_id + trip_id = uuid4       -> like useTrip.tsx loadOrCreateIds(); the guest
                                                    session row is created lazily by the first pin
  4. POST /trip/{trip_id}/apply-route            -> pins the route's components in day order
  5. GET  /trip/{trip_id}                         -> confirm the itinerary is non-empty
  6. POST /trip/{trip_id}/send-to-advisor         -> ONE send, with registration (skipped by --dry-run)

Safety:
  * stops on the first non-2xx and prints the response body;
  * never retries the send; the ids are written to a state file BEFORE the send, so a lost response
    can be re-checked with --resume (the server answers already_sent=true for the same hand-off);
  * refuses to start a second hand-off if the state file records a completed send
    (override: --allow-second-handoff).

Usage:
  python3 .tmp-session/s235/tp_e2e.py --dry-run
  python3 .tmp-session/s235/tp_e2e.py
  python3 .tmp-session/s235/tp_e2e.py --resume      # only if the send response was lost
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import boto3
import requests

PROFILE = "aa365-admin"
REGION = "us-west-1"
EXPECTED_ACCOUNT = "005097885195"
API_ID = "9vqkfbukvh"
# tripplanner.tf: aws_apigatewayv2_stage.tripplanner name = "$default" -> no stage path segment.
BASE_URL = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com"
API_KEY_SECRET = "tripplanner/dev/api-key"  # tripplanner.tf aws_secretsmanager_secret.tripplanner_api_key
STATE_FILE = Path(__file__).resolve().parent / "tp_e2e_state.json"
DRY_STATE_FILE = Path(__file__).resolve().parent / "tp_e2e_state.dryrun.json"  # never touches the real guard

CUSTOMER = {
    "name": "S235 E2E Test",
    "email": "e2e-s235+booking@adventure.asia",
    "phone": None,
    "consent": True,
}
COUNTRIES = ["Bhutan", "Vietnam"]
DAY_CANDIDATES = [7, 6, 8, 5, 10, 4, 12]
MIN_PINS = 2
TIMEOUT = 60


class StepFailed(SystemExit):
    pass


def _boto_session() -> boto3.Session:
    """Exported env credentials win (aws configure export-credentials ... --format env); otherwise
    the aa365-admin profile, reusing the AWS CLI's assume-role cache so MFA is not asked twice."""
    if os.environ.get("AWS_ACCESS_KEY_ID") and not os.environ.get("AWS_PROFILE"):
        return boto3.Session(region_name=REGION)
    sess = boto3.Session(profile_name=PROFILE, region_name=REGION)
    try:
        from botocore.credentials import JSONFileCache

        cache = JSONFileCache(os.path.expanduser("~/.aws/cli/cache"))
        sess._session.get_component("credential_provider").get_provider("assume-role").cache = cache  # noqa: SLF001
    except Exception:  # noqa: BLE001 — cache reuse is a convenience only
        pass
    return sess


def _api_key(sess: boto3.Session) -> str:
    ident = sess.client("sts").get_caller_identity()
    if ident["Account"] != EXPECTED_ACCOUNT:
        raise StepFailed(f"[0] STS account {ident['Account']} != {EXPECTED_ACCOUNT} (acc2). Abort.")
    print(f"[0] STS ok: account {ident['Account']}")
    value = sess.client("secretsmanager").get_secret_value(SecretId=API_KEY_SECRET)["SecretString"].strip()
    if not value:
        raise StepFailed(f"[0] secret {API_KEY_SECRET} is empty. Abort.")
    print(f"[0] API key loaded from {API_KEY_SECRET} (len={len(value)}, value not printed)")
    return value


def _call(http: requests.Session, step: str, method: str, path: str, *, params=None, body=None) -> dict:
    url = f"{BASE_URL}{path}"
    resp = http.request(method, url, params=params,
                        data=json.dumps(body) if body is not None else None, timeout=TIMEOUT)
    print(f"[{step}] {method} {path}{'?' + '&'.join(f'{k}={v}' for k, v in params.items()) if params else ''}"
          f" -> HTTP {resp.status_code}")
    if not 200 <= resp.status_code < 300:
        print(f"[{step}] response body: {resp.text[:4000]}")
        raise StepFailed(f"[{step}] stopped on HTTP {resp.status_code}")
    try:
        return resp.json()
    except ValueError:
        raise StepFailed(f"[{step}] non-JSON 2xx body: {resp.text[:1000]}")


def _pick_route(http: requests.Session) -> tuple[str, dict, list[str]]:
    data = _call(http, "1", "GET", "/browse/countries")
    available = {c["country"].lower(): c["country"] for c in data.get("countries", [])}
    for wanted in COUNTRIES:
        country = available.get(wanted.lower())
        if not country:
            print(f"[1] {wanted}: not in /browse/countries, skipping")
            continue
        for days in DAY_CANDIDATES:
            routes = _call(http, "2", "GET", "/browse/routes", params={"country": country, "days": days})
            for p in routes.get("proposals", []):
                ids = list(dict.fromkeys(d["component_id"] for d in p.get("days", []) if d.get("component_id")))
                if len(ids) >= MIN_PINS:
                    return country, p, ids
            print(f"[2] {country} days={days}: no proposal with >= {MIN_PINS} components")
    raise StepFailed("[2] no usable AA route found for Bhutan or Vietnam")


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    (DRY_STATE_FILE if state.get("dry_run") else STATE_FILE).write_text(json.dumps(state, indent=2))


def _send(http: requests.Session, trip_id: str, session_id: str, step: str = "6") -> dict:
    return _call(http, step, "POST", f"/trip/{trip_id}/send-to-advisor",
                 body={"session_id": session_id, "customer": CUSTOMER})


def _report_send(trip_id: str, res: dict) -> None:
    handoff_id = res.get("handoff_id")
    print(f"[6] status={res.get('status')} handoff_id={handoff_id} already_sent={res.get('already_sent')}")
    # backend/assembly/handoff.py idempotency_key(): f"{trip_id}:{handoff_id}"
    print(f"[6] outbox idempotency_key = {trip_id}:{handoff_id}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="do everything except the final send")
    ap.add_argument("--resume", action="store_true",
                    help="re-POST send for the trip in the state file (server answers already_sent)")
    ap.add_argument("--allow-second-handoff", action="store_true",
                    help="start a new trip even though the state file records a completed send")
    args = ap.parse_args()

    state = _load_state()
    if (not args.resume and not args.dry_run and not args.allow_second_handoff
            and (state.get("sent") or state.get("send_attempted"))):
        what = "records a hand-off" if state.get("sent") else "records a send whose response was lost"
        print(f"State file {STATE_FILE} {what} (trip_id={state.get('trip_id')}, "
              f"key={state.get('idempotency_key')}). Refusing a second one; use --resume to re-check "
              f"that trip, or --allow-second-handoff to start a new one.")
        return 2

    sess = _boto_session()
    http = requests.Session()
    http.headers.update({"content-type": "application/json", "x-tripplanner-key": _api_key(sess)})
    print(f"[0] base URL {BASE_URL}")

    if args.resume:
        if not state.get("trip_id") or not state.get("session_id"):
            raise StepFailed(f"--resume: no trip in {STATE_FILE}")
        print(f"[resume] trip_id={state['trip_id']} session_id={state['session_id']}")
        res = _send(http, state["trip_id"], state["session_id"], step="6-resume")
        _report_send(state["trip_id"], res)
        state.update(sent=True, handoff_id=res.get("handoff_id"),
                     idempotency_key=f"{state['trip_id']}:{res.get('handoff_id')}")
        _save_state(state)
        return 0

    country, proposal, component_ids = _pick_route(http)
    segs = ", ".join(f"{s['tour_id']} d{s['day_from']}-{s['day_to']} ({s.get('tour_name')})"
                     for s in proposal.get("segments", []))
    print(f"[2] picked {country}: {proposal.get('total_days')} days, whole_tour={proposal.get('whole_tour')}, "
          f"segments: {segs}; {len(component_ids)} components to pin")

    session_id, trip_id = str(uuid.uuid4()), str(uuid.uuid4())
    print(f"[3] session_id={session_id} trip_id={trip_id}")
    state = {"session_id": session_id, "trip_id": trip_id, "country": country,
             "component_ids": component_ids, "dry_run": args.dry_run, "sent": False}
    _save_state(state)

    res = _call(http, "4", "POST", f"/trip/{trip_id}/apply-route",
                body={"session_id": session_id, "component_ids": component_ids})
    print(f"[4] itinerary days after apply-route: {len(res.get('itinerary', []))}")

    res = _call(http, "5", "GET", f"/trip/{trip_id}")
    itin = res.get("itinerary", [])
    if len(itin) < MIN_PINS:
        raise StepFailed(f"[5] itinerary has {len(itin)} days, expected >= {MIN_PINS}")
    tours = sorted({str(d.get("source_tour_id")) for d in itin if d.get("source_tour_id")})
    print(f"[5] itinerary days={len(itin)} source_tour_ids={tours}")

    if args.dry_run:
        print("[6] --dry-run: send-to-advisor NOT called. Draft trip left as a guest draft.")
        return 0

    state["send_attempted"] = True  # before the call: a lost response must not lead to a new trip
    _save_state(state)
    res = _send(http, trip_id, session_id)
    _report_send(trip_id, res)
    state.update(sent=True, handoff_id=res.get("handoff_id"),
                 idempotency_key=f"{trip_id}:{res.get('handoff_id')}")
    _save_state(state)
    print(f"State written to {STATE_FILE}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except StepFailed as e:
        print(str(e.code) if e.code else "stopped")
        sys.exit(1)
