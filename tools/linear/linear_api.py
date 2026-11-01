"""Shared Linear API access for the tools in tools/linear/ (stdlib only).

Split out of linear_export.py (S263, AA-896 lane plan-sync) so plan_sync.py uses the same key lookup and error
handling. The API key is read from Secrets Manager (aa-ecosys/ops/linear-api-key, acc2) into memory only; it is never
printed or written. LINEAR_API_KEY in the environment overrides it (CI / testing).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.linear.app/graphql"
SECRET_ID = "aa-ecosys/ops/linear-api-key"


def api_key() -> str:
    key = os.environ.get("LINEAR_API_KEY", "").strip()
    if key:
        return key
    r = subprocess.run(
        ["aws", "secretsmanager", "get-secret-value", "--secret-id", SECRET_ID, "--query", "SecretString",
         "--output", "text", "--profile", os.environ.get("AWS_PROFILE_LINEAR", "aa365-admin"), "--region", "us-west-1"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
    )
    key = r.stdout.strip()
    if r.returncode != 0 or not key:
        sys.exit(f"cannot read {SECRET_ID} (aws exit {r.returncode}); unlock MFA or set LINEAR_API_KEY")
    return key


def gql(key: str, query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        API, data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Linear API HTTP {e.code}: {e.read()[:300]!r}")
    if body.get("errors"):
        sys.exit(f"Linear API error: {json.dumps(body['errors'])[:500]}")
    return body["data"]
