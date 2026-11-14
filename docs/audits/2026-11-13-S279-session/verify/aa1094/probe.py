"""AA-1094 S279 live probe: browse Lambda tenant routes through API Gateway (edge key on stdin, never printed/saved)."""
import json, sys, urllib.request, urllib.error

BASE = "https://9vqkfbukvh.execute-api.us-west-1.amazonaws.com"
OUT = sys.argv[1]
edge = sys.stdin.read().strip()


def get(path):
    req = urllib.request.Request(BASE + path, headers={"x-tripplanner-key": edge, "user-agent": "aa-verify-s279"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            st, body = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        st, body = e.code, e.read().decode()
    try:
        j = json.loads(body)
    except ValueError:
        j = body[:300]
    return st, j


def keys_deep(o, acc=None):
    acc = set() if acc is None else acc
    if isinstance(o, dict):
        for k, v in o.items():
            acc.add(k)
            keys_deep(v, acc)
    elif isinstance(o, list):
        for v in o:
            keys_deep(v, acc)
    return acc


out = {}


def rec(name, path):
    st, j = get(path)
    out[name] = {"path": path, "status": st, "body": j}
    print(name, path, st, json.dumps(j)[:400])
    return st, j


def items(j):
    if isinstance(j, dict):
        for k in ("tours", "items", "results"):
            if isinstance(j.get(k), list):
                return j[k]
    return []


rec("a_tenant", "/browse/tenant/audit-atlas-hearth")
st, j = rec("b_tours", "/browse/tenant/audit-atlas-hearth/tours?limit=60")
lst = items(j)
off = 60
while isinstance(j, dict) and j.get("total") and off < j["total"]:
    _, j2 = rec(f"b_tours_{off}", f"/browse/tenant/audit-atlas-hearth/tours?limit=60&offset={off}")
    lst += items(j2); off += 60
summary = {"b_source": j.get("source") if isinstance(j, dict) else None,
           "b_total": j.get("total") if isinstance(j, dict) else None,
           "b_count": len(lst),
           "b_source_ids": [t.get("source_id") for t in lst],
           "b_slugs": [t.get("slug") for t in lst]}
if lst:
    slug = lst[0].get("slug")
    st, d = rec("c_detail", f"/browse/tenant/audit-atlas-hearth/tours/{slug}")
    ks = keys_deep(d)
    summary["c_price_keys"] = sorted(k for k in ks if "price" in k.lower())
    summary["c_contract"] = d.get("contract") if isinstance(d, dict) else None
    t = d.get("tenant") if isinstance(d, dict) else None
    summary["c_tenant_slug"] = t.get("slug") if isinstance(t, dict) else None
st, aa = rec("d_aa_tours", "/browse/tenant/aa-tripplanner/tours?limit=5")
st, cat = rec("d_catalog_tours", "/browse/catalog/tours?limit=5")
summary["d_aa_source"] = aa.get("source") if isinstance(aa, dict) else None
summary["d_aa_total"] = aa.get("total") if isinstance(aa, dict) else None
summary["d_catalog_total"] = cat.get("total") if isinstance(cat, dict) else None
aa_items = items(aa)
if aa_items:
    s = aa_items[0].get("slug")
    summary["d_aa_slug"] = s
    st, _ = rec("d_aa_detail", f"/browse/tenant/aa-tripplanner/tours/{s}")
    summary["d_aa_detail_status"] = st
for slug in ("audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel", "audit-harbour-lights", "audit-sen-vang"):
    st, j = rec(f"e_{slug}", f"/browse/tenant/{slug}/tours?limit=5")
    summary[f"e_{slug}"] = {"status": st, "source": j.get("source") if isinstance(j, dict) else None,
                            "total": j.get("total") if isinstance(j, dict) else None,
                            "error": j.get("error") if isinstance(j, dict) else None}
out["summary"] = summary
print(json.dumps(summary, indent=2))
assert edge not in json.dumps(out)
json.dump(out, open(OUT, "w"), indent=2)
