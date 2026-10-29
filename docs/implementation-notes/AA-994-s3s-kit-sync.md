# AA-994 S3s — kit sync automation, root side (S257)

The bot itself is in AA-CIS-App (`kit-sync.yml`, `kit-consumers.yml`, `.github/scripts/kit_sync_bot.py`, notes in
AA-CIS-App `docs/implementation-notes/AA-994-kit-sync-bot.md`). This root PR keeps the ecosystem docs and the agent
tool in line with it.

## Decisions

- `tools/kit/kit-sync.sh` becomes a wrapper around AA-CIS-App `.github/scripts/kit-sync.sh` (the copy code moved
  there so the CIS workflows can run it after the root repo goes private, and so a hand sync equals a bot sync). The
  wrapper keeps the old command line and defaults (`--cis` = `$AA_WORKSPACE/apps/AA-CIS-App`, `--dest-repo` =
  `<workspace>/apps/<repo>`). It runs the CIS main checkout's file, else that checkout's `origin/main` version;
  `KIT_SYNC_IMPL` points it at a CIS worktree for a try-out.
- ADR 0011a decision 3 and `docs/security/github-apps.md` §8 said "no app workflow mints a token for another repo",
  which contradicts ADR 0016 decision 6 (the CIS kit sync mints one per consumer repo). They now say "for AA-CIS-Infra
  or the root repo" and name the kit sync as the one cross-repo app token (consumer app repos only, Contents + Pull
  requests write, `release` environment, never merges). ADR 0011a is still Proposed, so this is a clarification, not
  an amendment of an accepted decision.

## Changed

- `tools/kit/kit-sync.sh` (wrapper), `tools/kit/test_kit_sync.sh` (header: how to run it before the CIS PR merges).
- `docs/adr/0011a-…md` (scope line, decision 3), `docs/adr/0016-…md` (dated update note under decision 6),
  `docs/security/github-apps.md` §8, `docs/security/secrets-register.{yaml,md}` (CIS `release` row: new consumer).

## Tradeoffs

- The wrapper depends on the CIS PR: merge AA-CIS-App first, then this PR. Until the CIS main checkout is pulled the
  wrapper falls back to `git show origin/main:` of that checkout, so a fetch is enough.

## Should know

- Verified: `KIT_SYNC_IMPL=<CIS worktree script> bash tools/kit/test_kit_sync.sh` → pass=20 fail=0 (the unchanged
  fixture suite through the wrapper); without the CIS file the wrapper exits 2 with a "pull AA-CIS-App main" message.
