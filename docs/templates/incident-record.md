---
id: OPS-04-inc-yyyy-mm-dd-slug
title: "Incident: <short title> (<YYYY-MM-DD>)"
description: <One sentence - what broke, the severity, how long, and whether a postmortem follows.>
type: report
status: draft
owner: replace-me
audience: [engineer, devops, cto, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: [OPS-04]
---

# Incident: <short title> (<YYYY-MM-DD>)

<!-- Light incident record (new-project playbook, phase 7 Operate; ITIL incident management, trimmed). Open it when
the incident starts, fill it as you go, close it when service is restored. SEV1 and SEV2 also get a postmortem
(postmortem.md) when a trigger in its first section applies. No secrets, account IDs or personal data. Delete this
comment. -->

| Field | Value |
|---|---|
| Severity | <SEV1: users cannot use the product or data exposed or lost / SEV2: degraded with a workaround / SEV3: internal only> |
| Status | <open / mitigated / resolved> |
| Started (UTC+7) | <hh:mm> |
| Detected by | <alarm, person, user report> |
| Incident lead | <role> |
| Who was told, when | <business owner at hh:mm; tenants at hh:mm> |
| Restored (UTC+7) | <hh:mm> |
| Postmortem | <yes: link / no: why> |

## Timeline

| Time | What happened or was done | Who |
|---|---|---|
| <hh:mm> | <...> | <role> |

## Impact

<Who was affected, what they could not do, data involved, cost involved.>

## Mitigation

<What restored service: rollback, flag off, scale up, manual fix. Commands or links.>

## Follow-ups

| Action | Owner | Tracker link |
|---|---|---|
| <...> | <role> | <issue> |
