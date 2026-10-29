#!/usr/bin/env bash
# Copy the canonical UI kit core of AA-CIS-App into one consumer app and rewrite its kit.lock.json
# (AA-994, root ADR 0016 decisions 2, 5 and 6). Agent tool: it writes files in the consumer checkout and stops;
# committing, pushing and the PR stay with the caller.
#
# Usage:
#   tools/kit/kit-sync.sh <consumer> [--from-local] [--ref <git-ref>] [--cis <path>] [--dest-repo <path>]
#                                    [--no-fetch] [--dry-run]
#   tools/kit/kit-sync.sh --list
#
# Since AA-994 S3s this is a wrapper: the copy code lives in AA-CIS-App `.github/scripts/kit-sync.sh`, the same file
# the CIS Kit Sync bot and Kit Consumers check run, so a hand sync and a bot sync cannot differ. Options, consumers,
# profiles, the lock format and the exit codes are that script's (run with --help).
#
# Which copy of the script runs: $KIT_SYNC_IMPL when set (a CIS worktree's file, for a try-out), else
# <workspace>/apps/AA-CIS-App/.github/scripts/kit-sync.sh, else that checkout's `origin/main` version. <workspace> is
# the main checkout of the root repo. Defaults kept from before: --cis is $AA_WORKSPACE/apps/AA-CIS-App (or
# <workspace>/apps/AA-CIS-App), --dest-repo is <that workspace>/apps/<repo>.
set -euo pipefail

die() { echo "kit-sync: $*" >&2; exit 2; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
common=$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
  || die "cannot find the root repo from $script_dir"
real_ws=$(dirname "$common")
ws=${AA_WORKSPACE:-$real_ws}
canon_cis=$real_ws/apps/AA-CIS-App
rel=.github/scripts/kit-sync.sh

impl=${KIT_SYNC_IMPL:-$canon_cis/$rel}
if [ ! -f "$impl" ]; then
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  git -C "$canon_cis" show "origin/main:$rel" > "$tmp/kit-sync.sh" 2>/dev/null \
    || die "AA-CIS-App $rel not found in $canon_cis (working tree or origin/main); pull AA-CIS-App main (AA-994 S3s)"
  impl=$tmp/kit-sync.sh
fi

has_cis=0
for a in "$@"; do [ "$a" = --cis ] && has_cis=1; done
extra=()
[ "$has_cis" = 1 ] || extra=(--cis "$ws/apps/AA-CIS-App")

AA_WORKSPACE=$ws bash "$impl" "$@" "${extra[@]}"
