"""AA-806 WAF pre-flip test (S239). Large realistic content writes against Dev that cannot change data:
every write targets a random, non-existent id (UUID or case code), so the app answers 404 after the WAF
has already inspected the full request. Before/after hashes of the related real resources prove no change.
No secret is printed or written; output holds only labels, sizes, statuses and hashes."""
import datetime as dt
import json
import sys
import time
import uuid

import common as c
import payloads

OUT = sys.argv[1]
TOUR_ID = "3fa33633-8502-4b53-a775-a0491fd2e509"
SLUG = "atlas-hearth"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def body_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")  # browsers send raw UTF-8, not \u escapes


adm = c.admin_web_session()
ten_tok = c.tenant_token(SLUG)
TH = {"Authorization": f"Bearer {ten_tok}", "User-Agent": c.UA}
ten_web = c.tenant_web_session(SLUG)
bk_tok = c.booking_token(c.admin_cis_token())
BH = {"Authorization": f"Bearer {bk_tok}", "User-Agent": c.UA}


def snapshot():
    s = {}
    r = adm.get(f"{c.CIS_WEB}/api/admin/tours/{TOUR_ID}/detail", timeout=60)
    j = r.json()
    s["cis_tour_detail_raw"] = c.sha(j["raw"])
    s["cis_tour_detail_generated"] = c.sha(j["generated"])
    s["cis_tour_detail_published"] = c.sha(j["published"])
    mv = c.requests.get(f"{c.CIS_API}/v1/tours/my-versions?limit=100", headers=TH, timeout=60).json()
    s["tenant_my_versions"] = c.sha(mv)
    s["tenant_my_versions_total"] = (mv.get("pagination") or {}).get("total", len(mv.get("data", [])))
    rv = c.requests.get(f"{c.CIS_API}/v1/content-writing/reviews", headers=TH, timeout=60).json()
    s["tenant_reviews"] = c.sha(rv)
    s["tenant_reviews_total"] = rv.get("total")
    tc = c.requests.get(f"{c.BOOKING_API}/booking/trip-cases?limit=100", headers=BH, timeout=60).json()
    s["booking_trip_cases"] = c.sha(tc)
    sp = c.requests.get(f"{c.BOOKING_API}/booking/suppliers", headers=BH, timeout=60).json()
    s["booking_suppliers"] = c.sha(sp)
    au = c.requests.get(f"{c.BOOKING_API}/booking/audit-logs?limit=20", headers=BH, timeout=60)
    s["booking_audit_logs_latest20"] = c.sha(au.content) if au.ok else f"http {au.status_code}"
    return s, j, mv


before, detail, mv = snapshot()
version = mv["data"][0]
vc = version["rewritten_content"]
version_content = json.loads(vc) if isinstance(vc, str) else vc
P = payloads.build(detail["raw"], version_content)

rid = lambda: str(uuid.uuid4())  # noqa: E731
plan = [
    # label, channel, method, url builder, payload key, client
    ("A1 admin raw PATCH, real fields unchanged (plain text)", "BFF->api-cis", "PATCH",
     f"{c.CIS_WEB}/api/admin/tours/{rid()}/raw", "admin_raw_unchanged", "admin"),
    ("A2 admin raw PATCH, HTML description", "BFF->api-cis", "PATCH",
     f"{c.CIS_WEB}/api/admin/tours/{rid()}/raw", "admin_raw_html", "admin"),
    ("A3 admin generated-content PATCH, HTML", "BFF->api-cis", "PATCH",
     f"{c.CIS_WEB}/api/admin/tours/{rid()}/generated/{rid()}", "admin_generated_html", "admin"),
    ("T1 tenant version edit, real rewritten_content unchanged", "direct api-cis", "PATCH",
     f"{c.CIS_API}/v1/tours/versions/{rid()}", "tenant_version_unchanged", "tenant"),
    ("T2 tenant version edit, HTML summary", "direct api-cis", "PATCH",
     f"{c.CIS_API}/v1/tours/versions/{rid()}", "tenant_version_html", "tenant"),
    ("T3 tenant piece edit, markdown blog", "direct api-cis", "PATCH",
     f"{c.CIS_API}/v1/content-writing/pieces/{rid()}", "tenant_piece_markdown", "tenant"),
    ("T4 tenant version edit via portal BFF, HTML summary", "BFF->api-cis", "PATCH",
     f"{c.CIS_WEB}/api/tenant/v1/tours/versions/{rid()}", "tenant_version_html", "tenant_web"),
    ("T5 tenant piece edit via portal BFF, markdown blog", "BFF->api-cis", "PATCH",
     f"{c.CIS_WEB}/api/tenant/v1/content-writing/pieces/{rid()}", "tenant_piece_markdown", "tenant_web"),
    ("C1 control: small HTML (< 8 KB) piece edit", "direct api-cis", "PATCH",
     f"{c.CIS_API}/v1/content-writing/pieces/{rid()}", "control_small_html", "tenant"),
    ("C2 control: large plain text (> 8 KB) piece edit", "direct api-cis", "PATCH",
     f"{c.CIS_API}/v1/content-writing/pieces/{rid()}", "control_large_plain", "tenant"),
    ("B1 Booking trip case notes PATCH", "direct api-booking", "PATCH",
     f"{c.BOOKING_API}/booking/trip-cases/TC-9{int(time.time()) % 100000:05d}", "booking_case_notes", "booking"),
    ("B2 Booking contract terms PATCH", "direct api-booking", "PATCH",
     f"{c.BOOKING_API}/booking/contracts/{rid()}", "booking_contract_terms", "booking"),
]

results = []
window_start = now()
for label, channel, method, url, key, client in plan:
    data = body_bytes(P[key])
    hdr = {"Content-Type": "application/json; charset=utf-8", "User-Agent": c.UA, "x-aa806-test": label.split()[0]}
    if client == "admin":
        r = adm.request(method, url, data=data, headers=hdr, timeout=60)
    elif client == "tenant_web":
        r = ten_web.request(method, url, data=data, headers=hdr, timeout=60)
    elif client == "tenant":
        r = c.requests.request(method, url, data=data, headers={**TH, **hdr}, timeout=60)
    else:
        r = c.requests.request(method, url, data=data, headers={**BH, **hdr}, timeout=60)
    path = url.split(".com", 1)[1]
    results.append({
        "id": label.split()[0], "label": label, "channel": channel, "method": method, "path": path,
        "body_bytes": len(data), "status": r.status_code, "response": r.text[:200], "at": now(),
    })
    print(label, len(data), r.status_code, r.text[:120])
    time.sleep(1)
window_end = now()

time.sleep(3)
after, _, _ = snapshot()
json.dump({
    "window_start_utc": window_start, "window_end_utc": window_end, "tour_id": TOUR_ID, "tenant": SLUG,
    "tenant_version_used": {"id": version["id"], "rewritten_content_bytes": len(body_bytes(version_content))},
    "requests": results, "hash_before": before, "hash_after": after,
    "unchanged": {k: before[k] == after[k] for k in before},
}, open(OUT, "w"), indent=2, ensure_ascii=False)
print(json.dumps({k: before[k] == after[k] for k in before}, indent=1))
print(window_start, window_end)
