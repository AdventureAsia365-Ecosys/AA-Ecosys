---
id: OPS-04-pm-yyyy-mm-dd-slug
title: "Postmortem: <short title> (<YYYY-MM-DD>)"
description: <One sentence - what broke and for how long.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [replace-me]
last_reviewed: 2026-10-19
related: [OPS-04]
---

# Postmortem: <short title> (<YYYY-MM-DD>)

<!-- Blameless. Store at docs/ops/postmortems/<YYYY-MM-DD>-<slug>.md (single place for incident records, G-14).
Write within 5 working days of a SEV1 or SEV2 (docs/ops/incident-response.md). Delete this comment. -->

## Summary

<Two or three sentences: what happened, impact, how it ended.>

## Impact

- Who: <tenants / travellers / staff / none external>.
- How long: <start - end, duration>.
- Data: <lost / exposed / none>. Dev holds test data only (D-01).
- SEV: <1 / 2 / 3>.

## Timeline (UTC+7)

| Time | Event |
|---|---|
| <hh:mm> | <alarm fired / user report / action> |

## Detection

<How we found out and how long it took. Which alarm should have fired.>

## Root causes

<Technical and process causes. Five-whys if useful.>

## Trigger

<The change or event that set it off: PR, deploy SHA, job kind, external outage.>

## Resolution

<What stopped the impact (rollback, flag, scale) and what fixed it.>

## Action items

| Action | Type (prevent / detect / mitigate) | Issue | Status |
|---|---|---|---|
| <action> | <type> | AA-<n> | <open> |

## Lessons learned

### Went well

- <...>

### Went wrong

- <...>

### Where we got lucky

- <...>

Lesson line added to `skill/aa-lessons/lessons.md`: <yes - quote it / no - why>.

## Business summary (VI)

<Ba câu cho chị Thư: chuyện gì xảy ra, ảnh hưởng gì, đã làm gì để không lặp lại. Không mã Linear, không thuật ngữ.>
