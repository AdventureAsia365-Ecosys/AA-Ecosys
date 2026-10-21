# AA_Ecosys living backlog (ordered work queue)

**Purpose:** the single ordered list of what to do next, so a session starts here instead of re-auditing Linear. Built from the S238 full audit (69 open issues + data standards + logs + code + Jira, `docs/audits/2026-10-15-S238-backlog-audit/`) and updated at the end of every session since.

**HTML view:** [tracker/](tracker/README.md) — the same plan as a filterable page (private artifact <https://claude.ai/artifact/2VSP2stGG1TF7uXvqgQTUY>); update `tracker/plan.json` in the same PR as this file.

**Rules:** at session start read §1–§3 and pick the session's parallel items from §3 and §3b by slot (skip items blocked in §2 or by the "blocked by" notes). At session end update the Status column, move closed items to §5, add new items. Re-audit only when this file is older than ~2 weeks or many issues were created outside sessions.

_Last updated: S246 close, 21/10/2026 (Claude Code), statuses read from Linear at session end. 8 issues closed (list in §5); AA-803 reopened with a new scope. The queue now follows the S246 master plan ([plan-and-status.json](../audits/2026-10-21-S246-master-plan/plan-and-status.json)): 9 parallel lanes (L0–L7, LP), 16 sessions S247–S262, 11 milestones (M1–M5 plus C-M1, P-M1, C-M2, C-M3 for the CRM and the portal move). 53 CRM issues (AA-928…AA-980) were created from CRM design v3 (D1–D8 approved, `docs/audits/2026-10-21-S246-crm-design-v3/`)._

## 1. Time-gated checks (do these first when due)

| Due | Issue | Check |
|---|---|---|
| now (S247) | AA-903 | CIS #901 (Dependabot, `/frontend`) is open: check that "Vercel deploy" shows skipped while required checks pass; link it and close AA-903. |
| daily 06:15 UTC | AA-816 | Ops probe enqueues `staff_directory_reconcile` (Infra #195). Check one job per UTC day in `shared.job` and its drift report (Cognito groups vs `staff_app_grant`). |
| daily 22:00 UTC | AA-869 | Snapshot expiry Lambda `aa-cis-dev-rds-snapshot-expiry` runs live (deletes manual snapshots > 30 d unless `keep-` / `aa:retain*`). An SNS mail only when it deletes, caps, finds a malformed tag or an orphan. |
| ≥01/11 (≈S257) | (cost) / AA-896 | Infra cost audit Aug/Sep/Oct 2026 per `App` tag and service (acc2) + acc3 Bedrock + AWS Lift credits, with AA-838 and AA-665. The numbers feed the Jira platform report (PR-20 Epic). Slot by date, not by session number (~1.2 sessions a day). |
| ~02/11 | (Jira) PR-20 | Platform report period 2 (Story under Epic PR-20): draft → Nghiệp approves → post. |
| ≤11/11 | AA-820 | Tenant terms AI clause (slot S256) — Ms. Thư decides whether counsel is needed. |
| ~mid-Nov | AA-862 follow-up | Re-request acc2 quotas in small steps (Cohere 20 → 100 rpm). |
| 18/11 | AA-878 (Done) | The 4 orphan secrets deleted 19/10 (`aa-cis/dev/api-keys`, `aa-cis/dev/acp-webhook-secret`, `aa-cis/dev/acp-partner-api`, `tripplanner/dev/mapbox-geocoding-token`) leave the recovery window. Nothing to do unless one must be restored before then (`restore-secret`). |
| P2b + 7 calendar days (~S265) | AA-979 | Keep Vercel `aa-cis-portal` at least 7 days after P2b; then remove Vercel, delete `portal/` from CIS, invert the guard tests, update CONTEXT.md + ecosystem-architecture. |
| **before prod** | chore (security) | Rotate the GitHub OAuth token and the RDS master password (printed into the local S240 transcript; D-02/D-03: keep until prod). |

## 2. Waiting on Nghiệp (decisions / manual steps)

- **MFA on the right session:** AA-931 (S248), AA-932 + AA-972 M2M pool (S249, one MFA for both), AA-939 partner pool (S254).
- **AA-847 flip chain (moved to S247 by Nghiệp):** pick the place-pipeline model (Haiku 5.5 trial once CIS #903 is live, else keep Sonnet), approve the AA-905 quote for the paid place run (~$1–10), then set `PLACES_SOURCE` on the TripPlanner browse Lambda and `PLACE_SHAPES_ENABLED` on CIS by hand (underscore env vars, edit in VSCode / console).
- **Jira drafts S246:** review and post `docs/audits/2026-10-21-S246-jira-drafts/README.md` (PR-19 carries the CRM UI page link).
- **AA-928:** accept the CRM ADRs (S248).
- **S1-first A/B (L1):** arbitrate ~30 pieces after run 2 (S251, ~30–45 min) and fix the reference examples (~1 h).
- **Ask before creating issues:** T13 route stitching (needed by AA-948), splitting P2a out of AA-979 (P2a runs before P1, which AA-979's blocked-by does not allow). Linear quota 143/250: archive Done every session.
- **AA-Partner repo:** Nghiệp creates it if "members can create repositories" is turned off (access review Q-2); AA-933 needs it in S250.
- **AA-901:** install the GitHub App for agents + release-please (S251).
- **Ms. Thư:** tax, deposit %, payment marking and the B2B margin (AA-682 + Lane B); AI terms clause by 11/11 (AA-820) and the /privacy, /terms wording (AA-886).
- **TasteWP test site:** revoke the AA portal e2e application password on the TasteWP test site when no longer needed (the value was shown in the S245 transcript).
- Access review 2026-Q4 (`docs/audits/2026-10-20-S245-access-review/`): Q-1 (Ms. Thư `cis-admin` or `cis-reviewer`), Q-2 (narrow 4 GitHub Apps, turn off "members can create repositories"); owner OK to delete the orphan IAM user `s226-should-fail` (AA-878 finding 2).
- **Break-glass TOTP:** add the NEW `totp_seed` (rotated S244) from Secrets Manager `aa-identity/dev/breakglass` to an authenticator app, if wanted.
- **Ms. Thư's first admin login** (invite sent 18/10; Google cleared the Chrome warning 19/10). Optional: Nghiệp dropped it from AA-858 Done-when (S243).
- AA-855 UAT videos: when Nghiệp says (after all the tech work, >S262). Product questions from S238: T2 day separator; "— N Days" vs ", N Days".
- AA-829: approve deleting/securing the 2026-09-16 real-data dumps; DSN CNAME secrets are edited by hand.
- AA-905 geo backfill: quote first, then approve a subset (S256).
- Settled in S246 (end): AA-847 flip chain → S247; AA-911 P5–P8 (bridge retirement) → after all project code is done, like the A10 e2e mail exception, with a new gate (agent signs in to Booking and CIS through Cognito with the E2E user + Playwright spec green); legal (AA-886) is not urgent, technical work first; all 25 AA-803 Jev proposals approved.
- Settled in S246: CRM design v3 D1–D8 approved (replaces the 16 recommendations ask); Ms. Thư's questionnaire v2 counts as settled (not sent); writing for the adventure.asia site is AA staff's job and out of scope (CIS focuses on tenants); AA-816 A10 stays until all project code is done (no new @adventure.asia mailbox).

## 3. Ordered work queue (S247–S262)

Source: the S246 master plan ([plan-and-status.json](../audits/2026-10-21-S246-master-plan/plan-and-status.json), keys `plan.lanes`, `plan.sessions`, `plan.blocked_by_relations`). Slot = the first session whose parallel items name the issue. Items not named in any session keep their old slot (AA-783 S251, AA-839 S253) or go to §4.

**Lanes** (work runs in parallel, one lane item per session as a rule):

| Lane | Scope | Issues in order |
|---|---|---|
| L0 | Tracker + docs sync at the start of each session (orchestrator, root repo) | AA-886, AA-803, AA-896 (AA-925, AA-915, AA-821 Done S246) |
| L1 | CIS quality, S1-first; T9 tuning in parallel (Q2 = b) but no new gates for 4 weeks; ≤2 CIS backend PRs from L1 per session | AA-845, AA-779, AA-780, AA-645, AA-926, AA-916, AA-924, AA-790, AA-789, AA-788, AA-795, AA-783, AA-741, AA-765, AA-900, AA-917…AA-923, AA-642 |
| L2 | CIS places + TripPlanner flip (AA-847), then paid place runs in subsets | AA-847, AA-712, AA-905, AA-784 |
| L3 | Identity + security (subagent review for auth/IAM PRs) | AA-911, AA-816, AA-813, AA-820, AA-874, AA-871, AA-859, AA-829, AA-873, AA-703 |
| L4 | Booking: CRM Lane B (B1 → B2 → B2b → B3 in sequence, review every bk-019+) + AA-682; ≤1 Booking item per session | AA-972…AA-977, AA-682, AA-910, AA-835 |
| L5 | TripPlanner, in sequence (same files) | AA-909, AA-906, AA-837, AA-908, AA-871, AA-861 |
| L6 | CRM W0–W4 in AA-Partner: ≤1 critical-path step and ~3 CRM items (incl. Lane B/P) per session | AA-928…AA-951 |
| LP | Portal move (CRM Lane P) + portal issues | AA-759, AA-760, AA-978, AA-979, AA-761, AA-669, AA-671, AA-762 |
| L7 | Platform / FinOps / release | AA-903, AA-879, AA-901, AA-891, AA-896, AA-838, AA-665, AA-899, AA-825, AA-880, AA-864, AA-855 |

**Session rules (S246 plan):** at most ~3 heavy code items per session (RAM); only the orchestrator merges, deploys and verifies; one Terraform state, so applies run one after another; DM-11.4 blocks backend merge/deploy (not only DB Migrate) while `shared.job` has jobs, so a paid run starts only after the session's first deploy and the flip session (S247 since the S246 close) runs nothing paid besides the approved place run; date-gated work is slotted by date (≈1.2 sessions a day, first session ≥01/11 ≈ S257). The CRM pace assumes Ultracode every session (C-M1 ≈ S252–S253, C-M2 ≈ S258–S260, C-M3 ≈ S262–S265); in normal sessions use the design's dates (C-M1 ~mid-Nov, C-M2 ~mid-Dec, C-M3 ~early Jan 2027).

**Work without a Linear issue:**

- L1 S1-first steps: S247 step 0/1 ($0: fact table, code checks on 50 S1 pieces, panel re-score twice); S248 step 2 (prompt surgery behind a flag, build A+ and E, 3-model screen on 12 tours ~$2.5, with AA-645); S250 A/B run 1 (25 golden × A+/A'/W/E, ≤$10); S251 run 2 + Nghiệp arbitration; S252 step 4 (winner into shadow/review, T2 reads the fact table); S253 step 5 written go/no-go for AA-926, AA-916, AA-924, AA-790, Writing Memory P1+ and a catalog rerun.
- LP P2a (S255) and P2b (S258) are parts of AA-979; T13 route stitching (L5, ~S258) needs a new issue (ask first).
- S262: L0 wrap-up and re-plan of CRM W5–W8, A10 migration renumber (AA-816), Vercel portal removal if 7 days have passed; CRM C-M3 check.

| # | Issue | Work | Lane | Size | Slot · status / next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| 1 | AA-847 | Places: L4 catalog read model fast enough for PLACES_SOURCE=cis + flip + content-validity report | L2 | L | **S247 flip chain** (moved from S249 by Nghiệp). **In Progress**; everything before the flip shipped S246: CIS 253, 255–258 + tp-017 applied on Dev, CIS #895/#896/#897, TP #120/#121, probe parity 21/21, contract pins v1.2 (Infra #259), tour on/off check PASS. Place model trial: Haiku 4.5, GPT-6 Luna, GPT-5.6 Luna all below the 95% bar vs Sonnet. Next: Haiku 5.5 trial once CIS #903 is live (else keep Sonnet) → AA-905 quote + paid place run (~$1–10) until the coverage gate shows 0 missing (66 now) → env switches by hand → post-flip parity + screenshots → 7-day window | Model choice; AA-905 quote; env switches by hand |
| 2 | AA-803 | Jev: evaluate every Jev question on live data; keep the ones with real effect, switch off the rest | L0 | M | S247. **In Progress** (reopened S246 with this scope). 25 questions evaluated (`docs/audits/2026-10-21-S246-jev-question-eval/`), Nghiệp approved all: keep 9, retune 2, switch off 5, 9 T-series stay off. Applied: a1_brand_fit off, a1_keyword_about_tour reject 0.40, a3_question_foreign off; a3_idea_traveller kept (J09). Left: ship the meal rule (J04: Jev waived meal codes on 7.8% of tours), then switch off a1_claim_supported + a1_promise_unsupported | — |
| 3 | AA-845 | Jev: A-axis ground-truth loop + a1_claim_supported reject ceiling + 402 investigation | L1 | M | S247. **In Progress**; low-credit + 402 e-mail alerts shipped and verified with test e-mails (CIS #898); no reject ceiling meets the bar (kept NULL); 402 root cause = prepaid credit ran out twice. Close once the meal rule ships and a1_claim_supported is off (AA-803) | — |
| 4 | AA-886 | /privacy and /terms pages + legal readiness packet for Ms. Thư | L0 | S | **In Progress**, not urgent (Nghiệp S246: technical work first, no push in Jira or the plan). Technical part done: root #144 + /privacy, /terms 200 on TP and the portal, consent capture run 39596391333 clean. Left: GDrive upload (Drive connector needs re-auth) | Ms. Thư: wording, when she has time |
| 5 | AA-813 | Tenant user accounts — invites, roles (owner/editor/viewer), API key rotation | L3 | M | S247. Not built alone: re-scoped inside AA-928 (S247), delivered through AA-939 (partner pool, S254) + AA-978 (membership feed, S256); blocks AA-978 | Confirm the rescope (AA-928) |
| 6 | AA-911 | Staff sign-in for Booking (and CIS) Vercel Previews, then retire the CIS → Booking bridge | L3 | M | **In Progress**. P1–P4 shipped S246: CIS #899 (BFF refuses cross-site writes), CIS #900 (E2E targets the Booking Preview host), Infra #260 (Preview-only Cognito clients + DNS), Booking #54 (Preview sign-in through a read-only client; verified). Branch `preview-signin` locked by a ruleset. **P5–P8 (bridge retirement) after all project code is done** (Nghiệp), gate: agent signs in through Cognito with the E2E user + Playwright green; branches stay local | — |
| 7 | AA-780 | LinkedIn: 120-word floor, Trail Pulse voice, broetry + new stock lines | L1 | S | **In Progress**; S248 T9 tuning (Q2 = b), no new gates. S246 panel: adjust, do not close — 120-word floor met (shortest 149 words), but light 4/15, 11 false passes, Trail Pulse 1/3; most failures are outside AA-780 (fidelity, tenant voice) | — |
| 8 | AA-779 | T9 FAQ: questions from People Also Ask first; every answer names its subject | L1 | M | **In Progress**; S248, no new gates. S246: 200-question labelled set (κ 0.913); the rule branch is not better than main (McNemar p 0.68) and is not shipped; main precision 0.64. Next: small-LLM option (~$0.18 for 200 questions), ship only if it passes the bar | Approve the LLM trial |
| 9 | AA-645 | Claude Sonnet 5 for writer stages (t2_generate, t8_angle_gen, t9_write, s1_atom_writer) vs Sonnet 4.5/4.6 on Bedrock | L1 | S | S248. Folded into S1 step 2 (S248): 3-model screen on 12 tours (~$2.5) | — |
| 10 | AA-903 | Skip the "Vercel deploy" job for Dependabot PRs (Booking, TripPlanner, CIS) | L7 | XS | S247. **In Progress**; fix on main in all 3 repos since 19/10. CIS #901 (Dependabot, `/frontend`) is open: link its skipped Vercel deploy and close | — |
| 11 | AA-816 | Staff user management UI + Cognito cutover (retire create_staff_user.py) | L3 | S | **In Progress**; S249 S2: API legacy login flag off (CIS deploy in an idle shared.job window). AA-911 P1–P4 are live but its bridge retirement (P5–P8) waits for the end of the project, so re-check what S2 still depends on before S249. A10 (E2E exception removal; mig 252 held locally) moves to the end of the project (Nghiệp, S246): no new @adventure.asia mailbox | — |
| 12 | AA-879 | CI gate parity across CIS, Booking and TripPlanner | L7 | M | S249 (pulled ahead from S253): CI gate parity + scheduled Terraform drift detection before the 4th repo (AA-933, S250) | Branch-protection toggles |
| 13 | AA-759 | PortalShell on the kit — grouped nav, real ⌘K, mobile bottom bar, theme, route renames (no T-number slugs) | LP | M | S249 PortalShell on the kit, in CIS before P2a (UI + Vercel deploy, needs no idle job window) | — |
| 14 | AA-909 | TripPlanner: check the guest token on the read GETs (trip, suggestions, coverage, activities) | L5 | S | S250 guest-token check on the 4 read GETs, right after AA-847 slice 6d | — |
| 15 | AA-760 | Page-by-page audit + state fixes — statuses from the job, never inferred from rows ("Writing…" bug) | LP | M | S250 page-by-page audit + state fixes, in CIS before P2a | — |
| 16 | AA-783 | Human calibration of the T9 commercial panel — 40 pieces labelled by Nghiệp | L1 | M | S251. Agreement analysis once Nghiệp's 40 labels exist (not slotted in the S247–S262 sessions; kept at S251) | 2–3 h labelling |
| 17 | AA-901 | GitHub App for agents and release-please, ADR 0010/0011, CODEOWNERS (U-25) | L7 | M | S251 GitHub App (Nghiệp installs it) + ADR 0011, CODEOWNERS | Install the App |
| 18 | AA-906 | TripPlanner Next.js 15 → 16 upgrade (React Compiler lint refactor) | L5 | M | S252 Next 15 → 16 + React Compiler refactor (after AA-847 6d; not in the same session as AA-934/935) | — |
| 19 | AA-891 | Version traceability — release-please, CHANGELOG and first tags per app | L7 | M | S252 release-please and first tags per app (after AA-901) | Version numbers |
| 20 | AA-790 | T10: tenant-voice rubric gate + post-repair integrity check | L1 | L | S253. Held until the S253 written go/no-go | LLM judge vs deterministic rubric |
| 21 | AA-916 | Capture writing signals: before/after text, reason codes, every T9 attempt | L1 | M | S253. Held until the S253 go/no-go; on go: Writing Memory P0 (migration + RLS → agent review) | — |
| 22 | AA-926 | Q-1: error taxonomy, gate registry, single thresholds file and lint | L1 | M | S253. Built on branch feat/aa-926-quality-registry (11 commits), parked per Q1; merge only on a go at S253 | — |
| 23 | AA-924 | Severity per violation in the gate ledger, then merge F15_voice_warn→F15 and F2 variants + stock list → one lexicon gate | L1 | M | S253. Held until the S253 go/no-go (after AA-926) | — |
| 24 | AA-871 | JSON logs with request ids + Sentry for Booking and TripPlanner | L3 | M | S253 Booking/TP part (Sentry + structlog) if no other Booking/TP subagent runs that session, else later; portal Sentry comes with P2b (AA-979) | — |
| 25 | AA-835 | ADR 0004a supply content — supply contracts, Booking supply outbox, CIS consumer | L4 | — | S253. Its outbox pattern merges into AA-975 (CRM-B3, S253); paid consumer trial later | Paid consumer trial |
| 26 | AA-837 | TripPlanner /plan UI leftovers: 7 WCAG AA contrast violations, Customise 404, "1 DAYS" | L5 | S | S253 /plan contrast and labels (after AA-906, same files) | Clarify dark mode |
| 27 | AA-839 | Erasure runbook + DRY RUN job for a traveller and an offboarded tenant | — | XS | S253. Now: remove the "GDPR" wording from the offboard endpoint; erasure runbook before prod | — |
| 28 | AA-712 | ADR 0002: move the place pipeline (itinerary places, geocoding, tour graph) from TripPlanner into CIS | L2 | M | S254 trial place pass (3, then ≤50 tours), only in a session without an A/B run; after the AA-847 flip | Quote and country order |
| 29 | AA-762 | Team & roles — tenant users (owner/editor/viewer), invites, self-serve API keys — after the ecosystem identity ADR | LP | S | S254. Close as a duplicate of AA-939 (CRM-11) in S254 | — |
| 30 | AA-874 | Redis AUTH/TLS/at-rest encryption + tenant-flag read-failure alarm | L3 | M | S255 Redis AUTH/TLS/at-rest + flag alarm, in an idle CIS window | Cost (D-19) |
| 31 | AA-682 | Operations MVP — supplier bookings, trip checks, invoices + payment schedule, supplier bills | L4 | XL | S255. Part 1 S255, part 2 S258 (payment schedule, manual payment marking), part 3 S260 — only once Ms. Thư settles tax, deposit % and payment marking. Blocked by AA-928 (commercial-core memo) and AA-974; never between B1–B3 (same files) | Ms. Thư: tax, deposit %, payment marking |
| 32 | AA-910 | Booking staff admin at 1440 px (table overflow, FX wrap, scrollbar) + audit rows for room type / rate | L4 | S | S255. Fallback in S255/S260 while AA-682 still waits for Ms. Thư | — |
| 33 | AA-908 | Traveller sign-in on Cognito EXTERNAL, TripPlanner guest linking and My Trips (customer half of AA-680) | L5 | M | S255 traveller sign-in on Cognito EXTERNAL, guest linking, My Trips (after AA-909) | — |
| 34 | AA-905 | Geo graph backfill for the 8 countries without one (paid place-pipeline run, needs a quote) | L2 | M | S256 geo backfill subset inside the place pass | Quote first |
| 35 | AA-820 | Tenant Terms clause for the Anthropic Usage Policy (effective 12/11/2026) + AI-content attribution | L3 | — | S256, deadline ≤11/11: tenant terms AI clause; Ms. Thư decides on counsel | Ms. Thư (counsel) |
| 36 | AA-917 | Rule store and the mining job (scoped rules, fact filter, cheaper drafter) | L1 | M | S257. Writing Memory P1 at S257 if the S253 decision is go | Release click per rule set |
| 37 | AA-918 | R0 replay engine ($0) and the L0 lexicon fast path | L1 | M | S257. Writing Memory P1 at S257 if the S253 decision is go | — |
| 38 | AA-665 | Cost Operations — budgets, DFS/Jev/LLM/AWS spend, research triggers audit, alerts (reopened) | L7 | L | S257. First session ≥01/11 (≈S257): Cost Operations page (reopened) | — |
| 39 | AA-896 | FinOps doc, Cost Anomaly Detection and the monthly cost report with unit costs | L7 | S | S257. **In Progress**; First session ≥01/11 (≈S257, slotted by date): cost report Aug/Sep/Oct per App tag and service, acc3 Bedrock + credits, unit costs | Decision list |
| 40 | AA-838 | Capacity review (monthly), pg_stat_statements (weekly), access review (quarterly); first capacity review | L7 | M | S257. First session ≥01/11 (≈S257): first capacity review | — |
| 41 | AA-761 | Account pages with real data — Billing usage/overage, Activity timeline, Integrations (WordPress health, API key view) | LP | M | S257 account pages in AA-Partner/portal (after P2a); blocked by AA-979 | — |
| 42 | AA-859 | Tenant pool wave 2: tenant write/planning routes on aa_app_user, RLS on the tables they touch | L3 | L | **In Progress**; S258 tenant pool wave 2/3 (re-plan after S22, renumber migrations, D5b) | Wave-4 route retire |
| 43 | AA-919 | Eval and release gate: golden set, R2 runner, targeted shadow, Releases tab | L1 | L | S259. Writing Memory P2 at S259 if go | Each release |
| 44 | AA-920 | Inject approved rules into the four writers with a post-activation check | L1 | M | S259. Writing Memory P2 at S259 if go | — |
| 45 | AA-829 | Restore drill on Dev + private DSN CNAME + secure the real-data dumps (2026-09-16) | L3 | M | **In Progress**; S259 restore drill; dumps: DRY RUN then move/delete once approved; DSN CNAME | Approve dumps; DSN secrets by hand |
| 46 | AA-899 | OpenAPI export and breaking-change check for CIS and Booking | L7 | M | S259 OpenAPI export + breaking-change check (after AA-891) | — |
| 47 | AA-669 | My Content as a DataTable — columns, filters, sort, bulk export/publish (reopened) | LP | M | S259 My Content DataTable in AA-Partner/portal (after P2a, AA-979) | Rescope or build |
| 48 | AA-741 | T-series audit: end-to-end T0→T11 run on controlled tenants + per-mechanism report | L1 | XL | S260 T-series G7 + G8 report (paid), per the S253 go/no-go | Paid run ~$10–20 |
| 49 | AA-784 | Place cards platform-wide build — ~7–9.7k places, staged by country (≈$15–25) | L2 | L | S260 place cards in paid subsets by country | Quote |
| 50 | AA-873 | Account detection baseline: GuardDuty, Access Analyzer, S3 BPA, CloudTrail | L3 | M | S261 after the GuardDuty quote; reuse the KMS/alarm pattern of AA-932 | Cost per item |
| 51 | AA-825 | Retention + rollups for log tables (reopened: one real Booking retention run) | L7 | S | S261 retention rollups: one real Booking retention run under a Dev override, or drop the Done-when line | Drop the line or allow the run |
| 52 | AA-671 | Marketplace redesign — catalog grid with filters, detail drawer | LP | M | S261 Marketplace redesign in AA-Partner/portal (after P2a) | Merge with Browse Tours? (Ms. Thư) |
| 53 | AA-921 | Pinned example sets and tenant preference summaries | L1 | M | S262. Writing Memory P3 at S262 if go | — |
| 54 | AA-922 | Weekly KPIs, soft-stop rollback and the disagreement queue | L1 | M | S262. Writing Memory P3 at S262 if go | — |
| 55 | AA-923 | Labels for T2/A1, offboarding deletion, retire the old lesson paths | L1 | M | S262. Writing Memory P3 at S262 if go | — |
| 56 | AA-880 | L9 prod blueprint + ADR 0012 environment model (trigger: go-live date) | L7 | L | S262 ADR 0012 draft (before CRM W8); L9 prod blueprint on the go-live date | Date; account (AA-864) |

## 3a. Platform roadmap keys (PLAT-01)

Content and status live in the [engineering handbook §9](../engineering-handbook.md#9-roadmap). This list only orders the next picks.

| Order | U-xx / key | Issue | Next step |
|---|---|---|---|
| 1 | U-09, U-11, AA-887–890 | AA-889, AA-890 | Done: AA-902, AA-895, AA-887 (S244–S245), AA-889 and AA-890 (19/10) |
| 2 | U-42 | AA-846 | Done S245 (apply guard, exact pin, hidden drift, apply-role narrowing) |
| 3 | AA-888, AA-892 follow-ups | AA-888 | AA-888 Done S245 (docs lint in every repo, red evidence). Owner option: "Docs lint" as a required check on Booking / TripPlanner main |
| 4 | AA-893 | AA-893 | Done S245 (generated `alarms.md` + outputs, Infra #244) |
| 5 | U-26 + U-04 | AA-878 | Done S245 (drift diff = 0, first access review); its open findings: §2 |
| 6 | U-25 → AA-891 | AA-901, AA-891 | GitHub App (Nghiệp installs it, S251), then release-please (S252) |
| 7 | AA-896, U-38 | AA-896, AA-838 | First session ≥01/11 (≈S257) |
| 8 | U-28 + U-61, U-44, AA-894 | AA-879, AA-899, AA-894 | CI parity + drift detection pulled ahead to S249 (before the 4th repo, AA-933); OpenAPI S259 after AA-891; env register later (AA-893 is Done) |
| later | U-15, U-24, U-37, U-39, U-35, U-56 | AA-848, AA-877, AA-850, AA-851, AA-853, AA-881 | AA-848 Done (20/10), AA-877 Done S246; AA-850/AA-851 unblocked since X1 S22; AA-826 and AA-849 Done S245, so AA-853 can start; AA-881 at 05/2027 |

## 3b. CRM / AA-Partner queue (W0–W4, Lane B, Lane P)

53 issues AA-928…AA-980, project "Partner CRM — AA-Partner", from CRM design v3 (`docs/audits/2026-10-21-S246-crm-design-v3/`, issue map `linear-issue-map.json`). Critical path: AA-928 → AA-932 → AA-933 → AA-934/AA-935 → AA-936 (C-M1) → AA-937 → AA-939 → AA-943 → AA-944/AA-945 → AA-946 (C-M2) → AA-947 → AA-949 → AA-950 (C-M3). Blocked-by lists come from `plan.blocked_by_relations` (corrected against the design cards). W5–W8 are in §4 until the S262 re-plan.

| # | Issue | Work | Lane | Size | Slot · next action | Needs Nghiệp |
|---|---|---|---|---|---|---|
| C1 | AA-928 | CRM-01a ADRs + contracts + spec errata | L6 | M | W0 · S247: incl. ADR AA-Partner, contracts, errata, AA-813 re-scope, W1 sign-in, Booking commercial-core memo, ADR 0008a vs AA-804 | Accept the ADRs (S248) |
| C2 | AA-929 | CRM-01b Data-standards bump | L6 | M | W0 · S247: docs/root only, no code subagent | — |
| C3 | AA-930 | CRM-02 Readiness checks (read-only) | L6 | S | W0 · S247: docs/root only, no code subagent | — |
| C4 | AA-931 | CRM-03 Infra bootstrap + CloudFront VPC-origin spike | L6 | M | W0 · S248: apply-role grants (kms alias/crm-*, VPC origin), CloudFront → VPC origin → NLB → ALB host-rule spike | MFA (Infra apply) |
| C5 | AA-972 | CRM-B1 M2M + B2B quote | L4 | L | Lane B · S249: bk-019, review; blocked by AA-928, AA-911 | MFA (M2M pool); Ms. Thư: B2B margin |
| C6 | AA-932 | CRM-04 Infra + DB owner `crm` | L6 | L | W1 · S249; blocked by AA-928, AA-929, AA-931 | MFA (KMS policies) |
| C7 | AA-933 | CRM-05 AA-Partner repo, API, job runner | L6 | L | W1 · S250: branch protection + required CI from day one; blocked by AA-928, AA-932 | Create the AA-Partner repo if repo creation is turned off (access review Q-2) |
| C8 | AA-973 | CRM-B2 Departures, capacity, holds | L4 | L | Lane B · S251: bk-020 + channel on trip_cases, review; blocked by AA-972 | — |
| C9 | AA-934 | CRM-06 KeyProvider and field encryption | L6 | M | W1 · S251; blocked by AA-932, AA-933 | — |
| C10 | AA-935 | CRM-07 Web skeleton + synthetic agencies | L6 | M | W1 · S251; blocked by AA-933 | Create the e2e-test-crm-* users |
| C11 | AA-974 | CRM-B2b Booking commercial rules (new, Fix C2, A3, A8) | L4 | L | Lane B · S252: bk-021: VND, shared cancellation fees, hold extension (ADR 0005 d5); blocked by AA-973 | — |
| C12 | AA-936 | CRM-08 Slice 1: intake → Inquiry → board | L6 | L | W1 · S252: → C-M1; blocked by AA-934, AA-935 | — |
| C13 | AA-975 | CRM-B3 Event feed + on-request desk + incident flag | L4 | M | Lane B · S253: bk-022, shared outbox (takes the AA-835 pattern) + on-request desk; blocked by AA-973 | — |
| C14 | AA-937 | CRM-09 F1/F2 complete | L6 | L | W2 · S253; blocked by AA-934, AA-936 | — |
| C15 | AA-976 | CRM-B4 CIS catalog over HTTP | L4 | M | Lane B · S254: needs the places flip; blocked by AA-928, AA-972, AA-847 | — |
| C16 | AA-939 | CRM-11 F4 roles, partner pool, MFA, permission matrix | L6 | L | W2 · S254; blocked by AA-928, AA-937 | MFA (Cognito) |
| C17 | AA-940 | CRM-12 F5 audit | L6 | M | W2 · S254; blocked by AA-937 | — |
| C18 | AA-938 | CRM-10 F3 scrubber | L6 | M | W2 · S255; blocked by AA-930, AA-937 | — |
| C19 | AA-942 | CRM-14 Data lifecycle rules | L6 | M | W2 · S255; blocked by AA-940 | — |
| C20 | AA-979 | CRM-P2 Move `portal/` into AA-Partner | LP | L | Lane P · S255: P2a S255 (portal/ into AA-Partner/portal, keep history + Vercel + API-key auth); P2b S258 (CloudFront → Fargate, partner pool, 301 /trip/*, Sentry); remove Vercel ≥7 days after P2b (~S265); blocked by AA-978, AA-935, AA-931 | Approve P2a before P1 (split AA-979 or note the exception) |
| C21 | AA-977 | CRM-B5 AA-authored content in CIS (new, Fix C1) | L4 | M | Lane B · S256: CIS migration, review; blocked by AA-976 | — |
| C22 | AA-943 | CRM-15 Modules 1 + 2 complete | L6 | L | W3 · S256; blocked by AA-937, AA-939 | — |
| C23 | AA-978 | CRM-P1 Membership feed + tenant API | LP | M | Lane P · S256: membership feed + cis.tenant-api.v1 (CIS); blocked by AA-939, AA-813 | — |
| C24 | AA-941 | CRM-13a AA admin L1 console | L6 | M | W2 · S257; blocked by AA-939, AA-940 | — |
| C25 | AA-944 | CRM-16 Agency-line ledger + suppliers | L6 | M | W3 · S257; blocked by AA-943 | — |
| C26 | AA-945 | CRM-17 Module 5 email | L6 | L | W3 · S257; blocked by AA-938, AA-943 | — |
| C27 | AA-946 | CRM-18 Thin full lifecycle | L6 | L | W3 · S258: → C-M2; blocked by AA-944, AA-945 | — |
| C28 | AA-947 | CRM-19 B2B client + AA lines | L6 | M | W4 · S259; blocked by AA-944, AA-972, AA-973, AA-974, AA-975, AA-976 | — |
| C29 | AA-948 | CRM-20 Builder map fork (enhancement) | L6 | M | W4 · S260: enhancement, does not block C-M3; needs T13 (no issue yet) + AA-906 + 6d; blocked by AA-935, AA-847, AA-906 | — |
| C30 | AA-949 | CRM-21a Proposal model + day-list builder | L6 | L | W4 · S260; blocked by AA-947 | — |
| C31 | AA-950 | CRM-21b Client proposal + accept + hold | L6 | L | W4 · S261: → C-M3; blocked by AA-949, AA-973, AA-974 | — |
| C32 | AA-951 | CRM-22 Module 4 + "Before you go" | L6 | M | W4 · S261; blocked by AA-949, AA-977 | — |

## 4. Later / parked

| Issue | Work | Milestone | Status / trigger | Needs Nghiệp |
|---|---|---|---|---|
| AA-855 | Ecosystem UAT with recorded run videos: CIS admin + portal, TripPlanner, AA-Booking | M4 | after M2a. UAT videos for all apps after all technical work (>S262), Cognito login, bilingual guides | Go signal |
| AA-804 | AI platform ADR + ledger v2 — one gateway library, attempt-level llm_call_log, AI Use Register | M5 | later. AI platform ADR + ledger v2 + AI Use Register before prod; AA-928 settles ADR 0008a vs AA-804 (S247) | Accept the ADR |
| AA-851 | shared.countries (ISO-3166) + v_countries / v_destinations catalog views | M5 | later. shared.countries + v_countries / v_destinations (unblocked by S22) | — |
| AA-642 | Model Gateway — one routing layer for Claude/Bedrock, OpenAI, Jev, driven by admin UI settings | later | later. Model Gateway epic; last in the L1 order | — |
| AA-703 | Identity epic (ADR 0006): Cognito workforce + external pools, staff/tenant/traveller sign-in | M1 | later. **In Progress**; Epic: post a Phase 2/3 status comment with evidence links (M1 criterion); closes when AA-816, AA-911, AA-813 and AA-908 land | — |
| AA-788 | T10: promote F12_scope, F14 under-length and F9_brand_style to blocking | M2a | later. Promote F12_scope / F9_brand_style to blocking (after AA-924) | — |
| AA-789 | T10 gates recall tunes (F17, F18, F15, F13, F16) | M2a | later. Gate recall tunes, lexical part only; not slotted in the S1-first plan (no new gates for 4 weeks) | — |
| AA-795 | T2: persist the judge breakdown per version + brand-claim fidelity check | M2a | later. T2 judge breakdown + brand-claim fidelity | Still wanted? |
| AA-814 | Facts Entry API + UI — platform and tenant-scope facts used by T2/T9 | M5 | later. Facts Entry API + UI (after AA-859 / AA-813) | Priority vs place cards |
| AA-850 | Dead Table Registry + wave-1 quarantine | M5 | later. Dead Table Registry + wave-1 quarantine (unblocked by S22) | Approve the DRY RUN |
| AA-853 | Schema drift diff against a replayed DB + migration ownership lint | M5 | later. Schema drift diff + ownership lint (after AA-826) | — |
| AA-898 | Docs reader page in the CIS admin — S3 sync, manifest, /admin/docs | M5 | later. /admin/docs reader page | Bucket (~0.01 USD/month) |
| AA-765 | Consolidate judge clients, move T11 dispatch into services/acp_publish, clean model docstrings (G6) | M2a | later. Gateway refactor + AA-799 follow-ups; after the S253 go/no-go | — |
| AA-861 | TripPlanner outbox payload PII redaction after 90 days | M5 | later. tripplanner.job + outbox PII redact; first rows age past 90 d ~01/2027 | Approve the first real run |
| AA-864 | Research: consolidate on one AWS account | later | later. Consolidate on one AWS account — decide before AA-880 | Still wanted? |
| AA-894 | Generated env-config register (names only) and DB ERD | M5 | later. Env-config register + ERD (after AA-893) | — |
| AA-900 | LLM operations docs, prompt versioning and eval gate | M2a | later. LLM ops docs, prompt register, manual eval gate; after the S253 go/no-go | — |
| AA-881 | PostgreSQL 15 major-upgrade rehearsal on a restored snapshot (trigger 05/2027) | parked | 05/2027. PG 15 major-upgrade rehearsal | — |
| AA-655 | One design system for the ecosystem — shared tokens + component kit | parked | parked. Shared design system package; after P2a the kit lives in 3 copies (CIS admin, portal, CRM web), byte guard until then | Package vs copies |
| AA-704 | In-app AI assistant for admin + tenant | parked | parked. In-app AI assistant — after AA-703 phases 1 and 3 | Keep on the roadmap? |
| AA-781 | F9 v2: fix place_background / opinion claim classification | parked | parked. F9 v2 claim rules | Keep or park |
| AA-782 | T9 cost: A/B a cheaper blog writer on 8 paired blogs | parked | parked. Cheaper T9 blog writer A/B (~$1.20) | Vendor rule |
| AA-842 | Investigate OpenTelemetry gen_ai tracing for every LLM call (read-only report) | parked | parked. OTel gen_ai tracing — build option B only on a trigger | — |
| AA-628 | Engagement feedback loop for T-series | parked | parked. Engagement feedback loop — needs real publish volume | Park or cancel |
| AA-697 | Architecture diagrams with official AWS icons — ecosystem + each repo | parked | parked. Architecture diagrams — after M1 | Scope |
| AA-710 | B2B benchmark: Asian Trails (eConnect, API, Lemax) | parked | parked. Asian Trails B2B benchmark (KAN-20) — at B2B design start | Close or keep |
| AA-952…AA-980 | CRM W5–W8 (21 issues: AA-952, AA-953, AA-954, AA-955, AA-956, AA-957, AA-958, AA-959, AA-960, AA-961, AA-962, AA-963, AA-964, AA-965, AA-966, AA-967, AA-968, AA-969, AA-970, AA-971, AA-980) | later; AA-969, AA-970, AA-980 in M5 | ≥S263: not slotted before S262; re-plan at S262 from the real pace (blocked-by lists in `plan.blocked_by_relations`) | AA-964 and AA-971 need MFA; AA-971 needs Ms. Thư to name the second alarm recipient |

## 5. Closed in S246

Evidence per issue: Linear comments, then `docs/linear-export/` once exported and archived.

- **Done (8 of the 20 planned):** **AA-927** (CIS #888: every LLM call writes exactly one `llm_call_log` row; rerun 210 calls = 210 rows), **AA-876** (CIS #889 login rate limit, CORS off on deployed environments, security headers; Booking #52; TP #118; Infra #247/#249 API Gateway throttles; the WAF moved to AA-908), **AA-877** (Infra #245/#250, Booking #53 bk-018, TP #119 tp-016, root #148 RoPA column inventory), **AA-844** (Infra #246/#251 photos CDN `img.lumiguides.it.com`, CIS #890 daily `photo_sync`), **AA-729** (before/after numbers on fixture 1.1.0 posted), **AA-925** (CIS #891/#893/#894; live forced-Jev drill holds the output with `degraded = jev_unavailable`), **AA-915** (CIS #887, root #145; WM-01 live check PASS, no read or insert on `shared.pipeline_lessons`), **AA-821** (CRM final design pack `docs/audits/2026-10-21-S246-crm-design-v3/final/` + 53 issues).
- Shipped, still In Progress: **AA-847** (all pre-flip work: CIS 253, 255–258 + tp-017 applied, TP #121, pins Infra #259, parity 21/21, tour on/off PASS; the flip chain moved to S247), **AA-911** (P1–P4: CIS #899/#900, Infra #260, Booking #54, Booking Preview sign-in verified; P5–P8 after all project code is done), **AA-845** (CIS #898 credit alerts verified with test e-mails), **AA-803** (reopened; 25 Jev questions evaluated and approved, J06/J07/J16 applied, meal rule in progress), **AA-886** (technical part done; not urgent per Nghiệp), **AA-779** / **AA-780** (S246 panel measurements, see §3), **AA-816** (A10 to the end of the project), **AA-903** (waiting for evidence, CIS #901). **AA-926**, **AA-916**, **AA-924**, **AA-790** held by the quality decisions (Q1, S253 go/no-go).
- Model refresh (no issue): Bedrock listing on 3 accounts (`docs/audits/2026-10-21-S246-bedrock-models/`), Infra #261 invoker IAM (applied on acc3 and acc1), CIS #902 + CIS 259 (Haiku 5.5, Sonnet 5.5 in the catalog; stale acc2 Sonnet 4.5 profile dropped; applied 15:41 UTC), gateway fix CIS #903 (merged 15:50 UTC, deploy running at close). Smoke: Haiku 5.5 / Sonnet 5.5 OK on acc3, not available on acc1.
- Tracker cleanup: **AA-848** (20/10), **AA-889** and **AA-890** (19/10) were already Done in Linear; removed from the queue.
- New in S246: **AA-928…AA-980** (53 CRM issues: W0–W8, Lane B AA-972…AA-977, Lane P AA-978/AA-979).
- Plan: the S246 master plan ([plan-and-status.json](../audits/2026-10-21-S246-master-plan/plan-and-status.json)) replaces the S244 slots; tracker `index.html` now shows S247…S262 and the new milestones.

## 5a. Closed in S245

Evidence per issue: `docs/linear-export/` (closed issues exported, then archived) and the S245 session log.

- **Quality / content:** **AA-800** (tenant signature words, CIS #875), **AA-865** (r8: 0/28 errors from retries, pooled F9 6.2%), **AA-787** (T10 gates 31 → 26, CIS #878; F15 / lexicon merges moved to AA-924), **AA-914** (route guard: no Segments from another country, CIS #879).
- **Security / platform:** **AA-912** (CodeQL CIS 31 → 0: 13 regexes rewritten linear with fuzz + time-bound tests, shared citation tags, 5 stack-trace leaks closed; CIS #885, deploy da07b7db), **AA-913** (alert recipients managed on an admin page, mig 251, CIS #872–#874, Infra #237), **AA-875** (`safe_http`, CIS #880; blocked case 422 + log, positive case on terra-family connect → publish → trash → disconnect), **AA-846** (Terraform apply guard, exact pin, hidden drift, apply-role narrowing), **AA-878** (secrets register drift diff = 0, first access review), **AA-907** (pip-audit ignores gone: langchain / langgraph bumped, chromadb dropped), **AA-895** (security baseline + vulnerability policy), **AA-860** (X1 close-out).
- **Docs / CI:** **AA-888** (docs lint in every repo), **AA-887** (documentation standard, front-matter on the 4 CONTEXT.md), **AA-893** (generated alarm catalog + Terraform outputs, Infra #244), **AA-826** (new-app playbook + contract hash guard, Infra #241), **AA-849** (TripPlanner migration replay; Nghiệp turned on the required check).
- **Apps:** **AA-805** (TripPlanner AI Phase 0, the 4 reopened checks pass live), **AA-680** (staff half: WORKFORCE user with no `booking-*` group refused live; bridge retirement → AA-911).
- Shipped, still In Progress: **AA-729** (golden fixture 1.1.0, 100/100 labelled; baseline `docs/audits/2026-10-20-S245-aa729-baseline/`: S1 missed 26/44 bad pieces, T9 held 12 good ones, judge/gate vs label disagreement 43.6%), **AA-779** (#877, #882; rule loop stopped per D10), **AA-780** (120-word floor, #881), **AA-845**, **AA-821** (CRM v2–v2.2, Tern / TravelJoy teardown from public sources, 16 recommendations).
- New in S245: **AA-911** (Preview staff sign-in, bridge retirement), **AA-912–AA-914**, **AA-915–AA-923** (Writing Memory v1), **AA-924** (from AA-787), **AA-925** (Q-2), **AA-926** (Q-1), **AA-927** (LLM calls without a log row).
- Tools: `tools/linear/linear_export.py` exports closed issues to `docs/linear-export/` and archives them through the API (Linear Free plan, no upgrade); secret `aa-ecosys/ops/linear-api-key`.

## 5b. Closed in S244

- **AA-904 Done** (TP Next 15.5.28 / React 19, TP #107; preview smoke 4 flows desktop + 390 px, prod verified, `npm audit --omit=dev` 0).
- **AA-902** Done on the S244 root PR merge (0 real account IDs on main of the 3 public repos; CI probe PRs CIS #857 / Booking #47 / TP #108 red as intended; baseline row in place).
- **X1 S20–S22** shipped (see §3 row 2); **AA-816 S1, C9, I6** shipped (see §3 row 3).
- Bhutan 33 vs 32 fixed: funnel stages count only active raw tours (CIS #852; live 32/32/32/32).
- Chore: Terraform `use_lockfile` + CI Terraform 1.15.5 (Infra #218).
- TP #109 (pytest 9 + pytest-asyncio 1.4.0) merged.
- Reopened as false Done (S244 audit, verified): AA-825, AA-805, AA-665, AA-669. New: AA-906 (TP Next 16).
- Audit proposals approved by Nghiệp and applied in Linear: **AA-852 Done** (X1 S1–S22 evidence; 179/180 revoke moved to AA-847), **AA-675 / AA-689 Canceled** (superseded), new **AA-907** (pip-audit expiry, High), **AA-908** (AA-680 customer half), **AA-909** (TP guest-token check on GETs), **AA-910** (Booking 1440 UI + audit rows); priority up AA-901 / AA-875 / AA-876; In Progress moves per the audit.
- N-F: `e2e-claude-code-2` disabled on the Staff page (Nghiệp, verified S244). Root #117 merged (data standards v1.2, XD3 exception row).
- Jira PR-14: same-day comment 10485 extended with the S244 cutover bullets + login screenshot (Nghiệp approved).
- Master plan HTML tracker: `docs/backlog/tracker/` (artifact <https://claude.ai/artifact/2VSP2stGG1TF7uXvqgQTUY>).

## 5c. Closed in S243

- **AA-885 Done** (tenant portal on its own Vercel project `aa-cis-portal`, `portal.lumiguides.it.com`; CIS #832, Infra #197; prod smoke 24/24).
- **AA-892 Done** (ops runbooks/playbooks in root #105; every runbook either active with `last_tested` evidence or draft with the UNTESTED banner; alarm links Infra #213).
- **AA-858 Done** (CIS #839/#840/#848/#850/#851, Booking #37, TP #98, Infra #205/#206/#214): live 19/10, 71/71 number source tooltips, screenshots 1440/390; Ms. Thư's confirmation dropped by Nghiệp.
- **AA-884 Done** (CIS #835–#838/#844/#848, Infra #208/#209): Apps SHA 411e5f18 = api:703/worker:260 images; audit UPDATE/DELETE → 42501 as cis_app (rolled back); cost per day = Cost Explorer by App tag for 01–17/10 (18/10 gap = snapshot before AWS finished posting).
- **AA-897 Done** (root #105 + #108): fresh-agent onboarding walkthrough to a lint-clean PR; 2 guide gaps fixed.
- **Infra #217:** denied secret reads have their own alert ("Denied secret access", rule `aa-identity-dev-denied-secret-read`); the break-glass alert now fires only for calls that name the break-glass secret (tested live 09:39Z: new rule 1, break-glass 0).
- Shipped, still In Progress: **AA-680** staff half (Booking #34/#35/#36, Infra #199), **AA-878** (root #101, CIS #841, Infra #195/#207, TP #99, 4 orphan secrets deleted).
- **AA-816:** Cognito E2E (CIS #842, Infra #198) + temporary E2E staff exception (CIS #849 mig 250, Infra #215/#216, root #106 ADR 0006a A10); break-glass OTP probe (Infra #196); daily reconcile trigger (Infra #195). Cutover still open.
- **AA-860 / AA-852:** X1 S15–S19 (CIS #833/#834/#843/#845, Infra #200/#201/#202/#203/#204/#214, root #99/#100).
- Chore row closed: stale Terraform `import` blocks removed (Infra #195), `middleware.ts` → `proxy.ts` (CIS #831); `use_lockfile` stays as row 10.
- Docs: unified engineering handbook, role guides (bilingual), runbooks, data standards v1.1 (root #105); schema reference regenerated (root #102/#103/#104). PR templates + title checks in all repos; Dependabot config in Booking (#43) and TripPlanner (#101); Dependabot PRs merged: Booking #38/#40/#44, TP #102 (open: Booking #39 superseded by #40, TP #104 → §3 row 5).
- Jira: Epic PR-20 + Story PR-21 (platform report period 1) posted. Google Safe Browsing review of lumiguides.it.com passed (19/10): the §1 check is removed.
- New Linear issues (Nghiệp approved S243): **AA-902** public-repo account ID/ARN scrub (High), **AA-903** skip Vercel deploy for Dependabot, **AA-904** TripPlanner Next 15, **AA-905** geo backfill (paid, quote first). CIS logout → Cognito `/logout` stays a scope line of AA-816; Bhutan 33 vs 32 stays §3 row 13.

## 5d. Closed in S242

- **AA-854 Done** (Cognito Phase 0: break-glass, email-code spike, no-group deny, self sign-up rejected; evidence `docs/audits/2026-10-18-S242-cognito-phase1/`).
- **AA-816** shipped (In Progress until cutover): Infra #183/#184/#185/#191/#194, CIS #807/#808/#809/#810/#811/#812/#813/#826/#827/#828/#829, mig 247.
- **AA-852** X1 S9–S14 shipped (Booking #33, TP #97, root #95, Infra #179/#180/#182/#187/#188/#189/#190).
- Dependabot cleared in all repos (CIS #814/#819/#820/#830, Infra #192/#193 — AWS provider 6.69.1); CIS `dependabot.yml` groups security updates.
- AA-869 confirmed Done (S241). New issue: none.

## 5e. Closed in S241

- Done with live evidence: **AA-883** (console 2 sections + Staff), **AA-882** (server-side staff authz), **AA-836**, **AA-863**, **AA-834**,
  **AA-866** (main-only OIDC trust), **AA-867** (GitHub security, org 2FA, AA-ACP-App deleted), **AA-868** (CI hardening),
  **AA-870** (Sentry backend, API GW alarms, uptime CIS), **AA-872** (OK e-mails, retention).
- Done on merge of the S241 root PR: **AA-751** (X6 second wave; R1 docs in that PR), **AA-869** (runbook + incident page).
- In Progress with shipped waves: **AA-852** (X1 S1–S8), **AA-854** (Cognito Phase 0), **AA-859**.
- Also shipped without an issue: Vercel admin pollers, CI-created Vercel deploys (3 repos), admin secret rotation (5 places),
  admin GET authz hotfix + route-auth CI guard, tenant pool fail-closed (D-12), ECS Exec session logging + RDS connection logs (D-07/D-08),
  restore drill (D-10, comment on AA-829), root repo private (D-14).
- New in S241: AA-866…AA-886 (25 issues from the SDLC review + admin console advice); AA-729 rewritten.

## 6. Environment notes for the next session

- CIS API + worker on **dev-7a4b0759** (CIS #902), task defs api **:743** / worker **:300** at the S246 close; CIS #903 (31341906) merged 15:50 UTC 21/10 with Deploy Dev running — verify it first in S247. CIS migrations on Dev: **253, 255, 256, 257, 258, 259** applied S246 (254 not used); Booking API **dcb9936** on task def **:35**, **bk-018**; TripPlanner main **6675519** (TP #121), **tp-016** and **tp-017** applied; Infra main 3e81ce1; roles **rl-002**. `PLACES_SOURCE` still legacy, `PLACE_SHAPES_ENABLED` off.
- **LLM models:** Haiku 5.5 and Sonnet 5.5 are in `shared.llm_model_catalog` (CIS 259) and callable on acc3 only (acc1 reports the models not available for the account). The place pipeline stays on Sonnet until a trial passes the 95% bar. Terraform: **1.15.5** pinned exactly, S3 `use_lockfile` only (DynamoDB lock table removed S245, AA-846); AWS provider 6.69.1.
- **DB access after X1 S22:** CIS objects are owned by `cis_owner` (NOLOGIN); runtime `cis_app`; DB Migrate, Schema Dump and the probe log in as `db_migrator` (limit 5) and switch to the live owner (`cis_owner` / `bk_owner` / `tp_owner`); the master `aa-cis/dev/rds` is read only inside the migrator task for `roles/`, `set-password` and `run-script`. ECS exec scripts still use the container `DATABASE_URL` (`cis_app`). Catalog views: the S22 recipe (`GRANT CREATE ON SCHEMA catalog TO catalog_owner; SET LOCAL ROLE catalog_owner; …; SET LOCAL ROLE cis_owner; REVOKE …`, never `RESET ROLE`).
- **Identity:** staff sign-in = <https://staff-auth.lumiguides.it.com> for CIS and Booking. **Production CIS has no password login any more** (Vercel `LEGACY_ADMIN_LOGIN_ENABLED=false`, S244 S1); Preview keeps it, but Preview's `ADMIN_SECRET` is the viewer-capped `aa-cis/dev/admin-secret-preview` (C9), and GitHub `E2E_ADMIN_*` is the viewer account, so preview smoke runs in viewer mode. The API legacy flag stays on until S2. Break-glass `admin@adventure.asia` disabled, password + TOTP rotated S244 (secret `aa-identity/dev/breakglass`). Main `aa-cis/dev/admin-secret` rotated S244 (copies: GitHub CIS env dev, Vercel Production). Agents verifying admin UI on production must use a Cognito session (no `e2e-claude-code` password login there).
- **Preview sign-in (AA-911, S246):** fixed Preview hosts with Preview-only Cognito clients (Infra #260); Booking Preview signs staff in through a read-only client (Booking #54); the `preview-signin` branch exists (= main) and is locked by a ruleset. The CIS → Booking bridge is still on until the end of the project.
- **Portal:** tenant portal = Vercel project `aa-cis-portal` on <https://portal.lumiguides.it.com>; admin stays on aa-cis.lumiguides.it.com. The code still lives in `apps/AA-CIS-App/portal/` (no repo split yet); the move is CRM Lane P (AA-979: P2a S255, P2b S258).
- **Edge (S246):** API Gateway stage throttles 50/100 by default, 20/40 on login, 300/600 on content (AA-876, Infra #247–#249), WAF off on purpose; photos CDN `img.lumiguides.it.com` (CloudFront + OAC on the private bronze bucket, AA-844).
- **Network (X1 S11–S14):** one SG per caller; RDS admits tp-lambda, booking-api, cis-api, cis-worker, db-migrate; Redis/EFS only cis-api + cis-worker. DB Migrate / Schema Dump / probe run on a temporary `aa-cis-dev-db-migrate` revision (still the master login until S22); modes `set-password:<role>` and `run-script:db/scripts/*.py`.
- **X1:** Booking/TripPlanner objects owned by `bk_owner` / `tp_owner` (NOLOGIN). DB Migrate reads the LIVE owner of `anchor_schema` and runs each file as that role (`owners.yaml`). Probe workflow `db-isolation-probe.yml` (schedule + after each apply). The `migration` input carries the owner prefix (`cis/250_x.sql`).
- **OIDC:** `aa-cis-dev-app-deploy` and `aa-cis-infra-tf-apply` trust only `ref = refs/heads/main`. CIS env `dev` allows only `main`; `ADMIN_SECRET` is an env secret. Bootstrap roles/policies are applied by hand with the MFA admin profile.
- **ECR CIS IMMUTABLE**, lifecycle 30 `dev-*` + untagged 7 d; Deploy Dev reuses an existing `dev-<sha>`. Rollback runbook: `skill/aa-ship` §5.
- **Alarms** e-mail on ALARM and OK (D-20), each with a runbook link (Infra #213). Cost anomaly subscription (IMMEDIATE, ≥ $5) to the alerts topic. New S243: `cis_app` connection-limit alarm (SQLSTATE 53300), AdminCreateUser-with-password alarm.
- **Sentry:** CIS backend → project `aa-cis-api` (secret `aa-cis/dev/sentry-dsn-api`), frontend → `aa-cis-frontend`; uptime monitor for CIS `/health` (free plan: 1 monitor).
- **Vercel:** Git integration off; `vercel-deploy.yml` creates deploys only when `frontend/**` changes (`VERCEL_TOKEN` per repo; Dependabot runs have no token, so that job is red on Dependabot PRs).
- **GitHub:** rulesets "no force-push / no deletion" on the 3 public repos; Dependabot in all repos (grouped security updates, actions weekly); PR template + title check + ADR index in all repos; CodeQL default setup.
- Tenant pool flags fail closed: unreadable flag = tenant pool; explicit `"false"` = admin pool (`TENANT_POOL_FORCE_ADMIN_FLAGS` env for an emergency).
