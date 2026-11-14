---
id: ARCH-00-contract-replace-me
title: Contract <name>.v<major>
description: <One sentence - what data or events this contract carries, who produces it and who consumes it.>
type: reference
status: draft
owner: replace-me
audience: [engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 180
related: []
---

# Contract <name>.v<major>

<!-- Contract folder template (new-project playbook, phases 2 and 4). A contract is the only way one app reads another
app's data: a database view, an HTTP API or an event. Folder layout:
  contracts/<name>.v<major>/README.md       this page
  contracts/<name>.v<major>/schema.json     JSON Schema (or <name>.openapi.yaml for HTTP)
  contracts/<name>.v<major>/samples/valid/*.json and samples/invalid/*.json
and one row in contracts/README.md (the registry). CI validates every valid sample and rejects every invalid one.
Delete this comment. -->

## 1. What it carries

<Entities and fields, in plain words. Link the schema file for the exact shape.>

## 2. Producer and consumers

| Role | App | How it reads or writes | Since version |
|---|---|---|---|
| Producer (one) | <app> | <view, endpoint, event topic> | <1.0> |
| Consumer | <app> | <...> | <1.0> |

## 3. Kind and access

- **Kind:** <database view | HTTP | event>.
- **Access:** <role or token that may read it; tenant scoping>.
- **Personal data:** <none | classes, with the retention rule>.

## 4. Versions

| Version | Date | Change | Breaking? |
|---|---|---|---|
| 1.0 | <YYYY-MM-DD> | First version | - |

Minor versions only add optional fields. A breaking change is a new major served in parallel for at least 30 days
after the last consumer has moved.

## 5. Samples

- Valid: `samples/valid/<case>.json` (<what each case shows>).
- Invalid: `samples/invalid/<case>.json` (<what each must fail on>).
