---
id: TPL-01-dor
title: Definition of Ready for a Linear issue
description: The fields an issue needs before it is assigned to Kiro, a subagent or a builder lane.
type: template
status: active
owner: nghiep
audience: [pm, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 180
related: [GUIDE-07, skill/aa-linear-issue/SKILL.md, skill/aa-ship/SKILL.md]
---

# Definition of Ready for a Linear issue

An issue is **ready** when every section below is filled in. Not ready means it is not handed to Kiro, a subagent
or a builder lane yet (S243 guide §5.6). The Linear description keeps the house template from
`skill/aa-linear-issue` (Problem / Scope / Done when / Related); the extra DoR sections go under it.
Issues are written in English.

```markdown
## Problem
What is wrong or missing, where, and the evidence (session S<nnn>, PR, numbers). No "might".

## Goal
One or two sentences: the business outcome.

## Scope
1. In: repo, schema, files, endpoints, pages.
Out of scope: ...

## Done when
- 3 to 6 testable criteria on the real environment (endpoint X returns field Y; page Z shows ...).

## Verify
How to prove it live: curl + expected shape, page + screenshot, SQL query, workflow run.

## Risk class
none | auth | migration | IAM/secret | delete | cost | LLM
(auth, migration, IAM/secret, delete -> kiro-reviewer on the PR, per kiro-delegate)

## Dependencies
Issues, PRs or migrations that must land first (blocks / blockedBy in Linear).

## Docs impact
CONTEXT.md | ADR | runbook | contract | catalog page (ID) | none

## Cost
0 USD, or the monthly estimate for any new AWS resource / paid run (DM-10.7). LLM runs: subset size and stage name adhoc_<issue>.

## Related
AA-xxx (why)
```

## Checklist

- [ ] Problem has evidence, not a guess.
- [ ] Scope names the repo(s) and says what is out.
- [ ] Done-when items are checkable on Dev, not "code merged".
- [ ] Verify says exactly which command, page or query proves it.
- [ ] Risk class set; a risky class names the reviewer.
- [ ] Dependencies linked in Linear.
- [ ] Docs impact named (or "none").
- [ ] Cost stated when the work adds AWS resources or paid calls.
- [ ] The issue sits in a project under the 100 unarchived-issue limit.
