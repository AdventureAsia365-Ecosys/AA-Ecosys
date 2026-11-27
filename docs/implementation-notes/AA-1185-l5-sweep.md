# AA-1185 — S295 audit sweep (root part, lane l5-sweep, S296)

## Decisions

- The docs lint `resource-ids` runs in **error mode** on the docs pages (journals, the onboarding account map and
  generated pages excepted): account IDs, ARNs, VPC ids, API Gateway hosts, user-pool IDs and a new kind `mail` (an
  e-mail address outside the company and test domains, only common real TLDs so code like `@router.get` passes).
  The same tool file is copied to Infra (both copies stay identical).
- The 104 hits (mostly `docs/linear-export/`) were masked like the generated pages: `{acc2}`, `arn:...:{acc2}:`,
  `sg-{masked}`, `{apigw-id}.execute-api.`; vendor and root mailboxes became role words.
- The WordPress CVE exception row is removed: the Infra PR turns the test site off outside test windows, so the image
  no longer runs (a window registers a new dated row if it needs one).
- `docs/security/baseline.md`: rows for the AA-1185 controls, written as "in place after the apply/deploy"; the RDS
  caller list now names `crm-api`. `last_reviewed` is not raised (no live re-read in this lane).

## Changed

- Journals (sessions, audits, implementation notes, backlog) and the agent files (`.claude/`, `.kiro/`, `skill/`) still
  hold account IDs: the lint does not scan journals, and agents do not edit the agent files (follow-up for the tech lead).

## Tradeoffs

- Masking `docs/linear-export/` rewrites exported issue text: the history keeps the original, the HEAD no longer
  hands out the IDs.

## Should know

- Merge the Infra PR (test site off) before or with this PR: the exception row goes away here.
