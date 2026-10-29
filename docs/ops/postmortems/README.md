---
id: OPS-04-postmortems
title: Postmortems
description: Index of incident and cost-incident postmortems (report OPS-04), newest first, with severity and status.
type: reference
status: active
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 90
related: [OPS-04, docs/templates/postmortem.md, docs/reports/catalog.yaml]
---

# Postmortems

One place for incident records (G-14). Each SEV1 or SEV2, and each cost incident, gets one page here within 5 working
days, written from [the template](../../templates/postmortem.md) and named `<YYYY-MM-DD>-<slug>.md` (the day the impact
started, ICT). How to classify and whom to tell: [incident response](../incident-response.md). SEV3 items stay a line
in the session log.

Pages are blameless and public-safe: no account IDs, ARNs, secrets, personal data or vendor contract terms.

| Date (ICT) | Incident | SEV | Status | Page |
|---|---|---|---|---|
| 2026-10-29 | Bedrock refused every model on the LLM account (acc3): all platform LLM calls stopped | 2 | open, waiting for a decision | [2026-10-29-acc3-bedrock-access-refusal.md](2026-10-29-acc3-bedrock-access-refusal.md) |

Status words: `open` (impact continues), `mitigated` (impact stopped, actions open), `closed` (actions done or moved
to the backlog).
