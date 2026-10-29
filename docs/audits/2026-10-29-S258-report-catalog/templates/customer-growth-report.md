---
id: APP-15-yyyy-mm
title: Customers and growth report <YYYY-MM>
description: <One sentence - where travellers and partners came from, how many activated, and how satisfied completed travellers were.>
type: report
status: draft
owner: nghiep
audience: [owner, pm, staff, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-29
review_every_days: 90
related: [PLAT-01]
---

# Customers and growth report <YYYY-MM>

<!-- Report family: customer and growth. Register APP-15 in docs/README.md before first use. Covers MKT-01 (acquisition),
MKT-02 (SEO and content), EX-07 (partner onboarding) and CX-01 (traveller satisfaction). Generated on business day 2.
Counts and rates only: no traveller names, contact data or free-text answers; CRM numbers arrive as counts via crm.ops.v1.
Proposed data (survey table, session source columns) must exist in db-schema-reference.md before a section is filled;
until then the section says `not collected yet`. Delete this comment. -->

> [!NOTE]
> Dev data. Targets are set after the first production quarter.

Month: <YYYY-MM>. Generated: <UTC time>, run <id>. KPI definitions v<n>.

## 1. Summary

NARRATIVE: three lines - best source, onboarding bottleneck, satisfaction headline.

## 2. How to read this report

- Source is first-touch: the first referrer or campaign seen in a planner session.
- Activation counts a partner once it reaches first value (first publish or first proposal) within 14 days.
- NPS = % promoters (9-10) - % detractors (0-6); fewer than 20 answers is shown as `too few answers`.

## 3. KPIs

| KPI (ID@version) | Definition | Target | Actual | Previous | Status |
|---|---|---|---|---|---|
| K-MKT-SOURCE@1 | Sessions by first-touch source | trend | | | |
| K-MKT-CONV@1 | Inquiries / sessions per source | set later | | | |
| K-SEO-COVER@1 | Live tours with current keyword data | >= 95 % | | | |
| K-PART-ACT@1 | Tenants activated within 14 days | >= 60 % | | | |
| K-ONB-TTV@1 | Median days to first value | <= 7 | | | |
| K-CX-RESP@1 | Survey response rate | >= 30 % | | | |
| K-CX-CSAT@1 | Share scoring 4-5 | >= 85 % | | | |
| K-CX-NPS@1 | Net promoter score | set later | | | |

## 4. Acquisition (MKT-01)

| Source | Sessions | Trips | Inquiries | Confirmed | Conversion |
|---|---|---|---|---|---|

## 5. SEO and content (MKT-02)

| Page or tour | Impressions | Clicks | CTR | Avg position | Change | Action |
|---|---|---|---|---|---|---|

## 6. Partner onboarding (EX-07)

| Step | Partners reached | Median days from previous step | Stuck > 7 days |
|---|---|---|---|

## 7. Traveller satisfaction (CX-01)

| Cut (destination, style, channel) | Answers | CSAT | NPS | Complaints | Closed on time |
|---|---|---|---|---|---|

Supplier mentions with low scores go to BK-04.

## 8. Decisions needed

| # | Decision | Context | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

## Sources

Views and tables read, Search Console property (if verified), run ids.
