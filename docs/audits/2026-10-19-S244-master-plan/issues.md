# S244 master plan — every open issue

Audit date: 19/10/2026 (S244, Claude Code). Read-only: nothing was changed in Linear.

There are 84 open issues: 17 In Progress and 67 Backlog. They are listed first, grouped by project. Below them are 6 Done issues whose status should change (reopen or Canceled).

**Proposed status** names only proposals that the independent verify pass upheld. Every other issue reads "keep". Where a proposal was rejected by that pass, a short note says so.

**Priority** shows the current value, then a suggestion after "→". Priority suggestions were not verified; Nghiệp decides them.

**Milestones** (defined in [README.md](README.md) §2):
- M1: platform block.
- M1b: SDLC/docs "Now".
- M2a: CIS content quality.
- M2b: places, photos and Jev.
- M3: Booking wave 3.
- M4: UAT.
- M5: first paying tenant, then prod.
- Parked: no milestone.

**Session slots** assume about one session per day (S245 ≈ 20/10). "≥S254" means after the planned window (S244–S253).

Project keys: DP = Data Platform (P-AA-16), CC = CIS Core (P-AA-15), PO = CIS Portal, TB = TripPlanner & AA-Booking.

## Open issues

| ID | Title (short) | Proj | Status | Proposed status | Priority | Size | Milestone | Session | Done-when | Remaining work | Blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AA-902 | Scrub account IDs/ARNs from public repos | DP | In Progress | keep | High | M | M1b | S244 → S245 | concrete | CIS #854 (11:49:56Z), Booking #45 (11:44:15Z), TP #105 and Infra #221 are merged and CIS Deploy Dev on 1d16adf succeeded (gh, 12:00Z re-check). Left: live-verify CIS/Booking/TP; check the migration 153/240 copy guard; remove the 2 TP test-file hits; red-check PR; update baseline.md; decide on history rewrite and Cognito IDs | Nghiệp decisions (history rewrite, Cognito IDs) |
| AA-903 | Skip Vercel deploy on Dependabot PRs | DP | In Progress | keep | Low | XS | M1b | S244 | concrete | CIS #855, Booking #46 and TP #106 are merged (gh, 11:31–11:32Z). Left: link one Dependabot run per repo; close Booking #39 | — |
| AA-860 | X1 split of the CIS runtime role | DP | In Progress | keep | Medium → High | L | M1 | S244 (S20), S245 (S21), S246 (S22–S23) | vague | S20 probe; S21 mig 245; S22 `db_migrator` login and probe 246; S23 close-out; one rollback test | Done-when (1) contradicts mig 244 (needs Nghiệp); Infra #220 plan must be rerun; H6 manual secret |
| AA-852 | Per-app DB owner roles + migrator task def | DP | In Progress | **Done** | Medium | XS | M1 | S244 | concrete | Comment that moves the 179/180 revoke to AA-847; drop the stale AA-826 relation | — |
| AA-895 | Security baseline + Dependabot | DP | In Progress | keep (verify rejected Done for now) | Medium | XS | M1b | S245 (close-along) | concrete | Point baseline.md row "Public repos content" at AA-902 | Root PR |
| AA-890 | PR template, title lint, squash-only | DP | In Progress | keep | Medium → Low | XS | M1b | S247 (close-along) | concrete | `gh api` settings on 5 repos; DRY RUN list of merged CIS branches before any prune | Only the orchestrator may run gh writes |
| AA-889 | Stale docs and agent-instruction drift | DP | In Progress | keep | Medium | XS | M1b | S245 (close-along) | concrete | Close once CIS #854 merges and the scan is clean; fix 2 stale TP CONTEXT lines | AA-902 |
| AA-888 | Docs lint, ADR indexes, ID checks | DP | In Progress | keep | Medium | S | M1b | S248, S251 | concrete | Link and ID jobs in Infra and the app repos; red test PR; link the first scheduled run (26/10) and check that freshness.md is written | Time-gated to 26/10 |
| AA-887 | Adopt the documentation standard | DP | In Progress | keep | Medium → Low | XS | M1b | S246–S247 (close-along) | concrete | Front-matter on the 4 CONTEXT.md files; correct the Done-when from "x5" to "x4" | — |
| AA-896 | FinOps doc, anomaly detection, monthly report | DP | In Progress | keep | High → Medium | S | M1b | First session ≥01/11 | concrete | October report with unit costs, including acc3 spend and credits; 5-line Vietnamese summary; PR-20 period 2 | Time-gated to 01/11 |
| AA-893 | Alarm catalog + Terraform outputs | DP | In Progress | keep | Medium | M | M1b | S251 | concrete | alarms.md generator with link check; outputs + docs-gen.yml on a read-only OIDC role (IAM review) | — |
| AA-891 | release-please + first tags | DP | Backlog | keep | High → Medium | M | M1b | S252 | concrete | Manifest mode in 3 repos; first tags; release-note template | AA-901; version numbers (Nghiệp) |
| AA-878 | Secrets register and orphan cleanup | DP | In Progress | keep | Medium | S | M1b | S247 | concrete | Drift diff = 0; confirm the 2 GitHub orphans; PAT revoke; access review via AA-838; U-04 | PAT and Mapbox revoke (Nghiệp) |
| AA-900 | LLM ops docs, prompt versions, eval gate | DP | Backlog | keep | Low | M | M2a | ≥S254 | concrete | Prompt register; route table; one PR carrying an eval run ID and its cost | AA-729 |
| AA-879 | CI gate parity | DP | Backlog | keep | Medium | M | M5 | S253 (moved from S252 to keep S252 at 5) | concrete | Required tsc/build in CIS; Trivy blocking with an expiring ignore list; TP deploy needs ci; coverage ratchet; U-61 | Branch-protection toggles |
| AA-880 | Prod blueprint + ADR 0012 | DP | Backlog | keep | Low | L | M5 | Unscheduled | concrete | ADR 0012; prod plan and cost quote; no apply | Go-live date; AA-864 decision |
| AA-901 | GitHub App, ADR 0010/0011, CODEOWNERS | DP | Backlog | keep | Medium → High | M | M1b | S251 | concrete | Nghiệp creates the App; CI mints a token; test PR; write the ADRs | Org owner (Nghiệp) |
| AA-899 | OpenAPI export + oasdiff | DP | Backlog | keep | Low | M | M5 | ≥S254 | concrete | Export, oasdiff, response_model; do not re-expose the Booking docs | AA-891 |
| AA-874 | Redis AUTH/TLS + flag alarm | DP | Backlog | keep | High | M | M5 | S250 | concrete | Quote; new replication group; switch CIS in a quiet window; test the alarm; drop Booking from scope if it does not use Redis | Cost quote approval |
| AA-876 | API edge hardening | DP | Backlog | keep | Medium → High | M | M5 | S249 | concrete | Login rate limit first; CORS; headers; Booking docs; WAF after its quote | WAF quote |
| AA-873 | GuardDuty, Access Analyzer, BPA, CloudTrail | DP | Backlog | keep | Medium | M | M5 | M5 security order #3 (≥S254, after AA-846) | concrete | 5 items, each with a quote | Quotes; do after AA-846 |
| AA-894 | Env-config register + ERD | DP | Backlog | keep | Low | M | M5 | ≥S254 | concrete | Names-only env register; Mermaid ERD | AA-893 |
| AA-829 | Restore drill, DSN CNAME, real-data dumps | DP | Backlog | **In Progress** | Medium → High | M | M5 | Dumps: any session once approved; rest ≥S254 | concrete | DRY RUN the dumps, then move or delete them; single-schema rehearsal; CNAME | Nghiệp approval (dumps); DSN secrets edited by hand |
| AA-871 | JSON logs + Sentry for Booking and TP | DP | Backlog | keep | Medium | M | M5 | M5 security order #4 (≥S254) | concrete | structlog with request IDs in 3 apps; Sentry for Booking and TP; add a Booking uptime line (gap left by AA-870) | Sentry free-plan quota |
| AA-859 | Tenant pool waves 3–4 | DP | In Progress | keep (verify rejected Backlog) | High → Medium | L | M5 | S251 | concrete | Comment naming the real gate; renumber the migrations; D5b; wave 3; wave 4; extend the probe | X1 S21/S22; wave-4 route retire (Nghiệp) |
| AA-848 | X2 RLS catalogue CI guard | DP | Backlog | keep | High | M | M5 | S250 | concrete | Replayed-DB test for rules a–e, PUBLIC grants and an allowlist that includes the cis_app USING(true) set; one red run per rule | — |
| AA-851 | shared.countries + v_countries | DP | Backlog | keep | High → Medium | M | M5 | ≥S254 | concrete | Migration; views; backfill; orphan report | catalog.* freeze until S22 |
| AA-850 | Dead Table Registry + quarantine | DP | Backlog | keep | Medium | M | M5 | ≥S254 | concrete | Registry; DRY RUN; approval; drop as cis_owner; archive pipeline_jobs | CIS freeze until S22; DRY RUN approval |
| AA-839 | Erasure runbook + DRY RUN (parked) | DP | Backlog | keep | Low | L | M5 | S253 ("GDPR" wording fix); full scope M5 security order #5 (before prod) | concrete | Runbooks and tests; remove the "GDPR" wording from the offboard endpoint now | Trigger: Phase 4 or before prod |
| AA-838 | Capacity, pg_stat and access review cadences | DP | Backlog | keep | Low → Medium | M | M1b | First session ≥01/11 | concrete | Cadences in the skill; probe via run-script; first capacity review; one access review shared with AA-878 | Nghiệp approves the decision list |
| AA-881 | PG 15 major-upgrade rehearsal | DP | Backlog | keep | Low | S | M5 | 05/2027 | concrete | Full scope at the trigger date | Time trigger |
| AA-864 | Research: consolidate on one AWS account | DP | Backlog | keep | Low → Medium | M | M5 | Decide before AA-880 | concrete | Research doc | Nghiệp: still wanted? (CLAUDE.md S235 says acc2) |
| AA-849 | TP migration replay CI | DP | Backlog | **In Progress** | High → Medium | S | M5 | S253 (moved from S252 to keep S252 at 5) | concrete | Replay all tp files twice and assert keys; one red run; make it a required check | Branch-protection toggle |
| AA-877 | Booking/TP PII column tags | DP | Backlog | keep | Medium | S | M5 | S249 | concrete | `pii:<class>` comments through bk/tp migrations; regenerate the reference; RoPA | — |
| AA-875 | SSRF-safe outbound client | DP | Backlog | keep | Medium → High | S | M5 | S248 | concrete | safe_http; route all WP fetches through it; tests; live 4xx on an internal address | — |
| AA-846 | Clean full-root TF plan + apply guard | DP | Backlog | **In Progress** | High | M | M1b | S245 | concrete | Exact required_version; resolve hidden diffs; apply guard with one refused run; 0-change apply; tag check; apply-role narrowing line | — |
| AA-826 | New-app playbook (owners.yaml) | DP | Backlog | **In Progress** | High → Medium | M | M5 | ≥S254 | vague | Reword the Done-when; template; hash guard; dry-run add-owner PR | Nghiệp: Done-when and owner of owners.yaml |
| AA-847 | L4 catalog read model + PLACES_SOURCE flip | DP | Backlog | keep | High | L | M2b | S248–S249 | concrete | Read model; parity; content-validity report; defect fixes; flip; plus the 179/180 revoke, Geoapify attribution and the AA-674 property test | catalog.* freeze until S22; Nghiệp on the 7-day watch |
| AA-853 | Schema drift diff + ownership lint | DP | Backlog | keep | Medium | M | M5 | ≥S254 | concrete | Nightly replay diff; owners.yaml lint; red and green run links | AA-826 |
| AA-703 | Identity epic (ADR 0006) | CC | In Progress | keep | Medium → High | XL | M1 (phases 0–2), M5 (phases 3–4) | S246 (record phases 1–2) | concrete | Cutover; bridge drop; AA-813; traveller sign-in; abuse-limit evidence; docs; legacy removal +30 days | AA-816; Nghiệp: keep phases 3–4 in this epic? |
| AA-820 | Tenant Terms AI clause (AUP, 12/11) | CC | Backlog | keep | High | M | M5 (fixed date) | Jira draft at S244 end; decision ~01/11 | concrete | Ms. Thư review and counsel; contract schedule; tenant notice | Ms. Thư; due 11/11 |
| AA-697 | Architecture diagrams | CC | Backlog | keep | Low | L | Parked | After M1 | concrete | Refresh the scope; draw the diagrams | Architecture still moving |
| AA-729 | Golden set + scoring script | CC | Backlog | keep | High | L | M2a | S247 | concrete | ~100 samples; labels; quote; trial of 3; baseline report; reword Done-when line 3 | Nghiệp: sample plan and cost |
| AA-804 | AI platform ADR + ledger v2 | CC | Backlog | keep | High → Medium | XL | M5 | M5 security order #6 (≥S254, before prod) | concrete | ADR (renumber to 0009); ledger v2 migration; attempt logging; AI Use Register; PII decision | Nghiệp decisions |
| AA-842 | OTel tracing investigation | CC | Backlog | keep (verify rejected Done; S238 decision) | Medium → Low | XS | Parked | — | concrete | None; option B only on a trigger | — |
| AA-865 | Pooled F9 re-flag rate | CC | Backlog | keep | Low | S | M2a | S245 | concrete | Pool r5–r7 retries (n≥60, $0); classify; 95% CI; fix only if above 8% | — |
| AA-712 | Place pipeline into CIS (leftovers) | CC | Backlog | keep | High → Medium | M | M2b | S252 | concrete | Laos covers; 142 geo names; a3 parity; TP grant check; narrow the bare except | Next-country paid batch |
| AA-741 | T-series audit G7/G8 | CC | Backlog | keep | Medium | XL | M2a | S250 | concrete | G7 paid run (48 tours); G8 report; exclude test rows | AA-787 and AA-800 shipped; paid approval |
| AA-783 | Human calibration of the T9 panel | CC | Backlog | keep | Medium | M | M2a | S251 (analysis, once labels exist) | concrete | 40 labels; κ; report; exclude the ZZ test label | Nghiệp labelling time |
| AA-800 | Tenant signature vocabulary | CC | Backlog | keep | High | M | M2a | S246 | concrete | 3 layers; source field; per-tenant rule 1; fidelity flag; live A&H check | <$1 approval |
| AA-803 | Calibrate a1_promise_unsupported | CC | Backlog | keep | High → Medium | M | M2b | S252 | concrete | ~100 labels shared with AA-845; floors; enforce, or switch off | Nghiệp |
| AA-845 | Jev A-axis ground truth + 402s | CC | Backlog | keep | High | M | M2b | S247 (402 report), S252 (rest) | concrete | 402 report; record_rejected_outcome; reject ceiling; keyword retune | Label-source decision |
| AA-784 | Platform-wide place cards | CC | Backlog | keep | Medium | L | M2b | S252 (trial country) | concrete | Trial of ~50 places; staged build | Paid approval; HNSW precondition (ADR 0007) |
| AA-790 | Tenant-voice gate + post-repair integrity | CC | Backlog | keep (verify rejected split) | High | L | M2a | S249 | concrete | Gate-type decision; integrity check (owns orphans); 20-piece pilot with panel | Gate type (Nghiệp); AA-800 |
| AA-814 | Facts Entry API + UI | CC | Backlog | keep | Medium | L | M5 | ≥S254 | concrete | Admin and tenant CRUD on the tenant pool; writers prefer tenant facts | AA-859, AA-813 |
| AA-789 | Gate recall tunes | CC | Backlog | keep | Medium | M | M2a | S250 | concrete | Lexical recall only (orphans go to AA-790, FAQ to AA-779) | Scope split |
| AA-787 | Drop/merge T10 gates | CC | Backlog | keep | High | M | M2a | S247 | concrete | Remove 4 gates; merges; ADR note; UI verify; before/after numbers on the golden set | Re-confirm promises_an_option |
| AA-780 | LinkedIn floor, voice, stock lines | CC | Backlog | keep (verify rejected the merge) | High | S | M2a | S248 | vague | 6 stock lines; broetry warn; hashtag check; Trail Pulse voice; reword "r5" | Trail Pulse voice review (Nghiệp) |
| AA-779 | FAQ from PAA + subject check | CC | Backlog | keep | Medium | M | M2a | S248 | vague | PAA into write_faq; head-entity check; tests; reword "r6" | — |
| AA-795 | T2 judge breakdown + brand-claim check | CC | Backlog | keep | Medium → Low | M | M2a (later) | ≥S254 | concrete | Storage decision; drawer; check | Nghiệp: still wanted? |
| AA-788 | Promote F12 / F9_brand_style to blocking | CC | Backlog | keep (verify rejected the merge) | Medium → Low | S | M2a (later) | ≥S254, after AA-787 | vague | Offline F12 replay; flip; one-repair rule; pilot; numeric Done-when | AA-787 order |
| AA-782 | Cheaper T9 writer A/B | CC | Backlog | keep (parked) | Medium → Low | M | Parked | — | concrete | Paired A/B (~$1.2) | Vendor rule |
| AA-781 | F9 v2 claim rules | CC | Backlog | keep (verify rejected Canceled) | Medium → Low | M | Parked | — | concrete | Keep or park | Nghiệp |
| AA-765 | Gateway refactor (judge, T11 dispatch) | CC | Backlog | keep | Low | M | M2a (later) | ≥S254 | concrete | Judge client into shared; dispatch into acp_publish; docstrings; AA-799 follow-ups (check AA-882 first) | — |
| AA-628 | Engagement feedback loop | CC | Backlog | keep (verify rejected Canceled) | Low | L | Parked | — | missing | Idea only; no build before real publish volume | No publish volume |
| AA-704 | In-app AI assistant | CC | Backlog | keep (parked) | Medium → Low | L | Parked | — | concrete | ADR, then build | AA-703 phases 1 and 3 |
| AA-905 | Geo backfill for 8 countries | CC | Backlog | keep | Low | S | M2b | S252 (one place pass) | concrete | List the countries; quote; run; verify | Quote approval |
| AA-816 | Staff management + Cognito cutover | PO | In Progress | keep | Medium → High | M | M1 | S244 (prep), S245 (S1), S246 (A10, close) | vague | #856 merged 11:41:30Z and deployed with 1d16adf (re-check: run `e2e-cognito.yml`); cutover-plan step E (C9 principal-aware admin-secret check, a CIS auth PR) is missing from this list; N-A..N-F ack; viewer E2E secrets; break-glass; legacy hash; flag off on Production; ADMIN_SECRET rotation; A10; retire the script; update the Done-when | Nghiệp ack; underscore env var permission; CIS freeze (A10) |
| AA-898 | Docs reader page /admin/docs | PO | Backlog | keep | Medium | M | M5 | ≥S254 | vague | Bucket, sync, owner-only endpoints, page; add N-3 and K-15 to the Done-when | Bucket approval |
| AA-855 | UAT videos for all apps | PO | Backlog | keep | Medium | L | M4 | After M2a, on Nghiệp's go | concrete | Scripts; videos at 1440/390; report; sign-off; Cognito login method; bilingual guides | Go signal; AA-816 |
| AA-813 | Tenant users on Cognito (Phase 3) | PO | Backlog | keep (verify rejected the split; rescope instead) | Medium (High before the first paying tenant) | L | M5 | M5 security order #1 (rescope ≥S254, build before the first paying tenant) | concrete (stale design) | Rewrite to ADR 0006 Phase 3, then build | Rescope confirmation |
| AA-821 | Tenant CRM research | PO | Backlog | keep | Low | M | M5 | ≥S254 | concrete | Research and a phased MVP plan | Approval from Nghiệp and Ms. Thư |
| AA-671 | Marketplace redesign | PO | Backlog | keep (parked) | Medium → Low | M | Parked | — | missing | Decide whether to merge with Browse Tours; add a Done-when | Ms. Thư decision |
| AA-655 | Shared design system | PO | Backlog | keep (parked) | Medium → Low | XL | Parked | — | concrete | Package vs copies | Decision |
| AA-904 | TripPlanner Next 15 | TB | In Progress | keep | Medium → High | S | M1b | S244 | concrete | Preview smoke of 4 flows with a test contact; merge #107; prod verify; npm audit | — |
| AA-906 | TripPlanner Next 16 | TB | Backlog | keep | Low | M | M4 prerequisite | ≥S254 | concrete | Bump; proxy.ts; fix the 23 React Compiler errors; smoke | AA-904 |
| AA-680 | Staff RBAC + customer OTP | TB | In Progress | keep, **split** (staff half stays; customer half becomes a new issue after approval) | Medium | XL (staff half S) | M1 | S246 | vague | Live no-group refusal; bridge drop; write a staff Done-when | AA-816 cutover; split approval |
| AA-886 | /privacy, /terms + legal packet | TB | Backlog | keep | Medium → High (pages) | M | M5 (pages early) | S246 (pages); packet with AA-820 | concrete | Draft pages on TP and the portal; consent check; packet | Wording approval |
| AA-861 | TP outbox PII redaction | TB | Backlog | keep | Low | L | M5 | M5 security order #7 (≥S254; no row is 90 days old before ~01/2027) | concrete | tripplanner.job, worker and redact kind; seeded test row; fix the stale title and relation | Destructive-run approval |
| AA-844 | CloudFront for photos + daily sync (PR-11) | TB | Backlog | keep | Medium | M | M2b | S249 | concrete | CloudFront with OAC, cert and DNS; resolve the host in the app layer; daily schedule; 2 scheduled runs | Cost quote |
| AA-837 | /plan contrast, 404, "1 DAYS" | TB | Backlog | keep | Low | S | M4 prerequisite | With or after AA-906 | concrete | Tokens; formatDays; axe; clarify the dark-mode Done-when | AA-904/AA-906 |
| AA-835 | ADR 0004a supply content | TB | Backlog | keep | Medium → Low | XL | M3 | ≥S254 | concrete | The whole cross-repo chain | X1 S22; paid runs |
| AA-682 | Booking operations MVP (wave 3) | TB | Backlog | keep (verify rejected the split; add a Done-when now) | Low | XL | M3 | Unscheduled | missing | Write the Done-when; split at pickup | Tax and payment decisions |
| AA-710 | Asian Trails B2B benchmark | TB | Backlog | keep (verify rejected Done) | Low | XS | Parked | — | missing | Map gaps to issues; KAN-20 reply | — |

## Done issues whose status should change (verify upheld)

| ID | Title (short) | Proj | Status | Proposed status | Priority | Size | Milestone | Session | Done-when | Remaining work | Blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AA-825 | Retention TTL (CIS + Booking) | DP | Done | **In Progress** (reopen) | — | S | M5 | S251 | concrete | One real Booking run under a Dev override (inbox redact plus booking.job rows), or Nghiệp drops that Done-when line | — |
| AA-805 | TP AI Phase 0 (caps, cache, label) | TB | Done | **In Progress** (reopen) | High → Medium | XS | M1b | S247 | concrete | 4 checks (~$0.02): narrate 429, llm_spend_daily, narration cache hit, inactive-tour join | — |
| AA-665 | Cost Operations page | PO | Done | **Todo** (reopen) | High → Medium | L | M5 | First session ≥01/11 (with AA-896) | concrete | Rename; research-run history; demand explorer; DataTable; month-end forecast | — |
| AA-669 | My Content as a DataTable | PO | Done | **Todo** (reopen), or a rescope by Nghiệp | Medium | M | M4 prerequisite | ≥S254 | missing | Place/topic, words, published-at; date filter; duplicate/regenerate; preset saved views | Nghiệp: rescope or build |
| AA-675 | TP re-extraction job | TB | Done | **Canceled** (superseded by AA-712/AA-905) | — | — | — | S244 (status only) | concrete | Closing note | — |
| AA-689 | TP visual planner epic | TB | Done | **Canceled** (superseded) | — | — | — | S244 (status only) | — | Closing note mapping each phase to its successor issue | Nghiệp: is Phase B (My itineraries, share link, PDF) still wanted? |

Two more need a comment only, with no status change:

- **AA-674:** keep Done. Add a correction comment, and move the property test into AA-847.
- **AA-902:** already reopened and In Progress.
