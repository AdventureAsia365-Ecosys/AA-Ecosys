#!/bin/bash
# Offline test of tools/llm/anthropic_key_plug_in.sh (AA-1026): fake `aws` and `curl` on PATH, no network, no AWS.
# Run: bash tools/llm/test_anthropic_key_plug_in.sh
# Proves: the key never reaches argv (no `ps` / history exposure) nor the output; the secret holds exactly the key; the
# order is secret -> budget -> probe -> enable; a failed probe never enables; a malformed key writes nothing; no key file
# is left behind; --check writes nothing.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SCRIPT="$HERE/anthropic_key_plug_in.sh"
ROOT=$(cd "$HERE/../.." && pwd)
pass=0; fail=0
ok() { if eval "$2"; then pass=$((pass+1)); else fail=$((fail+1)); echo "MISS: $1"; fi; }

W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
mkdir -p "$W/bin"
# a made-up key, built at run time (no key-shaped literal in the repo)
KEY="sk-ant-$(printf 'test%.0s' {1..3})-$(printf 'Zq9%.0s' {1..25})"

cat >"$W/bin/aws" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
log = os.environ["FAKE_LOG"]
with open(log, "a") as f:
    f.write("aws " + json.dumps(a) + "\n")
def arg(name):
    return a[a.index(name) + 1] if name in a else None
if a[:2] == ["sts", "get-caller-identity"]:
    print("111122223333"); sys.exit(0)
if a[:2] == ["secretsmanager", "describe-secret"]:
    sid = arg("--secret-id")
    if sid == "aa-cis/dev/admin-secret" or (sid == "aa-llm/dev/anthropic-direct" and os.environ.get("FAKE_HAVE_SECRET")):
        print(sid); sys.exit(0)
    sys.stderr.write("ResourceNotFoundException\n"); sys.exit(254)
if a[:2] == ["secretsmanager", "get-secret-value"]:
    print("fake-admin-credential"); sys.exit(0)
if a[:2] in (["secretsmanager", "create-secret"], ["secretsmanager", "put-secret-value"]):
    src = arg("--secret-string")
    assert src.startswith("file://"), src
    path = src[len("file://"):]
    with open(path) as f:
        value = f.read()
    with open(os.environ["FAKE_STORE"], "w") as f:
        f.write(value)
    with open(log, "a") as f:
        f.write("mode %o\n" % (os.stat(path).st_mode & 0o777))
    print("ok"); sys.exit(0)
sys.stderr.write("unexpected aws call\n"); sys.exit(1)
EOF

cat >"$W/bin/curl" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
log = os.environ["FAKE_LOG"]
headers = []
i = 0
method, url, body = "GET", None, None
while i < len(a):
    if a[i] == "-X": method = a[i + 1]; i += 2; continue
    if a[i] == "-d": body = a[i + 1]; i += 2; continue
    if a[i] == "-H":
        h = a[i + 1]
        if h.startswith("@"):
            with open(h[1:]) as f:
                headers += [x.strip() for x in f if x.strip()]
        else:
            headers.append(h)
        i += 2; continue
    if a[i].startswith("http"): url = a[i]
    i += 1
with open(log, "a") as f:
    f.write("curl " + json.dumps(a) + "\n")
    f.write("call %s %s %s\n" % (method, url.split(".com", 1)[1], body or ""))
assert "X-Admin-Secret: fake-admin-credential" in headers, headers
path = url.split(".com", 1)[1]
code, out = 404, {"detail": "unexpected"}
if method == "GET" and path == "/admin/llm-connections":
    code, out = 200, {"connections": [{"connection_key": "anthropic-direct", "kind": "anthropic",
                                       "secret_name": os.environ.get("FAKE_SECRET_NAME", "aa-llm/dev/anthropic-direct"),
                                       "policy_problems": [], "enabled": False, "monthly_budget_usd": 150.0,
                                       "cost_policy": {"alert_pct": 80, "hard_stop": True}}]}
elif method == "PATCH" and path == "/admin/llm-connections/anthropic-direct":
    b = json.loads(body)
    code, out = 200, {"connection_key": "anthropic-direct", "enabled": bool(b.get("enabled")), "changed": True,
                      "changed_fields": sorted(b)}
elif method == "POST" and path == "/admin/llm-connections/anthropic-direct/test":
    ok = not os.environ.get("FAKE_PROBE_FAIL")
    code, out = 200, {"model_key": "haiku-5-5", "wire_id": "claude-haiku-5-5", "ok": ok, "reply_usable": ok,
                      "error_class": None if ok else "access_denied", "cost_usd": 0.00001 if ok else 0.0,
                      "latency_ms": 420}
sys.stdout.write(json.dumps(out))
sys.stderr.write(str(code))
EOF
chmod +x "$W/bin/aws" "$W/bin/curl"

run() {  # run <name> <stdin-string> <args...>
  local name=$1 input=$2; shift 2
  : >"$W/$name.log"; rm -f "$W/$name.store"
  printf '%s\n' "$input" | env PATH="$W/bin:$PATH" FAKE_LOG="$W/$name.log" FAKE_STORE="$W/$name.store" \
    bash "$SCRIPT" "$@" >"$W/$name.out" 2>&1
  echo $? >"$W/$name.rc"
}
leftover() { ls "$ROOT/.tmp-session"/anthropic-key.* 2>/dev/null | wc -l; }

# 1. the happy path
run apply "$KEY" --apply
ok "apply exits 0" '[ "$(cat "$W/apply.rc")" = 0 ]'
ok "secret holds exactly the key" '[ "$(cat "$W/apply.store")" = "$KEY" ]'
ok "key file was mode 600" 'grep -q "^mode 600$" "$W/apply.log"'
ok "key never in argv" '! grep -qF -- "$KEY" "$W/apply.log"'
ok "key never in output" '! grep -qF -- "$KEY" "$W/apply.out"'
ok "admin credential never in argv" '! grep -q "fake-admin-credential" <(grep "^curl " "$W/apply.log")'
ok "created (no secret yet)" 'grep -q "\"create-secret\"" "$W/apply.log"'
order() {  # the write steps of a run, in order
  grep -E '"(create-secret|put-secret-value)"|^call (PATCH|POST)' "$1" | sed -E \
    -e 's/^aws .*/secret/' -e 's/^call PATCH .*monthly_budget_usd.*/budget/' -e 's/^call POST .*/probe/' \
    -e 's/^call PATCH .*"enabled".*/enable/' | tr '\n' ' '
}
ok "order secret, budget, probe, enable" '[ "$(order "$W/apply.log")" = "secret budget probe enable " ]'
ok "budget 150 USD hard stop" 'grep -q "\"monthly_budget_usd\": 150, \"budget_hard_stop\": true" "$W/apply.log"'
ok "no key file left" '[ "$(leftover)" = 0 ]'

# 2. an existing secret gets a new version
FAKE_HAVE_SECRET=1 run put "$KEY" --apply
ok "put-secret-value when the secret exists" 'grep -q "\"put-secret-value\"" "$W/put.log" && ! grep -q "\"create-secret\"" "$W/put.log"'

# 3. a failed probe never enables
FAKE_PROBE_FAIL=1 run probe_fail "$KEY" --apply
ok "probe failure exits 1" '[ "$(cat "$W/probe_fail.rc")" = 1 ]'
ok "probe failure does not enable" '! grep -q "enabled" <(grep "^call PATCH" "$W/probe_fail.log")'
ok "probe failure names the class" 'grep -q "access_denied" "$W/probe_fail.out"'

# 4. malformed keys write nothing
for bad in "not-a-key" "$KEY$KEY" "$KEY extra" "sk-ant-short"; do
  run bad "$bad" --apply
  ok "malformed key refused (${#bad} chars)" '[ "$(cat "$W/bad.rc")" = 1 ] && [ ! -e "$W/bad.store" ] && ! grep -q "^call PATCH" "$W/bad.log"'
  ok "malformed key not echoed" '! grep -qF -- "$bad" "$W/bad.out" || [ "$bad" = "not-a-key" ]'
done

# 5. --check writes nothing
run check "" --check
ok "check exits 0" '[ "$(cat "$W/check.rc")" = 0 ]'
ok "check writes nothing" '! grep -qE "create-secret|put-secret-value|^call (PATCH|POST)" "$W/check.log"'

# 6. a connection pointing at another secret is refused before any write
FAKE_SECRET_NAME=aa-llm/dev/other run other "$KEY" --apply
ok "wrong secret name refused" '[ "$(cat "$W/other.rc")" = 1 ] && [ ! -e "$W/other.store" ]'

ok "no key file left at the end" '[ "$(leftover)" = 0 ]'
echo "pass=$pass fail=$fail"
[ "$fail" = 0 ]
