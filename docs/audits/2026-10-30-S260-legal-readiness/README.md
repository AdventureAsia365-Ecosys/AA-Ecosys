# Legal readiness: privacy, terms, DPAs and the AI clause (2026-10-30)

<!-- Report SEC-10 (legal, policy and AI-terms readiness tracker), docs/reports/catalog.yaml. Template:
docs/audits/2026-10-29-S258-report-catalog/templates/readiness-signoff.md (section 6). First version; monthly count
inside SEC-03, full review each quarter, weekly inside OPS-17 once a go-live date is set. The Vietnamese copy for the
business owner is README.vi.md in this folder. Legal items are proposals: whether to involve a lawyer is the
business owner's call. -->

Scope: the twelve readiness topics of the [legal readiness packet](../../legal/readiness-packet.md), the four draft
public pages, vendor DPAs, the tenant AI clause. Prepared: 2026-10-30 (S260) by the tech lead (agent-prepared).
Decision needed by: **2026-11-11** for topic 12 (the AI provider's usage policy takes effect on 2026-11-12); the
others before the first real personal data or the first paying partner.

## 1. Summary

**Not ready; nothing urgent except topic 12.** The packet gives each topic a fact, options and a proposed answer;
no answer has been recorded yet (the decisions log of the [register](../../legal/register.md) section (c) is
empty), so all twelve are open. The four public pages are online as drafts. No vendor DPA is signed. The system
holds no real traveller or customer data (Dev only), so the open items block go-live, not today's work.

| KPI | Value | Target |
|---|---|---|
| K-LEGAL-OPEN, topics without an accepted answer | 12 of 12 | 0 before go-live |
| K-LEGAL-TBC, "[to be confirmed]" points on the four public pages (packet table A.0) | 20 | 0 before go-live |
| K-LEGAL-TBC, "[to be confirmed]" markers in the register | 31 | 0 before go-live |
| K-VEND-DPA, personal-data vendors with a signed DPA | 0 of 8 | 100 % before prod go-live |

## 2. How to read this report

- A topic counts as answered only when the business owner's decision is a row in the register's decisions log.
- Counts were read from the files in this repo on 2026-10-30; each row names the file it comes from.

## 6. Legal topics

| # | Topic | Current fact (short) | Proposed answer (packet) | Decided? |
|---|---|---|---|---|
| 1 | Data controller entity | Both privacy notices say "[to be confirmed]" | The company that runs adventure.asia, full name and address | no |
| 2 | Privacy, cookie and terms wording | Four draft pages live, marked "Draft - pending legal review" | Business owner reads Annex A, answers the business points, then decides on counsel | no |
| 3 | Consent capture | One purpose (contact about the trip); tested 2026-10-20, 0 mismatches | Keep one purpose; add an unticked marketing box only when marketing exists | no |
| 4 | DPA and service providers | DPA template drafted; no vendor DPA signed | Use the template; list every provider | no |
| 5 | Records of processing | Provisional register in place | Use the provisional register now | no |
| 6 | Access and deletion requests | Manual procedure and runbook | Manual now, tested job before real data | no |
| 7 | Data stored in the US | Hosting in us-west-1 | Keep US hosting, prepare transfer documents | no |
| 8 | Service levels | None promised | Response times only until production | no |
| 9 | Support address | Not set up | `support@` to a shared mailbox | no |
| 10 | Status page | None | None until the first paying partner | no |
| 11 | Vercel plan | Hobby (non-commercial) for three web apps | Pro before the first partner is charged (D-18) | no |
| 12 | AI acceptable-use clause | Schedule at Draft v0.2; short summary in the portal terms | A or C: adopt the Schedule now; answer needed by 2026-11-11 | no |

## Draft public pages

| Page | State | Open points (packet table A.0) |
|---|---|---|
| TripPlanner `/privacy` | Draft - pending legal review | entity, legal basis, providers list, transfers, retention, request time, minimum age |
| TripPlanner `/terms` | Draft - pending legal review | operating entity, booking conditions, liability, governing law |
| Portal `/privacy` | Draft - pending legal review | entity, legal basis, AI providers list, transfers, retention, request time, partner DPA |
| Portal `/terms` | Draft - pending legal review | entity, relation to the partner agreement, AI summary approval, notice and termination, content ownership, fees, service levels, governing law |

## Vendor DPAs and AI zero retention

From the register, section (b) "Sub-processors": no DPA has been signed or checked for any vendor. Personal-data
vendors (PII yes or possible): AWS (acc2), the acc2 reseller, Amazon SES, Amazon SNS, Amazon Cognito, Vercel, Mapbox
(IP only), the adventure.asia mail host. AI providers: Bedrock on the LLM account (no zero-retention question for
Bedrock by AWS documentation, to confirm with counsel), the OpenAI API (last resort; abuse logs up to 30 days unless
zero retention is approved), Jev (DM-6.4: a DPA or zero-retention agreement before tenant content is sent).

## Tenant AI clause

[AI acceptable-use clause draft](../../legal/tenant-terms-ai-clause-draft.md): Schedule at Draft v0.2, the portal
terms §3 carry its summary under the draft banner, 14 questions for a lawyer listed in its §6. No real or paying
partner yet, so no notice is due; each partner accepts the Schedule when it joins. The agency CRM does not call the
AI provider yet.

## 7. Blockers

| Blocker | Impact | Plan | Owner role | Date |
|---|---|---|---|---|
| Topic 12 unanswered | The portal summary stays a draft past the 2026-11-12 policy date | Business owner picks A or C | business owner | 2026-11-11 |

## 8. Decision and sign-off

| Decision | Options | Recommendation | Decided by (role) | Date | Result |
|---|---|---|---|---|---|
| Topic 12, AI acceptable-use clause | A adopt now; B lawyer first; C adopt now, lawyer before the first paying partner | A or C (no partners yet, adopting costs nothing) | business owner | by 2026-11-11 | open |
| Topics 1-11 | per the packet | the packet's proposed answers | business owner | before go-live | open |

## Changes since last review

First review.

## Sources

`docs/legal/readiness-packet.md` (last reviewed 2026-10-28), `docs/legal/register.md` sections (b) and (c),
`docs/legal/tenant-terms-ai-clause-draft.md`, read 2026-10-30.
