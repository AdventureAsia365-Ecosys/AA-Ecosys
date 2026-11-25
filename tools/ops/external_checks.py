#!/usr/bin/env python3
"""AA-1142 (S292) — the external synthetic checks of the Ecosystem status page (CIS /admin/overview): what a customer
outside the VPC meets, checked from GitHub Actions every 15 minutes (workflow .github/workflows/external-checks.yml).

For every target of tools/ops/external_checks.json:

  dns   the host resolves (getaddrinfo, port 443)
  tls   a verified TLS handshake (the system trust store, the host name checked) and the certificate's end date
  http  (mode "health") one GET of the target's path without following redirects: the status and the time; the
        status must be one of the target's ``expect`` list (a sign-in redirect is an answer, not a failure)

and writes one run, format 1, read by the CIS status sampler (api/services/ops_status/external.py, which derives the
state with the certificate limits of its own settings):

  {"format": 1, "checked_at": "<UTC ISO>", "results": [{"target", "app", "host", "url", "mode", "dns_ok", "tls_ok",
    "cert_not_after", "http_status", "http_ok", "latency_ms", "error"}]}

Since S293 this is the second vantage point (source ``github`` of acp_shared.ops_external_check): GitHub started the
schedule 0 times on its first day, so the CIS worker runs the same checks itself every
``cis.ops.external_check_interval_min`` minutes (job kind ops_external_check, source ``worker``, target list in the CIS
setting ``cis.ops.external_check_targets``). Keep tools/ops/external_checks.json and that setting in step when a public
host is added; the status page goes grey only when every source in use stopped reporting.

Public hosts only, names and numbers only: no secret, no account ID, no cookie, no request body. Standard library only.

    python3 tools/ops/external_checks.py run --out _out/external-checks.json
    python3 tools/ops/external_checks.py run --out - --only cis-api
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

CONFIG = Path(__file__).with_name("external_checks.json")
FORMAT = 1
TIMEOUT_S = 10.0
USER_AGENT = "aa-external-checks/1"
TARGET = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")
HOST = re.compile(r"^[a-z0-9.-]{1,253}$")
APPS = ("cis", "tripplanner", "booking", "crm", "shared")


class ConfigError(ValueError):
    pass


def load_config(path: Path = CONFIG) -> list[dict]:
    """The targets, every field checked (ConfigError on a bad one)."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    targets = doc.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ConfigError("targets missing")
    seen = set()
    for t in targets:
        if not (isinstance(t.get("id"), str) and TARGET.match(t["id"])):
            raise ConfigError(f"bad id {t.get('id')!r}")
        if t["id"] in seen:
            raise ConfigError(f"duplicate id {t['id']}")
        seen.add(t["id"])
        if not (isinstance(t.get("host"), str) and HOST.match(t["host"])):
            raise ConfigError(f"{t['id']}: bad host")
        if t.get("app") not in APPS:
            raise ConfigError(f"{t['id']}: unknown app")
        if t.get("mode") not in ("health", "tls"):
            raise ConfigError(f"{t['id']}: mode must be health or tls")
        if t["mode"] == "health":
            if not (isinstance(t.get("path"), str) and t["path"].startswith("/")):
                raise ConfigError(f"{t['id']}: a health target needs a path")
            expect = t.get("expect")
            if not (isinstance(expect, list) and expect and all(isinstance(c, int) and 100 <= c <= 599
                                                                 for c in expect)):
                raise ConfigError(f"{t['id']}: expect must be a list of HTTP statuses")
    return targets


def _short(e: BaseException) -> str:
    return f"{type(e).__name__}: {e}"[:300]


def cert_end(cert: dict) -> Optional[str]:
    """The certificate's notAfter as an UTC ISO time (None when absent). Pure."""
    raw = (cert or {}).get("notAfter")
    if not raw:
        return None
    return datetime.fromtimestamp(ssl.cert_time_to_seconds(raw), tz=timezone.utc).isoformat()


def check_dns(host: str, resolve: Callable[..., Any] = socket.getaddrinfo) -> tuple[bool, Optional[str]]:
    try:
        resolve(host, 443, proto=socket.IPPROTO_TCP)
        return True, None
    except OSError as e:
        return False, _short(e)


def check_tls(host: str, timeout: float = TIMEOUT_S) -> tuple[Optional[bool], Optional[str], Optional[str]]:
    """(tls_ok, cert_not_after, error): False on a refused certificate, None when no connection was made."""
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2   # a host that only offers TLS 1.0/1.1 counts as a TLS failure
    try:
        with socket.create_connection((host, 443), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as s:
                return True, cert_end(s.getpeercert()), None
    except ssl.SSLCertVerificationError as e:
        return False, None, _short(e)
    except ssl.SSLError as e:
        return False, None, _short(e)
    except OSError as e:
        return None, None, _short(e)


def check_http(host: str, path: str, timeout: float = TIMEOUT_S) -> tuple[Optional[int], Optional[int], Optional[str]]:
    """(status, latency_ms, error) of one GET without following redirects."""
    start = time.monotonic()
    conn = http.client.HTTPSConnection(host, 443, timeout=timeout, context=ssl.create_default_context())
    try:
        conn.request("GET", path, headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/html"})
        resp = conn.getresponse()
        resp.read(65536)
        return resp.status, int((time.monotonic() - start) * 1000), None
    except (OSError, http.client.HTTPException) as e:
        return None, int((time.monotonic() - start) * 1000), _short(e)
    finally:
        conn.close()


def check_one(t: dict, *, dns: Callable = check_dns, tls: Callable = check_tls, get: Callable = check_http) -> dict:
    """One target's result (a failed step leaves the later ones unchecked)."""
    out = {"target": t["id"], "app": t["app"], "host": t["host"], "mode": t["mode"],
           "url": f"https://{t['host']}{t.get('path', '/')}", "dns_ok": None, "tls_ok": None, "cert_not_after": None,
           "http_status": None, "http_ok": None, "latency_ms": None, "error": None}
    ok, err = dns(t["host"])
    out["dns_ok"] = ok
    if not ok:
        out["error"] = err
        return out
    tls_ok, end, err = tls(t["host"])
    out.update(tls_ok=tls_ok, cert_not_after=end)
    if not tls_ok:
        out["error"] = err
        return out
    if t["mode"] == "health":
        status, ms, err = get(t["host"], t["path"])
        out.update(http_status=status, latency_ms=ms, error=err)
        out["http_ok"] = status in t["expect"] if status is not None else None
    return out


def run(targets: list[dict], now: Optional[datetime] = None, **checks: Callable) -> dict:
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    return {"format": FORMAT, "checked_at": now.isoformat(), "results": [check_one(t, **checks) for t in targets]}


def summary(doc: dict) -> str:
    """A Markdown table for the job summary. Pure."""
    lines = ["### External checks", "", "| Target | DNS | TLS | Certificate ends | HTTP | Time |",
             "|---|---|---|---|---|---|"]
    yes = {True: "ok", False: "FAIL", None: "–"}
    for r in doc["results"]:
        lines.append(f"| {r['host']} | {yes[r['dns_ok']]} | {yes[r['tls_ok']]} | {(r['cert_not_after'] or '–')[:10]}"
                     f" | {r['http_status'] or '–'} | {r['latency_ms'] if r['latency_ms'] is not None else '–'} ms |")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="check every target and write the run")
    r.add_argument("--out", required=True, help="file to write, or - for stdout")
    r.add_argument("--summary", help="also append a Markdown table to this file (the job summary)")
    r.add_argument("--only", help="check only this target id")
    sub.add_parser("validate", help="check the config only")
    a = ap.parse_args(argv)
    targets = load_config()
    if a.cmd == "validate":
        print(f"{len(targets)} targets OK")
        return 0
    if a.only:
        targets = [t for t in targets if t["id"] == a.only]
    doc = run(targets)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out == "-":
        print(text)
    else:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    if a.summary:
        with open(a.summary, "a", encoding="utf-8") as f:
            f.write(summary(doc) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
