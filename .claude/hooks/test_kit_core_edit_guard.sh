#!/bin/bash
# Table test for kit-core-edit-guard.sh (AA-994, root ADR 0016 decision 8).
# Run: bash .claude/hooks/test_kit_core_edit_guard.sh   (exit 0 = all pass)
set -u
H="$(cd "$(dirname "$0")" && pwd)/kit-core-edit-guard.sh"
pass=0; fail=0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
W="$TMP/ws" # a workspace-shaped path; most cases need no files on disk
mkdir -p "$W/apps"

# t <want exit> <tool> <path> [cwd]
t() {
  local want=$1 tool=$2 path=$3 cwd=${4:-/}
  local got
  got=$(python3 -c '
import json, sys
tool, path, cwd = sys.argv[1:4]
key = "notebook_path" if tool == "NotebookEdit" else "file_path"
print(json.dumps({"tool_name": tool, "cwd": cwd, "tool_input": {key: path, "content": "x"}}))
' "$tool" "$path" "$cwd" | "$H" 2>"$TMP/err" >/dev/null; echo $?)
  if [ "$got" = "$want" ]; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "MISS want=$want got=$got :: $tool $path (cwd $cwd)"; fi
  if [ "$want" = 2 ] && [ "$got" = 2 ] && ! grep -q "edit the CIS canonical copy\|Edit the CIS canonical copy" "$TMP/err"; then
    fail=$((fail + 1)); echo "MISS message :: $path"
  fi
}

# Fixture repos: a CIS worktree outside apps/ (recognised by its origin) and a Booking repo.
git init -q "$TMP/cis-wt" && git -C "$TMP/cis-wt" remote add origin git@github.com:AdventureAsia365-Ecosys/AA-CIS-App.git
mkdir -p "$TMP/cis-wt/frontend/app/_kit/core" "$TMP/cis-wt/portal/app/_kit/core"
git init -q "$TMP/bk" && git -C "$TMP/bk" remote add origin https://github.com/AdventureAsia365-Ecosys/AA-Booking.git
mkdir -p "$TMP/bk/frontend/ui/core"

# --- blocked: vendored copies (2)
t 2 Edit "$W/apps/AA-Partner/portal/app/_kit/core/primitives.tsx"
t 2 Write "$W/apps/AA-Partner/web/app/_kit/core/tokens.css"
t 2 MultiEdit "$W/apps/AA-Booking/frontend/ui/core/DataTable.tsx"
t 2 Write "$W/apps/AA-TripPlanner-Web/frontend/ui/core/tokens.css"
t 2 NotebookEdit "$W/apps/AA-Booking/frontend/ui/core/notes.ipynb"
t 2 Write "$W/.tmp-session/wt/partner-x/portal/app/_kit/core/new-file.tsx"     # a new file in a consumer worktree
t 2 Edit "$TMP/bk/frontend/ui/core/theme.ts"                                     # consumer repo by origin
t 2 Edit "apps/AA-Booking/frontend/ui/core/brand.ts" "$W"                        # relative path, read against cwd
t 2 Edit "$W/apps/AA-CIS-App/portal/app/_kit/core/x.tsx"                         # CIS repo, but not frontend/
t 2 Edit "$TMP/cis-wt/portal/app/_kit/core/x.tsx"                                # CIS worktree, but not frontend/
t 2 Edit "$W/apps/AA-CIS-App/frontend/app/_kit/core/../../../../../AA-Booking/frontend/ui/core/x.ts"  # .. escape
# --- allowed: the canonical CIS copy (0)
t 0 Edit "$W/apps/AA-CIS-App/frontend/app/_kit/core/primitives.tsx"
t 0 Write "$W/apps/AA-CIS-App/frontend/app/_kit/core/new/Gallery.tsx"
t 0 Edit "$TMP/cis-wt/frontend/app/_kit/core/tokens.css"                         # CIS worktree by origin
t 0 Edit "frontend/app/_kit/core/tokens.ts" "$TMP/cis-wt"                        # relative, inside CIS worktree
# --- allowed: unrelated paths and tools (0)
t 0 Edit "$W/apps/AA-Partner/portal/app/_kit/index.ts"
t 0 Edit "$W/apps/AA-Partner/portal/app/_kit/local/PortalShell.tsx"
t 0 Edit "$W/apps/AA-Booking/frontend/ui/booking/PageFrame.tsx"
t 0 Write "$W/docs/adr/0016-one-design-system-guarded-kit-copies.md"
t 0 Edit "$W/apps/AA-CIS-App/frontend/app/core/page.tsx"                         # `core/` without _kit/ or ui/
t 0 Edit "$W/apps/AA-Booking/frontend/myui/core/x.ts"                            # `myui` is not `ui`
t 0 Read "$W/apps/AA-Booking/frontend/ui/core/tokens.css"                        # reading a copy is fine
# --- malformed input passes
got=$(echo 'not json' | "$H" >/dev/null 2>&1; echo $?); if [ "$got" = 0 ]; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "MISS malformed input -> $got"; fi

echo "pass=$pass fail=$fail"; [ "$fail" = 0 ]
