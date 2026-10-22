# AA Partner CRM: final design

Status: accepted (S246). Owner: nghiep. Related: AA-821, PR-19, AA-928, AA-979. Final, accepted design of the
partner-agency CRM and how it merges with the tenant portal into one app, AA-Partner; it supersedes design v3
where decisions changed it.

S246, 2026-10-21. Agent: Claude Code. Parent issue AA-821 (Jira PR-19). Linear project "Partner CRM — AA-Partner",
issues AA-928 to AA-980.

**What this document is.** The final design. It is design v3 ([`../design-v3.md`](../design-v3.md)) with the
eight decisions D1–D8 applied (all approved as recommended), the two questionnaire rounds applied, the issue cards
mapped to Linear ids, and the delivery plan and portal move re-cut to the S246 master plan
([`../../2026-10-21-S246-master-plan/plan-and-status.json`](../../2026-10-21-S246-master-plan/plan-and-status.json)).
Where this document and v3 differ, this document wins. Long tables (every column, every wireframe at full width,
every issue checklist) stay in v3 and its lanes; this document links to them.

**Errata S247 (bring-your-own integrations).** [`errata-s247-byo.md`](errata-s247-byo.md) changes the integration,
onboarding, sub-processor and cost rows below under [ADR 0010](../../../adr/0010-aa-partner-app.md) decision 9
(Proposed): agencies connect their own vendor accounts, AA's SES sends system mail only, the Twilio subaccount
fallback is removed. Where the two differ, the errata wins once ADR 0010 is accepted.

| Source | Path |
|---|---|
| Spec (Ms. Thư) | [`docs/research/partner-crm-spec.md`](../../../research/partner-crm-spec.md) |
| Design v3 + lanes | [`../design-v3.md`](../design-v3.md); [`../lanes/ux-design.md`](../lanes/ux-design.md), [`../lanes/data-privacy-integrations.md`](../lanes/data-privacy-integrations.md), [`../lanes/delivery-plan.md`](../lanes/delivery-plan.md) |
| v2.2 base decisions (S1–S7, A1, V1–V3) | [`../inputs/crm-v2.2-simplified.md`](../inputs/crm-v2.2-simplified.md), [`../inputs/decisions-v2.2.json`](../inputs/decisions-v2.2.json) |
| Decisions D1–D8 | [`../decisions.json`](../decisions.json) |
| Linear map (53 issues) | [`../linear-issue-map.json`](../linear-issue-map.json) |
| Questionnaire | [`answers.md`](../../2026-10-21-S246-thu-questionnaire/answers.md) (v1, 41), [`reply-to-notes.md`](../../2026-10-21-S246-thu-questionnaire/reply-to-notes.md), [`answers-v2.md`](../../2026-10-21-S246-thu-questionnaire/answers-v2.md) (v2, 12, decided) |
| Ideas R1–R16 / R17–R44, C12, C31 | [`2026-10-20-S245-crm-tern-traveljoy/`](../../2026-10-20-S245-crm-tern-traveljoy/README.md), [`2026-10-21-S246-crm-more-ideas/`](../../2026-10-21-S246-crm-more-ideas/README.md) |

**Conventions.** `Mn` = spec module n; `F1–F5` = foundation modules; `Rn` = approved idea; `Q1 x.y` / `Q2 x.y` =
questionnaire v1 / v2 answer; `N x.y` = reply-to-notes row; `A-nn` / `C-nn` / `S-nn` = agency / client / AA staff
screen; `AA-nnn` = Linear issue; `CRM-nn` = the card name used inside v3. "Agency" in this document is a **tenant**
in platform terms. *(est.)* = estimate.

---

## 0. Summary

1. **What we build.** A CRM that AA gives free to partner travel agencies to run their own clients: inquiry →
   proposal → booking → payment → trip → follow-up. All 23 spec modules (F1–F5, M1–M18) plus the approved ideas are
   built and tested on Dev with synthetic agencies before any real agency is invited.
2. **One app for agencies: AA-Partner.** The CRM and the existing tenant portal (Content studio) become one app in a
   new public repo, AA-Partner, on one host (`portal.`), with one sign-in (a partner Cognito pool, two-step sign-in
   required for owner and agent) and one sidebar. The move is staged (P2a code move ~S255, P1 membership feed ~S256,
   P2b host and sign-in switch ~S258) so Content studio never breaks (§4).
3. **The trip is the folder.** A lead is a trip in the first column. Messages, tasks, proposal, booking lines,
   invoices, documents and audit lines hang off the trip workspace. The board is an action queue with one
   "waiting on" chip: agency (shown as "Me"), client, AA, supplier, none.
4. **AA supply inside the builder.** The "+ Add" drawer shows AA products with B2B price, sell, margin and
   availability (Instant / On request, AA confirms within 1 business day / Sold out). Clients keep or swap options
   per day on a phone page, see the total plus per-option sell deltas, and never create an account.
5. **Holds tied to money.** Accepting a proposal places one hold set per proposal version. The deposit link dies
   at hold expiry; a bank-transfer client who presses "I have paid" gets one bounded hold extension and the agent a
   "verify transfer" task. Cancelling a trip is one action with a dry-run preview.
6. **Privacy by architecture.** Identity (F1) is encrypted per agency and every reveal is logged; AI and AA see
   bands and flags only (F2/F3); AA staff never see agency clients except (a) confirmed-departure ops data, (b) a
   support window the owner grants, (c) a logged break-glass that the agency sees in its own log.
7. **Plan.** 53 Linear issues (AA-928…AA-980). Design effort ≈ 40–45 sessions. The master plan slots W0–W4 into
   S247–S262 (C-M1 "CRM runs on Dev" ≈ S252–S254, C-M2 "full lifecycle with agency goods" ≈ S258–S260, C-M3 "AA
   supply in the CRM" ≈ S261–S265) assuming Ultracode sessions; W5–W8 are re-planned at S262. Without Ultracode the
   design calendar applies: 23 modules on Dev ≈ mid-Feb to end-Mar 2027 (§7).
8. **Cost** *(est., AA AWS per month)*: Dev ≈ $13–22; 10 agencies ≈ $84–97; 50 agencies ≈ $319–344. AA's vendor cost
   is $0: each agency pays its own Stripe, Twilio and mailbox (§8).
9. **Biggest risks.** AA-Booking has no departures, holds or B2B API yet (Lane B builds them); real net rates are
   not entered; effort may still be under-estimated; Twilio's ISV rule; the insurer may refuse self-built e-sign (§9).

---

## 1. Decisions log

### 1.1 Design decisions D1–D8 (all approved as recommended, S246)

| Id | Decision | Resulting rule |
|---|---|---|
| D1 | Client price detail | The client page shows the **total plus per-option sell deltas** ("+$40 pp"), never per-line prices. The agent can switch one proposal to "total only". Enum `proposal.price_visibility = total_with_deltas (default) \| total_only`; `per_line` does not exist. Deltas are computed on the agency's sell price, so no AA B2B price leaks |
| D2 | Bank transfer vs hold expiry (C31) | "I have paid" sets the invoice to `payment_claimed`, the CRM asks Booking **once** to extend the hold (length set by Booking, proposed +72 h) and creates "Verify transfer before <new expiry>". Marked received late → re-hold; if that fails → `paid_unfulfillable` + refund request |
| D3 | Partner pool timing | A separate **partner Cognito pool** with two-step sign-in required (passkey or TOTP) is built on Dev in AA-939 (W2), synthetic users only. The EXTERNAL pool (TripPlanner, Booking travellers) is not changed. ADR 0006 is amended in AA-928 |
| D4 | AA access build order | L1 platform console (no PII) in AA-941 (W2). L2 owner-granted support and L3 break-glass in AA-971 (W7), still before Go-real |
| D5 | Pace | ≈ 2.8 CRM sessions a week, the rest for CIS / Booking / TripPlanner; the weekly CIS/CRM split is stated each session. R28, R36, R40, R41, R42 may land after M4 and before W8. Note "Làm luôn": **start now**, W0 begins at S247 |
| D6 | Data-standards bump | New PII classes `government_id`, `health`, `emergency_contact`; DM-6.8 (Booking never creates a customer for CRM trips, ops data stays in the CRM); DM-7 rows and the DM-7.5 windows in §5.6; signed agreements kept until trip end + 3 years *(est., lawyer confirms)* even after an erasure request |
| D7 | List-view logging | One `audit_event action=list_view` per page load (ids + field name). Lists show the display name only, no partial phone numbers. Passport, DOB, health, emergency contact, full email and full phone stay click-to-reveal, one event per field |
| D8 | v2.2 approval record | v2.2 S1–S7, A1, V1–V3 are approved as recommended; the copy is in [`../inputs/crm-v2.2-simplified.md`](../inputs/crm-v2.2-simplified.md) and is cited by the ADRs in AA-928 |

### 1.2 Questionnaire answers that shape the product

Answers were given by Nghiệp (v1, 41 questions; v2, 12 questions, treated as decided). Items marked "name" still
need Ms. Thư to fill a blank (a person, the legal entity, the current B2B terms, the insurer); the rule itself is
decided.

| Area | Answer | Resulting rule in the product |
|---|---|---|
| Price model (Q1 1.1, N 1.1) | Free for every agency at launch; tiers later | `tenant_entitlement` fields exist from AA-939; Settings shows "Plan: Free". Move to free core + paid tier only when one trigger is hit: CRM cost > $150/month or 20 agencies; an agency asks for a tier feature; an active agency books no AA tour for 2 quarters. 60-day notice clause in the contract; pilot agencies keep the core free forever; fair-use AI |
| Net price (Q2 1.1) | Existing B2B net table (15 % margin); agency sets its own sell price | Builder shows B2B price ("Net"), sell, margin. Booking returns `b2b_price`; `supplier_net` never leaves Booking |
| How AA bills the agency (Q2 1.2) | Current B2B terms, outside the CRM | "Owed to suppliers" for AA is a link to Booking, not an invoice in the CRM. *Name: current B2B terms* |
| Below the public "from" price (Q2 1.3) | Contract clause only | The builder **warns, never blocks** |
| Net-rate entry (Q2 1.4) | AA ops/product team enters rates before the pilot | Go-real (AA-980) blocks without the ops owner's sign-off. *Name: ops person* |
| Support model (Q2 2.1) | Self-serve first; one AA person for all 3–5 pilot agencies | In-app first-run checklist, help pages + 15–20 short videos, office hours every 2 weeks, one shared support inbox (1 business day), kickoff call + week-2 check-in. Help bot only after ~50 real questions. *Name: support person* |
| Group tours (Q1 2.1, R12) | After the 23 modules | Hooks only (`trip.group_departure_ref`, Booking `departure`) |
| Campaigns (Q1 2.2, R14) | Yes, consented contacts only, in the agency's name, AA content blocks | M-level feature in AA-968 with CIS content from AA-977 |
| "Before you go" (Q1 2.3, R38) | AA writes prep packs; visa = official link only; insurance = reminder only | Day 0 of every proposal; packs authored in CIS (AA-977); agency can edit before sending |
| Flight changes (Q1 2.5, R44) | Step 1 only ($0) | T-48 h task "Confirm arrival flight"; paid flight API only after ops report real missed pickups, price approved first |
| Domains and mail (Q1 2.6) | Neutral product domain, optional agency custom domain; mail from the agency mailbox | Client host `go.` now, product domain later |
| Zalo (Q1 2.7) | Not in v1 | Revisit when a VN agency uses real data |
| Privacy promise (Q2 3.3, Q1 3.4, 3.6) | Promise kept, placed in the DPA and the public data page; spec F1 and §8 wording corrected | "AA manages agency accounts without viewing client records. AA staff see data only when the owner grants a time-limited support window (read-only, identity hidden by default). In a security or legal emergency AA can open one agency's data with two-step sign-in, and that access appears in the agency's own log." Exceptions written out: M8 ops release, M17 aggregates |
| Break-glass (Q1 3.4, Q2 6.2) | Emergencies only, MFA, ≤ 1 h, one agency, visible in the agency log, owner emailed within 24 h; a non-engineer AA manager is alerted (notify only) | L3 in AA-971. *Name: second alarm recipient* |
| Support window (Q1 3.5, N 3.5) | Owner-enabled only | 1–7 days, default 24 h, read-only, identity hidden unless ticked, revocable |
| BYOK (Q1 3.6) | Not in v1 | `KeyProvider` with a rewrap contract test, so BYOK later only rewraps DEKs |
| Deletion (Q1 3.7, N 3.7) | Gone in the app at once; unreadable everywhere, backups included, within 30 days | Backups and DEK copies ≤ 30 days with an alarm; fallback wording 90 days |
| Access-log retention (Q1 3.8, N 3.8) | 12 months in the app; then locked archive | Object Lock compliance 12 months + governance to 7 years total |
| Ops visibility (Q1 3.9, 3.10) | The agency log shows "AA ops viewed trip X"; ops gets minimal fields | Names, pax, dietary/mobility flags, flights; passport only if the supplier requires it |
| Sub-processors (Q1 3.11, N 3.11) | List the company, not the account | "Amazon Web Services, Inc.: hosting + AI (Bedrock), US regions" on a public page, 30 days' notice of changes |
| Insights (Q1 3.12, N 3.12) | Spec k ≥ 10, plus ≥ 3 agencies, default included, opt-out on request | No opt-in screen; the owner asks, AA sets the opt-out through L1 |
| Two-step sign-in (Q1 3.13) | Required for owner and agent | Partner pool (D3) |
| Certification (Q1 3.14) | No SOC 2 / ISO now | Public data page states AWS's certifications as AWS's |
| E-sign (Q1 4.1, N 4.1) | Self-built (email code, typed name, consent ticks, sealed PDF) | BoldSign is the fallback slot if the insurer refuses |
| WhatsApp / SMS (N 4.2, Q1 4.3, 4.4) | Agency's own Twilio, one adapter for both; Messenger/IG after the 23 modules | AA pays $0; Twilio's ISV rule checked first (AA-930) |
| Card payments (Q1 4.5, 4.6) | Stripe Connect Standard per agency, no stored cards; VN agencies mark payments manually | VN gateway quotes only when a VN agency uses real data |
| Email (Q2 4.1, N 4.8) | Send-as Gmail **and** Outlook, inbound by forwarding/BCC, no two-way sync | Spec M5 wording corrected; two-way sync only if agencies ask (CASA cost) |
| WAF (Q1 4.9) | Platform cost, on with the first real agency | Part of every future tier's base price |
| Insurance (Q2 5.1, Q1 5.2) | Ask the insurer two things: approve the waiver, accept self-built e-sign | v1 has only "I decline travel insurance", signed with the waiver. In-app insurance sales after the 23 modules; agencies would keep all commission. *Name: insurer and contact* |
| Terms templates (Q1 5.3) | AA drafts EN–VI templates from current terms; sales reviews; insurer approves | Library seeds in AA-955 |
| Vendor verifications (N 6.1) | Start the day the 23 modules are done | Google, Microsoft (and Meta only if Twilio requires it) in W8 |
| Departures (Q2 6.1) | Fixed departures auto-confirm; others on request, AA ops answers within 1 business day | Booking `departure.auto_confirm`; on-request desk in the Booking staff admin. *Name: departure owner* |
| Owner leaves (Q1 6.3) | AA promotes an existing member after 14 days, old owner emailed, logged | L1 action; every member sees a banner with [Cancel] |
| Legal (Q2 3.1, 3.2) | Existing AA partner-contract entity + drafted DPA; lawyer at the first of: a VN/EU agency wants real data, a 6th agency, 60 days after the first real client | *Name: legal entity* |

### 1.3 Ideas and flow gaps

| Item | Status | Rule |
|---|---|---|
| R1–R16 (S245) | Approved; R15 (call booking + calendar) and R16 (offline itinerary) moved to "add now" | R11 = entitlement fields only; R12 = hooks only; R13 = signed decline only |
| R17–R44 (S246) | Approved; R41 (voice profiles) and R42 (what's new + preview) were recommended "later" but are included | R28, R36, R40, R41, R42 may land after M4, before W8 (D5) |
| C12 one-action cancel, C31 deposit link tied to hold | Approved (AA's own flow gaps) | §3.3 flows, §5.4 rules |
| C13 "show total only" | Not approved | Replaced by D1 |
| C47 repeat inquiry attaches to the open trip | Folded into R6 + M1 dedupe | AA-936 |
| C39 drafts / scheduled send | Autosaved drafts = basic M5; scheduled send not built | AA-945 |
| C34 "view as client" checklist step | Dropped | "Preview as client" in the builder covers it |

### 1.4 What changed from v3

- **Status:** v3 was a draft with eight open decisions; this design is accepted.
- **Portal move:** v3 had one step P2 after P1. Final: **P2a (code move, keeps Vercel and API-key sign-in) → P1 →
  P2b (host + partner-pool sign-in)**, Vercel kept ≥ 7 calendar days after P2b (§4).
- **Sign-in before P2b:** v3 said CRM W1 shares a session with the portal through the `cis-portal` client. The
  portal still signs in with the tenant API key (checked 2026-10-21), so there is no shared session until P2b.
  Synthetic CRM users sign in separately until then.
- **Delivery:** cards carry Linear ids and master-plan session slots; milestones are named C-M1/C-M2/C-M3/P-M1 to
  match the master plan (v3's M1–M5 map onto them, §7).
- **v2.2 copy:** done ([`../inputs/crm-v2.2-simplified.md`](../inputs/crm-v2.2-simplified.md)); X1 closed.

---

## 2. Scope and traceability

### 2.1 Scope

| Bucket | Items |
|---|---|
| Build before any real agency (W0–W7) | F1–F5, M1–M18; R1–R10, R15–R44 (R38 content in CIS, R43 in-app part, R44 step 1); R11 entitlement fields; R13 signed decline; R14 campaigns; C12; C31 |
| Go-real (W8, AA-980) | Prod placement, prod partner pool, WAF, vendor verifications, Stripe live per agency, DPA, public data page, sub-processor page |
| After the 23 modules (backlog, no issues) | R12 group departures; in-app insurance sales; Messenger/IG; BYOK; help bot; paid flight API; two-way mail sync; Zalo; tier billing; VN payment gateway |
| Not in scope | Post-trip rating form; Content studio → CRM "start a proposal with this tour" link (suggestion only) |

### 2.2 Spec module → screen → entity → Linear issue

Entities are in schema `crm` unless noted. Full column lists: v3 §3.3 and
[`data-privacy-integrations.md`](../lanes/data-privacy-integrations.md) §2.

| Spec | Screens | Main entities | Issues |
|---|---|---|---|
| F1 identity vault | A-03 Travellers, A-07, A-08 (masked + reveal), C-07, C-08 | `traveler`, `traveler_health`, `traveler_flight`, `document`, `consent`, `tenant_key` | AA-934, AA-937, AA-953, AA-971 |
| F2 pseudonymous profile | A-07 profile, A-04 defaults | `traveler_profile`, `trip_party`, `profile_history` | AA-936, AA-937 |
| F3 PII filter | A-21 AI cards | `placeholder_map`, `llm_call` | AA-938, AA-964 |
| F4 tenancy and roles | A-18 Team, Security; S-01; S-04 | `tenant`, `member`, `owner_recovery_request`, `support_grant`, RLS | AA-933, AA-935, AA-939, AA-941, AA-971, AA-978 |
| F5 audit | A-18 Access log, A-03 Activity | `audit_event`, `audit_export_manifest` | AA-936, AA-940, AA-941, AA-956, AA-971 |
| M1 intake | C-01, A-18 Forms & embed | `intake_form`, `form_definition`, `form_submission` | AA-936, AA-943 |
| M2 pipeline | A-02, A-03 | `trip` (+ transitions, history), `task`, `note`, `tag` | AA-936, AA-943 |
| M3 interactive proposal | A-04, C-03, C-04, C-12 | `proposal`, `proposal_day`, `option_block`, `option`, `option_rule`, `selection`, `client_link`; Booking quote/hold | AA-948, AA-949, AA-950 (+ AA-947, AA-972, AA-973, AA-974) |
| M4 text proposal | A-05 | `proposal.price_hash`, `message_template` | AA-946, AA-951 |
| M5 email | A-08, A-18 Channels | `channel_account`, `ingest_address`, `conversation`, `message`, `dispatch_queue` | AA-945 |
| M6 bookings ledger | A-03 Bookings, A-11 | `booking_line`, `booking_line_money`, `agency_supplier` | AA-944, AA-947, AA-975 |
| M7 invoices and payments | A-10, A-03 Payments, C-04, C-10 | `invoice`, `payment_schedule`, `payment`, `refund_request`, `payment_provider_account` | AA-946, AA-952 |
| M8 AA ops release | S-02, A-03 Activity, A-18 Access log | `ops_release`, `supplier_manifest_export` | AA-956 |
| M9 WhatsApp/SMS | A-08, A-18 Channels | `conversation`, `message`, `integration_credential` | AA-958 |
| M10 workflows | A-17, A-09, A-16 | `workflow_template`, `workflow_rule`, `workflow_run`, `task` | AA-959, AA-960 |
| M11 client portal | C-05 – C-10 | `client_link`, `traveler_access`, `otp_challenge` | AA-946, AA-953, AA-954 |
| M12 contracts and waivers | C-08, A-16 Terms, A-03 Travellers | `agreement_doc`, `terms_acceptance`, `signature_request`, `signature_event` | AA-946, AA-955 |
| M13 commission | A-12, A-03 Bookings | `commission` | AA-957 |
| M14 AI layer | A-21 cards, A-00 meter, A-18 AI | `ai_draft`, `voice_profile`, `spend_budget`, `llm_call` | AA-936 (stub), AA-964, AA-965 |
| M15 supplier directory | A-13, A-04 drawer | `agency_supplier` (AA built-in row) | AA-944 |
| M16 agency reports | A-14, A-01 | `metric_event`, `metric_daily` | AA-966 |
| M17 AA insights | S-03; A-18 "Included, request opt-out" | `insight_fact` view → `insight_aggregate` | AA-966 |
| M18 portability and deletion | A-18 Export/Trash, A-07 Export/Delete | `export_job`, `erasure_request`, `crm.erase_subject()` | AA-942, AA-967 |
| §4 pipeline + gates | A-02, A-03, gate dialog | `trip.stage` incl. `cancelled` | AA-943, AA-957 |
| §5 traveller info panel | A-03 Overview, A-09 | `trip.intake_completeness`, `form_definition` | AA-943, AA-959 |
| §9 AA inventory + builder | A-04 | Booking `b2b_*`, `departure` | AA-972, AA-973, AA-975, AA-947, AA-948, AA-949 |
| §11.5 onboarding | A-20, A-01 checklist | import jobs | AA-962 |
| §11.6 NFR | all screens | — | AA-935, AA-969 |
| §11.7 events | — | `metric_event` | AA-966 |

### 2.3 R and C items → screen → Linear issue

Entities per item: v3 §1.4.

| Id | Item | Screens | Issues |
|---|---|---|---|
| R1 | Waiting on + bulk by stage | A-02, A-03 | AA-943 |
| R2 | Special dates | A-07, A-17, A-09, A-15 | AA-959 |
| R3 | Tags + tag workflows | A-02, A-06, A-07, A-17 | AA-960 |
| R4 | Proposal viewed + nudge | A-03, A-02, A-00 | AA-950 |
| R5 | AI usage meter | A-00, A-18 | AA-964 |
| R6 | Merge duplicates + staged import (+ C47) | A-06, A-07, A-20, C-01 | AA-936, AA-962 |
| R7 | Relationships + multi-traveller form | A-07, C-01 | AA-937, AA-943 |
| R8 | Agency owns clients; owner reassigns | A-03, A-07, A-18 | AA-939 |
| R9 | Template library + AA content | A-16, A-04 | AA-977, AA-951, AA-959, AA-963 |
| R10 | AI reads supplier confirmations | A-03, A-08, A-21 | AA-965 |
| R11 | Tiers (free now) | A-18 Plan & usage | AA-939 |
| R12 | Group booking (later) | reserved slot | hooks in AA-973, AA-943 |
| R13 | Insurance decline only | C-07, C-08, A-03 | AA-955 |
| R14 | Consent campaigns | A-15, C-11 | AA-977, AA-968 |
| R15 | Call booking + calendar sync | C-01, A-18, A-09 | AA-943, AA-961 |
| R16 | Offline itinerary | C-09, C-05 | AA-954 |
| R17 | FX rules | A-03, A-10, A-14, A-18 | AA-944, AA-947, AA-957 |
| R18 | Line status + strictness | A-03, A-11, A-18 | AA-944, AA-947, AA-975 |
| R19 | Choice diff | A-03, A-00 | AA-950 |
| R20 | Task buckets + relative dates | A-09, A-00 | AA-959 |
| R21 | Trash + "Cancel instead of Delete" | A-03, A-18 | AA-933, AA-942, AA-957 |
| R22 | Per-person client view | C-05 – C-10, A-03 | AA-953 |
| R23 | Archive + Lost reasons | A-07, A-02, A-14 | AA-942, AA-947, AA-966 |
| R24 | Sender table + reconnect | A-08, A-18, A-05 | AA-945 |
| R25 | Pay on arrival | A-04, A-03, C-03, C-04, A-10 | AA-976, AA-952 |
| R26 | Grouped confirmation + decline task | C-04, A-03, A-09 | AA-950, AA-952 |
| R27 | Service-fee invoice | A-10, A-18, C-10 | AA-952 |
| R28 | Year-on-year KPI tiles | A-01, A-14 | AA-966 (may land after M4) |
| R29 | System-tag workflows | A-17, A-02 | AA-976, AA-960 |
| R30 | Missing-workflow badge | A-02, A-17 | AA-960 |
| R31 | Conditional forms | C-01, C-02, C-07, A-16 | AA-943 |
| R32 | Locale dates + age band | A-00, A-07, A-04, client pages | AA-935, AA-937 |
| R33 | Time zones + overnight flights | A-04, C-07, C-09, S-02 | AA-949, AA-953, AA-956 |
| R34 | Versioned terms | C-04, A-16, A-18 | AA-955 |
| R35 | Global search | A-00 | AA-963 |
| R36 | Ready to travel again | A-15, A-07 | AA-960 (may land after M4) |
| R37 | Where are my clients + incident flag | A-02 Travelling now; Booking staff admin | AA-975, AA-961 |
| R38 | "Before you go" | A-04, A-16, C-03, C-09 | AA-977, AA-951 |
| R39 | AI guardrails | A-21 | AA-964 |
| R40 | Notes → AA options | A-04, A-03 | AA-965 (may land after M4) |
| R41 | Voice profiles | A-18 AI, A-05 | AA-965 (may land after M4) |
| R42 | What's new + preview switch | A-00, A-18, S-01 | AA-970 (may land after M4) |
| R43 | Self-serve onboarding / support | A-20, Help | AA-962, AA-970 |
| R44 | T-48 h flight task (step 1) | A-09, S-02 | AA-956, AA-959 |
| C12 | One-action cancellation | A-03, cancel dialog, A-10 | AA-974, AA-943, AA-956, AA-957 |
| C31 | Link valid until hold expiry | C-04, C-12, A-10, A-09, A-02 | AA-973, AA-974, AA-950, AA-952 |

---

## 3. Product and UX

### 3.1 Who uses which host

| Host (Dev) | Users | Sign-in | Contains |
|---|---|---|---|
| Agency app `portal.lumiguides.it.com` → AA-Partner. The CRM runs on `partner-dev.` until P2b | Owner, agent, assistant; AA support only inside a granted session | Partner pool from AA-939; two-step sign-in required for owner and agent | CRM + Content studio (one shell after P2b) |
| Client pages `go-dev.` (later a neutral product domain, optional agency custom domain) | Travellers and prospects | Signed link for forms and proposal; email code per person for the client portal | C-01 … C-12 |
| CIS admin `aa-cis.` | AA staff (WORKFORCE + MFA) | Existing | S-01 "Agencies (CRM)" (no PII), S-03 insights |
| AA-Partner staff routes | AA ops (`crm-ops`), AA support (`crm-support`) | WORKFORCE, separate app client | S-02 ops release, S-04 support session |
| Booking staff admin | AA ops | Existing | On-request desk, "Flag incident on departure" |

Cookies are host-only: the agency and client hosts never share a session. AA never messages travellers in its own
name; the agency is the brand on every client page.

### 3.2 Agency information architecture (the one AA-Partner sidebar)

```text
AA Partner  [agency name v]                         [Search Ctrl+K] [+ New] [Tasks] [Bell] [AI 62%] [EN|VI] [me v]
-------------------------------------------------------------------------------------------------------------------
HOME                A-01  KPI tiles, "needs you", first-run checklist (3 required + optional)
CRM   Pipeline      A-02  Board | List | Travelling now | Closed (Lost, Cancelled, Completed)
      Clients       A-06  Directory, tags, archived, duplicates
      Inbox    [5]  A-08  Email, WhatsApp, SMS, AI drafts, Unmatched, Waiting for reconnect
      Tasks    [7]  A-09  Overdue / Today / Upcoming / Later / Waiting for dates
MONEY Payments      A-10  Receivables, schedules, reminders queue, owed to suppliers
      Bookings      A-11  All booking lines across trips
      Commissions   A-12  Expected vs received                                        (hidden: assistant)
GROW  Reports       A-14  Conversion, margin, sources, option picks                  (margin hidden: assistant)
      Marketing     A-15  Ready to travel again, special dates, campaigns            (owner/agent)
      Suppliers     A-13  AA (built in) + own suppliers
      Library       A-16  Itinerary items, task lists, messages, forms, prep packs, terms/waivers
      Automations   A-17  Workflows, tags, triggers                                  (owner edits; agent applies)
CONTENT STUDIO            existing portal pages (§4.3): Brand, Rewrite, Tour pool, Social planning,
                          Angle gate, My content, Publish, Marketplace, Activity
-------------------------------------------------------------------------------------------------------------------
Settings            A-18  Agency & branding, Team & roles, Security, Channels, Payments, Forms & embed, AI,
                          Data & privacy, Trash, Plan & usage, API keys (machine access)
Help & what's new         R42, R43
```

Items a role cannot use are hidden, not disabled. Inside a trip (A-03) the tabs are Overview · Proposal · Bookings ·
Payments · Travellers & docs · Messages · Tasks & notes · Activity; the builder (A-04) opens full screen.

**Global shell (A-00):** search (`bk-` codes, supplier confirmation numbers, phones and emails by exact blind index;
accent-insensitive on non-PII), `+ New`, tasks and notes drawers, bell (viewed/chosen, re-hold placed, payment
claimed/received, hold expiring, AA confirmed/declined, AA incident, mailbox disconnected), AI meter (75/90/100 %;
at 100 % AI stops), EN/VI with locale dates, an amber support banner that cannot be dismissed, and a 10-second Undo
for moves, bulk actions, archive and delete (queued sends are cancelled by Undo; bulk sends say "Undo until sent").

### 3.3 Main flows

| Flow | What happens | Key rules |
|---|---|---|
| F1 Inquiry | Prospect submits C-01 → dedupe by blind index (a repeat attaches to the open Inquiry) → traveller (F1) + profile (F2) + companions + trip at Inquiry + "Reply within 2 h" task + confirmation mail | Card on the board within ~1 min, waiting on "Me" |
| F2 Qualifying | Agent sends C-02 (or a workflow does) or fills in from a call | Gate to Proposal: Stage 2 ≥ 80 % or a logged override (409 `stage2_incomplete`) |
| F3 Build (A-04) | Skeleton from Stage 2; agent sets rooms; AA items from the "+ Add" drawer, agency items from Suppliers/Library; sell or markup; pay-on-arrival lines; per-day time zones; Day 0 "Before you go"; Preview as client → Publish vN | Below AA "from" price warns only. Day-list builder; the map (AA-948) is an enhancement and never blocks M3 |
| F4 Send (A-05) | Visual link, email text or WhatsApp/SMS text, all sharing one `price_hash`; template or AI draft; a human sends | Mail goes send-as from the agency mailbox; a dead token holds it in "Waiting for reconnect" |
| F5 Client choice (C-03) | Keep or Swap per block, live re-price; "Request a change" sends one bundled diff | "Choose later" only for agency-supplier items. Viewed but no choice for 2 days → nudge. Booking down → "last checked", Accept disabled |
| F6 Accept, hold, deposit (C-04) | Grouped lines → client **confirms** travellers and rooms → accepts the terms version, types full name → one hold set per proposal version → pay by card (Stripe Checkout on the agency's account, expires with the earliest hold) or bank transfer ("I have paid" → D2) | Paid → Booked; AA lines go to confirm; each traveller gets a portal invite; Stage 3 unlocks |
| F7 Booking lines | `planning → confirmed → cancelled`; only `confirmed` counts. AA lines fill from the Booking feed and are read-only | AA decline → task [Swap product] / [Refund that part] |
| F8 Pre-trip | Each traveller signs in with their own code, fills Stage 3, signs terms + waiver + insurance decision in one envelope. Ops release created when an AA line is confirmed, refreshed as Stage 3 fills | Gate to Pre-departure: Stage 3 complete + waiver signed. T-21 nudges; passport expiring within 200 days of return → task; T-48 h flight task |
| F9 Travelling | Moves on the departure date even if the gate is unmet (timeline note + urgent task). "Travelling now" groups by AA region. AA incident → banner + WhatsApp draft per affected agency | Offline itinerary for travellers |
| F10 Post-trip | Completed on the return date; "Welcome home" draft; commission expected vs received; ops release purged at return + 90 days with a receipt | Ready-to-travel-again and special dates feed Marketing, consent required |
| Side: Lost | Fixed reasons (price, price AA tour, AA sold out, AA declined, dates changed, went elsewhere, no response, postponed, other), pre-selected from the Booking feed | Client can be archived |
| Side: Cancel trip (C12) | Dialog with dry-run preview and typed CANCEL: AA lines cancelled with Booking's fee; one task per agency supplier; invoices voided; refund requests (approval matrix); commission cancelled; ops release withdrawn; workflows stop; stage `cancelled` | Booking down → "cancellation pending", never "cancelled" early |
| Side: Onboarding | 3 required steps (connect Gmail or Outlook, invite the team, embed the inquiry form); the rest has "Later" | Safe defaults, no forced settings |

### 3.4 Screen index

| Agency (A-) | Client (C-) | AA staff (S-) |
|---|---|---|
| A-00 shell, A-01 Home, A-02 Pipeline, A-03 Trip workspace, A-04 Builder, A-05 Send, A-06 Clients, A-07 Client profile, A-08 Inbox, A-09 Tasks, A-10 Payments, A-11 Bookings, A-12 Commissions, A-13 Suppliers, A-14 Reports, A-15 Marketing, A-16 Library, A-17 Automations, A-18 Settings, A-20 Onboarding/import, A-21 AI card | C-01 Inquiry form, C-02 Planning form, C-03 Proposal, C-04 Accept + deposit, C-05 Code sign-in, C-06 Portal home, C-07 My forms, C-08 Sign, C-09 Itinerary (offline), C-10 Payments, C-11 Preferences/unsubscribe, C-12 Link or hold expired | S-01 Agencies (CRM) console (CIS admin), S-02 Ops release, S-03 AA insights, S-04 Support session |

### 3.5 Wireframes

The expected look of the key screens. Remaining screens (client profile, send dialog, payments, tasks, reports,
dialogs) are at full width in [`ux-design.md`](../lanes/ux-design.md) §4; where they differ from v3 §2.8, v3 wins.

**WF-1 Pipeline board (A-02).** The board is an action queue: the chip row filters by who must act next.

```text
+------------------------------------------------------------------------------------------------------------------+
| AA Partner | [ Search trips, clients, bk-1234, conf. no, phone  Ctrl+K ] [+ New] [Tasks 7] [Bell 3] [EN|VI] [ML] |
+------------+-----------------------------------------------------------------------------------------------------+
| HOME       | Pipeline              View: [Board] List  Travelling now  Closed         [Filters v] [Saved views v]|
| CRM        | Waiting on: (All) (Me 9) (Client 14) (AA 2) (Supplier 3)   Owner: [Anyone v]  Tags: [trekking x]    |
| >Pipeline  | ! 4 trips quiet for more than 3 days  [Show]              ! 2 holds expire in 24 h  [Show]          |
|  Clients   +---------------+---------------+---------------+---------------+---------------+---------------+------+
|  Inbox  5  | INQUIRY 6  [:]| QUALIFYING 5[:]| PROPOSAL 8 [:]| BOOKED 4   [:]| PRE-DEP 3  [:]| TRAVELLING 2  | DONE |
|  Tasks  7  |  $ -          |  $ -          |  $48.2k sell  |  $31.0k       |  $22.4k       |               | >    |
| MONEY      | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ |      |
|  Payments  | |Sapa trek  | | |Ha Giang 6d| | |Laos+Cambo.| | |Mekong 4d  | | |Nepal ABC  | | |Hoi An fam.| |      |
|  Bookings  | |Anna M. +2 | | |Tom K.     | | |Lee family | | |Ruiz x2    | | |Kim S. +1  | | |Do family  | |      |
|  Commiss.  | |Mar 27 ~   | | |Apr 27     | | |12-26 Feb  | | |3-6 Jan    | | |T-19       | | |day 3/9    | |      |
| GROW       | |$1.5-2.5k  | | |S2 60%     | | |v2 viewed  | | |AA 2/3 conf| | |S3 2/2 ok  | | |           | |      |
|  Reports   | |[Me] 2h    | | |[Client]   | | |[Client] 1d| | |[AA] 6h    | | |waiver 1/2 | | |[None]     | |      |
|  ...       | |trekking   | | |quiet 4d ! | | |hold 20h ! | | |           | | |[Me]       | | |           | |      |
| CONTENT    | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ |      |
| STUDIO  >  |               |               |               |               |               |               |      |
| Settings   | Lost / Cancelled are under "Closed". Drag a card to move stage; gates ask for a reason when not met. |
+------------+-----------------------------------------------------------------------------------------------------+
Column menu [:] on PROPOSAL: send follow-up to clients waiting > 2 days (undo until sent) . apply workflow (preview
count) . tag . reassign (owner) . mark lost (reason) . "3 trips missing workflow X" [Preview][Run]
```

Cards never show margin. The AA chip means an on-request line is pending; its action is "Escalate to AA ops". On a
phone the board shows one stage per screen with swipe.

**WF-2 Trip workspace (A-03), Overview.** One place for everything about a trip.

```text
+------------------------------------------------------------------------------------------------------------------+
| < Pipeline   Laos + Cambodia, 14 days  [PROPOSAL v]  Waiting on: [Client v] since 1 d   Owner: Minh L. [v]       |
|              Lee family (4) . 12-26 Feb 2027 . AUD . tags: family, culture [+]          [Cancel trip] [... ]       |
| Overview | Proposal (v2 sent) | Bookings 3 | Payments | Travellers & docs 4 | Messages 6 | Tasks & notes 2 | Activ.|
+--------------------------------------------------------------+---------------------------------------------------+
| TRAVELER INFO                                                | NEXT ACTIONS                                      |
| [ok] Basics (Stage 1)            100%                        | [ ] Follow up if no choice by Fri   due Fri  Me    |
| [..] Planning info (Stage 2)      60%  missing: fitness,     | [+ task]                                          |
|      dietary   [Send follow-up form] [Fill in from call]     |                                                   |
| [lock] Booking details (Stage 3)  locked until deposit paid  |                                                   |
+--------------------------------------------------------------+---------------------------------------------------+
| PROPOSAL                                                     | MONEY (owner/agent only)                          |
| v2 published 18 Oct . viewed 19 Oct 21:04 (3x) . no choice  | Sell AUD 18,640  Net 15,220  Margin 3,420 (18%)   |
| Client picks so far: Day 3 Lodge (+$40) . Day 7 kept         | Deposit 30% on accept . Pay on arrival AUD 180    |
| Holds: none yet (placed at accept)                           | (assistant sees Sell and payments only)           |
| [Open builder] [Send reminder] [Preview as client]           |                                                   |
+--------------------------------------------------------------+---------------------------------------------------+
| TIMELINE                                      [All] [Messages] [Client actions] [System] [Notes]               |
| 19 Oct 21:06  Client chose Day 3: Homestay -> Riverside Lodge  +$40 sell / +$12 margin  [available, instant]   |
| 19 Oct 21:04  Client viewed proposal v2 (phone)                                                                |
| 18 Oct 10:15  Minh sent proposal v2 by email + WhatsApp text (same price hash 7f3a)                            |
| 18 Oct 10:14  Stage moved Qualifying -> Proposal (gate override: "call covered fitness", Minh)                  |
| 14 Oct 08:51  Inquiry received from website widget (source: AA blog "Laos slow travel")                        |
+------------------------------------------------------------------------------------------------------------------+
```

Bookings tab columns: Day · Item · Supplier · Conf. no · Status (AA rows from the feed) · Cost · Sell · FX (rate @
date) · Collect (agency / on arrival). Travellers tab: identity fields show fully masked as `••••` (no partial
digits) with [Reveal]/[Copy], each logged with a reason.

**WF-3 Proposal builder (A-04).** AA stock opens from "+ Add"; the map is collapsed by default; rules sit under
Advanced.

```text
+------------------------------------------------------------------------------------------------------------------+
| < Trip  Laos + Cambodia   Working copy v3 . Published v2 (viewed 19 Oct)        [Preview as client] [Publish v3] |
| Sell AUD 18,680 . Net 15,248 . Margin 3,432 (18.4%) . Pay on arrival 180 . AUD                       [Send...]   |
+------------------------+-----------------------------------------------------------------------------------------+
| DAYS          [+ Day]  | DAY 3  Luang Prabang  (UTC+7)                                       [Map v] (collapsed)|
|  0 Before you go       | OPTION BLOCK: Lodging        default from Stage 2         client may swap [on]          |
|  1 Arrive LPQ          |  (*) Homestay Ban Xang  comfort   Instant      net 140 . sell 280         default       |
|  2 Kuang Si            |  ( ) Riverside Lodge    comfort   On request   net 252 . sell 440 . +40 pp sell         |
| >3 Luang Prabang       |      AA confirms within 1 business day . requires Day 4 private slow boat               |
|  4 Mekong slow boat    |  ( ) Amantaka           luxury    Sold out 12-14 Feb (cannot add)                       |
|  ...                   | OPTION BLOCK: Morning                                                                   |
|  14 Depart PNH         |  (*) Alms + market walk (AA)  Instant      ( ) Cooking class (agency)  Agency books     |
| Rooms: 1 family (2A2C) |  [+ Add] -> drawer: [AA inventory (live, synced 10:42)] [Suppliers] [Library]            |
| Checks:                |  > Advanced: requires / excludes rules . choose later (agency items only)               |
| ! Day 1 lands 19:40    |  [AI: ideas from call notes]  (suggestions from AA stock only, preview card)            |
+------------------------+-----------------------------------------------------------------------------------------+
| ! Sell for "Kayak" is below the AA public "from" price: warning only                                             |
+------------------------------------------------------------------------------------------------------------------+
```

The assistant sees no Net or Margin. If AA is offline the drawer says so and AA adds are disabled. Shortening dates
re-quotes and shows a before/after diff. Building is a desktop task; the phone handles edits (swap, price, text).

**WF-4 Client proposal (C-03), phone first.** No login, no traveller names, no net or per-line prices.

```text
+----------------------------------------------+
| [Agency logo]           Laos + Cambodia      |
| 12-26 Feb 2027 . 2 adults, 2 children         |
| Prepared by Minh, Sunshine Travel            |
| Total  AUD 18,680                            |
| (park fees AUD 180 paid on arrival)          |
| [ Accept and continue ]                      |
| Before you go  >  (packing, visa links, ...)  |
| -------------------------------------------- |
| DAY 3 . Luang Prabang . Where you stay       |
| | [photo] Homestay Ban Xang       Included | |
| |  Family room, garden.  [Keep] (selected) | |
| | [photo] Riverside Lodge          +$40 pp | |
| |  Confirmed by our partner within 1       | |
| |  business day after you accept           | |
| |  Needs the private slow boat on Day 4    | |
| |                         [Swap to this]   | |
| | [photo] Amantaka        Not available    | |
| Morning: Alms + market walk     Included     |
|          Cooking class    +$25 pp [Swap]     |
| [Ask for a change on Day 3]                  |
| Questions? [Email Minh] [WhatsApp Minh]      |
| Agency terms . Privacy                       |
+----------------------------------------------+
```

**WF-5 Accept and deposit (C-04) and hold expired (C-12).**

```text
+----------------------------------------------+
| 1 Review . 2 Travellers & rooms . 3 Terms . 4 Pay |
| CONFIRMED AS SOON AS YOU PAY                 |
|   Luang Prabang 3 days, Kuang Si, ...        |
| CONFIRMED BY OUR PARTNER WITHIN 1 BUSINESS DAY|
|   Riverside Lodge (Day 3) - alternative or   |
|   refund of that part if not available       |
| YOUR AGENT BOOKS                              |
|   Hotel in Siem Reap (Day 8-10)              |
| PAID ON ARRIVAL (not charged now)  AUD 180   |
| Travellers: 2 adults, 2 children (7, 9)      |
| Rooms: 1 family room   [Ask for a change]    |
| [x] I accept Sunshine Travel's booking terms |
|     (version 2026-09)                         |
| Full name [ Grace Lee               ]         |
| Deposit now (30%)              AUD 5,604     |
| Balance due 12 Dec 2026        AUD 13,076    |
| Your places are held until 23 Oct, 17:00.    |
| [ Pay deposit by card ]                      |
| [ Bank transfer -> details + "I have paid" ] |
+----------------------------------------------+
C-12: "Your reservation hold has expired" [Check availability again] (3 a day) -> new hold, maybe a new price;
      after the 3rd: "Ask your agent".
```

**WF-6 Client portal (C-05 / C-06).** Every traveller signs in with their own email code.

```text
Sign-in (C-05)                                   Home for a companion (C-06)
+----------------------------------------------+ +----------------------------------------------+
| [Agency logo]  Your trip: Laos + Cambodia    | | Hi Tom                     [EN|VI] [Sign out]|
| Email (hint t***@o*****.com)  [Send code]    | | Laos + Cambodia . 12-26 Feb 2027 . T-112     |
| Code [ _ _ _ _ _ _ ]  [Continue]  (10 min)   | | TO DO: My details 2/6 > . Sign terms + waiver|
| If this email belongs to 2+ travellers:      | |        > . Insurance: I have my own [x]      |
|   "Who are you?"  [Tom] [Lily (guardian)]    | | ITINERARY > (works offline)                  |
+----------------------------------------------+ | DOCUMENTS > (online only, mine)              |
Lead home adds: PARTY STATUS (progress only,     | [Email Minh] [WhatsApp Minh]                 |
not data) . [Fill for Max] . PAYMENTS balance >  +----------------------------------------------+
```

**WF-7 Inbox (A-08).**

```text
+------------------------------------------------------------------------------------------------------------------+
| Inbox  [All] [Email] [WhatsApp] [SMS] [AI drafts 3] [Unmatched 2] [Waiting for reconnect 0]   [Mine v]           |
+---------------------------------+--------------------------------------------------------+-----------------------+
| Grace Lee - Laos+Cam.   WA  2m  | Grace Lee  (WhatsApp ••••••)  [Reveal]                 | TRIP Laos + Cambodia  |
| "Can Max do the kayak?"         | 19 Oct 21:10  Grace: Can Max do the kayak? He is 7.   | PROPOSAL . waiting on |
| Unknown sender         WA  3h   | 19 Oct 21:12  (internal note, Minh) min age is 8 ...  |   Me                  |
| "Hi, saw your tour..."  [Link]  | AI DRAFT (review before sending)      [+] [-] reason   | [Open trip]           |
|                                 | "Hi Grace, the kayak trip has a minimum age of 8 ..."  | [Insert proposal link]|
|                                 | checked: in stock . price unchanged                    | [Saved replies v]     |
|                                 | [Use draft] [Edit] [Discard]                           |                       |
|                                 | WhatsApp window open 21 h left (outside: templates)    |                       |
|                                 | [Type a reply...]               [Template v] [Send]    |                       |
+---------------------------------+--------------------------------------------------------+-----------------------+
| Email: sent from minh@sunshine.au (send-as) . inbound via forwarding address (BCC also works)                    |
+------------------------------------------------------------------------------------------------------------------+
```

The conversation list shows display names only (D7): an unmatched sender appears as "Unknown sender", never as a
partial phone number; the number shows only after [Reveal], which is logged.

**WF-8 Settings, Data & privacy (A-18).** One settings area for CRM and Content studio after P2b.

```text
+---------------------------+--------------------------------------------------------------------------------------+
| Agency & branding         | DATA & PRIVACY                                                                       |
| Team & roles              |  AA support access: [off] -> Allow for [24 h v] (1-7 days), read-only,               |
| Security (2-step)         |     show traveller identity [ ]   (every view is logged; revoke any time)            |
| Channels                  |  Access log: [user] [AI] [AA ops] [AA support] [AA emergency]          [Download]   |
|   Email . WhatsApp & SMS  |   20 Oct 14:02  AA ops viewed trip "Nepal ABC" (ops release)                         |
|   Calendar                |   19 Oct 09:11  Minh revealed passport (Tom) - reason: supplier booking              |
| Payments (Stripe / bank,  |  AA insights: included (groups >= 10 travellers, >= 3 agencies) [Request opt-out]    |
|   deposit rules, FX auto, |  Export all data . Trash (7 days)                                                    |
|   service fee off, line   |                                                                                      |
|   rules Basic)            |                                                                                      |
| Forms & embed . AI (off)  |                                                                                      |
| Data & privacy            |                                                                                      |
| Plan & usage: Free        |  (from the portal: plan and usage)                                                   |
| API keys                  |  (from the portal: machine access to the content API)                                |
| What's new . preview [ ]  |                                                                                      |
+---------------------------+--------------------------------------------------------------------------------------+
```

### 3.6 Client-page rules

1. **No accounts.** Signed links for forms and the proposal; on first open the token becomes a host-only cookie and
   is stripped from the URL, but stays valid until `expires_at` so a second device works. Opens are rate-limited;
   the agent can re-issue a link, which revokes the old one. The portal uses a 6-digit email code per person,
   asked again at signing.
2. **Per person.** Each traveller sees their own forms, documents flagged visible to travellers, the itinerary and
   their own signatures. The lead also sees party progress (not data) and payments.
3. **Never shown:** other travellers' data, passports after upload, B2B price or margin, per-line prices, cancelled
   lines, internal notes, AI drafts.
4. **Stages.** Stage 3 only after the deposit; health only after consent; answers as bands. Signed-link forms
   pre-fill bands only; identity fields only inside the portal.
5. **Money.** Deposit and balance always separate; pay-on-arrival shown, never charged; lines grouped by
   confirmation class; the hold deadline sits next to the pay button.
6. **Offline.** Only the itinerary is cached; documents and Stage 3 data open online only; the cache clears at
   sign-out and link expiry.
7. **Language.** EN/VI, month names spelled out, per-day local time. Phone first.

---

## 4. Portal integration: one app, AA-Partner

### 4.1 Where we are (checked 2026-10-21)

- The tenant portal (Content studio) is a separate **deployment** since AA-885: Vercel project `aa-cis-portal`,
  domain `portal.lumiguides.it.com`. Its **code** is still in `apps/AA-CIS-App/portal/` (101 files, Next 16.4.2,
  React 19.2.4, own package, no imports outside `portal/`). The repo AA-Partner does not exist yet.
- The portal signs in with the tenant's **API key** through a BFF that mints httpOnly JWT cookies. The `cis-portal`
  EXTERNAL Cognito client exists in Terraform (ADR 0006) but the portal does not use it yet.
- Content studio data stays in CIS (ADR 0002: only CIS writes content). The portal calls the CIS API server to
  server (about 15 route groups).
- Portal CI and guards live in the CIS repo: `test_aa885_portal_split.py` (kit byte compare),
  `smoke-portal/aa885-portal-host.spec.ts`, `vercel-deploy-portal.yml`, `ui-smoke-portal.yml`.
- The portal is still changing (7 commits to `portal/` in the last 7 days).

### 4.2 End state

| Aspect | End state |
|---|---|
| Repo | AA-Partner (public): `portal/` (Content studio, moved with history), `web/` (CRM UI + client host), `api/` (FastAPI + `crm.job` worker) |
| Host | One agency host `portal.lumiguides.it.com` on CloudFront → VPC origin → ALB → Fargate (proven by the AA-931 spike); client host `go-dev.` separate |
| Sign-in | One sign-in for every agency person: the **partner pool**, two-step required for owner and agent. Tenant API keys stay for machine access only (ADR 0006 decision 12) |
| Membership and roles | CIS owns agency membership and Content studio roles (owner/editor/viewer) and publishes `tenant.membership.v1` (AA-978); the CRM owns CRM roles (owner/agent/assistant). A CIS event can never grant a CRM role. One person can hold both |
| Navigation | One sidebar (§3.2): CRM groups first, then CONTENT STUDIO, then Settings. Account pages (settings, billing, API) become Settings sections |
| Data | Content studio data stays in CIS (`cis.tenant-api.v1` from P1); CRM data in schema `crm`. No cross-schema grants; HTTP contracts only |
| UI kit | One kit for portal and CRM (AA-759 PortalShell on kit); a shared package (AA-655) later; until then CI byte-compares the kit files against CIS main |

### 4.3 Which portal features move, and when

| Portal page today | Place in AA-Partner | Moves at |
|---|---|---|
| `t0-brand`, `t1-rewrite`, `t4-pool`, `t7-planning`, `t8-angle-gate`, `t10-review`, `t11-publish` (+ connection), `marketplace`, `activity`, `help/facebook` | CONTENT STUDIO section, same routes and behaviour | Code: P2a (S255). Inside the shared shell and on the partner pool: P2b (S258) |
| `dashboard` | Content studio overview, linked from Home | P2a / P2b |
| `settings`, `billing`, `api` | Settings → Agency & branding, Plan & usage, API keys | AA-761 account page in `AA-Partner/portal` (S257) |
| `tenant-login` (API key) | Replaced by partner-pool sign-in; API keys remain for machines only | P2b |
| `privacy`, `terms` | Public pages of the agency host | P2a |
| `/trip/[tourId]` public pages | 301 to the client host | P2b |
| My Content table, Marketplace redesign | Built directly in AA-Partner | AA-669 (S259), AA-671 (S261) |

### 4.4 Steps

| Step | Session *(master plan)* | Issue | What happens | Done when |
|---|---|---|---|---|
| Prep | S249–S250 | AA-759, AA-760 | PortalShell on the kit; portal audit + state fixes, still in CIS | Merged, Vercel green |
| CRM skeleton | S251 | AA-935 | CRM web on `partner-dev.`; portal sidebar gets a "CRM" link, CRM sidebar a "Content studio" link | Cross-links work both ways |
| Freeze | S254 | — | No new portal features in CIS for one session | — |
| **P2a** code move | S255 | AA-979 (part 1) | `git filter-repo` move into `AA-Partner/portal/` (not `web/`, which AA-935/936 are building). Vercel `aa-cis-portal` re-pointed to the new repo; API-key + BFF sign-in kept; deploy/smoke workflows, Playwright and e2e secrets moved (⚠️ secret names contain underscores, edit manually in VSCode); kit guard pulls raw files from CIS main | History kept; the 24 portal smokes green from AA-Partner CI; Vercel deploys from the new repo; CIS copy kept until then |
| **P1** membership feed | S256 | AA-978 | CIS publishes `tenant.membership.v1` and `cis.tenant-api.v1`; CRM caches membership, invalidated within 60 s | A CIS membership change reaches the CRM ≤ 1 min; CIS granting a CRM role is rejected; revoking the last owner locks the agency until recovery |
| **P2b** host + sign-in | S258 | AA-979 (part 2) | `portal.` moves to CloudFront → Fargate (ALB host rule + secret origin header); Content studio users invited to re-enrol in the partner pool; 301 `/trip/*`; Sentry on the portal; rollback drill to Vercel | 24 smokes green; a `cis-admin` token gets no portal session; re-enrolled users keep tenant and content; old Vercel URL redirects with path; rollback drill passes |
| Clean-up | First session ≥ P2b + 7 calendar days (≈ S265) | AA-979 close | Remove Vercel project, delete `portal/` from CIS, invert the AA-885 guard, update CIS `CONTEXT.md` and `ecosystem-architecture.md` | No `portal/` in CIS; docs updated |

**Linear note.** AA-979 is blocked by AA-978 in Linear, but P2a runs before P1. Either create one P2a issue (ask
Nghiệp; quota allows it) or record the exception in AA-979. This is an open point (§9.2).

**Before P2b, two sign-ins.** From W1 the CRM signs synthetic users in on its own (the `cis-portal` client until
AA-939, the partner pool after); the portal keeps API keys. Nobody real is affected: Dev has synthetic agencies only.

### 4.5 Risks of the merge

| Risk | Mitigation |
|---|---|
| Content studio breaks for live tenants on the host or sign-in switch | Vercel kept ≥ 7 calendar days (≈ 6–8 sessions), rollback drill, invite-to-re-enrol, smokes before cut-over |
| CIS work drifts into AA-Partner ("CIS App first") | P2a→P2b gap ≤ 3 sessions; CIS-first note in the AA-Partner ADR (AA-928); feature freeze one session before P2a |
| Kit becomes three copies (CIS admin, portal, CRM) | Byte-compare guard is mandatory; shared package AA-655 later |
| Three tenant sign-in paths (API key, EXTERNAL `cis-portal`, partner pool) | AA-928 records the partner pool as the only human sign-in; AA-813 re-scoped so membership is built once (CIS feed + CRM roles); AA-762 closed as a duplicate of AA-939 |
| CloudFront → VPC origin bypasses API Gateway throttling; WAF only at W8 | App-level rate limits on public and sign-in routes from AA-933 |
| CORS is off, so the portal must keep calling CIS server to server | `cis.tenant-api.v1` (P1) before P2b |
| Repo creation may be restricted (access review) | Nghiệp creates AA-Partner if needed; branch protection + required CI from day one (AA-879 pulled to S249) |
| Docs drift | `ecosystem-architecture.md`, CIS `CONTEXT.md` and `applies_to` updated in the P2a and P2b sessions |

---

## 5. Data model and privacy (F1–F5)

Full tables, columns and rules: v3 §3–§4 and [`data-privacy-integrations.md`](../lanes/data-privacy-integrations.md).

### 5.1 Placement

- **Owner:** AA-Partner, schema `crm`, migrations `crm-NNN` with a byte copy in `AA-CIS-Infra/db/migrations/crm/`,
  applied only by DB Migrate. Registered in `owners.yaml`; `crm_` job kinds in `IDLE_EXEMPT_KINDS` from AA-932.
- **Where:** Dev on `aa-cis-dev-db`, and only synthetic tenants (`tenant.is_synthetic = true`). Prod placement (prod
  cell or shared prod RDS) is decided in AA-980.
- **Roles:** `crm_owner` (NOLOGIN, owns objects); `crm_app` (LOGIN, connection limit 6, pool 3); NOLOGIN roles
  reached only by `SET LOCAL ROLE` inside `tenant_tx()`: `crm_ai_reader`, `crm_insights`, `crm_support_reader`,
  `crm_eraser`.
- **Isolation:** no cross-schema grants. The isolation probe expects 42501 for `cis_app`, `booking`, `tripplanner`
  and `aa_app_user` on every `crm.*` object, and for every NOLOGIN reader on `trip_traveler` and vault tables.
- **Other apps over HTTP only:** Booking `booking.b2b.v1`; CIS `tenant.membership.v1`, `tenant.entitlements.v1`,
  `catalog.http.v1`; CRM publishes `crm.ops.v1` (under `/crm/ops/v1`) and `crm.insights.v1`. Jobs, outbox and
  events carry ids only; CI rejects `pii:` keys.

### 5.2 Conventions and tables

- Every tenant table: `tenant_id`, `created_at`, `created_by`, `updated_at`, ENABLE + FORCE RLS on `app.tenant_id`;
  trash columns (`deleted_at`, `deleted_by`, `purge_after`) from the first migration on every user-deletable table.
- Encrypted columns `*_enc` (AES-256-GCM, AAD = tenant ‖ table ‖ column ‖ row id); blind indexes `*_bidx`; every PII
  column tagged `COMMENT 'pii:<class>'`; status as `TEXT + CHECK` plus a transitions table.
- Money rows carry a frozen FX block; a trigger blocks updates; corrections are new rows.
- About 76 tables in 10 groups: A tenancy/keys/access, B F1 vault, C F2, D pipeline, E proposal and agreements,
  F money, G communications, H automation and AI, I ops and AA, J audit/deletion/platform (v3 §3.3).
- Key enums: `trip.stage = inquiry|qualifying|proposal|booked|pre_departure|travelling|completed|lost|cancelled`;
  `trip.waiting_on = agency|client|aa|supplier|none`; `invoice.status = draft|open|payment_claimed|paid|
  paid_unfulfillable|void|expired`; `proposal.price_visibility = total_with_deltas|total_only`.
- **Safe defaults** (`tenant_settings`): line strictness Basic, FX automatic, service fee off, trash 7 days,
  reminders agent-first, platform sender off, AI off, AI budget $2, refund owner threshold 1,000 base currency *(est.)*.

### 5.3 Booking-owned additions (AA-Booking, `bk-NNN`, no PII)

`b2b_partner`; `b2b_quote` (+ lines) returning `b2b_price` (never `supplier_net`), FX lock, `price_hash`,
`valid_until`; VND as selling currency; `departure` (capacity, held, sold, `auto_confirm`); `b2b_hold` (+ lines,
`extended_count` max 1, idempotent per tenant + proposal + version); re-hold limit 3 a day (429); cancellation-fee
policy with dry run; B2B trip case (`channel='b2b'`, no customer); `b2b_event` outbox (`hold.expired`,
`hold.extended`, `line.confirmed`, `line.declined`, `booking.cancelled`, `departure.guaranteed`,
`departure.incident`, `departure.time_change`). Issues AA-972…AA-975.

### 5.4 Cross-cutting rules

- **FX (R17):** sell, cost and expected commission convert at the line's confirmation date (AA lines use the quote's
  FX lock); receipts at the receipt date; stored base amounts never re-convert; "underpaid" judged in the original
  currency.
- **Stage edges:** enforced by the DB; `cancelled` from booked, pre-departure, travelling; `lost` before booked; the
  date rule moves trips to travelling and completed even when a gate is unmet, with a logged reason and a task.
- **Delete block (R21):** a trip with a succeeded payment, a signed signature request, a received/claimed commission,
  or an AA line `held`/`confirmed` cannot be deleted; the UI offers "Cancel trip". Restore re-checks Booking.
- **Deposit link (C31, D2):** stable CRM URL; card Checkout expires at `min(earliest hold − 15 min, now + 24 h)`;
  bank details only while the hold is active; bank claim per D2; a card payment after hold expiry → re-hold or
  `paid_unfulfillable` + refund request.
- **Undo:** sends and workflow starts from a user action wait 10 s (`not_before`) so Undo can cancel them.

### 5.5 Privacy foundation

| Module | Design |
|---|---|
| F1 identity vault | Keys `alias/crm-<env>/data`, `ingest`, `seal` (created in AA-932, alarms on policy/grant/delete/disable and unusual Decrypt, nightly policy diff). One DEK per agency per purpose (vault, docs, integration, scrub, ops_release, export, mail), cached ~5 min. Documents encrypted client-side with the docs DEK, then SSE-KMS. `KeyProvider` with a rewrap test (BYOK path). Blind indexes from HKDF of the vault DEK: exact search and dedupe only |
| F2 pseudonymous profile | Random token, bands and flags, no FK to F1. **Honest threat model:** the split protects against the AI, insight and support roles (none can read `traveler`, `trip_traveler`, `note`, `message`, `document`, `ops_release`); it does **not** protect against `crm_app` or the RDS master, which can join a solo or lead traveller through `trip_id`. The DPA says so |
| F3 PII filter | Known values → numbered placeholders; regex (email, phones incl. VN, passport, 12-digit CCCD, DOB, cards, links, OTPs); Bedrock Guardrails `ApplyGuardrail` on the rest. Fails closed. Placeholder map encrypted, 24 h, restored only in the agency session. Guardrails on acc2 if allowed, else the acc3 CRM-only role (planned path). CI corpus ≥ 200 EN/VI samples, 0 leaks, nightly |
| F4 tenancy and roles | `tenant_tx()` sets tenant and member role after the membership check; a lint forbids raw queries. Permission matrix below; per-role serializer allow-list plus a contract test over every `/crm/v1` route. Route groups: `/crm/v1` partner-pool users only; `/crm/ops/v1` WORKFORCE `cis-admin` (read) and `crm-platform-admin` (write); `/crm/staff/v1` `crm-ops`, `crm-support`. Travellers never get an AA Cognito account |
| F5 audit | Sign-ins, role changes, every F1 reveal (same transaction), list views (D7), exports, deletes, key operations, AI context builds, AA ops reads, L1 writes, support reads, break-glass Decrypts. No PII in events. Hourly export to two Object Lock buckets with a SHA-256 chain. Agency sees 12 months and can download |

**Permission matrix** (margin = B2B price, cost, margin, commission):

| Action | Owner | Agent | Assistant |
|---|---|---|---|
| Reveal contact; reveal passport / DOB / health / emergency contact (logged) | ✔ | ✔ | ✔ |
| See margin fields | ✔ | ✔ | ✘ |
| Create / edit trips, forms, booking lines | ✔ | ✔ | ✔ (no money fields) |
| Publish and send proposals | ✔ | ✔ | ✘ (prepares drafts) |
| Send messages, approve an AI draft | ✔ | ✔ | ✔ on assigned trips |
| Mark payment received | ✔ | ✔ | ✘ |
| Approve refund | ✔ any | ✔ up to threshold | ✘ |
| Cancel trip | ✔ | ✔ | ✘ |
| Delete trip (to trash) | ✔ | ✔ own trips | ✘ |
| Delete client data, export client or agency, reassign clients | ✔ | ✘ | ✘ |
| Campaigns / Marketing | ✔ | ✔ | ✘ |
| Edit workflows | ✔ | apply only | ✘ |
| Publish terms / waiver / consent versions; AA support access; team, integrations, payments, plan | ✔ | own mailbox only | own mailbox only |
| Access log | ✔ | trip Activity only | ✘ |
| Reports | ✔ | ✔ | ✔ without margin |

**AA access, three layers:**

| Layer | Issue | Summary |
|---|---|---|
| L1 platform console, no PII | AA-941 (W2) | S-01 in CIS admin: meters; create agency; first-owner invite only while there is no owner and no traveller; lock; retry jobs; allow entitlements; insights opt-out on request; raise export/delete requests the owner confirms; owner recovery after 14 days. A test forbids trip, pipeline and revenue keys. Every write lands in that agency's audit |
| L2 owner-granted support | AA-971 (W7) | 1–7 days (default 24 h), read-only, identity hidden unless ticked, one staff member at a time, ticket required, banners both sides. Send, export, role, integration and support-setting changes blocked |
| L3 break-glass | AA-971 (W7) | IAM role, MFA, ≤ 1 h, one agency (session tag + KMS context), alerts to Nghiệp and a named non-engineer manager, CloudTrail Decrypt copied into the agency audit, owner emailed within 24 h |

**M8 ops release** (AA-956) is a business flow, not a support layer: created when an AA line is confirmed, minimal
fields, completeness shown, T-21 alert, each view logged into the agency audit, purged at return + 90 days.

### 5.6 Retention (DM-7, approved in D6)

| Data | Window |
|---|---|
| F1, F2, trips, money | Until the agency deletes or offboards; archive suggestion after 36 months inactive *(est.)* |
| Erased data in backups and DEK copies | ≤ 30 days (alarm, restore drill; fallback wording 90 days) |
| Trash | 7 days |
| Audit in the app / archive | 12 months viewable / Object Lock compliance 12 months + governance to 7 years (Dev: governance only) |
| Ops release | Trip end + 90 days, with a receipt |
| Signed agreements (waiver, insurance decline, signature events, terms acceptances) | Trip end + 3 years *(est., lawyer confirms)*, kept through an erasure request; the receipt says so |
| Accounting records | Statutory, per the agency's jurisdiction |
| Form submissions, inbox/outbox payloads | 90 days, redacted |
| OTP, placeholder map / raw inbound mail | 24 h / ≤ 1 day |
| AI prompts (scrubbed) / `llm_call` | 30 days *(est.)* / 180 days + rollup |
| `metric_daily` / export files / CloudWatch logs | 25 months / 7 days / 30 days with PII masking |

**Deletion (M18, AA-967):** owner confirms → DRY RUN counts → run → verify. The run goes through
`crm.erase_subject()` (SECURITY DEFINER, executable only by `crm_eraser`), the only path allowed to delete
append-only consent and signature rows. Export: full CSV + JSON zip under the export DEK, owner-only, 7-day link,
audited. AA staff can only raise requests.

---

## 6. Integrations

> Errata S247: rows Stripe, Twilio, Email, SES, E-sign and Sub-processors change under bring-your-own; see
> [`errata-s247-byo.md`](errata-s247-byo.md) §1–§3.

Details: v3 §5 and [`data-privacy-integrations.md`](../lanes/data-privacy-integrations.md) §6.

| System | Design | AA cost |
|---|---|---|
| Service identity | Cognito M2M pool `aa-m2m-<env>`, one client per caller, scoped tokens (6 h, cached); `X-AA-Tenant-Id` on every B2B call. ⚠️ This contains underscore env vars — edit manually in VSCode (Cognito client config, DSNs, Mapbox token) | ≈ $4/month with KMS |
| AA-Booking `booking.b2b.v1` (AA-972…AA-975) | `GET /products`; `POST /quotes` (`b2b_price`, VND, FX lock, `price_hash`, availability); `GET /departures`; `POST /holds` (idempotent, 429 after 3 re-holds a day); `POST /holds/{id}/extend` (once); confirm/release; `POST /bookings/{id}/cancel` (+ dry run, fee); `GET /events?after=` pulled every minute; `GET /fx-rates`, `GET /price-parity`. Payload: pax counts, age bands, rooms; never names, contacts, DOB or passports. Errors: 409 re-quote, 410 re-hold, 422 sold out, 503 indicative price + no deposit. AA↔agency settlement stays outside the CRM | $0 |
| CIS (AA-976, AA-977, AA-978) | `catalog.http.v1` (tour content, exclusions, facets for system tags, places, time zones, AA-authored prep packs, starter templates, campaign blocks); `tenant.membership.v1`; `tenant.entitlements.v1`; `cis.tenant-api.v1` for Content studio | $0 |
| Stripe Connect Standard (AA-952) | Each agency connects its own account; direct charges; on-demand Checkout Sessions; webhooks by `event.account`; refunds only from an approved refund request; no stored cards; VN agencies mark payments manually | $0 (agency pays fees) |
| Twilio, WhatsApp + SMS (AA-958) | Agency's own account (SID + token under the integration DEK); per-tenant webhook with HMAC check; inbound match by phone blind index, unknown → Unmatched; 24 h window enforced. Fallback if Twilio requires Meta Tech Provider: AA subaccounts, re-billed | $0 |
| Email (AA-945) | Send-as Gmail (`gmail.send`) and Outlook (Graph `Mail.Send`), built together; inbound via one SES domain rule + per-agency forwarding address (BCC fallback for Microsoft 365); raw mail ≤ 1 day under the ingest key; dead token → `held_reconnect`; platform sender opt-in, owner only, logged; autosaved drafts; no two-way sync | $0 |
| SES | Separate `crm-transactional` and `crm-marketing` configuration sets; per-tenant suppression; one-click unsubscribe; always in the agency's name | in AWS lines |
| E-sign (AA-946 v0, AA-955 v1) | Email code per signer → versioned documents → typed name + consent ticks → server PDF (terms + waiver + insurance decline in one envelope) → PAdES seal with the `seal` key → stored under the docs DEK. Provider-neutral adapter, BoldSign slot | $0 (BoldSign ≈ $30/month only if needed) |
| Calendar (AA-961) | Call slots in the inquiry form; Google `calendar.events` / Graph sync; ICS link fallback if the scope needs CASA | $0 |
| AI (AA-964, AA-965) | Haiku 5.5 through `us.` inference profiles, own CRM gateway, F3 first, budget cap $2 per agency per month, AI off by default; paid test runs: trial ~3, then ≤ 50 | in LLM line |
| Sub-processors (public page, AA-970) | Amazon Web Services, Inc. (hosting + Bedrock AI, US regions); Mapbox (to confirm); conditional: Twilio, BoldSign, a flight-status API, Sentry. Agencies' own processors: Stripe, Twilio/Meta, Google, Microsoft. Not used: OpenAI, Jev, Documenso, 360dialog | — |

---

## 7. Delivery plan

### 7.1 Rules

- One issue = one deliverable (~1 PR or a small group). Done = merged + CI green + Dev rollout COMPLETED + live
  check (aa-ship), commits `Refs AA-821` (+ the issue), implementation notes in `docs/implementation-notes/`.
- Every issue's Done-when has a refusal case and an edge case (cards in v3 §6.3).
- Risky PRs (auth/permissions, migrations, CI/workflow/secret, deletion) get an independent agent review first.
- Dev only, synthetic agencies only, vendors in test mode until W8.
- Master-plan limits: at most one critical-path step per session; at most ~3 CRM items per session including Lane B
  and Lane P (CIS-first, ~40 %); at most one Booking item per session; no backend merge or deploy while a job table
  is busy (DM-11.4).
- Critical path: AA-928 → AA-932 → AA-933 → AA-934/935 → AA-936 (C-M1) → AA-937 → AA-939 → AA-943 → AA-944/945 →
  AA-946 (C-M2) → AA-947 → AA-949 → AA-950 (C-M3).

### 7.2 Waves and issues

| Wave | Exit | Linear issues | Effort *(est.)* |
|---|---|---|---|
| W0 | ADRs + standards accepted; readiness verdicts; CloudFront → VPC origin proven | AA-928, AA-929, AA-930, AA-931 | 1.75 |
| W1 = C-M1 | Synthetic agency signs in; form → Inquiry card < 1 min; ciphertext only; CIS sees CRM jobs | AA-932, AA-933, AA-934, AA-935, AA-936 | 4.0 |
| W2 | F1–F5; partner pool + MFA; L1 console; trash/archive rules | AA-937, AA-938, AA-939, AA-940, AA-941, AA-942 | 4.0 |
| W3 = C-M2 | One trip Inquiry → Completed with agency suppliers | AA-943, AA-944, AA-945, AA-946 | 3.5 |
| W4 = C-M3 | AA products quoted, held and confirmed from the interactive proposal | AA-947, AA-948 (enhancement), AA-949, AA-950, AA-951 | 3.5 |
| W5 | Card and bank deposits, client portal, offline itinerary, waivers, ops release, commission, cancel | AA-952, AA-953, AA-954, AA-955, AA-956, AA-957 | 4.0 |
| W6 | WhatsApp/SMS, workflows, tags, duty of care, onboarding, search | AA-958, AA-959, AA-960, AA-961, AA-962, AA-963 | 4.5 |
| W7 = M4 "23 modules on Dev" | AI, reports + insights, portability, campaigns, security review, release train, L2/L3 | AA-964, AA-965, AA-966, AA-967, AA-968, AA-969, AA-970, AA-971 | 6.0 |
| Lane B (Booking + CIS) | B2B quote, departures/holds, commercial rules, feed, catalog, AA content | AA-972, AA-973, AA-974, AA-975, AA-976, AA-977 | 4.5 |
| Lane P (portal) | Membership feed; portal into AA-Partner (P2a + P2b) | AA-978, AA-979 | 1.5 |
| W8 = M5 Go-real | Opens when Ms. Thư names the first real agency | AA-980 | 2–3 + external clocks |

Nominal 37.25 sessions; with review loops and MFA waits ≈ 40–45 sessions. Blocked-by relations are in the master
plan (`blocked_by_relations`).

### 7.3 Session slots S247–S262 (master plan)

| Session | CRM items (L6), Lane B (L4), Lane P (LP) | Notes |
|---|---|---|
| S247 | AA-928 (ADRs incl. AA-Partner ADR, contracts, errata, AA-813 re-scope, sign-in decision, Booking commercial-core memo), AA-929, AA-930 | Docs only, no code subagent |
| S248 | AA-931 (Nghiệp MFA): apply-role permissions + CloudFront → VPC origin spike; Nghiệp accepts AA-928 ADRs | |
| S249 | AA-932 + AA-972 M2M pool (one MFA batch, two sequential applies); LP AA-759; L7 AA-879 CI parity | AA-879 before the 4th repo |
| S250 | AA-933 repo AA-Partner (branch protection + required CI from day one); AA-972 done (bk-019); LP AA-760 | |
| S251 | AA-934 + AA-935; AA-973 (bk-020) | |
| S252 | AA-936 → **C-M1**; AA-974 (bk-021) | |
| S253 | AA-937; AA-975 (bk-022) | |
| S254 | AA-939 (Nghiệp MFA; close AA-762 as duplicate), AA-940; AA-976 | Portal feature freeze starts |
| S255 | AA-938 + AA-942; **P2a** | |
| S256 | AA-943; **P1** AA-978; AA-977 (CIS migration, review) | |
| S257 | AA-944 + AA-945; AA-941; LP AA-761 | First session ≥ 2026-11-01 falls about here |
| S258 | AA-946 → **C-M2**; **P2b** | Vercel kept ≥ 7 days |
| S259 | AA-947; LP AA-669 | W4 opens once Lane B and AA-944 are done |
| S260 | AA-949; AA-948 if T13 + AA-906 + TP 6d are done | AA-948 never blocks C-M3 |
| S261 | AA-950, AA-951; LP AA-671 | |
| S262 | Check **C-M3** or record the slip; re-plan W5–W8 (AA-952…AA-971, AA-980) at real speed | Portal clean-up ≈ S265 |

### 7.4 Milestones

| Milestone | Window *(master plan, Ultracode)* | Window *(design pace, normal sessions)* | Criteria |
|---|---|---|---|
| C-M1 CRM runs on Dev (W0–W1) | S252–S254 | ≈ mid-Nov 2026 | AA-928…931 merged/applied; non-partner host → 403 via CloudFront; `crm_app` → `booking.*` and `cis_app` → `crm.*` give 42501; CIS DB Migrate not blocked by the CRM heartbeat; synthetic agency signs in, form → Inquiry card < 1 min, F1 ciphertext only, CIS sees `crm.job` |
| P-M1 Portal in AA-Partner | P2a S255; P1 S256; P2b S258; clean-up ≈ S265 | — | §4.4 "Done when" column |
| C-M2 Full lifecycle with agency goods (W2–W3) | S258–S260 | ≈ mid-Dec 2026 | AA-937…946 done; one trip Inquiry → Completed with agency suppliers; partner pool enforces MFA; field filter test passes on every route |
| C-M3 AA supply in the CRM (W4) | S261–S265 | ≈ early Jan 2027 | AA-947, 949, 950, 951 done; AA products quoted, held, confirmed from the interactive proposal; accept after hold expiry → 409 `hold_expired` |
| M4 23 modules on Dev (W5–W7) | Re-planned at S262 | ≈ mid-Feb to end-Mar 2027 | AA-952…AA-971 done; AA-969 security review with no High finding |
| M5 Go-real (W8) | > S262 | after M4 + external clocks | AA-980: prod placement, prod partner pool, WAF, vendor verifications, Stripe live, DPA + data page; first real agency invited; AA-880 ADR 0012, AA-873, AA-874 done |

The master-plan windows assume every session runs with Ultracode and CRM takes ≤ ~40 % of items. If sessions run
normally (3–5 issues), the design-pace column applies.

### 7.5 Who does what

| Work | Agent | Nghiệp | Ms. Thư |
|---|---|---|---|
| Code, migrations, Terraform, tests, docs | ✔ | — | — |
| Accept ADRs (AA-928), approve standards (AA-929) | writes | ✔ | — |
| MFA applies: AA-931, AA-932, AA-939, AA-972, AA-971, AA-964 (acc3 role), AA-980 (7 in all; later applies through the OIDC apply role) | prepares | ✔ | — |
| Secret values, DB Migrate `set-password`, test users (⚠️ underscore env vars, edit manually in VSCode) | — | ✔ | — |
| Free test accounts (Stripe, Twilio, Google, Microsoft) and the Twilio ISV question | drafts | ✔ | — |
| Names (ops person, departure owner, support person, second alarm recipient), legal entity, B2B terms, insurer contact | formats | — | ✔ |
| ~10 "Before you go" packs, bilingual terms and waiver templates, 15–20 help videos, real net rates, first real agency | — | — | ✔ (her team) |
| Risky PR review | independent agent | — | — |

---

## 8. Cost

> Errata S247: conditional vendor lines leave AA and the SES line shrinks; see
> [`errata-s247-byo.md`](errata-s247-byo.md) §4.

AA's AWS cost per month *(est.)*. Full line items: v3 §7.

| Line | Dev (0 real agencies) | 10 agencies (prod) | 50 agencies (prod) |
|---|---|---|---|
| API + web on Fargate | 5.4–7.2 | 18 | 55 |
| CloudFront / WAF | ≤ 0.2 / 0 | ≈ 0 / 7.5 | ≈ 0 / 8 |
| Database | 0 (shared Dev RDS) | 19 | 133 |
| LLM (Haiku 5.5, AI on for every agency) | ≤ 2 (test cap) | 13–15 | 67–75 |
| Guardrails, SES, S3, logs, secrets, ECR, alarms | 4–6 | 10 | 30 |
| KMS (3 keys) + Cognito M2M | ≈ 4 | ≈ 4 | ≈ 4 |
| Cognito partner pool | ≈ 0 | ≈ 0–1 | ≈ 1–5 |
| Second public service / audit Object Lock storage | 0 / ≈ 0 | 0 / ≈ 0.5 | 8.3 / 1–4 |
| **Total AA AWS** (prod shares networking) | **≈ $13–22** | **≈ $84–97** | **≈ $319–344** |
| If prod is a separate cell (ALB, NAT or endpoints) | — | $104–152 | $339–399 |
| Upper bound if every agency hits the $2 AI cap | — | +$5–7 | +$25–33 |

- Vendor cost for AA: **$0**. Conditional only: BoldSign ≈ $30/month (if the insurer refuses self-built e-sign);
  Tech Provider fallback (re-billed); CASA $675–5,400/year (only if two-way mail sync is ever required); ≈ +$38/month
  at 10 agencies if Haiku 5.5 `us.` is missing; a paid flight API (price unknown, approval first).
- Load test (AA-969): $0 on the shared Dev RDS; a throwaway RDS from a snapshot ≈ $1–2 a day, stated before use.
- Pricing trigger (Q1 1.1: tiers at > $150/month or 20 agencies): about 18–25 agencies on shared networking, 10–15
  for a cell.

---

## 9. Risks and open points

### 9.1 Risks

| Risk | Level | Mitigation / signal |
|---|---|---|
| AA-Booking has no departures, capacity, holds, B2B API, VND or fee policy | High | Lane B (AA-972…975) right after AA-928; fake prices on Dev; independent review of bk-019…bk-022; the commercial-core memo in AA-928 avoids collisions with AA-682 |
| Real net rates not entered before the pilot | High | Dev uses fake rates; AA-980 blocks without the ops owner's sign-off |
| Effort under-estimated again; master-plan windows are 3–5× faster than the design estimate | High | Milestones C-M2/C-M3 are usable checkpoints; re-plan at S262 on real speed; R28/36/40/41/42 may land after M4 |
| Portal move breaks Content studio for live tenants | Medium | §4.5 |
| Anonymous links abusing AA capacity | Medium | One hold set per version, 3 re-checks a day, Booking 429, bell per re-hold |
| Bank transfers outlast holds (VN) | Medium | D2: one extension + verify task; re-hold or refund |
| Twilio requires the Meta Tech Provider programme | Medium | Question in AA-930; subaccount fallback; the clock moves to W8 |
| Insurer rejects self-built e-sign | Medium | BoldSign slot in the adapter (+2–3 PRs, ≈ $30/month) |
| Guardrails or Haiku 5.5 not available where planned | Medium | AA-930 checks; acc3 CRM-only role; AI off by default |
| Partner-pool tier price or passkey gap | Medium | AA-930 checks before AA-939; TOTP-only fallback |
| RDS connection budget (~132/135) | Medium | `crm_app` limit 6 / pool 3; bounded load test; per-role alarm |
| One KMS data key for all agencies | Medium | Alarms on all keys, nightly policy diff, no task role administers keys |
| 30-day deletion depends on backup discipline | Medium | Backup/snapshot-age alarm, restore drill, 90-day fallback wording |
| Answers given by Nghiệp on Ms. Thư's behalf | Medium | Mail sync (Q2 4.1) is the most likely change → CASA cost + issues |
| Public repo leaks account ids | Medium | DM-6.10 scan in AA-Partner CI from AA-933 |

### 9.2 Open points (real ones only)

| # | Point | Owner | Needed by |
|---|---|---|---|
| 1 | P2a runs before P1, but Linear AA-979 is blocked by AA-978: create a P2a issue or record the exception in AA-979 | Nghiệp | S254 |
| 2 | Lock the single human sign-in (partner pool) and re-scope AA-813 accordingly | AA-928 (Nghiệp accepts) | S248 |
| 3 | T13 (TripPlanner route stitching, needed by AA-948) has no Linear issue | Nghiệp approves creation | ≈ S258 |
| 4 | Ms. Thư's blanks: ops person for net rates, departure owner, support person + hours, second break-glass recipient, legal entity, current B2B terms, insurer + contact | Ms. Thư | Before W8 (net rates before the pilot) |
| 5 | Content from Ms. Thư's team: ~10 prep packs, bilingual terms/waiver templates, help videos | Ms. Thư | AA-977 seed (S256) for packs; W7 for videos |
| 6 | External checks in AA-930: Twilio ISV, TrueIDC/eCloudvalley IAM roles in the accounts, Haiku 5.5 `us.` + Guardrails on acc2/acc3, Google calendar scope class, Cognito tier price, a free VND FX source, Stripe Checkout expiry range, BoldSign regions, Mapbox on the sub-processor list | Agent (+ Nghiệp sends the Twilio question) | S247 |
| 7 | Emergency contact in the ops release (X6): excluded by default | Ms. Thư | AA-956 |
| 8 | Estimates to confirm: hold defaults (48 h seats; on-request until ops answer + 24 h; extension +72 h, Booking decides); refund owner threshold 1,000 base currency; archive after 36 months; prompt retention 30 days; signed-agreement claim period (trip end + 3 years, lawyer) | Booking lane / lawyer | AA-974, AA-959, legal milestone |
| 9 | Who accepted (O-3): typed name + terms version + `price_hash` + time + link id; add an email code at accept only if the insurer or lawyer requires it. Party waivers per adult, guardian for minors (O-6) | Insurer via Q2 5.1 | AA-955 |
| 10 | Owed to suppliers (O-10): needs Booking to expose B2B invoices per agency; until then a link | Booking (AA-682) | After AA-682 |
| 11 | Module 17 insights only prove the guards on Dev; real value needs 3–6 months of real data after W8 | — | After W8 |
