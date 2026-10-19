<!--
Title: "<type>: <what changed>" in English. Types: feat, fix, chore, refactor, docs, ci, test, perf.
No "[AA-123]" in the title. In the body write "Refs AA-123"; never Fixes/Closes/Resolves (Linear would close the issue).
Write the body in English. Session logs and audits for Nghiệp may stay Vietnamese; the CEO guide is bilingual.
-->

## What

-

## Why

Refs AA-

## Risk and rollback

- Risk: low / medium / high (high: changes an agent rule, a skill used for deploys, a data standard, or an ADR)
- Rollback: revert this PR

## Cost

- [ ] 0 USD: docs, skills or root workflows only
- [ ] Changes recurring spend (Actions minutes, an AWS resource a doc tells someone to create): monthly cost here:

## Docs checklist

- [ ] Catalog pages keep valid front-matter (`docs/templates/frontmatter.schema.json`); `last_reviewed` moved only for pages checked against the real system
- [ ] Runbook steps run on Dev are marked tested (date + evidence in `docs/audits/`); the rest stay `status: draft` with the UNTESTED banner
- [ ] New or changed ADR is listed in `docs/adr/README.md` with its status
- [ ] No secret values, real customer data or dumps; account IDs only in the onboarding account map
- [ ] Every AWS CLI command is one line with `--profile` and `--region`
- [ ] Live backlog (`docs/backlog/README.md`) and session log updated, or N/A
- [ ] Implementation note `docs/implementation-notes/AA-xxx.md`, or N/A

## Verification

- [ ] `docs-lint` green (front-matter, ADR index, single-line AWS CLI, links; resource IDs are warnings)
- [ ] Facts checked against the source (CONTEXT.md, ADRs, data standards, live read-only command), listed here:
