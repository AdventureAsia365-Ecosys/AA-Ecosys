---
id: TPL-01-settings-entry
title: Settings registry entry template
description: How to add a threshold, limit or policy value as an admin-editable setting, with its registry row and operator guide.
type: template
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, CAT-01]
---

# Settings registry entry template

Every business policy value and every operational threshold or limit is a setting: versioned data with an admin page
for the administrator role, seeded with the approved default (handbook working rule W7, playbook principle "tolerances,
not approvals"). An environment variable or a constant in code is not enough, because changing it needs a deploy.
Deploy configuration (endpoints, secret references, per-environment switches) stays in the environment
(Twelve-Factor factor III).

## 1. Registry row

| Field | Value |
|---|---|
| Key | `<area>.<name>` (for example `quality.min_words`) |
| Type and unit | <integer, words / decimal, USD / duration, days / enum> |
| Default (approved) | <value, with who approved it and when> |
| Allowed range | <min to max, or the enum values> |
| Scope | <global / per tenant / per stage / per provider> |
| Who may change it | administrator (maker-checker when it moves money or data) |
| Read by | <module and function, through the one settings reader> |
| Effect of a change | <immediate / next job / next deploy of a cache> |
| Audit | every change keeps the old value, the new value, who and when |

## 2. Operator guide

Write two to five lines that appear next to the field on the admin page:

- **What it controls:** <plain words>.
- **Raise it when:** <symptom>. **Lower it when:** <symptom>.
- **Safe range:** <...>. Outside it: <what breaks>.

## 3. Checklist

- [ ] Seeded by a migration with the approved default.
- [ ] Read through the one settings reader; no literal copy of the value in code.
- [ ] A CI check refuses a literal threshold in the code path that reads it.
- [ ] The admin page shows the field, the unit, the range and the operator guide.
- [ ] A test changes the value and proves the behaviour changes without a deploy.
