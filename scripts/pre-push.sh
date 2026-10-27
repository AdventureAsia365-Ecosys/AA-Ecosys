#!/usr/bin/env bash
# Pre-push checks for the AA-Ecosys root repo (AA-993 H1, ADR draft D5).
#
# Runs the same commands as this repo's CI before a push, so a red CI run is caught locally:
#   - .github/workflows/docs-lint.yml : lint-tool unit tests, front-matter, PRD refs, ADR index, single-line AWS CLI,
#     alarm runbook links, literal resource IDs (warn-only), markdownlint-cli2 0.23.2, lychee offline links;
#   - .github/workflows/contracts.yml : contract/ADR unit tests, check_contracts.py, check_adr_numbers.py;
#   - .github/workflows/secret-scan.yml: gitleaks on the pushed commits, only when a `gitleaks` binary is on PATH
#     (local convenience; CI keeps its own pull_request_target job, so --ci never runs it).
# Every command below is copied from those workflow files. When a workflow step changes, change it here too.
#
# Modes:
#   (default)  fast: only the checks whose workflow path filter matches `git diff --name-only <base>...HEAD`
#              (base: origin/master, or $AA_PREPUSH_BASE). Lint-tool unit tests run only when their tool dir
#              changed; markdownlint runs on the changed docs/**/*.md files only. Missing optional binaries
#              (lychee, gitleaks) are skipped with a note: CI still runs them.
#   --full     every check on the whole repo, as CI runs it (also: AA_PREPUSH=full).
#   --ci       reserved for H2 (CI calls `scripts/pre-push.sh --full --ci`): never skips by diff, a missing tool
#              is a failure, no gitleaks (CI has its own job), ADR numbers use $BASE_SHA like contracts.yml.
#   --hook     set by .githooks/pre-push: reads git's pre-push lines from stdin (deleted refs are skipped).
#   --self-test runs the check-selection logic on fixture diffs; no tool is invoked.
#   --plan     print the checks fast mode would run for the current diff, run nothing.
#
# Install: scripts/install-hooks.sh. Bypass one push: git push --no-verify. Remove: git config --unset core.hooksPath.
set -uo pipefail

MODE=fast
CI_MODE=0
HOOK=0
PLAN_ONLY=0
SELF_TEST=0
[ "${AA_PREPUSH:-}" = "full" ] && MODE=full
while [ $# -gt 0 ]; do
  case "$1" in
    --full) MODE=full ;;
    --ci) CI_MODE=1; MODE=full ;;
    --hook) HOOK=1 ;;
    --plan) PLAN_ONLY=1 ;;
    --self-test) SELF_TEST=1 ;;
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
    *) # git passes <remote name> <remote url> to the hook
      [ "$HOOK" = 1 ] || { echo "pre-push: unknown option $1 (see --help)" >&2; exit 2; } ;;
  esac
  shift
done

MDL_VERSION=0.23.2 # docs-lint.yml: markdownlint-cli2-action v24.2.0 pins markdownlint-cli2 0.23.2

# --- check selection (pure: file list on stdin -> check ids on stdout) -------------------------------------------
# Path filters copied from the workflows' `on.pull_request.paths`. In a bash `case` pattern `*` also matches `/`,
# so `docs/*` is `docs/**` and `.claude/*.md` is `.claude/**/*.md`.
is_docs_lint_path() {
  case "$1" in
    docs/*|skill/*|.kiro/steering/*|.claude/*.md|tools/docs/*|.markdownlint-cli2.jsonc|.github/workflows/docs-lint.yml) return 0 ;;
  esac
  return 1
}
is_contracts_path() {
  case "$1" in
    docs/contracts/*|docs/adr/*|tools/contracts/*|tools/adr/*|.github/workflows/contracts.yml) return 0 ;;
  esac
  return 1
}

# plan_checks <fast|full> <ci 0|1>: reads changed paths (one per line) on stdin, prints the check ids in run order.
plan_checks() {
  local mode="$1" ci="$2" f docs=0 contracts=0 docs_unit=0 contracts_unit=0 adr_unit=0 md=0
  if [ "$mode" = full ]; then
    docs=1; contracts=1; docs_unit=1; contracts_unit=1; adr_unit=1; md=1
  else
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      if is_docs_lint_path "$f"; then docs=1; fi
      if is_contracts_path "$f"; then contracts=1; fi
      case "$f" in
        tools/docs/*|.github/workflows/docs-lint.yml) docs_unit=1 ;;
        tools/contracts/*) contracts_unit=1 ;;
        tools/adr/*) adr_unit=1 ;;
        .github/workflows/contracts.yml) contracts_unit=1; adr_unit=1 ;;
      esac
      case "$f" in docs/*.md|.markdownlint-cli2.jsonc|.github/workflows/docs-lint.yml) md=1 ;; esac
    done
  fi
  if [ "$docs" = 1 ]; then
    [ "$docs_unit" = 1 ] && echo docs-unit
    echo frontmatter; echo prd-refs; echo adr-index; echo aws-multiline; echo alarm-runbooks; echo resource-ids
    [ "$md" = 1 ] && echo markdownlint
    echo lychee
  fi
  if [ "$contracts" = 1 ]; then
    [ "$contracts_unit" = 1 ] && echo contracts-unit
    [ "$adr_unit" = 1 ] && echo adr-unit
    echo contracts; echo adr-numbers
  fi
  [ "$ci" = 1 ] || echo gitleaks
}

# markdownlint targets in fast mode: changed docs/**/*.md that still exist (the config's ignores still apply);
# the whole glob when the config or the workflow changed.
md_targets() {
  local f all=0 out=()
  while IFS= read -r f; do
    case "$f" in .markdownlint-cli2.jsonc|.github/workflows/docs-lint.yml) all=1 ;; docs/*.md) [ -f "$f" ] && out+=("$f") ;; esac
  done
  if [ "$all" = 1 ]; then echo 'docs/**/*.md'; else printf '%s\n' "${out[@]+"${out[@]}"}"; fi
}

# --- self-test -------------------------------------------------------------------------------------------------
self_test() {
  local fails=0 n=0
  expect() { # expect <name> <mode> <ci> <expected ids, space separated> <files...>
    local name="$1" mode="$2" ci="$3" want="$4" got; shift 4
    n=$((n + 1))
    got=$(printf '%s\n' "$@" | plan_checks "$mode" "$ci" | tr '\n' ' ' | sed 's/ $//')
    if [ "$got" = "$want" ]; then echo "ok   $name"; else echo "FAIL $name"; echo "     want: $want"; echo "     got:  $got"; fails=$((fails + 1)); fi
  }
  local DOCS="frontmatter prd-refs adr-index aws-multiline alarm-runbooks resource-ids"
  local ALL="docs-unit $DOCS markdownlint lychee contracts-unit adr-unit contracts adr-numbers"
  expect "empty diff"                     fast 0 "gitleaks" ""
  expect "README only"                    fast 0 "gitleaks" README.md
  expect "settings.json is not docs"      fast 0 "gitleaks" .claude/settings.json
  expect "catalog page"                   fast 0 "$DOCS markdownlint lychee gitleaks" docs/README.md
  expect "journal page (lint ignores it)" fast 0 "$DOCS markdownlint lychee gitleaks" docs/sessions/2026-10-27-x.md
  expect "skill file: no markdownlint"    fast 0 "$DOCS lychee gitleaks" skill/aa-ship/SKILL.md
  expect "nested .claude md"              fast 0 "$DOCS lychee gitleaks" .claude/agents/reviewer.md
  expect "steering"                       fast 0 "$DOCS lychee gitleaks" .kiro/steering/db-schema.md
  expect "ADR: docs + contracts"          fast 0 "$DOCS markdownlint lychee contracts adr-numbers gitleaks" docs/adr/0016-deploy-any-time.md
  expect "contract json"                  fast 0 "$DOCS lychee contracts adr-numbers gitleaks" docs/contracts/crm.ops.v1.json
  expect "docs tool: its unit tests"      fast 0 "docs-unit $DOCS lychee gitleaks" tools/docs/docslib.py
  expect "adr tool: its unit tests"       fast 0 "adr-unit contracts adr-numbers gitleaks" tools/adr/check_adr_numbers.py
  expect "contracts tool"                 fast 0 "contracts-unit contracts adr-numbers gitleaks" tools/contracts/check_contracts.py
  expect "contracts workflow"             fast 0 "contracts-unit adr-unit contracts adr-numbers gitleaks" .github/workflows/contracts.yml
  expect "docs-lint workflow"             fast 0 "docs-unit $DOCS markdownlint lychee gitleaks" .github/workflows/docs-lint.yml
  expect "markdownlint config"            fast 0 "$DOCS markdownlint lychee gitleaks" .markdownlint-cli2.jsonc
  expect "untracked-by-CI tools"          fast 0 "gitleaks" tools/finops/monthly_cost_report.py scripts/pre-push.sh
  expect "full ignores the diff"          full 0 "$ALL gitleaks" README.md
  expect "ci: all checks, no gitleaks"    full 1 "$ALL" ""
  # markdownlint target selection
  n=$((n + 1))
  local got
  got=$(printf '%s\n' docs/README.md skill/x.md docs/no-such-file.md | md_targets | tr '\n' ' ')
  if [ "$got" = "docs/README.md " ]; then echo "ok   md targets: existing changed docs pages"; else echo "FAIL md targets: got '$got'"; fails=$((fails + 1)); fi
  n=$((n + 1))
  got=$(printf '%s\n' docs/README.md .markdownlint-cli2.jsonc | md_targets)
  if [ "$got" = 'docs/**/*.md' ]; then echo "ok   md targets: config change lints everything"; else echo "FAIL md targets (config): got '$got'"; fails=$((fails + 1)); fi
  echo "self-test: $((n - fails))/$n passed"
  [ "$fails" = 0 ]
}

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "pre-push: not in a git repo" >&2; exit 2; }
cd "$ROOT" || exit 2

if [ "$SELF_TEST" = 1 ]; then self_test; exit $?; fi

# --- hook input: skip pure deletions, warn when the pushed commit is not the checked-out one -------------------
if [ "$HOOK" = 1 ] && [ ! -t 0 ]; then
  head_sha=$(git rev-parse HEAD)
  any=0
  while read -r _lref lsha _rref _rsha; do
    [ -n "${lsha:-}" ] || continue
    case "$lsha" in *[!0]*) ;; *) continue ;; esac # all zeros: a deleted ref, nothing to check
    any=1
    [ "$lsha" = "$head_sha" ] || echo "pre-push: note: pushing ${_lref} (${lsha:0:12}), but the checks run on the checked-out tree (HEAD ${head_sha:0:12})."
  done
  [ "$any" = 1 ] || exit 0
fi

# --- changed files ---------------------------------------------------------------------------------------------
BASE="${AA_PREPUSH_BASE:-origin/master}"
CHANGED=""
if [ "$MODE" = fast ]; then
  if git rev-parse -q --verify "$BASE^{commit}" >/dev/null; then
    CHANGED=$(git diff --name-only "$BASE...HEAD")
  else
    echo "pre-push: $BASE not found (git fetch origin?); running every check."
    MODE=full
  fi
fi
if [ "$MODE" = fast ] && [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "pre-push: note: uncommitted changes; the checks read the working tree, not only the pushed commits."
fi

PLAN=$(printf '%s\n' "$CHANGED" | plan_checks "$MODE" "$CI_MODE")
if [ "$PLAN_ONLY" = 1 ]; then echo "mode: $MODE$([ "$CI_MODE" = 1 ] && echo ' (ci)')"; echo "$PLAN"; exit 0; fi

# --- tools -----------------------------------------------------------------------------------------------------
# Python: the venv scripts/install-hooks.sh creates (pins of tools/docs + tools/contracts requirements.txt), shared
# by every worktree through the common git dir; else $AA_PREPUSH_PYTHON; else python3 (CI: setup-python 3.12).
VENV_PY="$(git rev-parse --path-format=absolute --git-common-dir)/aa-prepush/venv/bin/python"
if [ -n "${AA_PREPUSH_PYTHON:-}" ]; then PY="$AA_PREPUSH_PYTHON"
elif [ "$CI_MODE" = 0 ] && [ -x "$VENV_PY" ]; then PY="$VENV_PY"
else PY=$(command -v python3 || command -v python); fi
PY_DEPS_OK=1
"$PY" -c 'import jsonschema, referencing, yaml' 2>/dev/null || PY_DEPS_OK=0

declare -a FAILED=() SKIPPED=() WARNED=()
TOTAL_START=$(date +%s%N)

# run_check <id> <workflow step> <needs: py-deps|bin:<name>|-> <command...>
run_check() {
  local id="$1" step="$2" needs="$3"; shift 3
  local shown="$*" t0 t1 rc
  case "$needs" in
    py-deps)
      if [ "$PY_DEPS_OK" = 0 ]; then
        echo "FAIL $id: Python deps missing for $PY (jsonschema, referencing, PyYAML)."
        echo "     fix: scripts/install-hooks.sh   (or: $PY -m pip install -r tools/docs/requirements.txt -r tools/contracts/requirements.txt)"
        FAILED+=("$id|$step|$shown"); return
      fi ;;
    bin:*)
      local bin="${needs#bin:}"
      if ! command -v "$bin" >/dev/null 2>&1; then
        if [ "$CI_MODE" = 1 ]; then echo "FAIL $id: '$bin' not installed"; FAILED+=("$id|$step|$shown"); else
          echo "skip $id: '$bin' not on PATH (CI still runs it: $step)"; SKIPPED+=("$id"); fi
        return
      fi ;;
  esac
  echo "---- $id ($step)"
  echo "     \$ $shown"
  t0=$(date +%s%N)
  "$@"
  rc=$?
  t1=$(date +%s%N)
  if [ "$rc" = 0 ]; then echo "ok   $id ($(( (t1 - t0) / 1000000 )) ms)"
  else echo "FAIL $id (exit $rc, $(( (t1 - t0) / 1000000 )) ms)"; FAILED+=("$id|$step|$shown"); fi
}

run_planned() {
  local id
  for id in $PLAN; do
    case "$id" in
      docs-unit) run_check "$id" "docs-lint.yml: Unit tests of the lint tools" py-deps "$PY" -m unittest discover -s tools/docs -p 'test_*.py' ;;
      frontmatter) run_check "$id" "docs-lint.yml: Front-matter schema" py-deps "$PY" tools/docs/check_frontmatter.py ;;
      prd-refs) run_check "$id" "docs-lint.yml: PRD references" py-deps "$PY" tools/docs/check_prd_refs.py ;;
      adr-index) run_check "$id" "docs-lint.yml: ADR status and index" - "$PY" tools/docs/check_adr_index.py docs/adr ;;
      aws-multiline) run_check "$id" "docs-lint.yml: Single-line AWS CLI" - "$PY" tools/docs/check_docs_text.py aws-multiline ;;
      alarm-runbooks) run_check "$id" "docs-lint.yml: Alarm runbook links" - "$PY" tools/docs/check_alarm_runbooks.py ;;
      resource-ids)
        # warn-only in CI too: print a one-line count, never fail
        local out
        out=$("$PY" tools/docs/check_docs_text.py resource-ids --mode warn 2>&1 | tail -1)
        echo "warn resource-ids (warn-only, as in CI): $out"; WARNED+=("$id") ;;
      markdownlint)
        local -a targets=()
        if [ "$MODE" = full ]; then targets=('docs/**/*.md'); else mapfile -t targets < <(printf '%s\n' "$CHANGED" | md_targets); fi
        if [ "${#targets[@]}" = 0 ] || [ -z "${targets[0]}" ]; then echo "skip markdownlint: no changed docs page left"; SKIPPED+=("$id"); continue; fi
        run_check "$id" "docs-lint.yml: Markdown style" bin:npx npx --yes "markdownlint-cli2@$MDL_VERSION" "${targets[@]}" ;;
      lychee)
        run_check "$id" "docs-lint.yml: Internal links (offline)" bin:lychee lychee --config tools/docs/lychee.toml --exclude-path docs/linear-export 'docs/**/*.md' ;;
      contracts-unit) run_check "$id" "contracts.yml: Unit tests of the checks" py-deps "$PY" -m unittest discover -s tools/contracts -p 'test_*.py' ;;
      adr-unit) run_check "$id" "contracts.yml: Unit tests of the checks" - "$PY" -m unittest discover -s tools/adr -p 'test_*.py' ;;
      contracts) run_check "$id" "contracts.yml: Contracts, samples and field policy" py-deps "$PY" tools/contracts/check_contracts.py ;;
      adr-numbers)
        if [ "$CI_MODE" = 1 ]; then
          if [ -n "${BASE_SHA:-}" ]; then run_check "$id" "contracts.yml: ADR numbers" - "$PY" tools/adr/check_adr_numbers.py --base "$BASE_SHA"
          else run_check "$id" "contracts.yml: ADR numbers" - "$PY" tools/adr/check_adr_numbers.py; fi
        elif git rev-parse -q --verify "$BASE^{commit}" >/dev/null; then
          run_check "$id" "contracts.yml: ADR numbers" - "$PY" tools/adr/check_adr_numbers.py --base "$BASE"
        else run_check "$id" "contracts.yml: ADR numbers" - "$PY" tools/adr/check_adr_numbers.py; fi ;;
      gitleaks)
        local range="$BASE..HEAD"
        git rev-parse -q --verify "$BASE^{commit}" >/dev/null || range="-1 HEAD"
        run_check "$id" "secret-scan.yml: gitleaks (local copy)" bin:gitleaks gitleaks git . --log-opts="--no-renames $range" -c .gitleaks.toml -i .gitleaksignore --redact --no-banner ;;
    esac
  done
}

echo "pre-push ($MODE$([ "$CI_MODE" = 1 ] && echo ', ci'); base $BASE): $(printf '%s\n' "$PLAN" | grep -c . ) check(s)"
if [ -z "$PLAN" ]; then echo "pre-push: nothing to check."; exit 0; fi
run_planned
TOTAL_MS=$(( ($(date +%s%N) - TOTAL_START) / 1000000 ))

echo
if [ "${#FAILED[@]}" = 0 ]; then
  echo "pre-push: all checks passed in ${TOTAL_MS} ms${SKIPPED[*]:+ (skipped: ${SKIPPED[*]})}."
  exit 0
fi
echo "pre-push: ${#FAILED[@]} check(s) failed in ${TOTAL_MS} ms. The push is blocked."
for entry in "${FAILED[@]}"; do
  IFS='|' read -r id step cmd <<<"$entry"
  echo "  FAIL $id   [CI: $step]"
  echo "       command: $cmd"
done
echo "Fix and push again; the whole CI-equivalent run is: scripts/pre-push.sh --full"
echo "To push anyway (CI will still run these checks): git push --no-verify"
exit 1
