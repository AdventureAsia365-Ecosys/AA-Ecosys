#!/usr/bin/env bash
# Install the pre-push hook of this repo (AA-993 H1): points git at the tracked .githooks/ directory and creates a
# small Python venv with the pinned lint dependencies (tools/docs + tools/contracts requirements.txt).
#
#   scripts/install-hooks.sh              install (idempotent; every worktree of this clone shares the setting)
#   scripts/install-hooks.sh --no-venv    only set core.hooksPath (use python3 / $AA_PREPUSH_PYTHON as is)
#   scripts/install-hooks.sh --uninstall  git config --unset core.hooksPath (the venv is left; delete it by hand)
#
# The venv lives in the common git dir (<clone>/.git/aa-prepush/venv): never tracked, shared by worktrees.
# Optional binaries the hook uses when present: lychee (offline link check), gitleaks (secret scan of pushed commits);
# markdownlint-cli2 runs through npx (Node). Missing ones are skipped locally; CI runs them anyway.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
venv_dir="$(git rev-parse --path-format=absolute --git-common-dir)/aa-prepush/venv"

case "${1:-}" in
  --uninstall)
    git config --unset core.hooksPath || true
    echo "Removed core.hooksPath; git uses .git/hooks again. Venv left at $venv_dir"
    exit 0 ;;
  ""|--no-venv) ;;
  *) echo "usage: scripts/install-hooks.sh [--no-venv|--uninstall]" >&2; exit 2 ;;
esac

current=$(git config --get core.hooksPath || true)
if [ -n "$current" ] && [ "$current" != ".githooks" ]; then
  echo "core.hooksPath was '$current'; replacing it with .githooks"
fi
git config core.hooksPath .githooks
chmod +x .githooks/pre-push scripts/pre-push.sh
echo "core.hooksPath = .githooks"

if [ "${1:-}" != "--no-venv" ]; then
  # Recreate when pip is missing: a first `python3 -m venv` without python3-venv dies at ensurepip after it has
  # already created bin/python, and a plain existence test would then skip creation forever.
  if ! "$venv_dir/bin/python" -m pip --version >/dev/null 2>&1; then
    python3 -m venv --clear "$venv_dir" || { echo "python3 -m venv failed: sudo apt install python3-venv, then rerun" >&2; exit 1; }
  fi
  "$venv_dir/bin/python" -m pip install --quiet --disable-pip-version-check -r tools/docs/requirements.txt -r tools/contracts/requirements.txt
  echo "Python venv ready: $venv_dir"
fi

for b in npx lychee gitleaks; do
  if command -v "$b" >/dev/null 2>&1; then echo "found $b"; else echo "not found: $b (that check is skipped locally; CI still runs it)"; fi
done
echo "Versions CI uses: lychee 0.24.2 (https://github.com/lycheeverse/lychee/releases), gitleaks 8.30.1"
echo "(https://github.com/gitleaks/gitleaks/releases), markdownlint-cli2 0.23.2 through npx (Node.js)."
echo "Check the setup: scripts/pre-push.sh --self-test && scripts/pre-push.sh --plan"
