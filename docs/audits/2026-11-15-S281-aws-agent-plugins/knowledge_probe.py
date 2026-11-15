"""Probe AWS Knowledge MCP over streamable HTTP: list tools, then ask 3 questions we already know answers to."""
import json, sys, urllib.request

URL = "https://knowledge-mcp.global.api.aws"
HDR = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
sid = None

def rpc(method, params=None, i=1, notify=False):
    global sid
    body = {"jsonrpc": "2.0", "method": method}
    if not notify: body["id"] = i
    if params is not None: body["params"] = params
    h = dict(HDR)
    if sid: h["Mcp-Session-Id"] = sid
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        sid = r.headers.get("Mcp-Session-Id") or sid
        raw = r.read().decode()
    if notify or not raw.strip(): return None
    if raw.lstrip().startswith("{"): return json.loads(raw)
    for line in raw.splitlines():
        if line.startswith("data:"):
            d = json.loads(line[5:]); 
            if "id" in d: return d
    return raw

init = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}})
print("server:", init.get("result", {}).get("serverInfo"))
rpc("notifications/initialized", notify=True)
tools = rpc("tools/list", {}, 2)["result"]["tools"]
print("tools:", [t["name"] for t in tools])
name = next(t["name"] for t in tools if "search_documentation" in t["name"])
schema = next(t for t in tools if t["name"] == name)["inputSchema"]
print("search schema keys:", list(schema.get("properties", {})))
qs = [
    "WAFv2 web ACL Description allowed characters pattern",
    "WAFAssociatedItemException delete web ACL associated with CloudFront distribution",
    "DeleteRole iam:ListInstanceProfilesForRole remove role from instance profile before delete",
]
key = "search_phrase" if "search_phrase" in schema.get("properties", {}) else list(schema["properties"])[0]
for n, q in enumerate(qs, 3):
    args = {key: q}
    if "limit" in schema.get("properties", {}): args["limit"] = 3
    r = rpc("tools/call", {"name": name, "arguments": args}, n)
    txt = json.dumps(r.get("result", r), ensure_ascii=False)
    print(f"\n### Q{n-2}: {q}\n{txt[:1500]}")
