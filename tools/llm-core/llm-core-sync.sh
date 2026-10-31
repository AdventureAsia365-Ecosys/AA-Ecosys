#!/usr/bin/env bash
# Copy the shared AI gateway core of AA-CIS-App (shared/aa_llm/) into one consumer app and rewrite its
# aa_llm.lock.json (AA-642 S8, root ADR 0009 decision 13). Agent tool: it writes files in the consumer checkout and
# stops; committing, pushing and the PR stay with the caller.
#
# Usage:
#   tools/llm-core/llm-core-sync.sh <consumer> [--from-local] [--ref <git-ref>] [--cis <path>] [--dest-repo <path>]
#                                              [--no-fetch] [--dry-run]
#   tools/llm-core/llm-core-sync.sh --list
# Consumers: tripplanner (AA-TripPlanner-Web backend/aa_llm), crm (AA-Partner api/app/aa_llm).
#
# A wrapper, like tools/kit/kit-sync.sh: the copy code lives in AA-CIS-App `.github/scripts/llm-core-sync.sh`, the same
# file the CIS Llm Core Sync bot and Llm Core Consumers check run, so a hand sync and a bot sync cannot differ.
# Options, consumers, the lock format and the exit codes are that script's (run with --help).
#
# Which copy of the script runs: $LLM_CORE_SYNC_IMPL when set (a CIS worktree's file, for a try-out), else
# <workspace>/apps/AA-CIS-App/.github/scripts/llm-core-sync.sh, else that checkout's `origin/main` version. <workspace>
# is the main checkout of the root repo. Defaults: --cis is $AA_WORKSPACE/apps/AA-CIS-App (or
# <workspace>/apps/AA-CIS-App), --dest-repo is <that workspace>/apps/<repo>.
set -euo pipefail

die() { echo "llm-core-sync: $*" >&2; exit 2; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
common=$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
  || die "cannot find the root repo from $script_dir"
real_ws=$(dirname "$common")
ws=${AA_WORKSPACE:-$real_ws}
canon_cis=$real_ws/apps/AA-CIS-App
rel=.github/scripts/llm-core-sync.sh

impl=${LLM_CORE_SYNC_IMPL:-$canon_cis/$rel}
if [ ! -f "$impl" ]; then
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  git -C "$canon_cis" show "origin/main:$rel" > "$tmp/llm-core-sync.sh" 2>/dev/null \
    || die "AA-CIS-App $rel not found in $canon_cis (working tree or origin/main); pull AA-CIS-App main (AA-642 S8)"
  impl=$tmp/llm-core-sync.sh
fi

has_cis=0
for a in "$@"; do [ "$a" = --cis ] && has_cis=1; done
extra=()
[ "$has_cis" = 1 ] || extra=(--cis "$ws/apps/AA-CIS-App")

AA_WORKSPACE=$ws bash "$impl" "$@" "${extra[@]}"
