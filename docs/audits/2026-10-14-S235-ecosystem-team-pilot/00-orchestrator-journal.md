# S235 journal (orchestrator = Claude Code main session, Ultracode)
## Gate 0 (14/10) — OK, matches S234
- STS acc2 OK; 4 repos main clean; api :568 / worker :123 dev-20a2387 COMPLETED; RDS available; /health 200
- shared.job: 0 queued/running; 24h 139 succeeded
- Drift: AA-792/AA-797 already In Progress in Linear (no code yet); AA-797 plan_id backfill done S234
## Gate 1 — Nghiệp: "duyệt, bắt đầu làm" + Ultracode on (14/10)
## Gate 0.5 — architect + lane planning workflow: running
## Gate 0.5 done (9 agents) — synthesis: .tmp-session/team/S235/synthesis.json
- Fixed R6: MCP write guardrail hook (.claude/hooks/subagent-mcp-guardrails.sh) + Bash patterns (ecs exec, iam, gh api -f…) — verified live (subagent blocked on aws iam)
## Gate 1 answers (Nghiệp, 14/10)
- Infra batch: approve all 4 (OIDC trust narrowing, BookingRoleTagging + ALB output, mig 223 copy, booking.tf desired 0). Nghiệp merges + applies.
- Booking: minimal health slice (repo + CI + bk-001 first slice + /booking/health).
- Tenant data: remove quality fields from tenant pool AND llm_cost_usd/jev_cost_usd from /v1/billing (reverses AA-636).
- T2 judge: Nghiệp chose B — keep mission as a gate, sourced from tenant_brand_rules.core_idea (tenant mission), not AA mission. Batch-1 A-T2 coded default A → switch to B in a follow-up on feat/aa-792.
## Batch 1 workflow wf_1101e0c6-aec running (A-T2, A-T9, B, D)
## Batch 2a workflow wf_f2b57d7a-59f running (Infra-1 trust, Infra-2 booking.tf, Booking scaffold local, mig 223) — Nghiệp re-enabled via 'ultracode'
## Batch 1 done — all 4 lanes approved round 1 (batch1.json)
- PRs: CIS #699 AA-794 (auto-merge on, CI running) · #700 AA-776 · #701 AA-785 · #702 AA-797 (+rbac admin-only commit bb375a5) · root #58 ADR 0004 · root #59 guardrail hook
- Root #59 merge DENIED by auto-mode classifier → Nghiệp merges #58/#59 by hand; new hooks restored into the root working tree (uncommitted) meanwhile
- AA-794 A1 sizing: 892 active masters, ~82 heuristic cut endings (notes commit 67aaec7)
- AA-792 follow-up agent running: gate B (tenant core_idea mission) + tenant-voiced flag_fix
- Train order: 699 → 700 → 701 → 702 → (796) → 792 → W1 T2 rerun
- Open for Nghiệp: AA-797 offboard terminal (Done-when said restore); AA-785 '1600s' as century + '1637–38' start+1 rule; AA core forbidden list binds tenant voice ('luxury' vs Atlas & Hearth)
## Batch 2a done — all approved (batch2a.json)
- Infra #95 (OIDC trust pinned to immutable org/repo ids + Booking IAM prep + ALB http_listener_arn + 223 copy sha ca0faefe) — Nghiệp merges + applies
- Infra #96 (booking.tf desired 0 + bk-001 copy, stacked on #95) — after #95 applied; needs booking_github_repo_id after repo exists
- CIS #703 AA-798 mig 223 (draft): DB Migrate apply ONLY after /v1/billing drop (AA-796) is live
- AA-Booking local repo .tmp-session/wt/aa-booking (4 commits, 70 tests) — create remote after #95 applied
- ADR 0004 #58 amended: role booking USAGE only
- AA-796 implementer running (projection + pool quality removal + billing cost drop)
- #699 AA-794 merged 666dfef, deployed api :569 / worker :124 same SHA, health 200 (live verify = W1 rerun). Root #58/#59 merged (Nghiệp turned auto mode off).
- AA-796 PR #705 opened (3470 tests). SECURITY found by lane B: v1_pipeline /run has NO auth (Excel upload → rewrite ≤20 tours, LLM cost); review-queue GET/approve/reject accept ANY tenant JWT (role unchecked) → tenant can approve AA master to export. Verified in code (v1_pipeline.py:243, :337-351, :433). Issue pending Nghiệp approval.
## Nghiệp "Duyệt hết" (14/10): AA-797 restore (done, #702 updated b10bb92), created AA-799 (Urgent security /v1/pipeline, agent coding) + AA-800 (tenant signature vocabulary, after T2 rerun), AA-785 merge as is (comment posted)
- Train order now: 700 (running) → 701 → AA-799 → 702 → 705 → 704 → W1
- train.sh fixed: gh has no update-branch → gh api PUT .../update-branch
- #700 AA-776 merged 5012da4, deployed api/worker :125 same SHA, health 200
- AA-799 PR #706 opened (37 guard cases, 3496 tests)
- Infra #95 merged 6552b16 (Nghiệp approved) → Terraform Apply Prod 38492281140: 1 added, 5 changed, 1 destroyed (same as reviewed plan). Live trust = 2 pinned subs. DB Migrate check (Infra env:prod) OK after narrowing.
- Infra #96 rebased on main (8bf9c30, a2f14c6), base → main; bk-001 copy sha 6fc29b37 == Booking source. Plan running.
- Train: #701 AA-785 running
- Infra #96 merged fd48d5c → apply: 24 added / 0 changed (Booking: REST API 9z3xnalp59, ECR aa-booking-dev-api, ECS service desired 0, 3 roles, listener rule, TG, empty secret)
- AA-Booking repo created (private, id 1418188499, immutable OIDC sub); CI 5/5 green first run; Deploy Dev skipped (no vars). Branch protection 403 on private Free → ask Nghiệp (public?)
- bk-001: precheck (current_user aa_cis_admin, CREATEROLE) → DB Migrate apply 00:59:38Z → bk-001 registered, role booking NOLOGIN, 6 tables + v_schema_versions, USAGE only
- #701 AA-785 merged a60db7b, api :571 / worker :126 (also proves CIS deploy under narrowed trust); live replay --db: F1 10→0, added 0, other 0 → AA-785 DONE
- Jira: 3 drafts (PR-12 comment, 2 new PR issues) awaiting Nghiệp
- Train: #706 AA-799 running
- #706 AA-799 merged a41d2e7, api :572 / worker :127; in-container: no-auth 401, tenant JWT 403 on all 5 routes; edge returns 404 (not routed) → AA-799 DONE. Train: #702 running
- #702 AA-797 merged 5fe9595, api :573 / worker :128; live lifecycle on throwaway tenant ace1f389 (ends offboarded) all OK; DB plan_id correct, 0 NULL → AA-797 DONE (UI verify of /admin/tenants pending, batch with #705 portal). Train: #705 running
- #705 AA-796 merged 8b74b7a, api :574 / worker :129; live key-walk 8 tenant routes WildKind: 0 bad keys, 0 needs_review → API verified; UI verify agent running (admin tenants + portal). AA-798 app-half agent running. Train: #704 AA-792 running → then mig 223 apply → W1
- UI verify: /admin/tenants PASS; portal PASS on AA-796 points; pre-existing 422 (page_size=200) + mobile cards → fixed in #707 (Refs AA-796, AA-797). AA-798 app half rebased + force-pushed (#703, mig bytes unchanged ca0faefe). #704 AA-792 merged 3cd6fed, deploying.
- #704 AA-792 deployed 3cd6fed (worker :130). Mig 223: check OK, shared.job empty, apply 01:54:55Z → view llm_cost_usd == direct llm_call_log MTD sum for all 9 tenants (Atlas 6.7419, Terra 6.7924, Trail 1.6048, WildKind 1.9150). Train: #707 running → #703 manual merge → W1
- #707 merged ee7d9f1 deployed; #703 AA-798 merged 6699cc1 (api :577 / worker :132), live billing == SQL for 4 tenants, unknown 404 → AA-798 DONE; AA-796 DONE (UI verified + #707). W1 T2 rerun START (merges frozen) wave 1 pilot
- W1 wave 1 pilot (4 Bhutan, $1.083, $0.271/version): last-judge brand_fit Atlas 7 / Terra 7 / Trail 7 / WildKind 5 (Trail +1.67 claimable); meta 0 cut / 0 wrong country / 1 short (133); mission_present FALSE on 27/27 judge calls → all capped at 6. brand_fit repeat noise 4–8 on same draft.
- Root cause: judge asks mission "in each day's framing"; writer never told to use core idea as day lens + brand block says "at most one sentence about the brand". Fix agent running (fix/aa-792-mission-lens). Plan: merge → re-pilot 4 (~$1.1) → wave 2 (8, ~$2.2) → total ≈ $4.4 ≤ 4.50; wave 3 (A/A') replaced by re-pilot repeats.
- #708 mission-lens merged f66697c, worker :133; W1 wave 4 (re-pilot Bhutan x4) START
- Booking LIVE: role booking LOGIN (SCRAM verifier via ECS exec; plaintext only in Secrets Manager booking/dev/database-url; script removed from S3+local), Infra #97 applied (deploy trust pinned to repo id 1418188499, env:dev + main), AA-Booking public + branch protection + env dev (main only) + 5 vars, first Deploy Dev OK, service scaled to 1 (Nghiệp approved): /booking/health 200 (sha 0d90235), /booking/health/ready 200 db ok bk-001. CIS /health 200.
- Re-pilot wave 4 (after #708): mission 0/27 → 6/21; last judge Atlas 7, Terra 8, Trail 6, WildKind 5; $0.195/version; cumulative $1.867. Judge brand_fit noise 4–8. Wave 2 START.
- W1 CLOSED: wave 2 ran 5/8 (3 skipped by cost guard); total rerun 13 versions $3.492 ($0.269/v vs S234 $0.372). After #708 (9 versions): judge≥7 6/9, mission 19/50, mean bf same pairs 6.22→7.0; Terra 8/8/8, Atlas 7/6/8, Trail 6/7, WildKind 5. AA-794 DONE (0 cut, 0 wrong country /13). AA-792 stays In Progress (Trail 6.5, WildKind 5; judge noise 4–8; voice read pending). Summary: .tmp-session/team/S235/t2_rerun_summary.txt
- Lane A-T9 started: AA-786 agent running
- Created AA-801 (T2 judge stability). Jira drafts parked until end of session (Nghiệp).
- ADR 0004 decisions (Nghiệp 14/10): O3 = own booking.job table (same runner library); O1 = Booking staff use CIS staff login (shared.admin_users, thin booking profile); O8 = TripPlanner is the customer front door (Booking customer app = sign-in, My Trips, payments). O6 → advised market pattern (guest must give name+email, lead trip case, merge on OTP) — awaiting answer.
- Ecosystem design advisory requested: 3 read-only lens agents running (TripPlanner/journey, data/events, infra/ops) + reuse Gate 0.5
- O6 (Nghiệp 14/10): APPROVED market pattern — guest hand-off must carry name + email (phone optional) + consent, no registration; contract inquiry.submitted.v1.1 (customer always present, registered flag); Booking creates trip case at once with a lead customer (unverified email), merges on OTP sign-in; contact-less legacy hand-offs parked in inbox_events. Slice 'Inquiry intake' to be planned after the ecosystem advisory.
- Ecosystem blueprint published: https://claude.ai/artifact/Hz5bn9ryLDToqiNU7vrHpt (source .tmp-session/team/S235/advisory/). AA-786 PR #709 opened, reviewer running.
- AA-786 review: changes_needed — B1 blog body false claim demoted to meta warn (real regression); policy P1 keep F9 blocking (held = admin label per AA-770) unless every flagged truth sentence was cut + sentences_left; P2 cut only on last attempt; N1–N3. Sent back to implementer.
- AA-786 re-review APPROVE (2b53229f, 3670 tests). Non-blocking: tag-before-punctuation counting (fix before AA-777), stale flags after cut (cosmetic). Train #709.
- Nghiệp (14/10): APPROVE whole blueprint incl. Phase 0. No prod now; future prod on acc2 (no new account). O2: dev hostnames = sub-domains of lumiguides.it.com (like aa-cis); FE reviews on Vercel domains. O9 = bk_*. O7: all customer-facing content in CIS. Global ~/.claude/CLAUDE.md updated (AAA accounts removed; backup .tmp-session/team/S235/CLAUDE.md.global.bak).
- Redis: explained; recommend keep until prod (awaiting objection). Pricing advice given (data in booking schema, entry UI in shared admin; cost sheet × pax bands × season; margin rules; Excel versioned upload) — awaiting 4 answers (currency, margins, who enters, B2B resale).
