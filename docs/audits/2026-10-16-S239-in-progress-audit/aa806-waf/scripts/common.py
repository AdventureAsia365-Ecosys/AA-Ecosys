"""AA-806 WAF pre-flip test helpers. Secrets are read at run time and never printed or written."""
import hashlib
import json
import subprocess

import requests

CIS_API = "https://api-cis.lumiguides.it.com"
CIS_WEB = "https://aa-cis.lumiguides.it.com"
BOOKING_API = "https://api-booking.lumiguides.it.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 aa806-waf-test"


def secret(name: str) -> str:
    out = subprocess.run(
        ["aws", "secretsmanager", "get-secret-value", "--secret-id", name, "--query", "SecretString",
         "--output", "text", "--profile", "aa365-admin", "--region", "us-west-1"],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def sha(obj) -> str:
    if isinstance(obj, (bytes, bytearray)):
        b = bytes(obj)
    elif isinstance(obj, str):
        b = obj.encode()
    else:
        b = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(b).hexdigest()


def admin_web_session() -> requests.Session:
    """Admin cookie session on the CIS Vercel BFF (same path as the browser)."""
    c = json.loads(secret("aa-cis/dev/e2e-test-admin"))
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.post(f"{CIS_WEB}/api/auth/login", json={"username": c["username"], "password": c["password"]}, timeout=30)
    r.raise_for_status()
    return s


def admin_cis_token() -> str:
    c = json.loads(secret("aa-cis/dev/e2e-test-admin"))
    r = requests.post(f"{CIS_API}/auth/admin-login", json={"username": c["username"], "password": c["password"]},
                      headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r.json()["token"]


def booking_token(cis_token: str) -> str:
    r = requests.post(f"{CIS_API}/auth/booking-token", headers={"Authorization": f"Bearer {cis_token}", "User-Agent": UA},
                      timeout=30)
    r.raise_for_status()
    d = r.json()
    return d.get("token") or d.get("access_token")


def tenant_key(slug: str) -> str:
    raw = secret(f"aa-cis/dev/e2e-tenant/{slug}")
    try:
        d = json.loads(raw)
        return d.get("api_key") or d.get("key") or d.get("apiKey")
    except json.JSONDecodeError:
        return raw


def tenant_token(slug: str) -> str:
    r = requests.post(f"{CIS_API}/auth/tenant-login", json={"api_key": tenant_key(slug)}, headers={"User-Agent": UA},
                      timeout=30)
    r.raise_for_status()
    return r.json()["token"]


def tenant_web_session(slug: str) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.post(f"{CIS_WEB}/api/auth/tenant-login", json={"api_key": tenant_key(slug)}, timeout=30)
    r.raise_for_status()
    return s
