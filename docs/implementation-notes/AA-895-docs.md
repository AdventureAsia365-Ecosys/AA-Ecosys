# AA-895 implementation notes (root repo: security baseline and vulnerability management)

Scope: S243 (19/10/2026), Claude Code, branch `docs/aa895-aa896-security-finops` on top of the AA-887 foundation
branch. Pages: `docs/security/baseline.md` (SEC-01), `docs/security/vulnerability-management.md` (SEC-03),
`docs/security/README.md` (SEC-05 index). Companion commits: `.github/dependabot.yml` in AA-Booking and
AA-TripPlanner-Web (branch `chore/aa895-dependabot` in each).

## Decisions

- **Every status was read live on 19/10/2026**, read-only: GuardDuty, Access Analyzer, S3 account and bucket
  Block Public Access, CloudTrail trail and selectors, WAF web ACL and its associations, API Gateway stages,
  ElastiCache encryption and AUTH, RDS encryption / public flag / `rds.force_ssl`, log group retention, VPC flow
  logs, Security Hub; GitHub org 2FA, rulesets, branch protection, security-and-analysis settings, Dependabot
  alerts. `last_reviewed` is therefore today. IAM users were not listed: the session guard blocks IAM calls for
  subagents; the baseline sends that check to the quarterly access review (DM-8.10).
- **Status vocabulary** in, partial, gap, by decision. "By decision" rows name the S241 decision and its trigger
  (D-14 GitHub Team, D-15 agent role, Security Hub cost), per reconciliation correction 14.
- **Controls link, never absorb**: AA-873/874/875/876/879 keep their scope (reconciliation overlap row AA-895).
- **Fix-time SLA for the Dev phase** (Critical 7 d, High 30 d, Medium 90 d, Low next grouped PR) with an
  exposure rule; prod numbers (72 h / 14 d) are written as a proposal for the go-live checklist, not a rule.
- **Exceptions**: Python reuses the CIS `.github/pip-audit-ignore.txt` format and its expiring CI gate (AA-868);
  npm alerts get a GitHub dismissal by Nghiệp plus a row on the page. Agents never dismiss alerts.
- **Dependabot (BK, TP)**: CIS model for npm/pip (grouped security updates, version updates off) plus the Infra
  model for GitHub Actions (grouped weekly version updates). No docker entry (security updates do not cover base
  images; Trivy is AA-879).
- **Index page** `docs/security/README.md`: STYLE says a folder gets a README once it has two real pages; the
  catalog already names it as the SEC-05 index. ID `SEC-05-index`.

## Changed

- Brief said current open alerts were "CIS chromadb critical/high and sprintf-js medium". Live read found more:
  CIS also has four high `xlsx` alerts (frontend and portal, no npm fix; CIS only writes spreadsheets with it),
  and **Booking has 38 open alerts** (3 critical, 18 high) in `frontend/package-lock.json`, all fixed by
  `next` 16.3.8 and newer `postcss` / `sharp` / `source-map-js`. Both are on the page with a decision list.
- The WAF row says "partial": the web ACL is on the shared ALB; the two API Gateway stages have no web ACL.
- CloudTrail is single-region (not in the brief); recorded as partial under AA-873.
- Catalog rows SEC-01, SEC-03, SEC-05 status updated; `llms.txt` gains a Security section.
- S243 review fix: the baseline row "Public repos content" was first written as "in place". A `git grep` for
  the three account IDs on each public repo's `origin/main` (19/10) found them in 76 CIS files, 4 Booking files
  and 6 TripPlanner files (TP `deploy-lambdas.yml` role ARN and bucket defaults, Booking retention bucket name,
  CIS `CLAUDE.md` / `CONTEXT.md` / migrations / runbook). The row is now "gap", lists the places, and the
  summary table and "How to re-check" match. AA-889 covers only CIS `docs/` files added from now on
  (reconciliation item 13), so the scrub of already-tracked files has no issue: Nghiệp decides whether to open one.
- S243 review fix: the chromadb exception (critical, expiry 2026-12-31) now states the exposure rule (no runtime
  import, treated as High, 90 days max), so it no longer contradicts the fix-time table.

## Tradeoffs

- One baseline page with tables instead of one page per control: fewer pages to keep fresh; the issue links carry
  the detail.
- The open-alerts snapshot is hand-written until a generator exists (catalog SEC-03 "G" part). A dated
  snapshot is better than none; the monthly triage refreshes it.

## Should know

- Pages are `status: draft` until Nghiệp reads them (STYLE).
- Links to pages from other lanes that do not exist on this base yet are written as code spans, not links
  (`docs/onboarding.md`, `secrets-register.md`, `docs/legal/register.md`, `docs/ops/feature-flags.md`), so the
  internal link check stays clean.
- Nghiệp actions: bump Booking `next` (critical due 26/10); decide the CIS `xlsx` exception or replacement;
  merge the BK and TP Dependabot PRs, then close Booking Dependabot PRs #38-#40 once the bump lands.
