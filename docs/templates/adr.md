# ADR NNNN — <Decision in a few words>

<!-- Template for an ADR (docs/adr/NNNN-<slug>.md). Placement rule: two or more repos -> the root repo,
infrastructure only -> the infrastructure repo, one app -> that app. ADRs do not use the catalog front-matter.
Numbering: the next free number from the "Numbering" section of docs/adr/README.md. An amendment to an accepted ADR
is a separate file <nnnn>a-<slug>.md; the amended ADR gets a pointer line and its index row says "amended by". Never
rewrite the text of an accepted ADR. Delete this comment. -->
<!-- kit:skip -->
<!-- AA: follow the style of the accepted root ADRs (0004b, 0006a, 0008); placement rule in
skill/ai-nghiep/references/adr.md (infrastructure only -> AA-CIS-Infra); reserved numbers are listed in
docs/adr/README.md and CI tools/adr/check_adr_numbers.py rejects used, reserved or skipped numbers. -->
<!-- /kit:skip -->

- **Status:** Proposed (<dd/mm/yyyy>, S<nnn>). <!-- Proposed | Accepted (<date>, S<nnn>) | Superseded by ADR <nnnn> -->
- **Scope:** <apps, repos and environments the decision covers>.
- **Amends / Supersedes:** <ADR nnnn decision n, or "none">.
- **Implements:** <ADR or data-standard rule this realises, or "none">.
- **Design and evidence:** `docs/audits/<date>-S<nnn>-<slug>/...` <!-- plan, measurements, review -->
- **Related Linear:** AA-<n> (<why>). <!-- kit:drop -->

<!-- kit:only - **Related issues:** <KEY>-<n> (<why>). -->

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
  - <... include monthly USD for any new AWS resource (DM-10.7)> <!-- kit:drop -->

<!-- kit:only   - <... include the monthly cost of any new paid resource> -->

## Alternatives considered

- **<Option>.** Rejected: <reason>.
- **<Option>.** Rejected: <reason>.

## Follow-ups

- <Issue, owner, trigger>. Update `docs/adr/README.md` (index row) in the same PR.
- **Prune:** <the event that makes this ADR worth re-reading: a trigger, a date or a measured threshold>. When a later
  ADR replaces it, set `Superseded by ADR <nnnn>` here and in the index; delete the rule from every page that restated
  it, and do not keep the old and the new rule side by side.

<!-- MADR-minimal variant (small decisions, one repo, easy to reverse): keep only Status, Context, Decisions (one
numbered list), Consequences (one line each for good and bad) and the Prune line. Use the full shape above when two or
more repos change, money or data is at stake, or the decision is hard to reverse. Shape source: MADR (CC0),
https://github.com/adr/madr. Delete this comment. -->
