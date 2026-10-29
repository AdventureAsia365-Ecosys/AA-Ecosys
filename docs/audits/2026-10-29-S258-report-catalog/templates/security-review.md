---
id: SEC-03-yyyy-mm
title: Security review <YYYY-MM>
description: <One sentence - open vulnerabilities past SLA, secret or register drift, isolation probe results, privileged actions and legal readiness this month.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-29
review_every_days: 30
related: [SEC-01, SEC-02, SEC-03, SEC-04, SEC-05]
---

# Security review <YYYY-MM>

<!-- Report family: security and access review. Monthly SEC-03 (vulnerabilities, secrets drift, isolation probes) with
SEC-08 (privileged actions, audit chain), the monthly counts of SEC-09 (privacy) and SEC-10 (legal readiness). The quarterly
access review keeps docs/templates/access-review.md (SEC-05) and links here. Save as docs/audits/<date>-S<nnn>-security-review/README.md
with a root PR and list it in docs/security/README.md. While the root repo is public: no secret value, token, exploit
detail of an unfixed issue or personal data; name the repo and severity, link the private alert. Delete this comment. -->

Month: <YYYY-MM>. Generated: <UTC time>, run <id>. Collected: <Dependabot, scans, register check, probes>.
Previous: <link>. Approved by: <role>, <date>.

## 1. Summary

NARRATIVE: items past SLA, new findings, drift, and the one action that matters most.

## 2. How to read this report

- SLA per severity is defined in `docs/security/vulnerability-management.md`; past SLA is red.
- An ignored advisory needs an expiry date; an expired ignore is treated as open.
- Drift means a secret, role or key exists in one system and not in the register (or the reverse).

## 3. KPIs

| KPI (ID@version) | Definition | Target | Actual | Last month | Status |
|---|---|---|---|---|---|
| K-SEC-VULNSLA@1 | Critical/high alerts past SLA | 0 | | | |
| K-SEC-SECRETFIND@1 | Unresolved secret-scan findings | 0 | | | |
| K-SEC-DRIFT@1 | Secrets register drift items | 0 | | | |
| K-SEC-ISOLATION@1 | Failed isolation probe runs | 0 | | | |
| K-AUD-CHAIN@1 | CIS audit hash chain verify | pass | | | |
| K-AUD-BREAKGLASS@1 | Break-glass uses recorded | 100 % | | | |
| K-PRIV-DSAR@1 | DSARs closed on time | 100 % | | | |
| K-LEGAL-OPEN@1 | Open legal readiness topics | 0 before go-live | | | |

## 4. Vulnerabilities

| Repo | Critical | High | Medium | Oldest open (days) | Past SLA | Ignores expiring this month |
|---|---|---|---|---|---|---|

## 5. Secrets and keys

Register drift per system (Secrets Manager, Lambda env, GitHub, Vercel), rotations done, keys created or deleted.

## 6. Isolation and key policy probes

| Probe | Runs | Failed | Last failure | Follow-up |
|---|---|---|---|---|

## 7. Privileged actions (SEC-08)

Break-glass uses, deploy-gate overrides, role changes, admin bulk actions - each with its record link.

## 8. Privacy counts (SEC-09)

DSARs received / closed, erasure DRY RUNs / applies, retention runs, consent check result.

## 9. Legal readiness (SEC-10)

Open topics, '[to be confirmed]' markers left, DPAs signed / needed, AI clause status.

## 10. Quarter months only: access review

Link to the SEC-05 record and its open findings.

## 11. Decisions needed

| # | Decision | Context | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

## Actions

| Action | Severity | Owner role | Due | Status |
|---|---|---|---|---|
