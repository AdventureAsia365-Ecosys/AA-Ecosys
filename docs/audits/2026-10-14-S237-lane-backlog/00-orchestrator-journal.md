# S237 journal (orchestrator = Claude Code main session, Ultracode)

## Gate 0 (14/10) — matches S236
- STS acc2 OK; api :596 / worker :152 dev-44443ec COMPLETED; Booking :6; RDS available; /health 200
- shared.job: 0 queued/running. Lambda quota 1000 still CASE_OPENED. No T2 job since worker :152.

## Gate 0.5 — lane planning workflow wf_474768f3-774 (11 agents) → lanes.json

## Gate 1 — Nghiệp: "duyệt toàn bộ", full authority to run every lane to the end, then a detailed report
Decisions locked (all recommendations of the cross-lane review):
- D1 CIS migration numbers: 228 AA-712 catalog place/graph views · 229 AA-817 RLS · 230 AA-819 publish limit · 231 AA-791 label · 232 reserved (AA-679, now unused). Fix stale "227" in ADR 0007 / design 03 / schema-ownership in the 228 root PR.
- D2 229 = ENABLE ROW LEVEL SECURITY without FORCE (owner exempt, aa_app_user isolated; pattern 115/116/145). AA-817 step 1 proves the aa_cis_admin BYPASSRLS question first.
- D3 AA-819: cis-backend owns T9 guard + limit + 230; portal owns notice UI + Tenant 360 field. Nullable override, code default 20/day, UTC day, replays + 409 retries excluded, code tolerant of a missing column.
- D4 AA-679: Booking live-reads catalog views + commercial-only trip_plans row; reword Done-when; no CIS outbox this session (232 unused).
- D5 SES: identity per ADR 0006 item 5 (apex lumiguides.it.com, no-reply@), MAIL FROM sub-domain; hostnames per ADR 0006 / AA-818. DNS → Route 53 hosted zone (S236 decision), Nghiệp switches NS at Namecheap after record parity check.
- D6 AA-712: trial country Laos (11 tours in the frozen 56-set), 3 tours from the 56-set; batch (b) gated on TripPlanner slice 6a deployed.
- D7 228 = views only, no top-k function; TripPlanner keeps MIN(<=>) on the cis path until the catalog-wide run.
- D8 Migration flow: migration-file-only PR to owner main → Infra byte copy → DB Migrate check → apply → code PR that depends on it.
- D9 Linear: create Booking wave 2a / 2b issues (approved); steering 50 → 100 per project (skill wins).
- Paid windows approved: AA-712 trial + batch (≤50), AA-801 2–3 T2 jobs, AA-819/668 test writes, AA-793 rerun 3 then 14 pairs (≈ $6–9 total).

## Execution
- Batch 1 build workflow wf_8786f29a-119 (14 slices, build + adversarial review) running.
- Paid window 1: AA-712 trial enqueued (Laos, 3 tours of the 56-set, created_by backfill:admin:s237-trial): fde65bf0 Mekong Valley 10D (TP 72 comps, job 0ad5020d), 2bc45c55 North to South 16D (47, ec2c2e30), 16548cba Village Cycling 5D (9, e3d995d6). Note: TP source_tour_id is keyed by source_id for some tours and raw tour_id for others — parity must match both.
- AA-801: driver .tmp-session/s237/t2 (3 runs: trail-pulse Bhutan, wildkind Bhutan, trail-pulse Mongolia; hard stop $1.20) running.
- Linear: created AA-822 (wave 2a suppliers, bk-008), AA-823 (wave 2b hotels/services, bk-010); AA-679 comment = D4.
- AA-801 evidence: Trail Pulse 7.0 ($0.043), WildKind 7.0 ($0.092, 2 attempts) on Bhutan; judge rows gate=brand_fit, judge_anchors=true, mission_gated=false; judge = gpt-5.6-luna. Comments on AA-801 + AA-792. 3rd run skipped by cost-guard reserve (fine).
- AA-712 trial (a) PASS: $0.024/tour, overnights 12/13 + 2/2 same, geocode ≤25 km 36/37 (only TP 'Night Market' merge 219 km). 22 pending names (some real) → follow-up: second geocoder pass / admin fix. Report docs/audits/.../aa712-trial/. shared.job empty again 15:46Z → merge window open.
- Batch 2a build workflow wf_d4e0bfd4-d52 (AA-793, AA-668, AA-791, AA-802, AA-822) running.

## Interruption (15/10) — Claude Code process restarted; both build workflows stopped mid-run
- Batch 1 finished (build + review approved): inf-807, inf-806, portal-819, tp-6a, tp-805 (partial evidence), bk-close. Built, review not run: inf-703, inf-811, cis-817-probe. Unfinished (uncommitted work in worktree): cis-228, cis-819, portal-815, tp-812, bk-810 (1 commit + dirty).
- Batch 2a: no completed agent; partial worktrees cis-793, portal-668, portal-791, portal-802, bk-822.
- Nothing pushed, merged, applied or deployed. Live state unchanged (api :596 / worker :152).
- Root cause of the restarts: WSL 7.6 GB RAM, OOM killer (dmesg) — 14 parallel agents + VS Code/Kiro/Amazon Q. Lesson added (aa-lessons Vận hành). Remaining 13 slices relaunched as chunked workflow wf_8c2b7c0c-4ec (CHUNK=3, review-only for inf-703/inf-811/cis-817-probe).
- PRs: Infra #110 (AA-807), TP #75 (6a), TP #76 (AA-805 evidence), Booking #6 (AA-683 close-out, MERGED), CIS #727 (AA-819 portal, MERGED b3acd09, Deploy Dev 38655041923 running). Merges of #110/#75/#76 blocked: auto mode came back after the restart (classifier "Merge Without Review").
- #727 deployed: api :597 / worker :153 both dev-b3acd09, COMPLETED, /health 200. UI verify of the notice deferred until the AA-819 backend PR lands (one UI pass for both).
- Merged (auto mode off): Infra #110 AA-807 (4cb8942), TP #75 slice 6a (c06aaa8), TP #76 AA-805 evidence (00f4bb1). Linear comments AA-807, AA-683.
- TP 6a live: Deploy Lambdas success; assembly extraction op tour_days → 410 'unknown extraction op' (moved_to CIS); orphans OK (892 active, 0 orphans); browse search 200 (60 dest), routes Laos 10d 200 (5 proposals). → AA-712 batch (b) gate met.
- AA-712 batch (b): Laos rest, 43 tours, est $1.32, batch ec3a48be enqueued (place_extract cap 1). CIS merges must wait until these drain.
- Booking AA-681 demo agent running (bk_demo.md).
- AA-712 batch (b) DONE 00:08Z: 43/43 ok, Laos 46/46 builds ok, LLM $0.755, Geoapify 375 req $0; place_name pending 142/573 (follow-up). shared.job empty → CIS merge window open.
- Migration train (D8): CIS #728 (228 views) merged → Infra #111 copy (228 + bk-007; guard caught an empty-file copy first, then 25/25 ok) merged → DB Migrate check+apply 228 at 00:25:32Z → live: as tripplanner/booking v_tour_component 776, v_tour_stop 376, v_tour_leg 1796, v_graph_node 127, v_graph_edge 192, v_tour_junction 2796, v_tour 892, embedding column present; v_tour_place full count 3.3 s (note).
- Booking #8 (bk-007 migration-only) merged 77eb750 → DB Migrate check+apply bk-007 00:29:57Z → /booking/health/ready schema_version bk-007. Booking #7 (AA-810 code) rebased on main, ready.
- Root #71 docs (228 renumber + catalog.graph.v1 / catalog.tour.v1.1 contracts) merged.
- CIS #730 (AA-819 code): UI smoke AA-752 rail-collapse flake on first run, rerun green. Train for #729 (230) running after #728 deploy.

## Gate 2 — data architecture review (wf_e7e58903-801) → Nghiệp "đồng ý duyệt hết" + asks for standards + artifact (15/10)
- E1 ADR 0008 = new-app integration + data platform rules; ADR 0009 = AI platform (AA-804); ADR 0003 amendment (per-owner job tables; AA-751 premise superseded).
- E2 Role split: booking.* → bk_owner, tripplanner.* → tp_owner + separate db_migrator task def now; CIS runtime behind AA-817 D2.
- E3 Retention: llm_call_log raw 180 d + daily rollup; tenant_api_usage 90 d + monthly rollup; jobs succeeded 30 d / failed 90 d; outbox/inbox payload PII redacted after 90 d; archive to S3 Parquet before delete.
- E4 Tenant contract views live in `catalog` (no new contract schema).
- E5 Spend: Dev t3.micro → t4g.small + Performance Insights; RDS Proxy only at trigger; per-app cost allocation tags (Nghiệp activates in Billing).
- E6 N3 connection limits + Lambda reserved concurrency ship BEFORE the Lambda quota 1000 is applied.
- E7 inquiry.submitted v1.2 additive (source_system + source_id per leg).
- E8 booking.customers = single customer master; TripPlanner keeps subject + consent after ADR 0006 Phase 4.
- E9 CRM AA-821: research first (build vs HubSpot/Zoho); if built, CIS module with own `crm` schema + `crm-` key space.
- E10 Hygiene: real-data dumps docs/backups/2026-09-16 → encrypted private S3 then removed locally; repos stay public (no secrets in schema/RLS); fix AA-807 description.
- E11 Create Linear issues for N3, N4, X7, X8, X9, X10.
- Standards workflow wf_7f34466b-0c8 running → docs/architecture/data-standards/ + ADR 0008 + 0003 amendment.
- 230 applied 00:37:26Z; #730 AA-819 code deployed api :600 / worker :156 (dev-69c12be); Booking #7 AA-810 deployed :8 (bk-007).
- Infra #113 AA-811 merged → targeted LOCAL apply (CI full-root plan carries hidden-attribute drift on secrets/RDS/random_password; never CI-apply the whole root): 31 added, 1 changed (tf_apply bootstrap sids present). Route 53 zone NS: ns-1284.awsdns-32.org, ns-1671.awsdns-16.co.uk, ns-178.awsdns-22.com, ns-764.awsdns-31.net. SES DKIM/MAIL FROM PENDING until Nghiệp switches NS at Namecheap.
- Infra #114 AA-806 step 4 merged → targeted local apply 13 roles permissions_boundary (aa-workload-boundary: Allow * minus IAM writes/org). Smoke: CIS /health 200, Booking ready bk-007, TP search 200.
- AA-817 probe run + Linear matrix comment. Data architecture review (wf_e7e58903-801) + decisions E1–E11; Linear project "Data Platform — Schema, Ops & Scale" + AA-824…AA-829; AA-807 correction comment.
- Settings: allow gh workflow run / terraform apply (Nghiệp approved). Auto mode re-enables itself after a restart → classifier blocks; compound commands don't match allow prefixes → run merges as single commands.
- CIS train (AA-815 → AA-802 → AA-793) running; standards workflow wf_7f34466b-0c8 running.
- 15/10 ~01:40Z AWS approved Lambda concurrency 1000 (case 179197638600671) BEFORE AA-824 shipped → interim cap: put-function-concurrency 5 on aa-tripplanner-dev-browse and -assembly (total 10 = old account cap; TP pool max 5/instance → ≤50 conns). Terraform (AA-824 / inf-824) must encode reserved 5 each until the TP pool max 1 lands, then raise.
- Data standards v1.0 written (wf_7f34466b-0c8): docs/architecture/data-standards/{README,01-engineering,02-data-management,03-scaling}.md + ADR 0008 + ADR 0003a (uncommitted, go in the S237 root PR). Artifact 'AA Data Platform Standards' published: https://claude.ai/artifact/R1YLp4i1QCt3kjnKd6yvvJ (private).
- bk-009 (AA-679 trip_plans) migration-only Booking #11 → Infra #116 → DB Migrate apply 04:28:06Z. Booking #12 (AA-679 code) merged → deploy :10 COMPLETED, /booking/health schema_version bk-009.
- 231 (AA-791 content_piece_label) CIS #734 → Infra #117 → apply 04:29:28Z. CIS #735 (AA-791 code) hit a PieceDrawer.tsx import conflict after #731/#732/#733 → resolved (keep PieceLabelSection + TenantCopyNotice), train re-run for #735 then AA-668.
- Bilingual EN/VI artifact published to the same URL (version 2; toggle Tiếng Việt / English / Song ngữ, default vi).
- TP #77 (AA-812 PDP polish) merged 27a661c. Preview UI verify impossible: Vercel Preview target has NO BROWSE_API_URL / TRIP_API_URL / TRIPPLANNER_API_KEY (only production + development) → every TP preview 500s on data pages (pre-existing; not caused by the PR). Verify on production instead. Nghiệp to add the Preview env vars by hand (underscore env vars).
- CIS #735 (AA-791) deployed api :605 / worker :161; CIS #737 (AA-668) deployed api :606 / worker :162 (dev-55d9aa3), /health 200.
- Vercel TP Preview env (Nghiệp approved "làm luôn"): BROWSE_API_URL / TRIP_API_URL / TRIPPLANNER_API_KEY development vars now also target preview; NEXT_PUBLIC_MAPBOX_TOKEN production var now also targets preview (values never read; the env-file lookup was classifier-blocked as credential materialization, so the target-only edit was used).
- 229 (AA-817) CIS #736 migration-only (UI smoke failed twice on the AA-752 rail-collapse test — same flake as #730, unrelated) → Infra #118 → DB Migrate check + apply 05:10:15Z, all 5 guards passed. Probe after 229 (aa817/probe-after-229.json) as aa_app_user: foreign/empty/master 0 rows on angle_gate_request, content_piece, tenant_tour_versions; own 6/74/8; facts platform row only; default ACL to aa_app_user empty.
- CIS #738 AA-817 code (tenant latest-piece reads, flag aa817:content_piece_reads_pool default off, fail closed 503) → train.
- Batch 3 (wf_ad25d013-d6f) done: 9 slices, all approve_after_fixes; review fixes in the heads. Lessons from cis-229 (SET ROLE vs session_user, global conftest stand-in) added to aa-lessons.
- CIS #738 AA-817 code deployed api :608 / worker :164 (dev-1eb2dd0); route 401 without token; flag aa817:content_piece_reads_pool OFF.
- TP #78 slice 6b (rebased on #77) merged 1a46faa, Deploy Lambdas green, prod pages 200. Preview of #78 rendered data → Preview env fix verified. Dev parity Laos legacy vs cis (aa712-6b/): cis coverage far better (graph 45 vs 4 tours, tour-route 46/46 vs 27), latency worse (routes ~1 s vs 40 ms, tiles 1 s vs 0.12 s, destination detail 3.6 s vs 0.85 s) → keep legacy until L4.
- ECS exec output truncation (SSM) → exec_s3out.sh uploads runner stdout to S3 (lesson).
- Lane X (laneX.sh): 233 CIS #739 → Infra #119 → apply 05:51:59Z; live checks OK (range-predicate view, 16 cols, llm_call_daily + tenant_api_usage_monthly, indexes valid). Code PR #740 in train; then bk-010, Infra 824 (targeted apply with delete guard), 807n, 818 (round-1 apply deferred to NS switch).
- UI verify workflow wf_dd57cfa2-340 (4 areas × verify + refute, 2 at a time, read-only).

## Part 2 (15/10 afternoon) — the 7 follow-ups after the first report
- NS Namecheap → Route 53 (Nghiệp). Pre-switch parity 10/10; panel showed extra records: acp/langfuse (not needed, #126 reverted by #127), www/api dead (#128 destroyed), 6 ACM CNAMEs of unused acc1 certs (4 certs deleted). Public resolvers on awsdns; MX/api-cis/aa-cis OK.
- AA-818: ACM round 1 (6 add) → both certs ISSUED; round 2 (#130, 9 add) → api-booking / api-tripplanner / tripplanner.lumiguides.it.com live. SES: verified + DKIM SUCCESS, MAIL FROM pending (DNS correct); production access requested (PENDING).
- AA-824 Done: RDS reboot now (t4g.small, pg15 group in-sync, max_connections 181), mig 234 (pg_stat_statements + CONNECTION LIMIT tp 30 / bk 15 / aa_app_user 15), application_name per pool (CIS #742, Booking #15, TP #80) verified in pg_stat_activity.
- AA-807 N1 live: ROOT_REPO_DOCS_TOKEN (Nghiệp) → DB Schema Dump publish → root PR #73 merged.
- Mapbox token tripplanner-frontend: + tripplanner.lumiguides.it.com (wildcards refused); /plan map renders on the new domain.
- AA-815 Done: TasteWP test site (Nghiệp), round trip on terra-family (atlas-hearth key rotated by Nghiệp 07:11Z): publish → live → unpublish → 404 + WP trash → disconnect; FB fake token classified error. Temp secret deleted.
- AA-819: CTA review warning + admin bell (CIS #743), AA-820 Q14 (root #74); Zalo draft for Ms. Thư kept by Nghiệp.
- /admin/api-docs (CIS #744; review found + fixed a pre-existing BFF path-traversal with the admin secret attached). CI-only failure: newest FastAPI nests included routers (_IncludedRouter) → route-order test made behavioural.
- E2E tenant key sync (Infra #131 IAM Describe+PutSecretValue on aa-cis/dev/e2e-tenant/*, CIS #745): live rotate of atlas-hearth → test_secret_sync=synced, login 200.
- AA-810 Done (maker e2e, self-approve 403, checker Nghiệp, EUR quote 1,410). AA-793 Done earlier.
- TrueIDC activated the 5 cost allocation tags; Budgets can be created on 005097885195 (data in ~24 h).
- Session process: aa-session skill 4b + steering — draft Jira updates for Nghiệp's approval at session end (jira-drafts.md).
