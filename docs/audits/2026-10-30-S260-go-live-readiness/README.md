# Go-live readiness: all apps (2026-10-30)

<!-- Report OPS-17 (go-live readiness scorecard), docs/reports/catalog.yaml. Template:
docs/audits/2026-10-29-S258-report-catalog/templates/readiness-signoff.md. First version, prepared before a go-live
date exists so the list is ready when one is set; then weekly until go-live. The Vietnamese copy for the business
owner is README.vi.md in this folder. -->

Scope: CIS (content and catalog), Booking, TripPlanner, Partner (CRM and tenant portal). Prepared: 2026-10-30 (S260)
by the tech lead (agent-prepared). Decision needed by: none yet: no go-live date is set.

## 1. Summary

**Not ready, as expected:** no production environment exists. ADR 0012 (accepted 2026-10-29) sets the environment
model and the go-live gate; the build (about three to four weeks) starts only when the business owner sets a go-live
date. ADR 0018 (proposed 2026-10-30) would move prod into its own AWS account and must be accepted or declined first.
Of the 12 platform and linked must items below, none is done yet (ADR 0012 is accepted, ADR 0018 still open);
per app, 3 of 14 must items are done (the health endpoints). Nothing is blocked by a third party; item 3 (the
management-account review) depends on ADR 0018. Decision asked of the business
owner: **a go-live date (or a window), and which apps the first prod needs.**

## 2. How to read this report

- Must items block go-live; should items can carry over with an owner and a date.
- Done means evidence is linked; a claim without evidence counts as open.
- Items 1-8 are the ADR 0012 go-live gate (decision 11), items 9-12 the linked report gates of OPS-17.

## 3. Scorecard

| Area | Must items | Done with evidence | Blocked | Status |
|---|---|---|---|---|
| Platform gate (ADR 0012 decision 11) | 8 | 0 | 0 | open |
| Linked report gates (OPS-08, OPS-03, SEC-05, SEC-10, DEV-04, SEC-03, FI-06) | 4 | 0 | 0 | open |
| CIS | 3 | 1 | 0 | open |
| Booking | 4 | 1 | 0 | open |
| TripPlanner | 4 | 0 | 0 | open |
| Partner (CRM, tenant portal) | 3 | 1 | 0 | open |

## 4. Checklist

### Platform gate

| # | Item | Must / should | Status | Evidence | Owner role | Due |
|---|---|---|---|---|---|---|
| 1 | Environment model accepted (ADR 0012); ADR 0018 accepted or declined | must | ADR 0012 done; ADR 0018 open | [ADR 0012](../../adr/0012-environment-model.md) status line; [ADR 0018](../../adr/0018-lean-aws-account-model.md) Proposed | tech lead | before the build |
| 2 | Prod Terraform plan reviewed with one reconciled monthly cost, approved before apply (D-19) | must | open | — | tech lead | build week 2 |
| 3 | Agent role switched to a Dev-scoped role; management-account review recorded (ADR 0012 decisions 4.4, 4.5) | must | open | — | tech lead | before the build |
| 4 | ADR 0014 decision 4 re-decided for the private repos | must | open | — | tech lead | before the build |
| 5 | Restore drill on prod passed with its RTO recorded (DM-9.3, OPS-03) | must | open | [drills](../../ops/drills/README.md) | tech lead | build week 3 |
| 6 | Alarms with the paging route and a second alert channel tested; two SLOs per public API defined | must | open | OPS-13 measures 3 CIS objectives on Dev only | tech lead | build week 3 |
| 7 | Secrets rotated (D-02, D-03); break-glass PDF copy of the core runbooks in place | must | open | [break-glass](../../ops/runbooks/break-glass.md) | tech lead | go-live week |
| 8 | Every control the [security baseline](../../security/baseline.md) marks "before prod" closed; content seed job run and its counts checked against Dev | must | open | baseline: GuardDuty, Access Analyzer, S3 BPA, Redis AUTH/TLS gaps | tech lead | go-live week |

### Linked report gates

| # | Item | Must / should | Status | Evidence | Owner role | Due |
|---|---|---|---|---|---|---|
| 9 | Budget approved for prod (FI-06) and capacity / SLO set reviewed (OPS-08) | must | open | FI-06 and OPS-08 generated monthly on Dev (CIS report engine) | business owner, tech lead | build week 1 |
| 10 | Access review done for the quarter (SEC-05); security alerts past SLA = 0 (SEC-03) | must | open | SEC-03 draft generated monthly from 2026-11 (CIS facts; GitHub counts by hand) | tech lead | build week 3 |
| 11 | Legal readiness: the twelve topics answered (SEC-10) | must | open | [legal readiness 2026-10-30](../2026-10-30-S260-legal-readiness/README.md): 12 of 12 open | business owner | before go-live |
| 12 | UAT signed per app (DEV-04, AA-855: videos after the technical work) | must | open | — | business owner | go-live week |

### Per app

| App | Item | Must / should | Status | Evidence | Owner role |
|---|---|---|---|---|---|
| CIS | Health and readiness endpoints answer | must | done | OPS-12 daily digest probes `/health` + `/health/ready` | tech lead |
| CIS | Prod image promoted by digest from Dev (ADR 0012 decision 7) | must | open | Deploy Prod workflow not built | tech lead |
| CIS | Report engine and daily KPI snapshot live | should | done | /admin/reports (EX-04, EX-06, OPS-12 daily) | tech lead |
| CIS | Admin on a Vercel prod project, Pro plan (D-18) | must | open | Hobby today | tech lead |
| Booking | Health and readiness endpoints answer | must | done | OPS-12 daily digest | tech lead |
| Booking | Payments live only on prod (ADR 0012 decision 11 trigger) | must | open | Booking invoice / payment slices in progress (AA-952) | tech lead |
| Booking | Booking admin on a Vercel prod project, Pro plan | must | open | Hobby today | tech lead |
| Booking | Staff roles reviewed for prod (SEC-05) | must | open | — | tech lead |
| TripPlanner | Health endpoint (none today: status comes from Lambda traffic only) | must | open | OPS-12 lists TripPlanner as "no health endpoint yet" | tech lead |
| TripPlanner | Privacy and terms pages final (no "Draft - pending legal review" banner) | must | open | SEC-10 topic 2 | business owner |
| TripPlanner | Production Vercel project, Pro plan before charging (D-18) | must | open | Hobby today | tech lead |
| TripPlanner | Daily LLM spend cap set by the business (TP-01 K-TP-LLMCAP uses the 5 USD default) | must | open | TP-01 weekly from 2026-11-02 | business owner |
| Partner | Health and readiness endpoints answer | must | done | OPS-12 daily digest | tech lead |
| Partner | CRM Go-real: real agency data only on prod (AA-980) | must | open | — | tech lead |
| Partner | Portal terms with the AI Schedule accepted (SEC-10 topic 12, answer needed by 2026-11-11) | must | open | SEC-10 | business owner |
| Partner | Agency vendor accounts (BYO) documented per agency | should | open | — | tech lead |

## 7. Blockers

| Blocker | Impact | Plan | Owner role | Date |
|---|---|---|---|---|
| No go-live date | The 3-4 week build cannot start | Business owner sets a date or a window | business owner | — |
| ADR 0018 not decided | Where prod lives (acc2 or its own account) changes the Terraform root and item 3 | Tech lead accepts or declines ADR 0018 | tech lead | before the build |

## 8. Decision and sign-off

| Decision | Options | Recommendation | Decided by (role) | Date | Result |
|---|---|---|---|---|---|
| Go-live date | (A) set a date at least 4 weeks out; (B) set a window and decide the first apps | B: a window plus the first apps (likely TripPlanner + Booking) | business owner | — | open |

## Sources

ADR 0012 (2026-10-29), ADR 0018 (2026-10-30), `docs/ops/README.md` "Prod", `docs/security/baseline.md`, the report
registry `docs/reports/catalog.yaml` (OPS-17 linked gates), the OPS-12 digest of 2026-10-30, the legal readiness
report of the same day.
