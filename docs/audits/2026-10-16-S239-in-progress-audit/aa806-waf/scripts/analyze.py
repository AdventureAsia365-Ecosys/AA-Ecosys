"""Turn WAF Logs Insights raw results into a secret-free summary (no header values are kept)."""
import collections
import json
import re
import sys

AUD = sys.argv[1]
SENSITIVE = {"authorization", "x-admin-secret", "cookie", "x-api-key"}


def records(fn):
    for row in json.load(open(fn))["results"]:
        yield json.loads(next(f["value"] for f in row if f["field"] == "@message"))


def crs(m):
    rg = next((r for r in m.get("ruleGroupList") or [] if "CommonRuleSet" in r["ruleGroupId"]), {})
    term = (rg.get("terminatingRule") or {}).get("ruleId")
    nonterm = [x["ruleId"] for x in rg.get("nonTerminatingMatchingRules") or []]
    return term, nonterm


def summarize(m):
    term, nonterm = crs(m)
    hdr = {h["name"].lower(): h["value"] for h in m["httpRequest"]["headers"]}
    return {
        "time_ms": m["timestamp"], "method": m["httpRequest"]["httpMethod"], "uri": m["httpRequest"]["uri"],
        "action": m["action"], "terminatingRuleId": m["terminatingRuleId"],
        "crs_terminating_rule (BLOCK once enforced)": term,
        "crs_count_override_matches (stay COUNT)": nonterm,
        "labels": [l["name"] for l in m.get("labels") or []],
        "requestBodySize": m.get("requestBodySize"), "inspectedByWAF": m.get("requestBodySizeInspectedByWAF"),
        "user_agent": hdr.get("user-agent", "")[:40], "via_vercel_bff": "x-vercel-id" in hdr,
        "api_gw": hdr.get("x-amzn-apigateway-api-id"),
        "sensitive_headers_logged": sorted(SENSITIVE & set(hdr)),
    }


# 1. Test requests
tests = json.load(open(f"{AUD}/requests.json"))["requests"] + json.load(open(f"{AUD}/requests-controls.json"))["requests"]
logs = {summarize(m)["uri"]: summarize(m) for fn in ("patch_raw.json", "controls_raw.json") for m in records(fn)}
rows = []
for t in tests:
    p = t["path"].replace("/api/tenant", "").replace("/api/admin", "/admin")
    w = logs.get(p)
    rows.append({**{k: t[k] for k in ("id", "label", "path", "body_bytes", "status")}, "waf": w})
json.dump(rows, open(f"{AUD}/waf-matches-test.json", "w"), indent=2, ensure_ascii=False)

# 2. Whole count window before the test (14/10 00:00Z -> 16/10 04:01Z)
win = [summarize(m) for m in records("window_raw.json")]
total = int(json.load(open("window_total.json"))["results"][0][0]["value"])
by_rule = collections.Counter()
by_rule_uri = collections.Counter()
for w in win:
    rules = ([w["crs_terminating_rule (BLOCK once enforced)"]] if w["crs_terminating_rule (BLOCK once enforced)"] else []) \
        + [f"{r} (count override)" for r in w["crs_count_override_matches (stay COUNT)"]]
    for r in rules:
        by_rule[r] += 1
        uri = re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27}", "{uuid}", w["uri"])
        by_rule_uri[(r, w["method"], uri, w["api_gw"] or "-", "bff" if w["via_vercel_bff"] else w["user_agent"][:25])] += 1
json.dump({
    "window": "2026-10-14T00:00Z .. 2026-10-16T04:01Z (before the test)", "requests_logged": total,
    "requests_with_crs_label": len(win), "by_rule": by_rule.most_common(),
    "by_rule_method_uri_apigw_client": [list(k) + [v] for k, v in by_rule_uri.most_common()],
}, open(f"{AUD}/waf-matches-count-window.json", "w"), indent=2, ensure_ascii=False)

for r in rows:
    w = r["waf"] or {}
    print(r["id"], r["status"], r["body_bytes"], w.get("crs_terminating_rule (BLOCK once enforced)"),
          w.get("crs_count_override_matches (stay COUNT)"), w.get("sensitive_headers_logged"))
print(total, len(win), by_rule.most_common())
for k, v in by_rule_uri.most_common(40):
    print(v, k)
