# AA-1185 — S295 audit sweep (root part, lane l5-sweep, S296)

## Decisions

- The docs lint `resource-ids` runs in **error mode** on the docs pages (journals, the onboarding account map and
  generated pages excepted): account IDs, ARNs, VPC ids, API Gateway hosts, user-pool IDs and a new kind `mail` (an
  e-mail address outside the company and test domains, only common real TLDs so code like `@router.get` passes).
  The same tool file is copied to Infra (both copies stay identical).
- The 104 hits (mostly `docs/linear-export/`) were masked like the generated pages: `{acc2}`, `arn:...:{acc2}:`,
  `sg-{masked}`, `{apigw-id}.execute-api.`; vendor and root mailboxes became role words.
- The WordPress CVE exception row stays (review fix, S296; its way_out now names the order). The Infra PR turns the
  test site off, but the container keeps running until the next Booking admin deploy after the apply, and the nightly
  Image Scan reads the running digests. The row (and the Infra `.trivyignore` line) goes in a small follow-up once
  `aws ecs describe-tasks` shows the Booking admin task with one container, before its 02/12 expiry.
- `tools/linear/linear_export.py` masks every kind the lint fails on (review fix, S296): account IDs (`{acc2}` with
  `AWS_ACCOUNT_ALIASES`, else `{aws-account}`), the account of an ARN, VPC / load balancer / user-pool ids, API Gateway
  hosts and outside addresses (`{outside-mailbox}`), in the issue files and the index. Without it the next session-end
  export would write raw IDs into docs/ and turn the docs lint red. Test: the rendered page and index pass
  `check_docs_text.check_resource_ids`.
- `docs/security/baseline.md`: rows for the AA-1185 controls, written as "in place after the apply/deploy"; the RDS
  caller list now names `crm-api`. `last_reviewed` is not raised (no live re-read in this lane).

## Changed

- Journals (sessions, audits, implementation notes, backlog) and the agent files (`.claude/`, `.kiro/`, `skill/`) still
  hold account IDs: the lint does not scan journals, and agents do not edit the agent files (follow-up for the tech lead).

## Tradeoffs

- Masking `docs/linear-export/` rewrites exported issue text: the history keeps the original, the HEAD no longer
  hands out the IDs.

## Should know

- This PR no longer removes the exception row, so it can merge in any order with the Infra PR.
- The admin-group alert pages only on adds to the three admin groups; enabling a staff user is a ticket-severity
  record (the CIS Staff page sends it on routine Reset and Sync).
