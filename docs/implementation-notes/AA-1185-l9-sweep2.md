# AA-1185 lane l9-sweep2 (S296): root part

The Infra PR of this lane switches off the default execute-api endpoints, puts the Infra resource-ID lint in error mode
and drops the WordPress sidecar's `.trivyignore` line (Infra `docs/implementation-notes/AA-1185-l9-sweep2.md`).

## Decisions

- `docs/security/vuln-exceptions.toml`: the `CVE-2026-124851` row (AA-CIS-Infra, trivy, libzstd1 in the WordPress
  test sidecar) is removed. Its own way-out condition is met: the Booking admin task runs one container (task
  definition revision 75 and later, read on 27/11), so the WordPress image no longer runs and no nightly scan can
  report it. Removed before its 02/12 expiry.
- `docs/security/baseline.md`: the load balancer row states the default endpoints as switched off (with the guard
  test), and the public-repo identifiers row says both root and Infra lint every kind in error mode.
- `tools/docs/check_docs_text.py`: docstring only, same text as the Infra copy (error mode on pages in every repo, warn
  only for agent files).

## Changed

Nothing in behaviour on the root side: the register loses one row; no tool reads that row any more (the Infra
`.trivyignore` mirror goes in the same wave).

## Tradeoffs

- `last_reviewed` of the baseline page is not raised: the rows changed, the whole page was not re-read live.

## Should know

- Order does not matter between this PR and the Infra PR: the nightly image scan reads only this register, and no
  running image carries the CVE; the monthly triage cross-check would list an Infra entry without a row only if the
  Infra PR lagged a month.
