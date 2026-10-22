# ADR NNNN — <Decision in a few words>

<!-- Template for a root ADR (docs/adr/NNNN-<slug>.md). It follows the style of the accepted root ADRs
(0004b, 0006a, 0008). Placement rule: skill/ai-nghiep/references/adr.md - two or more repos -> root,
infrastructure only -> AA-CIS-Infra, one app -> that app. ADRs do not use the catalog front-matter.
Numbering: a next-free number from the "Numbering" section of docs/adr/README.md (reserved numbers are listed
there; CI tools/adr/check_adr_numbers.py rejects used, reserved or skipped numbers). An amendment to an accepted ADR is a separate file <nnnn>a-<slug>.md; the amended ADR gets a pointer
line and its index row says "amended by". Never rewrite the text of an accepted ADR. Delete this comment. -->

- **Status:** Proposed (<dd/mm/yyyy>, S<nnn>). <!-- Proposed | Accepted (<date>, S<nnn>) | Superseded by ADR <nnnn> -->
- **Scope:** <apps, repos and environments the decision covers>.
- **Amends / Supersedes:** <ADR nnnn decision n, or "none">.
- **Implements:** <ADR or data-standard rule this realises, or "none">.
- **Design and evidence:** `docs/audits/<date>-S<nnn>-<slug>/...` <!-- plan, measurements, review -->
- **Related Linear:** AA-<n> (<why>).

## Context

<Why a decision is needed now. Facts with their source (issue, PR, measurement, live check). No "might".>

## Decisions

### 1. <Decision title>

- <What we do, scope, and the rule a reviewer can check.>
- <Numbers and names, not IDs: resource names, Terraform output names.>

### 2. <Decision title>

- <...>

## Consequences

- **Positive:**
  - <...>
- **Negative / cost:**
  - <... include monthly USD for any new AWS resource (DM-10.7)>

## Alternatives considered

- **<Option>.** Rejected: <reason>.
- **<Option>.** Rejected: <reason>.

## Follow-ups

- <Issue, owner, trigger>. Update `docs/adr/README.md` (index row) in the same PR.
