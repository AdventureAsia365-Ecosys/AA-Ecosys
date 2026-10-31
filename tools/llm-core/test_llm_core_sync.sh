#!/bin/bash
# Fixture test for the root wrapper tools/llm-core/llm-core-sync.sh (AA-642 S8). No network, no real app checkout.
# Run: bash tools/llm-core/test_llm_core_sync.sh   (exit 0 = all pass). It runs the wrapper, so it needs AA-CIS-App
# .github/scripts/llm-core-sync.sh in the workspace (or on its origin/main), or LLM_CORE_SYNC_IMPL=<a CIS worktree>/...
# The copy itself is tested in AA-CIS-App (tests/unit/test_aa642_s8_llm_core_sync.py); this checks the wrapper wiring.
set -u
S="$(cd "$(dirname "$0")" && pwd)/llm-core-sync.sh"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass=0; fail=0
ok() { pass=$((pass + 1)); }
miss() { fail=$((fail + 1)); echo "MISS: $*"; }
g() { git -C "$TMP/ws/apps/AA-CIS-App" -c user.name=t -c user.email=t@t -c commit.gpgsign=false "$@"; }

# Workspace fixture: a CIS repo with a two-file core and its manifest, and both consumer checkouts.
core="$TMP/ws/apps/AA-CIS-App/shared/aa_llm"
mkdir -p "$core" "$TMP/ws/apps/AA-TripPlanner-Web/backend" "$TMP/ws/apps/AA-Partner/api/app"
printf 'X = 1\n' > "$core/__init__.py"
cat > "$core/check_copy.py" <<'PY'
import hashlib, json, sys
from pathlib import Path
here = Path(__file__).resolve().parent
m = json.loads((here / "MANIFEST.json").read_text())["files"]
bad = [f for f, v in m.items() if hashlib.sha256((here / f).read_bytes()).hexdigest() != v["sha256"]]
print("\n".join(bad), file=sys.stderr)
sys.exit(1 if bad else 0)
PY
python3 - "$core" <<'PY'
import hashlib, json, os, sys
c = sys.argv[1]
files = {f: {"sha256": hashlib.sha256(open(os.path.join(c, f), "rb").read()).hexdigest()}
         for f in sorted(os.listdir(c)) if f != "MANIFEST.json"}
json.dump({"name": "aa_llm", "files": files}, open(os.path.join(c, "MANIFEST.json"), "w"), indent=2)
PY
git -c init.defaultBranch=main init -q "$TMP/ws/apps/AA-CIS-App"
g add -A && g commit -qm core && g update-ref refs/remotes/origin/main HEAD

run() { AA_WORKSPACE="$TMP/ws" bash "$S" "$@" --cis "$TMP/ws/apps/AA-CIS-App" >"$TMP/o" 2>&1; }

if AA_WORKSPACE="$TMP/ws" bash "$S" --list >"$TMP/o" 2>&1 && grep -q "^tripplanner" "$TMP/o" && grep -q "^crm" "$TMP/o"; then ok; else miss "--list"; cat "$TMP/o"; fi
if run tripplanner --no-fetch && [ -f "$TMP/ws/apps/AA-TripPlanner-Web/backend/aa_llm/__init__.py" ] \
   && grep -q "\"ref\": \"$(g rev-parse HEAD)\"" "$TMP/ws/apps/AA-TripPlanner-Web/backend/aa_llm.lock.json"; then ok
else miss "sync tripplanner"; cat "$TMP/o"; fi
if run crm --no-fetch --dry-run && [ ! -e "$TMP/ws/apps/AA-Partner/api/app/aa_llm" ]; then ok; else miss "dry run crm"; cat "$TMP/o"; fi
printf 'X = 2\n' > "$core/__init__.py"
if run crm --from-local; then miss "stale manifest accepted"; elif grep -q "MANIFEST.json" "$TMP/o"; then ok; else miss "stale manifest message"; cat "$TMP/o"; fi

echo "llm-core-sync wrapper: $pass passed, $fail failed"
[ "$fail" = 0 ]
