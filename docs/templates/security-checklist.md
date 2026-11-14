---
id: SEC-00-asvs-replace-me
title: Security checklist - <area or release>
description: <One sentence - the ASVS level 1 items checked for the touched area, with the result and the gaps.>
type: report
status: draft
owner: replace-me
audience: [engineer, cto, cio, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
related: []
---

# Security checklist - <area or release>

<!-- New-project playbook, phases 5 and 6, gates G5 and G6. OWASP ASVS 5.0 level 1 is the release gate for every area;
level 2 for authentication, payment and personal data (kit decision D9). The rows below are a short, grouped reminder
of the ASVS chapters, not a copy of the standard: open the ASVS 5.0 release from the OWASP repository for the exact
requirement IDs and quote them in the "ASVS IDs" column. Check only the chapters the change touches. Write security
findings about a public repo in a private place. Delete this comment. -->

- **Area and change:** <routes, pages, jobs, data touched>.
- **Level:** <L1 | L2 because auth / payment / personal data>.

## Checks

| Group | What to confirm | ASVS IDs | Result | Evidence |
|---|---|---|---|---|
| Encoding and injection | Queries are parameterised; output is encoded for its context; no shell built from input | <...> | <pass / gap / n.a.> | <test, file> |
| Validation | Input is checked against an allow list on the server; file uploads limited by type and size | <...> | | |
| Authentication | Sign-in through the identity provider; no own password store; rate limits on sign-in | <...> | | |
| Sessions | Tokens short-lived, rotated, revoked on sign-out; cookies `Secure`, `HttpOnly`, `SameSite` | <...> | | |
| Authorization | Every route checks the role and the tenant on the server; deny by default | <...> | | |
| Data protection | Personal data classes known; encrypted in transit and at rest; no secret or personal data in logs | <...> | | |
| Secrets and config | Secrets only in the secret store; nothing in the repo; secret scan green | <...> | | |
| Errors and logging | Errors show no stack trace or internal ID; security events logged with who and when | <...> | | |
| Web front end | Security headers set (CSP, HSTS, frame options); cross-site writes refused | <...> | | |
| API | Problem details errors; limits on list size and request rate; idempotency keys on money moves | <...> | | |
| Dependencies | Known-vulnerability scan green; pinned versions; actions pinned by SHA | <...> | | |

## Gaps

| Gap | Risk | Owner | Tracker link | Accepted until |
|---|---|---|---|---|
| <...> | <...> | <role> | <issue> | <YYYY-MM-DD or "fix before release"> |

## SAMM light self-check (once per project, then yearly)

Rate each OWASP SAMM v2 business function 0 to 3 and name one next step: governance, design, implementation,
verification, operations. Target level 1 almost everywhere at startup scale.
